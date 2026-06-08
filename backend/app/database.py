import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_DIR = BASE_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "ai_banking.sqlite3"


def get_connection():
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    return connection


def column_exists(cursor, table_name, column_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()

    for column in columns:
        if column["name"] == column_name:
            return True

    return False


def add_column_if_missing(cursor, table_name, column_name, column_definition):
    if not column_exists(cursor, table_name, column_name):
        cursor.execute(
            f"""
            ALTER TABLE {table_name}
            ADD COLUMN {column_name} {column_definition}
            """
        )


def initialise_database():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS manual_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            date TEXT NOT NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            transaction_type TEXT NOT NULL,
            category TEXT NOT NULL,
            payment_method TEXT DEFAULT 'Manual',
            source TEXT DEFAULT 'manual',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS uploaded_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            date TEXT NOT NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            transaction_type TEXT NOT NULL,
            category TEXT NOT NULL,
            payment_method TEXT DEFAULT 'Uploaded CSV',
            source TEXT DEFAULT 'uploaded',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            month TEXT NOT NULL,
            monthly_income REAL NOT NULL,
            category TEXT NOT NULL,
            budget_amount REAL NOT NULL,
            source TEXT DEFAULT 'manual',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            action TEXT NOT NULL,
            record_type TEXT NOT NULL,
            record_id INTEGER,
            source TEXT,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS app_settings (
            setting_name TEXT PRIMARY KEY,
            setting_value TEXT NOT NULL
        )
        """
    )

    # These ALTER statements make the update safe if your old database already exists.
    add_column_if_missing(cursor, "manual_transactions", "user_id", "TEXT")
    add_column_if_missing(cursor, "uploaded_transactions", "user_id", "TEXT")
    add_column_if_missing(cursor, "budgets", "user_id", "TEXT")
    add_column_if_missing(cursor, "audit_log", "user_id", "TEXT")

    connection.commit()
    connection.close()


def add_audit_log(
    action,
    record_type,
    user_id,
    record_id=None,
    source=None,
    details=None,
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO audit_log (
            user_id,
            action,
            record_type,
            record_id,
            source,
            details
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user_id, action, record_type, record_id, source, details),
    )

    connection.commit()
    connection.close()