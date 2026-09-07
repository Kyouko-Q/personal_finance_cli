from flask import Flask, jsonify, request, g

from .db import get_connection
from .reports import filter_transactions


app = Flask(__name__)

DB_PATH = "finance.db"


def get_db():
    if "db" not in g:
        g.db = get_connection(DB_PATH)

    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)

    if db is not None:
        db.close()


def row_to_dict(row):
    return {k: row[k] for k in row.keys()}


@app.route("/transactions", methods=["GET"])
def list_transactions():
    conn = get_db()

    rows = filter_transactions(
        conn,
        category=request.args.get("category"),
        date_from=request.args.get("from"),
        date_to=request.args.get("to"),
    )

    return jsonify([
        row_to_dict(row)
        for row in rows
    ])


@app.route("/transactions/<int:txn_id>", methods=["GET"])
def get_transaction(txn_id):
    conn = get_db()

    row = conn.execute(
        "SELECT * FROM transactions WHERE id = ?",
        (txn_id,)
    ).fetchone()

    if row is None:
        return jsonify({"error": "not found"}), 404

    return jsonify(row_to_dict(row))


if __name__ == "__main__":
    app.run(debug=True, port=5000)