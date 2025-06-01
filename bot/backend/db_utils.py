import json
import os
import sqlite3
from typing import Dict


def parse_coins_json(coins_str: str) -> Dict[str, float]:
    """
    Safely parse a JSON string representing coin allocations.

    Args:
        coins_str: JSON string like '{"btc": 50, "eth": 50}'

    Returns:
        A dictionary with coin names (lowercased) as keys and float percentages as values.
    """
    try:
        data = json.loads(coins_str)
        return {k: float(v) for k, v in data.items()}
    except (json.JSONDecodeError, ValueError, AttributeError) as e:
        # Log or raise as needed
        return {}


def get_connection(db_path: str):
    return sqlite3.connect(db_path)

def init_db(db_path: str):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    # For schema reference: Check ./schema.md
    with get_connection(db_path) as conn:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS internal_config (
            id TEXT PRIMARY KEY NOT NULL,
            value TEXT NOT NULL,
            last_updated_at TEXT NOT NULL
        );
        """)
        # Create sip_config table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS sip_config (
            label TEXT PRIMARY KEY NOT NULL,
            coins TEXT NOT NULL,   -- JSON string like {"btc":60,"eth":40}
            interval TEXT NOT NULL,
            amount REAL NOT NULL,
            enabled INTEGER NOT NULL  DEFAULT 1,
            created_at TEXT NOT NULL
        );
        """)
        # Create sip_history table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS sip_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            config_id INTEGER NOT NULL,
            executed_at TEXT NOT NULL,
            coin TEXT NOT NULL,
            amount_usd REAL NOT NULL,
            size_received REAL NOT NULL,
            coin_price_usd REAL NOT NULL,
            fee_usd REAL NOT NULL,
            FOREIGN KEY(config_id) REFERENCES sip_config(id)
        );
        """)
        conn.commit()
