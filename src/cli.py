import sys

from .transactions import delete_transaction


def cli_guard(fn):
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)

        except FileNotFoundError as e:
            print(
                f"Error: file not found — {e}",
                file=sys.stderr
            )
            sys.exit(1)

        except ValueError as e:
            print(
                f"Error: invalid input — {e}",
                file=sys.stderr
            )
            sys.exit(1)

    return wrapper


@cli_guard
def cmd_delete(conn, txn_id):
    deleted = delete_transaction(conn, txn_id)

    if deleted == 0:
        raise ValueError(
            f"no transaction with id {txn_id}"
        )

    print(f"Deleted transaction {txn_id}")