import sqlite3
import pytest


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

    yield conn

    conn.close()