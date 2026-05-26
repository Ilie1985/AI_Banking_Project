"""Clean the uploaded banking CSV files.

Run from the backend folder:
    python clean_data.py

Input files:
    data/raw/personal_transactions.csv
    data/raw/Budget.csv

Outputs:
    data/cleaned/personal_transactions_cleaned.csv
    data/cleaned/budget_cleaned.csv
    data/cleaned/cleaning_report.json
"""
from pathlib import Path
from datetime import datetime
import csv
import json

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "data" / "raw"
CLEANED_DIR = BASE_DIR / "data" / "cleaned"
CLEANED_DIR.mkdir(parents=True, exist_ok=True)

RAW_TRANSACTIONS = RAW_DIR / "personal_transactions.csv"
RAW_BUDGET = RAW_DIR / "Budget.csv"


def clean_text(value, default=""):
    value = "" if value is None else str(value).strip()
    return value or default


def clean_category(value):
    value = clean_text(value, "Uncategorised")
    return " ".join(word.capitalize() if not word.isupper() else word for word in value.split())


def parse_date(value):
    value = clean_text(value)
    for fmt in ["%m/%d/%Y", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%y"]:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def parse_amount(value):
    value = clean_text(value).replace("£", "").replace("$", "").replace(",", "")
    try:
        return abs(float(value))
    except ValueError:
        return None


def normalise_transaction_type(value):
    value = clean_text(value).lower()
    if value in {"credit", "income", "deposit", "salary", "paycheck"}:
        return "income"
    return "expense"


def clean_transactions():
    with RAW_TRANSACTIONS.open(newline="", encoding="utf-8-sig") as file:
        raw_rows = list(csv.DictReader(file))
    cleaned = []
    seen = set()
    invalid_rows = 0
    for row in raw_rows:
        parsed_date = parse_date(row.get("Date"))
        amount = parse_amount(row.get("Amount"))
        if parsed_date is None or amount is None:
            invalid_rows += 1
            continue
        record = {
            "date": parsed_date.isoformat(),
            "month": parsed_date.strftime("%Y-%m"),
            "year": parsed_date.year,
            "description": clean_text(row.get("Description"), "Transaction"),
            "amount": f"{amount:.2f}",
            "transaction_type": normalise_transaction_type(row.get("Transaction Type")),
            "category": clean_category(row.get("Category")),
            "payment_method": clean_text(row.get("Account Name"), "Unknown"),
            "source": "uploaded_cleaned_demo",
        }
        key = tuple(record.values())
        if key not in seen:
            seen.add(key)
            cleaned.append(record)
    cleaned.sort(key=lambda item: item["date"])
    output = CLEANED_DIR / "personal_transactions_cleaned.csv"
    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(cleaned[0].keys()))
        writer.writeheader()
        writer.writerows(cleaned)
    return raw_rows, cleaned, invalid_rows


def clean_budget():
    with RAW_BUDGET.open(newline="", encoding="utf-8-sig") as file:
        raw_rows = list(csv.DictReader(file))
    totals = {}
    for row in raw_rows:
        category = clean_category(row.get("Category"))
        amount = parse_amount(row.get("Budget")) or 0
        totals[category] = totals.get(category, 0) + amount
    cleaned = [
        {
            "month": "2018-01",
            "monthly_income": "0.00",
            "category": category,
            "budget": f"{amount:.2f}",
            "source": "uploaded_cleaned_demo",
        }
        for category, amount in sorted(totals.items())
    ]
    output = CLEANED_DIR / "budget_cleaned.csv"
    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["month", "monthly_income", "category", "budget", "source"])
        writer.writeheader()
        writer.writerows(cleaned)
    return raw_rows, cleaned


def main():
    raw_transactions, cleaned_transactions, invalid_rows = clean_transactions()
    raw_budget, cleaned_budget = clean_budget()
    report = {
        "transactions_original_rows": len(raw_transactions),
        "transactions_cleaned_rows": len(cleaned_transactions),
        "transactions_removed_rows": len(raw_transactions) - len(cleaned_transactions),
        "invalid_transaction_rows_removed": invalid_rows,
        "transaction_date_min": cleaned_transactions[0]["date"] if cleaned_transactions else None,
        "transaction_date_max": cleaned_transactions[-1]["date"] if cleaned_transactions else None,
        "budget_original_rows": len(raw_budget),
        "budget_cleaned_rows": len(cleaned_budget),
        "cleaning_steps": [
            "standardised dates",
            "converted amounts to numeric values",
            "normalised transaction types to income or expense",
            "standardised categories",
            "filled blank text fields",
            "removed duplicate rows",
            "generated cleaned CSV files for the backend",
        ],
    }
    (CLEANED_DIR / "cleaning_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
