import sqlite3
import pytest

from src.transactions import (
    add_transaction,
    delete_transaction,
    edit_transaction,
)


@pytest.fixture
def conn():
    conn = sqlite3.connect(":memory:")

    conn.execute("""
        CREATE TABLE transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT
        )
    """)

    yield conn
    conn.close()


def test_add_transaction(conn):
    txn_id = add_transaction(
        conn,
        "2026-09-03",
        50.0,
        "groceries",
        "milk"
    )

    row = conn.execute(
        "SELECT * FROM transactions WHERE id = ?",
        (txn_id,)
    ).fetchone()

    assert row == (
        txn_id,
        "2026-09-03",
        50.0,
        "groceries",
        "milk"
    )


def test_add_transaction_default_description(conn):
    txn_id = add_transaction(
        conn,
        "2026-09-03",
        100.0,
        "salary"
    )

    row = conn.execute(
        "SELECT description FROM transactions WHERE id = ?",
        (txn_id,)
    ).fetchone()

    assert row[0] == ""


def test_delete_transaction(conn):
    txn_id = add_transaction(
        conn,
        "2026-09-03",
        50.0,
        "groceries"
    )

    result = delete_transaction(conn, txn_id)

    assert result == 1

    row = conn.execute(
        "SELECT * FROM transactions WHERE id = ?",
        (txn_id,)
    ).fetchone()

    assert row is None


def test_delete_nonexistent_transaction(conn):
    result = delete_transaction(conn, 999)

    assert result == 0


def test_edit_transaction(conn):
    txn_id = add_transaction(
        conn,
        "2026-09-03",
        50.0,
        "groceries",
        "milk"
    )

    result = edit_transaction(
        conn,
        txn_id,
        amount=75.0,
        category="food"
    )

    assert result == 1

    row = conn.execute(
        "SELECT amount, category, description FROM transactions WHERE id = ?",
        (txn_id,)
    ).fetchone()

    assert row == (75.0, "food", "milk")


def test_edit_nonexistent_transaction(conn):
    result = edit_transaction(
        conn,
        999,
        amount=50.0
    )

    assert result == 0


def test_edit_transaction_with_no_fields(conn):
    txn_id = add_transaction(
        conn,
        "2026-09-03",
        50.0,
        "groceries"
    )

    result = edit_transaction(conn, txn_id)

    assert result == 0