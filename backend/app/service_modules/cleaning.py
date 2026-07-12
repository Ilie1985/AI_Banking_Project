import pandas as pd


TRANSACTION_COLUMNS = [
    "date",
    "description",
    "amount",
    "transaction_type",
    "category",
    "payment_method",
    "source",
]

TRANSACTION_METADATA_COLUMNS = [
    "id",
    "created_at",
]


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
    value = str(value).strip()

    if value == "" or value.lower() in ["nan", "none", "null"]:
        return None

    try:
        converted = pd.to_datetime(value, format="%Y-%m-%d", errors="raise")
        return converted.strftime("%Y-%m-%d")
    except Exception:
        pass

    converted = pd.to_datetime(value, errors="coerce", dayfirst=True)

    if pd.isna(converted):
        return None

    return converted.strftime("%Y-%m-%d")


def normalise_transaction_dataframe(df, default_source):
    if df.empty:
        return pd.DataFrame(columns=TRANSACTION_COLUMNS + TRANSACTION_METADATA_COLUMNS)

    for column in TRANSACTION_COLUMNS:
        if column not in df.columns:
            if column == "date":
                df[column] = None
            elif column == "description":
                df[column] = "No description"
            elif column == "amount":
                df[column] = 0
            elif column == "transaction_type":
                df[column] = "expense"
            elif column == "category":
                df[column] = "Uncategorised"
            elif column == "payment_method":
                df[column] = default_source
            elif column == "source":
                df[column] = default_source

    for column in TRANSACTION_METADATA_COLUMNS:
        if column not in df.columns:
            df[column] = None

    return df[TRANSACTION_COLUMNS + TRANSACTION_METADATA_COLUMNS]