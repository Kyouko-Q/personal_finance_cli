import sqlite3
import pytest

from src.transactions import (
    add_transaction,
    delete_transaction,
    edit_transaction,
)


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

    assert row["id"] == txn_id
    assert row["date"] == "2026-09-03"
    assert row["amount"] == 50.0
    assert row["category"] == "groceries"
    assert row["description"] == "milk"


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

    assert row["amount"] == 75.0
    assert row["category"] == "food"
    assert row["description"] == "milk"


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