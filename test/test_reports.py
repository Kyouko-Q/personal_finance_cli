from src.transactions import (
    add_transaction,
)

from src.reports import (
    filter_transactions,
    monthly_summary
)

def test_filter_by_category(conn):
    add_transaction(conn, "2026-08-01", 20, "food")
    add_transaction(conn, "2026-08-02", 50, "transport")
    add_transaction(conn, "2026-08-03", 30, "food")

    rows = filter_transactions(conn, category="food")

    assert len(rows) == 2
    assert all(row["category"] == "food" for row in rows)

def test_filter_by_date_range(conn):
    add_transaction(conn, "2026-08-01", 20, "food")
    add_transaction(conn, "2026-08-15", 50, "food")
    add_transaction(conn, "2026-08-30", 30, "food")

    rows = filter_transactions(
        conn,
        date_from="2026-08-10",
        date_to="2026-08-20"
    )

    assert len(rows) == 1
    assert rows[0]["amount"] == 50

def test_monthly_summary(conn):
    add_transaction(conn, "2026-08-01", 20, "food")
    add_transaction(conn, "2026-08-02", 30, "food")
    add_transaction(conn, "2026-08-03", 50, "transport")

    rows, grand_total = monthly_summary(conn, "2026-08")

    assert grand_total == 100

    # First category should be transport because 50 > 20 + 30
    assert rows[0]["category"] == "transport"
    assert rows[0]["total"] == 50
    assert rows[0]["count"] == 1

    assert rows[1]["category"] == "food"
    assert rows[1]["total"] == 50
    assert rows[1]["count"] == 2

def test_monthly_summary_empty(conn):
    rows, grand_total = monthly_summary(conn, "2026-08")

    assert rows == []
    assert grand_total == 0

def test_filter_by_category_and_date(conn):
    add_transaction(conn, "2026-08-01", 20, "food")
    add_transaction(conn, "2026-08-15", 50, "food")
    add_transaction(conn, "2026-08-20", 30, "transport")
    add_transaction(conn, "2026-08-25", 40, "food")

    rows = filter_transactions(
        conn,
        category="food",
        date_from="2026-08-10",
        date_to="2026-08-20"
    )

    assert len(rows) == 1
    assert rows[0]["amount"] == 50