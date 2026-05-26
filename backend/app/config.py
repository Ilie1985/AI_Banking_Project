from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
CLEANED_DATA_DIR = DATA_DIR / "cleaned"
DATABASE_DIR = BASE_DIR / "database"
DATABASE_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_PATH = DATABASE_DIR / "ai_banking.sqlite3"
TRANSACTIONS_CSV = CLEANED_DATA_DIR / "personal_transactions_cleaned.csv"
BUDGET_CSV = CLEANED_DATA_DIR / "budget_cleaned.csv"
