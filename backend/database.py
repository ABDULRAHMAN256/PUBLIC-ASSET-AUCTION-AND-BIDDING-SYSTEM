# database.py — SQLite connection helper
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "auction.db"


def get_db():
    """Open a new SQLite connection with foreign keys enabled.
    New connection per request avoids threading issues on concurrent requests."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # access columns as dict-like keys
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db():
    """Run schema.sql once, if the users table doesn't yet exist."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if cursor.fetchone():
        conn.close()
        return False
    with open(Path(__file__).parent / "schema.sql", "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    return True
