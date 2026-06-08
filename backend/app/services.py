import io
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score

from app.database import get_connection, add_audit_log


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CLEANED_DIR = DATA_DIR / "cleaned"
RAW_DIR = DATA_DIR / "raw"


TRANSACTION_COLUMNS = [
    "date",
    "description",
    "amount",
    "transaction_type",
    "category",
    "payment_method",
    "source",
]


# -----------------------------
# Cleaning helper functions
# -----------------------------

def standardise_transaction_type(value, amount=None):
    value = str(value).strip().lower()

    if value in ["income", "credit", "deposit", "salary", "in"]:
        return "income"

    if value in ["expense", "debit", "withdrawal", "payment", "out"]:
        return "expense"

    if amount is not None:
        try:
            amount = float(amount)

            if amount < 0:
                return "expense"

            return "income"
        except ValueError:
            return "expense"

    return "expense"


def clean_amount(value):
    value = str(value)
    value = value.replace("£", "")
    value = value.replace("$", "")
    value = value.replace(",", "")
    value = value.strip()

    try:
        return abs(float(value))
    except ValueError:
        return 0.0


def clean_category(value):
    value = str(value).strip()

    if value == "" or value.lower() in ["nan", "none", "null"]:
        return "Uncategorised"

    return value.title()


def clean_description(value):
    value = str(value).strip()

    if value == "" or value.lower() in ["nan", "none", "null"]:
        return "No description"

    return value


def clean_date(value):
    converted = pd.to_datetime(value, errors="coerce", dayfirst=True)

    if pd.isna(converted):
        return None

    return converted.strftime("%Y-%m-%d")


# -----------------------------
# Dataset mode functions
# -----------------------------

def get_active_dataset_setting_name(user_id):
    return f"active_dataset:{user_id}"


def get_active_dataset_mode(user_id):
    setting_name = get_active_dataset_setting_name(user_id)

    connection = get_connection()

    row = connection.execute(
        """
        SELECT setting_value
        FROM app_settings
        WHERE setting_name = ?
        """,
        (setting_name,),
    ).fetchone()

    connection.close()

    if row is None:
        return "mock"

    return row["setting_value"]


def set_active_dataset_mode(mode, user_id):
    allowed_modes = ["mock", "uploaded", "manual", "combined"]

    if mode not in allowed_modes:
        raise ValueError(
            "Invalid dataset mode. Choose one of: mock, uploaded, manual, combined."
        )

    setting_name = get_active_dataset_setting_name(user_id)

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO app_settings (
            setting_name,
            setting_value
        )
        VALUES (?, ?)
        ON CONFLICT(setting_name)
        DO UPDATE SET setting_value = excluded.setting_value
        """,
        (setting_name, mode),
    )

    connection.commit()
    connection.close()

    add_audit_log(
        action="SWITCH",
        record_type="dataset_mode",
        user_id=user_id,
        record_id=None,
        source=mode,
        details=f"Application switched to {mode} data mode.",
    )

    return {
        "message": f"The app is now using {mode} data mode.",
        "active_dataset": mode,
        "changed": True,
    }


def count_mock_transactions():
    mock_df = load_demo_transactions()
    return int(len(mock_df))


def count_uploaded_transactions(user_id):
    connection = get_connection()

    row = connection.execute(
        """
        SELECT COUNT(*) AS total
        FROM uploaded_transactions
        WHERE user_id = ?
        """,
        (user_id,),
    ).fetchone()

    connection.close()

    return int(row["total"])


def count_manual_transactions(user_id):
    connection = get_connection()

    row = connection.execute(
        """
        SELECT COUNT(*) AS total
        FROM manual_transactions
        WHERE user_id = ?
        """,
        (user_id,),
    ).fetchone()

    connection.close()

    return int(row["total"])


def switch_dataset_mode(mode, user_id):
    mode = str(mode).strip().lower()

    if mode == "uploaded" and count_uploaded_transactions(user_id) == 0:
        return {
            "message": "No uploaded CSV data is available for your account. Upload a CSV before using uploaded mode.",
            "active_dataset": get_active_dataset_mode(user_id),
            "changed": False,
        }

    if mode == "manual" and count_manual_transactions(user_id) == 0:
        return {
            "message": "No manual transactions are available for your account. Add manual transactions before using manual mode.",
            "active_dataset": get_active_dataset_mode(user_id),
            "changed": False,
        }

    return set_active_dataset_mode(mode, user_id)


def get_data_status(user_id):
    active_dataset = get_active_dataset_mode(user_id)
    mock_count = count_mock_transactions()
    uploaded_count = count_uploaded_transactions(user_id)
    manual_count = count_manual_transactions(user_id)

    messages = {
        "mock": "The app is using the original mock/demo dataset.",
        "uploaded": "The app is using your uploaded CSV data only.",
        "manual": "The app is using your manually added transactions only.",
        "combined": "The app is using mock data, your uploaded CSV data and your manual transactions together.",
    }

    return {
        "active_dataset": active_dataset,
        "mock_transactions": mock_count,
        "uploaded_transactions": uploaded_count,
        "manual_transactions": manual_count,
        "available_modes": ["mock", "uploaded", "manual", "combined"],
        "message": messages.get(active_dataset, "Unknown data mode."),
    }


# -----------------------------
# Load transaction data
# -----------------------------

def load_demo_transactions():
    cleaned_file = CLEANED_DIR / "personal_transactions_cleaned.csv"
    raw_file = RAW_DIR / "personal_transactions.csv"

    if cleaned_file.exists():
        df = pd.read_csv(cleaned_file)
    elif raw_file.exists():
        df = pd.read_csv(raw_file)
    else:
        return pd.DataFrame(columns=TRANSACTION_COLUMNS)

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
        lambda row: standardise_transaction_type(row["transaction_type"], row["amount"]),
        axis=1,
    )
    df["category"] = df["category"].apply(clean_category)
    df["description"] = df["description"].apply(clean_description)
    df["payment_method"] = df["payment_method"].fillna("Mock data")
    df["source"] = "mock"

    return df[TRANSACTION_COLUMNS]


def load_manual_transactions(user_id):
    connection = get_connection()

    df = pd.read_sql_query(
        """
        SELECT
            date,
            description,
            amount,
            transaction_type,
            category,
            payment_method,
            source
        FROM manual_transactions
        WHERE user_id = ?
        """,
        connection,
        params=(user_id,),
    )

    connection.close()

    if df.empty:
        return pd.DataFrame(columns=TRANSACTION_COLUMNS)

    return df


def load_uploaded_transactions(user_id):
    connection = get_connection()

    df = pd.read_sql_query(
        """
        SELECT
            date,
            description,
            amount,
            transaction_type,
            category,
            payment_method,
            source
        FROM uploaded_transactions
        WHERE user_id = ?
        """,
        connection,
        params=(user_id,),
    )

    connection.close()

    if df.empty:
        return pd.DataFrame(columns=TRANSACTION_COLUMNS)

    return df


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
        return pd.DataFrame(columns=TRANSACTION_COLUMNS + ["month"])

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])

    if df.empty:
        return pd.DataFrame(columns=TRANSACTION_COLUMNS + ["month"])

    df["month"] = df["date"].dt.to_period("M").astype(str)
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
    df["category"] = df["category"].apply(clean_category)
    df["description"] = df["description"].apply(clean_description)
    df["transaction_type"] = df["transaction_type"].apply(standardise_transaction_type)

    return df


# -----------------------------
# Create manual data
# -----------------------------

def create_manual_transaction(transaction, user_id):
    cleaned_date = clean_date(transaction.date)

    if cleaned_date is None:
        raise ValueError("Invalid transaction date.")

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO manual_transactions (
            user_id,
            date,
            description,
            amount,
            transaction_type,
            category,
            payment_method,
            source
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            cleaned_date,
            clean_description(transaction.description),
            clean_amount(transaction.amount),
            standardise_transaction_type(transaction.transaction_type, transaction.amount),
            clean_category(transaction.category),
            transaction.payment_method or "Manual",
            "manual",
        ),
    )

    record_id = cursor.lastrowid
    connection.commit()
    connection.close()

    add_audit_log(
        action="CREATE",
        record_type="manual_transaction",
        user_id=user_id,
        record_id=record_id,
        source="manual",
        details=f"Manual transaction added: {transaction.description}",
    )

    return {"message": "Manual transaction saved successfully", "id": record_id}


def create_budget(budget, user_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO budgets (
            user_id,
            month,
            monthly_income,
            category,
            budget_amount,
            source
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            budget.month,
            budget.monthly_income,
            clean_category(budget.category),
            budget.budget_amount,
            "manual",
        ),
    )

    record_id = cursor.lastrowid
    connection.commit()
    connection.close()

    add_audit_log(
        action="CREATE",
        record_type="budget",
        user_id=user_id,
        record_id=record_id,
        source="manual",
        details=f"Budget added for {budget.category}",
    )

    return {"message": "Budget saved successfully", "id": record_id}


# -----------------------------
# Dashboard
# -----------------------------

def get_dashboard(user_id):
    df = get_all_transactions(user_id)
    active_dataset = get_active_dataset_mode(user_id)

    if df.empty:
        return {
            "active_dataset": active_dataset,
            "total_income": 0,
            "total_expenses": 0,
            "net_savings": 0,
            "transaction_count": 0,
            "spending_by_category": [],
            "monthly_spending_trend": [],
            "source_summary": [],
            "message": (
                "No transaction data is available for the selected data mode. "
                "Choose mock data, upload a CSV, or add manual transactions."
            ),
        }

    income_df = df[df["transaction_type"] == "income"]
    expense_df = df[df["transaction_type"] == "expense"]

    total_income = float(income_df["amount"].sum())
    total_expenses = float(expense_df["amount"].sum())
    net_savings = total_income - total_expenses

    spending_by_category = (
        expense_df.groupby("category")["amount"]
        .sum()
        .reset_index()
        .sort_values("amount", ascending=False)
        .to_dict(orient="records")
    )

    monthly_spending_trend = (
        expense_df.groupby("month")["amount"]
        .sum()
        .reset_index()
        .sort_values("month")
        .to_dict(orient="records")
    )

    source_summary = (
        df.groupby("source")
        .size()
        .reset_index(name="count")
        .to_dict(orient="records")
    )

    return {
        "active_dataset": active_dataset,
        "total_income": round(total_income, 2),
        "total_expenses": round(total_expenses, 2),
        "net_savings": round(net_savings, 2),
        "transaction_count": int(len(df)),
        "spending_by_category": spending_by_category,
        "monthly_spending_trend": monthly_spending_trend,
        "source_summary": source_summary,
        "message": f"Dashboard generated using {active_dataset} data mode.",
    }


# -----------------------------
# Budget tracker
# -----------------------------

def get_budget_summary(user_id):
    df = get_all_transactions(user_id)

    connection = get_connection()
    budgets_df = pd.read_sql_query(
        """
        SELECT *
        FROM budgets
        WHERE user_id = ?
        """,
        connection,
        params=(user_id,),
    )
    connection.close()

    if budgets_df.empty:
        return {
            "monthly_income": 0,
            "total_budget": 0,
            "spent_so_far": 0,
            "remaining_money": 0,
            "safe_daily_spending": 0,
            "category_budgets": [],
            "message": "No manual budget has been added yet for your account.",
        }

    latest_month = budgets_df["month"].max()
    latest_budget_df = budgets_df[budgets_df["month"] == latest_month]

    monthly_income = float(latest_budget_df["monthly_income"].max())
    total_budget = float(latest_budget_df["budget_amount"].sum())

    if df.empty:
        expense_df = pd.DataFrame(columns=df.columns)
    else:
        expense_df = df[
            (df["transaction_type"] == "expense")
            & (df["month"] == latest_month)
        ]

    spent_so_far = float(expense_df["amount"].sum())
    remaining_money = monthly_income - spent_so_far

    category_spending = (
        expense_df.groupby("category")["amount"]
        .sum()
        .reset_index()
        .rename(columns={"amount": "spent"})
    )

    merged = latest_budget_df.merge(
        category_spending,
        on="category",
        how="left",
    )

    merged["spent"] = merged["spent"].fillna(0)
    merged["remaining"] = merged["budget_amount"] - merged["spent"]

    def budget_status(row):
        if row["spent"] > row["budget_amount"]:
            return "Over budget"

        if row["spent"] >= row["budget_amount"] * 0.8:
            return "Close to limit"

        return "Healthy"

    merged["status"] = merged.apply(budget_status, axis=1)

    safe_daily_spending = remaining_money / 30 if remaining_money > 0 else 0

    return {
        "month": latest_month,
        "monthly_income": round(monthly_income, 2),
        "total_budget": round(total_budget, 2),
        "spent_so_far": round(spent_so_far, 2),
        "remaining_money": round(remaining_money, 2),
        "safe_daily_spending": round(safe_daily_spending, 2),
        "category_budgets": merged[
            ["category", "budget_amount", "spent", "remaining", "status"]
        ].to_dict(orient="records"),
        "message": "Budget summary generated using your selected active transaction dataset.",
    }


# -----------------------------
# Spending analysis
# -----------------------------

def get_spending_analysis(user_id):
    df = get_all_transactions(user_id)
    active_dataset = get_active_dataset_mode(user_id)

    if df.empty:
        return {
            "active_dataset": active_dataset,
            "average_monthly_spending": 0,
            "highest_spending_month": None,
            "lowest_spending_month": None,
            "top_categories": [],
            "monthly_analysis": [],
            "source_summary": [],
            "message": (
                "No spending analysis is available because the selected data mode has no transactions."
            ),
        }

    expense_df = df[df["transaction_type"] == "expense"]

    monthly = (
        expense_df.groupby("month")["amount"]
        .sum()
        .reset_index()
        .sort_values("month")
    )

    if monthly.empty:
        highest_month = None
        lowest_month = None
        average_monthly_spending = 0
    else:
        highest_row = monthly.loc[monthly["amount"].idxmax()]
        lowest_row = monthly.loc[monthly["amount"].idxmin()]

        highest_month = {
            "month": highest_row["month"],
            "amount": round(float(highest_row["amount"]), 2),
        }

        lowest_month = {
            "month": lowest_row["month"],
            "amount": round(float(lowest_row["amount"]), 2),
        }

        average_monthly_spending = round(float(monthly["amount"].mean()), 2)

    top_categories = (
        expense_df.groupby("category")["amount"]
        .sum()
        .reset_index()
        .sort_values("amount", ascending=False)
        .head(10)
        .to_dict(orient="records")
    )

    source_summary = (
        df.groupby("source")
        .agg(
            transaction_count=("amount", "count"),
            total_amount=("amount", "sum"),
        )
        .reset_index()
        .to_dict(orient="records")
    )

    return {
        "active_dataset": active_dataset,
        "average_monthly_spending": average_monthly_spending,
        "highest_spending_month": highest_month,
        "lowest_spending_month": lowest_month,
        "top_categories": top_categories,
        "monthly_analysis": monthly.to_dict(orient="records"),
        "source_summary": source_summary,
        "message": f"Spending analysis generated using {active_dataset} data mode.",
    }


# -----------------------------
# Forecast
# -----------------------------

def get_forecast(user_id):
    df = get_all_transactions(user_id)
    active_dataset = get_active_dataset_mode(user_id)

    if df.empty:
        return {
            "message": (
                "No transaction data is available for the selected data mode. "
                "Choose mock data, upload a CSV, or add manual transactions."
            ),
            "prediction": None,
            "mae": None,
            "r2_score": None,
            "chart_data": [],
            "active_dataset": active_dataset,
            "forecast_ready": False,
        }

    expense_df = df[df["transaction_type"] == "expense"]

    monthly = (
        expense_df.groupby("month")["amount"]
        .sum()
        .reset_index()
        .sort_values("month")
    )

    if len(monthly) < 6:
        chart_data = []

        for _, row in monthly.iterrows():
            chart_data.append(
                {
                    "month": row["month"],
                    "actual": round(float(row["amount"]), 2),
                    "predicted": None,
                }
            )

        return {
            "message": (
                f"The selected data mode is '{active_dataset}', but it only has "
                f"{len(monthly)} month(s) of expense history. At least 6 months "
                "are recommended for a more meaningful ML forecast. Use mock data "
                "for demonstration or add/upload more transaction history."
            ),
            "prediction": None,
            "mae": None,
            "r2_score": None,
            "chart_data": chart_data,
            "active_dataset": active_dataset,
            "forecast_ready": False,
        }

    monthly["month_number"] = np.arange(len(monthly))

    X = monthly[["month_number"]]
    y = monthly["amount"]

    model = LinearRegression()
    model.fit(X, y)

    monthly["predicted"] = model.predict(X)

    next_month_number = np.array([[len(monthly)]])
    next_prediction = float(model.predict(next_month_number)[0])

    mae = float(mean_absolute_error(y, monthly["predicted"]))
    r2 = float(r2_score(y, monthly["predicted"])) if len(monthly) > 1 else 0.0

    chart_data = []

    for _, row in monthly.iterrows():
        chart_data.append(
            {
                "month": row["month"],
                "actual": round(float(row["amount"]), 2),
                "predicted": round(float(row["predicted"]), 2),
            }
        )

    chart_data.append(
        {
            "month": "Next month",
            "actual": None,
            "predicted": round(next_prediction, 2),
        }
    )

    explanation = (
        f"The app is using '{active_dataset}' data mode. The model predicts that "
        f"next month's spending may be around £{next_prediction:.2f}. The MAE is "
        f"£{mae:.2f}, meaning predictions are usually around this amount away from "
        "the real monthly spending values."
    )

    return {
        "message": explanation,
        "prediction": round(next_prediction, 2),
        "mae": round(mae, 2),
        "r2_score": round(r2, 3),
        "chart_data": chart_data,
        "active_dataset": active_dataset,
        "forecast_ready": True,
    }


# -----------------------------
# Insights
# -----------------------------

def get_insights(user_id):
    dashboard = get_dashboard(user_id)
    budget = get_budget_summary(user_id)
    forecast = get_forecast(user_id)
    analysis = get_spending_analysis(user_id)
    active_dataset = get_active_dataset_mode(user_id)

    insights = []

    if dashboard["transaction_count"] == 0:
        insights.append(
            "No transactions are available in the selected data mode. Choose mock data, upload a CSV, or add manual transactions."
        )
    elif dashboard["total_expenses"] > dashboard["total_income"]:
        insights.append(
            "Your expenses are currently higher than your income. Consider reducing non-essential spending."
        )
    else:
        insights.append(
            "Your income is higher than your expenses, which is a positive sign for savings."
        )

    if dashboard["spending_by_category"]:
        top_category = dashboard["spending_by_category"][0]
        insights.append(
            f"Your highest spending category is {top_category['category']} at £{top_category['amount']:.2f}."
        )

    for category in budget.get("category_budgets", []):
        if category["status"] == "Over budget":
            insights.append(
                f"You are over budget in {category['category']}. You have spent £{category['spent']:.2f} against a budget of £{category['budget_amount']:.2f}."
            )
        elif category["status"] == "Close to limit":
            insights.append(
                f"You are close to your budget limit in {category['category']}. Monitor this category carefully."
            )

    if budget.get("safe_daily_spending", 0) > 0:
        insights.append(
            f"Your safe daily spending allowance is about £{budget['safe_daily_spending']:.2f}."
        )

    if forecast.get("forecast_ready") is True:
        insights.append(
            f"Based on the selected dataset, next monthly spending may be around £{forecast['prediction']:.2f}."
        )
    else:
        insights.append(
            forecast.get(
                "message",
                "A forecast cannot be generated yet because there is not enough monthly history.",
            )
        )

    if analysis.get("average_monthly_spending", 0) > 0:
        insights.append(
            f"Your average monthly spending is £{analysis['average_monthly_spending']:.2f}."
        )

    return {
        "active_dataset": active_dataset,
        "insights": insights,
        "summary": f"These insights are generated using {active_dataset} data mode.",
    }


# -----------------------------
# Transactions
# -----------------------------

def get_transactions(user_id, limit=100):
    df = get_all_transactions(user_id)

    if df.empty:
        return []

    df = df.sort_values("date", ascending=False).head(limit)
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


# -----------------------------
# CSV upload
# -----------------------------

def upload_csv_transactions(
    file_bytes,
    date_column,
    description_column,
    amount_column,
    type_column,
    category_column,
    user_id,
    payment_method_column=None,
):
    df = pd.read_csv(io.BytesIO(file_bytes))

    required_columns = [
        date_column,
        description_column,
        amount_column,
        category_column,
    ]

    for column in required_columns:
        if column not in df.columns:
            raise ValueError(f"Column '{column}' was not found in the uploaded CSV.")

    cleaned_rows = []

    for _, row in df.iterrows():
        date_value = clean_date(row[date_column])

        if date_value is None:
            continue

        amount_value = clean_amount(row[amount_column])

        if type_column and type_column in df.columns:
            transaction_type = standardise_transaction_type(row[type_column], amount_value)
        else:
            transaction_type = standardise_transaction_type("", amount_value)

        if payment_method_column and payment_method_column in df.columns:
            payment_method = str(row[payment_method_column])
        else:
            payment_method = "Uploaded CSV"

        cleaned_rows.append(
            (
                user_id,
                date_value,
                clean_description(row[description_column]),
                amount_value,
                transaction_type,
                clean_category(row[category_column]),
                payment_method,
                "uploaded",
            )
        )

    if len(cleaned_rows) == 0:
        raise ValueError(
            "The uploaded CSV could not be used because no valid transaction rows were found."
        )

    connection = get_connection()
    cursor = connection.cursor()

    # A new uploaded CSV replaces the previous uploaded CSV for this user only.
    cursor.execute(
        """
        DELETE FROM uploaded_transactions
        WHERE user_id = ?
        """,
        (user_id,),
    )

    cursor.executemany(
        """
        INSERT INTO uploaded_transactions (
            user_id,
            date,
            description,
            amount,
            transaction_type,
            category,
            payment_method,
            source
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        cleaned_rows,
    )

    connection.commit()
    connection.close()

    set_active_dataset_mode("uploaded", user_id)

    add_audit_log(
        action="UPLOAD",
        record_type="uploaded_transactions",
        user_id=user_id,
        record_id=None,
        source="uploaded",
        details=(
            f"{len(cleaned_rows)} transactions uploaded, cleaned, mapped and "
            f"set as the active dataset."
        ),
    )

    return {
        "message": "CSV uploaded, cleaned and set as the active dataset.",
        "rows_uploaded": len(cleaned_rows),
        "active_dataset": "uploaded",
    }


# -----------------------------
# Audit log
# -----------------------------

def get_audit_log(user_id):
    connection = get_connection()

    rows = connection.execute(
        """
        SELECT
            id,
            action,
            record_type,
            record_id,
            source,
            details,
            created_at
        FROM audit_log
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 100
        """,
        (user_id,),
    ).fetchall()

    connection.close()

    return [dict(row) for row in rows]