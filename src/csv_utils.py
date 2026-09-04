import csv

from .transactions import (
    add_transaction
)

CSV_COLUMNS = ["date", "amount", "category", "description"]


def export_csv(conn, filepath, filtered_rows=None):
    rows = filtered_rows if filtered_rows is not None else conn.execute(
        "SELECT date, amount, category, description FROM transactions ORDER BY date"
    ).fetchall()
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_COLUMNS)
        for r in rows:
            writer.writerow([r["date"], r["amount"], r["category"], r["description"]])
    return len(rows)


def import_csv(conn, filepath):
    imported = 0
    with open(filepath, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            add_transaction(
                conn,
                date=row["date"],
                amount=float(row["amount"]),
                category=row["category"],
                description=row.get("description", "")
            )
            imported += 1
    return imported