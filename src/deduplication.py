import sqlite3
import os
from src import config

def _get_conn() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(config.DB_PATH), exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS seen_posts "
        "(url TEXT PRIMARY KEY, seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
    )
    conn.commit()
    return conn

def is_seen(url: str) -> bool:
    with _get_conn() as conn:
        row = conn.execute("SELECT 1 FROM seen_posts WHERE url = ?", (url,)).fetchone()
        return row is not None

def mark_seen(url: str) -> None:
    with _get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO seen_posts (url) VALUES (?)", (url,)
        )
        conn.commit()
