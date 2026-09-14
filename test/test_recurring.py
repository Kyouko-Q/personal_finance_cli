import pytest
from src.recurring import advance_date, generate_due_transactions

from src.recurring import (
    add_recurring_rule,
    list_recurring_rules,
    deactivate_recurring_rule,
)


def test_add_recurring_rule(conn):
    rule_id = add_recurring_rule(
        conn,
        amount=50,
        category="rent",
        frequency="monthly",
        next_due_date="2026-10-01",
        description="Apartment rent",
        interval_count=1,
    )

    assert rule_id == 1

    row = conn.execute(
        "SELECT * FROM recurring_rules WHERE id = ?",
        (rule_id,)
    ).fetchone()

    assert row["amount"] == 50
    assert row["category"] == "rent"
    assert row["frequency"] == "monthly"
    assert row["next_due_date"] == "2026-10-01"
    assert row["description"] == "Apartment rent"
    assert row["interval_count"] == 1
    assert row["active"] == 1

def test_add_recurring_rule_defaults(conn):
    rule_id = add_recurring_rule(
        conn,
        20,
        "food",
        "weekly",
        "2026-09-20",
    )

    row = conn.execute(
        "SELECT * FROM recurring_rules WHERE id = ?",
        (rule_id,)
    ).fetchone()

    assert row["description"] == ""
    assert row["interval_count"] == 1
    assert row["end_date"] is None
    assert row["user_id"] is None

@pytest.mark.parametrize(
    "frequency",
    ["daily", "weekly", "monthly", "yearly"]
)
def test_valid_frequencies(conn, frequency):
    rule_id = add_recurring_rule(
        conn,
        10,
        "test",
        frequency,
        "2026-09-20",
    )

    assert rule_id is not None

def test_invalid_frequency(conn):
    with pytest.raises(ValueError, match="invalid frequency"):
        add_recurring_rule(
            conn,
            50,
            "rent",
            "every_two_weeks",
            "2026-10-01",
        )

def test_list_recurring_rules(conn):
    add_recurring_rule(
        conn, 20, "food", "weekly", "2026-09-20"
    )

    add_recurring_rule(
        conn, 1000, "rent", "monthly", "2026-10-01"
    )

    rules = list_recurring_rules(conn)

    assert len(rules) == 2
    assert rules[0]["category"] == "food"
    assert rules[1]["category"] == "rent"

def test_list_active_rules_only(conn):
    rule1 = add_recurring_rule(
        conn, 20, "food", "weekly", "2026-09-20"
    )

    rule2 = add_recurring_rule(
        conn, 1000, "rent", "monthly", "2026-10-01"
    )

    deactivate_recurring_rule(conn, rule1)

    rules = list_recurring_rules(conn)

    assert len(rules) == 1
    assert rules[0]["id"] == rule2

def test_list_all_rules_including_inactive(conn):
    rule_id = add_recurring_rule(
        conn, 20, "food", "weekly", "2026-09-20"
    )

    deactivate_recurring_rule(conn, rule_id)

    rules = list_recurring_rules(conn, active_only=False)

    assert len(rules) == 1
    assert rules[0]["id"] == rule_id
    assert rules[0]["active"] == 0

def test_list_recurring_rules_by_user(conn):
    add_recurring_rule(
        conn, 20, "food", "weekly", "2026-09-20",
        user_id=1
    )

    add_recurring_rule(
        conn, 100, "rent", "monthly", "2026-10-01",
        user_id=2
    )

    rules = list_recurring_rules(conn, user_id=1)

    assert len(rules) == 1
    assert rules[0]["user_id"] == 1
    assert rules[0]["category"] == "food"

def test_deactivate_recurring_rule(conn):
    rule_id = add_recurring_rule(
        conn,
        50,
        "rent",
        "monthly",
        "2026-10-01",
    )

    result = deactivate_recurring_rule(conn, rule_id)

    assert result == 1

    row = conn.execute(
        "SELECT active FROM recurring_rules WHERE id = ?",
        (rule_id,)
    ).fetchone()

    assert row["active"] == 0

def test_deactivate_nonexistent_rule(conn):
    result = deactivate_recurring_rule(conn, 999)

    assert result == 0

@pytest.mark.parametrize("interval_count", [0, -1, -5])
def test_invalid_interval_count(conn, interval_count):
    with pytest.raises(ValueError, match="interval_count must be positive"):
        add_recurring_rule(
            conn,
            50,
            "rent",
            "monthly",
            "2026-10-01",
            interval_count=interval_count
        )

def test_advance_date_daily():
    result = advance_date("2026-09-01", "daily", 3)
    assert result == "2026-09-04"

def test_advance_date_weekly():
    result = advance_date("2026-09-01", "weekly", 2)

    assert result == "2026-09-15"

def test_advance_date_monthly():
    result = advance_date("2026-09-01", "monthly", 2)

    assert result == "2026-11-01"

def test_advance_date_yearly():
    result = advance_date("2026-09-01", "yearly", 2)

    assert result == "2028-09-01"

def test_advance_date_end_of_month():
    result = advance_date("2026-01-31", "monthly", 1)

    assert result == "2026-02-28"

def test_advance_date_leap_year():
    result = advance_date("2028-02-29", "yearly", 1)

    assert result == "2029-02-28"

def test_generate_due_transaction(conn):
    rule_id = add_recurring_rule(
        conn,
        amount=50,
        category="rent",
        frequency="monthly",
        next_due_date="2026-09-01",
        description="Apartment rent",
    )

    created = generate_due_transactions(
        conn,
        as_of="2026-09-10"
    )

    assert len(created) == 1

    transaction_id = created[0]

    row = conn.execute(
        "SELECT * FROM transactions WHERE id = ?",
        (transaction_id,)
    ).fetchone()

    assert row["amount"] == 50
    assert row["category"] == "rent"
    assert row["date"] == "2026-09-01"
    assert row["description"] == "Apartment rent"

def test_generate_updates_next_due_date(conn):
    rule_id = add_recurring_rule(
        conn,
        50,
        "rent",
        "monthly",
        "2026-09-01",
    )

    generate_due_transactions(
        conn,
        as_of="2026-09-10"
    )

    rule = conn.execute(
        "SELECT * FROM recurring_rules WHERE id = ?",
        (rule_id,)
    ).fetchone()

    assert rule["next_due_date"] == "2026-10-01"

def test_generate_future_rule(conn):
    rule_id = add_recurring_rule(
        conn,
        50,
        "rent",
        "monthly",
        "2026-10-01",
    )

    created = generate_due_transactions(
        conn,
        as_of="2026-09-10"
    )

    assert created == []

    count = conn.execute(
        "SELECT COUNT(*) FROM transactions"
    ).fetchone()[0]

    assert count == 0

def test_generate_multiple_overdue_occurrences(conn):
    rule_id = add_recurring_rule(
        conn,
        20,
        "subscription",
        "monthly",
        "2026-01-01",
    )

    created = generate_due_transactions(
        conn,
        as_of="2026-04-10"
    )

    assert len(created) == 4

    rows = conn.execute(
        """
        SELECT date
        FROM transactions
        ORDER BY date
        """
    ).fetchall()

    assert [row["date"] for row in rows] == [
        "2026-01-01",
        "2026-02-01",
        "2026-03-01",
        "2026-04-01",
    ]

    rule = conn.execute(
        "SELECT * FROM recurring_rules WHERE id = ?",
        (rule_id,)
    ).fetchone()

    assert rule["next_due_date"] == "2026-05-01"

def test_generate_is_idempotent(conn):
    add_recurring_rule(
        conn,
        50,
        "rent",
        "monthly",
        "2026-09-01",
    )

    first = generate_due_transactions(
        conn,
        as_of="2026-09-10"
    )

    second = generate_due_transactions(
        conn,
        as_of="2026-09-10"
    )

    assert len(first) == 1
    assert second == []

    count = conn.execute(
        "SELECT COUNT(*) FROM transactions"
    ).fetchone()[0]

    assert count == 1

def test_generate_ignores_inactive_rule(conn):
    rule_id = add_recurring_rule(
        conn,
        50,
        "rent",
        "monthly",
        "2026-09-01",
    )

    deactivate_recurring_rule(conn, rule_id)

    created = generate_due_transactions(
        conn,
        as_of="2026-09-10"
    )

    assert created == []

    count = conn.execute(
        "SELECT COUNT(*) FROM transactions"
    ).fetchone()[0]

    assert count == 0

def test_generate_respects_end_date(conn):
    rule_id = add_recurring_rule(
        conn,
        20,
        "subscription",
        "monthly",
        "2026-09-01",
        end_date="2026-10-15",
    )

    created = generate_due_transactions(
        conn,
        as_of="2026-12-01"
    )

    assert len(created) == 2

    rows = conn.execute(
        """
        SELECT date
        FROM transactions
        ORDER BY date
        """
    ).fetchall()

    assert [row["date"] for row in rows] == [
        "2026-09-01",
        "2026-10-01",
    ]

    rule = conn.execute(
        "SELECT * FROM recurring_rules WHERE id = ?",
        (rule_id,)
    ).fetchone()

    assert rule["active"] == 0