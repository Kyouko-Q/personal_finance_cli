# recurring.py
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta  # pip install python-dateutil
from .transactions import add_transaction

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


def advance_date(current, frequency, interval_count):
    d = date.fromisoformat(current)
    if frequency == "daily":
        d += timedelta(days=interval_count)
    elif frequency == "weekly":
        d += timedelta(weeks=interval_count)
    elif frequency == "monthly":
        d += relativedelta(months=interval_count)
    elif frequency == "yearly":
        d += relativedelta(years=interval_count)
    return d.isoformat()

def generate_due_transactions(conn, as_of=None):
    """
    Idempotent: safe to run multiple times a day. Each due occurrence creates
    exactly one transaction, then next_due_date is advanced past 'as_of'.
    """
    as_of = as_of or date.today().isoformat()
    rules = conn.execute(
        "SELECT * FROM recurring_rules WHERE active = 1 AND next_due_date <= ?", (as_of,)
    ).fetchall()

    created = []
    for rule in rules:
        next_due = rule["next_due_date"]
        # loop in case the job hasn't run in a while and multiple occurrences are due
        while next_due <= as_of:
            if rule["end_date"] and next_due > rule["end_date"]:
                conn.execute("UPDATE recurring_rules SET active = 0 WHERE id = ?", (rule["id"],))
                break

            txn_id = add_transaction(
                conn, next_due, rule["amount"], rule["category"], rule["description"]
            )
            created.append(txn_id)
            next_due = advance_date(next_due, rule["frequency"], rule["interval_count"])

        conn.execute(
            "UPDATE recurring_rules SET next_due_date = ? WHERE id = ?",
            (next_due, rule["id"])
        )

    conn.commit()
    return created