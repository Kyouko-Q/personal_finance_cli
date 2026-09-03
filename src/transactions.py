# transactions.py
def add_transaction(conn, date, amount, category, description=""):
    cur = conn.execute(
        "INSERT INTO transactions (date, amount, category, description) VALUES (?, ?, ?, ?)",
        (date, amount, category, description)
    )
    conn.commit()
    return cur.lastrowid

def delete_transaction(conn, txn_id):
    cur = conn.execute("DELETE FROM transactions WHERE id = ?", (txn_id,))
    conn.commit()
    return cur.rowcount  # 0 means "no such id" — use this for error handling

def edit_transaction(conn, txn_id, **fields):
    # fields might be {"amount": 42.50, "category": "groceries"}
    if not fields:
        return 0
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [txn_id]
    cur = conn.execute(f"UPDATE transactions SET {set_clause} WHERE id = ?", values)
    conn.commit()
    return cur.rowcount