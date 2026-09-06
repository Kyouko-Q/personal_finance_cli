import pytest

from src.cli import cmd_delete
from src.transactions import add_transaction


def test_cmd_delete(conn, capsys):
    txn_id = add_transaction(
        conn,
        "2026-08-01",
        20,
        "food",
        "lunch"
    )

    cmd_delete(conn, txn_id)

    captured = capsys.readouterr()

    assert captured.out == f"Deleted transaction {txn_id}\n"

    row = conn.execute(
        "SELECT * FROM transactions WHERE id = ?",
        (txn_id,)
    ).fetchone()

    assert row is None

def test_cmd_delete_nonexistent(conn, capsys):
    with pytest.raises(SystemExit) as exc:
        cmd_delete(conn, 999)

    assert exc.value.code == 1

    captured = capsys.readouterr()

    assert captured.err == (
        "Error: invalid input — no transaction with id 999\n"
    )

def test_cli_guard_file_not_found(capsys):
    from src.cli import cli_guard

    @cli_guard
    def failing_command():
        raise FileNotFoundError("missing.csv")

    with pytest.raises(SystemExit) as exc:
        failing_command()

    assert exc.value.code == 1

    captured = capsys.readouterr()

    assert captured.err == (
        "Error: file not found — missing.csv\n"
    )