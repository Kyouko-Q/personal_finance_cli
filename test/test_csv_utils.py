from src.transactions import (
    add_transaction,
)

from src.reports import (
    filter_transactions
)

from src.csv_utils import (
    export_csv
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