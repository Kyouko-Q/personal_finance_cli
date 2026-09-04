import csv
import pytest

from src.transactions import (
    add_transaction,
)

from src.reports import (
    filter_transactions
)

from src.csv_utils import (
    export_csv,
    import_csv
)

def test_export_csv(conn, tmp_path):
    add_transaction(conn, "2026-08-01", 20, "food", "lunch")
    add_transaction(conn, "2026-08-02", 50, "transport", "bus")

    filepath = tmp_path / "transactions.csv"

    result = export_csv(conn, filepath)

    assert result == 2

    with open(filepath, newline="") as f:
        content = f.read()

    assert "date,amount,category,description" in content
    assert "2026-08-01,20.0,food,lunch" in content
    assert "2026-08-02,50.0,transport,bus" in content

def test_export_filtered_rows(conn, tmp_path):
    add_transaction(conn, "2026-08-01", 20, "food")
    add_transaction(conn, "2026-08-02", 50, "transport")

    rows = filter_transactions(conn, category="food")

    filepath = tmp_path / "food.csv"

    result = export_csv(conn, filepath, filtered_rows=rows)

    assert result == 1

def test_import_csv(conn, tmp_path):
    filepath = tmp_path / "transactions.csv"

    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)

        writer.writerow(["date", "amount", "category", "description"])
        writer.writerow(["2026-08-01", "20.0", "food", "lunch"])
        writer.writerow(["2026-08-02", "50.0", "transport", "bus"])

    result = import_csv(conn, filepath)

    assert result == 2

    rows = conn.execute(
        "SELECT date, amount, category, description "
        "FROM transactions ORDER BY date"
    ).fetchall()

    assert len(rows) == 2

    assert rows[0]["date"] == "2026-08-01"
    assert rows[0]["amount"] == 20.0
    assert rows[0]["category"] == "food"
    assert rows[0]["description"] == "lunch"

    assert rows[1]["date"] == "2026-08-02"
    assert rows[1]["amount"] == 50.0
    assert rows[1]["category"] == "transport"
    assert rows[1]["description"] == "bus"

def test_import_csv_without_description(conn, tmp_path):
    filepath = tmp_path / "transactions.csv"

    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)

        writer.writerow(["date", "amount", "category"])
        writer.writerow(["2026-08-01", "20.0", "food"])

    result = import_csv(conn, filepath)

    assert result == 1

    row = conn.execute(
        "SELECT * FROM transactions"
    ).fetchone()

    assert row["date"] == "2026-08-01"
    assert row["amount"] == 20.0
    assert row["category"] == "food"
    assert row["description"] == ""

def test_import_empty_csv(conn, tmp_path):
    filepath = tmp_path / "empty.csv"

    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "amount", "category", "description"])

    result = import_csv(conn, filepath)

    assert result == 0

    count = conn.execute(
        "SELECT COUNT(*) FROM transactions"
    ).fetchone()[0]

    assert count == 0

def test_import_empty_csv(conn, tmp_path):
    filepath = tmp_path / "empty.csv"

    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "amount", "category", "description"])

    result = import_csv(conn, filepath)

    assert result == 0

    count = conn.execute(
        "SELECT COUNT(*) FROM transactions"
    ).fetchone()[0]

    assert count == 0

def test_import_invalid_amount(conn, tmp_path):
    filepath = tmp_path / "bad.csv"

    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "amount", "category", "description"])
        writer.writerow(["2026-08-01", "abc", "food", "lunch"])

    with pytest.raises(ValueError):
        import_csv(conn, filepath)