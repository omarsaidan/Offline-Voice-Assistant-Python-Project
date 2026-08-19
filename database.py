import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone


APP_DATA_DIR = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
    "VoiceAssistant",
)
DB_PATH = os.path.join(APP_DATA_DIR, "users.db")


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    os.makedirs(APP_DATA_DIR, exist_ok=True)
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt          TEXT NOT NULL,
                created_at    TEXT NOT NULL,
                last_login    TEXT
            )
        """)


def username_exists(username: str) :
    with get_connection() as conn:
        row = conn.execute(
            "SELECT 1 FROM users WHERE username = ?", (username,)
        ).fetchone()
    return row is not None


def create_user(username: str, password_hash: str, salt: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO users (username, password_hash, salt, created_at)
               VALUES (?, ?, ?, ?)""",
            (username, password_hash, salt, datetime.now(timezone.utc).isoformat()),
        )


def get_user(username: str) :
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()


def update_last_login(username: str) :
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET last_login = ? WHERE username = ?",
            (datetime.now(timezone.utc).isoformat(), username),
        )
