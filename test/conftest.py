import sqlite3
import pytest

from src.api import app


@pytest.fixture
def conn():
    conn = sqlite3.connect(":memory:")

    conn.row_factory = sqlite3.Row

    conn.execute(
        """
        CREATE TABLE transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            import_hash TEXT UNIQUE
        )
        """
    )
    conn.execute("""
    CREATE TABLE recurring_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL NOT NULL,
        category TEXT NOT NULL,
        description TEXT,
        frequency TEXT NOT NULL,
        interval_count INTEGER NOT NULL DEFAULT 1,
        next_due_date TEXT NOT NULL,
        end_date TEXT,
        active INTEGER NOT NULL DEFAULT 1
    )
    """
    )

    yield conn

    conn.close()

@pytest.fixture
def client(conn):
    app.config["TESTING"] = True
    app.config["TEST_DB"] = conn

    with app.test_client() as client:
        yield client

    app.config.pop("TEST_DB", None)