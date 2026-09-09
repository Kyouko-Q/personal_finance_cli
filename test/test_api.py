from flask import g

from src.api import app
from src.transactions import add_transaction


def create_test_client(conn):
    """
    Create a Flask test client that uses the pytest
    database connection instead of finance.db.
    """

    app.config["TESTING"] = True

    def override_get_db():
        return conn

    app.view_functions["list_transactions"]
    app.view_functions["get_transaction"]

    return app.test_client(), override_get_db


def test_list_transactions(conn):
    add_transaction(
        conn,
        "2026-08-01",
        20,
        "food",
        "lunch"
    )

    add_transaction(
        conn,
        "2026-08-02",
        50,
        "transport",
        "bus"
    )

    with app.test_client() as client:
        with app.app_context():
            g.db = conn

            response = client.get("/transactions")

    assert response.status_code == 200

    data = response.get_json()

    assert len(data) == 2

    assert data[0]["date"] == "2026-08-01"
    assert data[0]["amount"] == 20.0
    assert data[0]["category"] == "food"
    assert data[0]["description"] == "lunch"

    assert data[1]["date"] == "2026-08-02"
    assert data[1]["amount"] == 50.0
    assert data[1]["category"] == "transport"
    assert data[1]["description"] == "bus"


def test_list_transactions_category_filter(conn):
    add_transaction(
        conn,
        "2026-08-01",
        20,
        "food",
        "lunch"
    )

    add_transaction(
        conn,
        "2026-08-02",
        50,
        "transport",
        "bus"
    )

    add_transaction(
        conn,
        "2026-08-03",
        30,
        "food",
        "dinner"
    )

    with app.test_client() as client:
        with app.app_context():
            g.db = conn

            response = client.get(
                "/transactions?category=food"
            )

    assert response.status_code == 200

    data = response.get_json()

    assert len(data) == 2

    assert data[0]["category"] == "food"
    assert data[1]["category"] == "food"


def test_list_transactions_date_filter(conn):
    add_transaction(
        conn,
        "2026-08-01",
        20,
        "food",
        "lunch"
    )

    add_transaction(
        conn,
        "2026-08-15",
        50,
        "transport",
        "bus"
    )

    add_transaction(
        conn,
        "2026-09-01",
        30,
        "food",
        "dinner"
    )

    with app.test_client() as client:
        with app.app_context():
            g.db = conn

            response = client.get(
                "/transactions?from=2026-08-01&to=2026-08-31"
            )

    assert response.status_code == 200

    data = response.get_json()

    assert len(data) == 2

    assert data[0]["date"] == "2026-08-01"
    assert data[1]["date"] == "2026-08-15"


def test_list_transactions_combined_filter(conn):
    add_transaction(
        conn,
        "2026-08-01",
        20,
        "food",
        "lunch"
    )

    add_transaction(
        conn,
        "2026-08-15",
        50,
        "transport",
        "bus"
    )

    add_transaction(
        conn,
        "2026-08-20",
        30,
        "food",
        "dinner"
    )

    add_transaction(
        conn,
        "2026-09-01",
        100,
        "food",
        "groceries"
    )

    with app.test_client() as client:
        with app.app_context():
            g.db = conn

            response = client.get(
                "/transactions"
                "?category=food"
                "&from=2026-08-01"
                "&to=2026-08-31"
            )

    assert response.status_code == 200

    data = response.get_json()

    assert len(data) == 2

    assert data[0]["date"] == "2026-08-01"
    assert data[1]["date"] == "2026-08-20"

    assert data[0]["category"] == "food"
    assert data[1]["category"] == "food"


def test_list_transactions_empty(conn):
    with app.test_client() as client:
        with app.app_context():
            g.db = conn

            response = client.get("/transactions")

    assert response.status_code == 200

    data = response.get_json()

    assert data == []


def test_get_transaction(conn):
    txn_id = add_transaction(
        conn,
        "2026-08-01",
        20,
        "food",
        "lunch"
    )

    with app.test_client() as client:
        with app.app_context():
            g.db = conn

            response = client.get(
                f"/transactions/{txn_id}"
            )

    assert response.status_code == 200

    data = response.get_json()

    assert data["id"] == txn_id
    assert data["date"] == "2026-08-01"
    assert data["amount"] == 20.0
    assert data["category"] == "food"
    assert data["description"] == "lunch"


def test_get_transaction_not_found(conn):
    with app.test_client() as client:
        with app.app_context():
            g.db = conn

            response = client.get(
                "/transactions/999"
            )

    assert response.status_code == 404

    data = response.get_json()

    assert data == {
        "error": "not found"
    }


def test_get_transaction_different_ids(conn):
    first_id = add_transaction(
        conn,
        "2026-08-01",
        20,
        "food",
        "lunch"
    )

    second_id = add_transaction(
        conn,
        "2026-08-02",
        50,
        "transport",
        "bus"
    )

    with app.test_client() as client:
        with app.app_context():
            g.db = conn

            response = client.get(
                f"/transactions/{second_id}"
            )

    assert response.status_code == 200

    data = response.get_json()

    assert data["id"] == second_id
    assert data["id"] != first_id
    assert data["category"] == "transport"

def test_create_transaction(conn):
    with app.test_client() as client:
        with app.app_context():
            g.db = conn

            response = client.post(
                "/transactions",
                json={
                    "date": "2026-09-09",
                    "amount": 25.5,
                    "category": "food",
                    "description": "lunch"
                }
            )

    assert response.status_code == 201

    data = response.get_json()

    assert "id" in data

    row = conn.execute(
        "SELECT * FROM transactions WHERE id = ?",
        (data["id"],)
    ).fetchone()

    assert row["date"] == "2026-09-09"
    assert row["amount"] == 25.5
    assert row["category"] == "food"
    assert row["description"] == "lunch"

def test_create_transaction_missing_field(conn):
    with app.test_client() as client:
        with app.app_context():
            g.db = conn

            response = client.post(
                "/transactions",
                json={
                    "date": "2026-09-09",
                    "amount": 25.5
                }
            )

    assert response.status_code == 400

    data = response.get_json()

    assert data == {
        "error": "missing fields: ['category']"
    }

def test_create_transaction_invalid_amount(conn):
    with app.test_client() as client:
        with app.app_context():
            g.db = conn

            response = client.post(
                "/transactions",
                json={
                    "date": "2026-09-09",
                    "amount": "abc",
                    "category": "food"
                }
            )

    assert response.status_code == 400

    data = response.get_json()

    assert data == {
        "error": "amount must be numeric"
    }

def test_update_transaction(conn):
    txn_id = add_transaction(
        conn,
        "2026-09-09",
        25,
        "food",
        "lunch"
    )

    with app.test_client() as client:
        with app.app_context():
            g.db = conn

            response = client.put(
                f"/transactions/{txn_id}",
                json={
                    "amount": 30,
                    "description": "dinner"
                }
            )

    assert response.status_code == 200

    assert response.get_json() == {
        "status": "updated"
    }

    row = conn.execute(
        "SELECT * FROM transactions WHERE id = ?",
        (txn_id,)
    ).fetchone()

    assert row["amount"] == 30.0
    assert row["description"] == "dinner"

def test_update_transaction_not_found(conn):
    with app.test_client() as client:
        with app.app_context():
            g.db = conn

            response = client.put(
                "/transactions/9999",
                json={"amount": 30}
            )

    assert response.status_code == 404

    assert response.get_json() == {
        "error": "not found"
    }

def test_remove_transaction(conn):
    txn_id = add_transaction(
        conn,
        "2026-09-09",
        25,
        "food",
        "lunch"
    )

    with app.test_client() as client:
        with app.app_context():
            g.db = conn

            response = client.delete(
                f"/transactions/{txn_id}"
            )

    assert response.status_code == 204
    assert response.data == b""

    row = conn.execute(
        "SELECT * FROM transactions WHERE id = ?",
        (txn_id,)
    ).fetchone()

    assert row is None

def test_remove_transaction_not_found(conn):
    with app.test_client() as client:
        with app.app_context():
            g.db = conn

            response = client.delete(
                "/transactions/9999"
            )

    assert response.status_code == 404

    assert response.get_json() == {
        "error": "not found"
    }