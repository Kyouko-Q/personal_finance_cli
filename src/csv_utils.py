import csv
import hashlib
import sqlite3


CSV_COLUMNS = [
    "date",
    "amount",
    "category",
    "description"
]


def row_hash(date, amount, category, description):
    key = (
        f"{date}|{amount}|{category}|{description}"
        .encode("utf-8")
    )

    return hashlib.sha256(key).hexdigest()


def export_csv(conn, filepath, filtered_rows=None):
    if filtered_rows is not None:
        rows = filtered_rows
    else:
        rows = conn.execute(
            """
            SELECT date, amount, category, description
            FROM transactions
            ORDER BY date
            """
        ).fetchall()

    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)

        writer.writerow(CSV_COLUMNS)

        for row in rows:
            writer.writerow([
                row["date"],
                row["amount"],
                row["category"],
                row["description"]
            ])

    return len(rows)


def import_csv(conn, filepath):
    results = {
        "imported": 0,
        "duplicates": 0,
        "malformed": []
    }

    with open(filepath, newline="") as f:
        reader = csv.DictReader(f)

        for i, row in enumerate(reader, start=2):
            try:
                date = row["date"].strip()

                amount = float(row["amount"])

                category = row["category"].strip()

                if not category:
                    raise ValueError("empty category")

                description = row.get(
                    "description",
                    ""
                ).strip()

            except (ValueError, KeyError) as e:
                results["malformed"].append(
                    (i, str(e))
                )
                continue

            h = row_hash(
                date,
                amount,
                category,
                description
            )

            try:
                conn.execute(
                    """
                    INSERT INTO transactions
                    (
                        date,
                        amount,
                        category,
                        description,
                        import_hash
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        date,
                        amount,
                        category,
                        description,
                        h
                    )
                )

                results["imported"] += 1

            except sqlite3.IntegrityError:
                results["duplicates"] += 1

    conn.commit()

    return results