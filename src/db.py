import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,            -- ISO format YYYY-MM-DD
    amount REAL NOT NULL,          -- positive = income, negative = expense (your call, document it)
    category TEXT NOT NULL,
    description TEXT,
    import_hash TEXT,              -- used for dedup on CSV import, NULL for manually added rows
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_import_hash ON transactions(import_hash)
    WHERE import_hash IS NOT NULL;
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    amount REAL NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    import_hash TEXT UNIQUE,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS recurring_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amount REAL NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    frequency TEXT NOT NULL
        CHECK (frequency IN ('daily', 'weekly', 'monthly', 'yearly')),
    interval_count INTEGER NOT NULL DEFAULT 1
        CHECK (interval_count > 0),
    next_due_date TEXT NOT NULL,
    end_date TEXT,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now'))
);
"""

def get_connection(db_path="finance.db"):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path="finance.db"):
    conn = get_connection(db_path)
    conn.executescript(SCHEMA)
    conn.commit()
    return conn

if __name__ == "__main__":
    conn = init_db()
    test_tables = conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    for test in test_tables:
        print(test['name'])
    conn.close()