from pathlib import Path

import pandas as pd

from app.database import (
    add_audit_log,
    insert_row,
    select_rows,
)
from app.service_modules.cleaning import (
    TRANSACTION_COLUMNS,
    TRANSACTION_METADATA_COLUMNS,
    clean_amount,
    clean_category,
    clean_date,
    clean_description,
    normalise_transaction_dataframe,
    standardise_transaction_type,
)
from app.service_modules.dataset import get_active_dataset_mode


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
CLEANED_DIR = DATA_DIR / "cleaned"
RAW_DIR = DATA_DIR / "raw"


def load_demo_transactions():
    cleaned_file = CLEANED_DIR / "personal_transactions_cleaned.csv"
    raw_file = RAW_DIR / "personal_transactions.csv"

    if cleaned_file.exists():
        df = pd.read_csv(cleaned_file)
    elif raw_file.exists():
        df = pd.read_csv(raw_file)
    else:
        return pd.DataFrame(columns=TRANSACTION_COLUMNS + TRANSACTION_METADATA_COLUMNS)

    df.columns = [column.strip().lower().replace(" ", "_") for column in df.columns]

    column_map = {}

    for column in df.columns:
        if column in ["date", "transaction_date", "posted_date"]:
            column_map[column] = "date"
        elif column in ["description", "details", "transaction_description", "memo"]:
            column_map[column] = "description"
        elif column in ["amount", "transaction_amount", "value"]:
            column_map[column] = "amount"
        elif column in ["type", "transaction_type", "income_expense"]:
            column_map[column] = "transaction_type"
        elif column in ["category", "transaction_category"]:
            column_map[column] = "category"
        elif column in ["payment_method", "method", "account"]:
            column_map[column] = "payment_method"

    df = df.rename(columns=column_map)

    for column in TRANSACTION_COLUMNS:
        if column not in df.columns:
            if column == "source":
                df[column] = "mock"
            elif column == "payment_method":
                df[column] = "Mock data"
            elif column == "transaction_type":
                df[column] = "expense"
            elif column == "category":
                df[column] = "Uncategorised"
            elif column == "description":
                df[column] = "Mock transaction"
            else:
                df[column] = None

    df["date"] = df["date"].apply(clean_date)
    df = df.dropna(subset=["date"])

    df["amount"] = df["amount"].apply(clean_amount)

    df["transaction_type"] = df.apply(
        lambda row: standardise_transaction_type(
            row["transaction_type"],
            row["amount"],
        ),
        axis=1,
    )

    df["category"] = df["category"].apply(clean_category)
    df["description"] = df["description"].apply(clean_description)
    df["payment_method"] = df["payment_method"].fillna("Mock data")
    df["source"] = "mock"

    df["id"] = None
    df["created_at"] = None

    return normalise_transaction_dataframe(df, "mock")


def load_manual_transactions(user_id):
    rows = select_rows(
        table_name="manual_transactions",
        filters={"user_id": user_id},
        order="created_at.desc",
    )

    if not rows:
        return pd.DataFrame(columns=TRANSACTION_COLUMNS + TRANSACTION_METADATA_COLUMNS)

    df = pd.DataFrame(rows)

    return normalise_transaction_dataframe(df, "manual")


def load_uploaded_transactions(user_id):
    rows = select_rows(
        table_name="uploaded_transactions",
        filters={"user_id": user_id},
        order="created_at.desc",
    )

    if not rows:
        return pd.DataFrame(columns=TRANSACTION_COLUMNS + TRANSACTION_METADATA_COLUMNS)

    df = pd.DataFrame(rows)

    return normalise_transaction_dataframe(df, "uploaded")


def count_mock_transactions():
    return int(len(load_demo_transactions()))


def count_uploaded_transactions(user_id):
    rows = select_rows(
        table_name="uploaded_transactions",
        filters={"user_id": user_id},
        columns="id",
    )

    return int(len(rows))


def count_manual_transactions(user_id):
    rows = select_rows(
        table_name="manual_transactions",
        filters={"user_id": user_id},
        columns="id",
    )

    return int(len(rows))


def get_all_transactions(user_id):
    active_dataset = get_active_dataset_mode(user_id)

    mock_df = load_demo_transactions()
    uploaded_df = load_uploaded_transactions(user_id)
    manual_df = load_manual_transactions(user_id)

    if active_dataset == "mock":
        df = mock_df
    elif active_dataset == "uploaded":
        df = uploaded_df
    elif active_dataset == "manual":
        df = manual_df
    elif active_dataset == "combined":
        df = pd.concat([mock_df, uploaded_df, manual_df], ignore_index=True)
    else:
        df = mock_df

    if df.empty:
        return pd.DataFrame(
            columns=TRANSACTION_COLUMNS + TRANSACTION_METADATA_COLUMNS + ["month"]
        )

    df = normalise_transaction_dataframe(df, active_dataset)

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])

    if df.empty:
        return pd.DataFrame(
            columns=TRANSACTION_COLUMNS + TRANSACTION_METADATA_COLUMNS + ["month"]
        )

    df["month"] = df["date"].dt.to_period("M").astype(str)
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
    df["category"] = df["category"].apply(clean_category)
    df["description"] = df["description"].apply(clean_description)
    df["transaction_type"] = df["transaction_type"].apply(standardise_transaction_type)

    return df


def create_manual_transaction(transaction, user_id):
    cleaned_date = clean_date(transaction.date)

    if cleaned_date is None:
        raise ValueError("Invalid transaction date.")

    row = {
        "user_id": user_id,
        "date": cleaned_date,
        "description": clean_description(transaction.description),
        "amount": clean_amount(transaction.amount),
        "transaction_type": standardise_transaction_type(
            transaction.transaction_type,
            transaction.amount,
        ),
        "category": clean_category(transaction.category),
        "payment_method": transaction.payment_method or "Debit Card",
        "source": "manual",
    }

    inserted = insert_row("manual_transactions", row)
    record_id = inserted["id"] if inserted else None

    add_audit_log(
        action="CREATE",
        record_type="manual_transaction",
        user_id=user_id,
        record_id=record_id,
        source="manual",
        details=f"Manual transaction added: {transaction.description}",
    )

    return {
        "message": "Manual transaction saved successfully",
        "id": record_id,
    }


def get_transactions(user_id, limit=100):
    df = get_all_transactions(user_id)

    if df.empty:
        return []

    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    if "created_at" not in df.columns:
        df["created_at"] = None

    if "id" not in df.columns:
        df["id"] = None

    df["created_at"] = pd.to_datetime(
        df["created_at"],
        errors="coerce",
        utc=True,
    )

    has_created_at_values = df["created_at"].notna().any()

    if has_created_at_values:
        df["sort_created_at"] = df["created_at"].apply(
            lambda value: value.timestamp() if pd.notna(value) else -1
        )

        df["sort_id"] = pd.to_numeric(
            df["id"],
            errors="coerce",
        ).fillna(0)

        df = df.sort_values(
            by=["sort_created_at", "sort_id", "date"],
            ascending=[False, False, False],
            na_position="last",
        )
    else:
        df = df.sort_values("date", ascending=False)

    df = df.head(limit)

    df["date"] = df["date"].dt.strftime("%Y-%m-%d")

    return df[
        [
            "date",
            "description",
            "amount",
            "transaction_type",
            "category",
            "payment_method",
            "source",
        ]
    ].to_dict(orient="records")