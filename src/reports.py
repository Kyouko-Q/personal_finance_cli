def filter_transactions(conn, category=None, date_from=None, date_to=None):
    query = "SELECT * FROM transactions WHERE 1=1"
    params = []
    if category:
        query += " AND category = ?"
        params.append(category)
    if date_from:
        query += " AND date >= ?"
        params.append(date_from)
    if date_to:
        query += " AND date <= ?"
        params.append(date_to)
    query += " ORDER BY date"
    return conn.execute(query, params).fetchall()

def monthly_summary(conn, year_month):  # "2026-08"
    rows = conn.execute(
        """SELECT category, SUM(amount) as total, COUNT(*) as count
           FROM transactions
           WHERE strftime('%Y-%m', date) = ?
           GROUP BY category
           ORDER BY total DESC""",
        (year_month,)
    ).fetchall()
    grand_total = sum(r["total"] for r in rows)
    return rows, grand_total