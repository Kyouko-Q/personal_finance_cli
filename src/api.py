from flask import Flask, jsonify, request, g

from .db import get_connection
from .reports import filter_transactions
from .transactions import add_transaction, edit_transaction, delete_transaction


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



@app.route("/transactions", methods=["POST"])
def create_transaction():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "request body must be JSON"}), 400

    required = {"date", "amount", "category"}
    missing = required - data.keys()
    if missing:
        return jsonify({"error": f"missing fields: {sorted(missing)}"}), 400

    try:
        amount = float(data["amount"])
    except (TypeError, ValueError):
        return jsonify({"error": "amount must be numeric"}), 400

    conn = get_db()
    txn_id = add_transaction(
        conn, data["date"], amount, data["category"], data.get("description", "")
    )
    return jsonify({"id": txn_id}), 201

@app.route("/transactions/<int:txn_id>", methods=["PUT"])
def update_transaction(txn_id):
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "request body must be JSON"}), 400

    conn = get_db()
    updated = edit_transaction(conn, txn_id, **data)
    if updated == 0:
        return jsonify({"error": "not found"}), 404
    return jsonify({"status": "updated"})

@app.route("/transactions/<int:txn_id>", methods=["DELETE"])
def remove_transaction(txn_id):
    conn = get_db()
    deleted = delete_transaction(conn, txn_id)
    if deleted == 0:
        return jsonify({"error": "not found"}), 404
    return "", 204


if __name__ == "__main__":
    app.run(debug=True, port=5000)