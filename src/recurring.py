# recurring.py
def add_recurring_rule(conn, amount, category, frequency, next_due_date,
                        description="", interval_count=1, end_date=None, user_id=None):
    if frequency not in ("daily", "weekly", "monthly", "yearly"):
        raise ValueError(f"invalid frequency: {frequency}")
    if interval_count <= 0:
        raise ValueError("interval_count must be positive")
    cur = conn.execute(
        """INSERT INTO recurring_rules
           (user_id, amount, category, description, frequency, interval_count, next_due_date, end_date)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, amount, category, description, frequency, interval_count, next_due_date, end_date)
    )
    conn.commit()
    return cur.lastrowid

def list_recurring_rules(conn, user_id=None, active_only=True):
    query = "SELECT * FROM recurring_rules WHERE 1=1"
    params = []
    if user_id is not None:
        query += " AND user_id = ?"
        params.append(user_id)
    if active_only:
        query += " AND active = 1"
    return conn.execute(query, params).fetchall()

def deactivate_recurring_rule(conn, rule_id):
    cur = conn.execute("UPDATE recurring_rules SET active = 0 WHERE id = ?", (rule_id,))
    conn.commit()
    return cur.rowcount