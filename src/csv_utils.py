import csv

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