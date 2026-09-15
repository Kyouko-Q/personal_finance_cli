from flask import Flask, jsonify, request, g
import re
import tempfile, os
from flask import send_file


from .db import get_connection
from .reports import filter_transactions, monthly_summary
from .transactions import add_transaction, edit_transaction, delete_transaction
from .csv_utils import import_csv, export_csv
from .recurring import generate_due_transactions
from .auth import require_auth

app = Flask(__name__)

DB_PATH = "finance.db"
MONTH_RE = re.compile(r"^\d{4}-\d{2}$")


def get_db():
    if "db" not in g:
        if "TEST_DB" in app.config:
            g.db = app.config["TEST_DB"]
        else:
            g.db = get_connection(DB_PATH)

    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)

    if db is not None and "TEST_DB" not in app.config:
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


@app.route("/summary", methods=["GET"])
def summary():
    month = request.args.get("month")
    if not month or not MONTH_RE.match(month):
        return jsonify({"error": "month must be in YYYY-MM format"}), 400

    conn = get_db()
    rows, grand_total = monthly_summary(conn, month)
    return jsonify({
        "month": month,
        "by_category": [
            {"category": r["category"], "total": r["total"], "count": r["count"]}
            for r in rows
        ],
        "grand_total": grand_total
    })

@app.route("/import", methods=["POST"])
def api_import_csv():
    if "file" not in request.files:
        return jsonify({"error": "no file field named 'file'"}), 400

    upload = request.files["file"]
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        upload.save(tmp.name)
        tmp_path = tmp.name

    try:
        conn = get_db()
        result = import_csv(conn, tmp_path)  # same function from the CLI's Day 6
    finally:
        os.unlink(tmp_path)

    return jsonify(result)

@app.route("/export", methods=["GET"])
def api_export_csv():
    conn = get_db()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        export_csv(conn, tmp.name)
        tmp_path = tmp.name

    response = send_file(
        tmp_path,
        mimetype="text/csv",
        as_attachment=True,
        download_name="transactions_export.csv"
    )

    @response.call_on_close
    def cleanup():
        os.unlink(tmp_path)

    return response

# API wiring
@app.route("/recurring/run", methods=["POST"])
@require_auth   # omit if no auth sprint
def run_recurring():
    conn = get_db()
    created = generate_due_transactions(conn)
    return jsonify({"created_count": len(created), "transaction_ids": created})

if __name__ == "__main__":
    app.run(debug=True, port=5000)