import os
import sqlite3
import pandas as pd
from datetime import datetime, timedelta, timezone
from typing import Dict
import logging

from app.config.constants import DATA_RETENTION_DAYS

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# === Configuration ===
DB_FILE = os.path.join(os.path.dirname(__file__), "stock_data.db")
TABLE_NAME = "stock_prices"

def delete_old_prices():
    """
    Delete rows older than the retention window.
    """
    cutoff_time = datetime.now(timezone.utc) - timedelta(days=DATA_RETENTION_DAYS)
    cutoff_str = cutoff_time.isoformat()

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {TABLE_NAME} WHERE timestamp < ?", (cutoff_str,))
        deleted = cursor.rowcount
        if deleted > 0:
            logging.info(f"Deleted {deleted} old price records.")


def initialize_db():
    """
    Initialize the database and create table if it doesn't exist.
    """
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                price REAL NOT NULL
            )
        """)
        conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_symbol_timestamp 
            ON {TABLE_NAME} (symbol, timestamp)
        """)
        
        # Count existing rows
        cursor = conn.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
        row_count = cursor.fetchone()[0]

    logging.info(f"Database initialized with {row_count} existing price records.")
    
    delete_old_prices()

initialize_db()


def store_prices_and_save_file(prices: Dict[str, float], timestamp: datetime):
    """
    Store a batch of current stock prices into the database.
    """
    records = [(timestamp, ticker, price) for ticker, price in prices.items()]

    with sqlite3.connect(DB_FILE) as conn:
        conn.executemany(
            f"INSERT INTO {TABLE_NAME} (timestamp, symbol, price) VALUES (?, ?, ?)", 
            records
        )
    delete_old_prices()
    logging.info(f"Stored {len(records)} new price records.")


def get_prices(symbol: str, from_ts: datetime, to_ts: datetime) -> pd.DataFrame:
    """
    Retrieve price records for a specific stock in the given time range.
    """
    from_ts = from_ts.astimezone(timezone.utc).isoformat()
    to_ts = to_ts.astimezone(timezone.utc).isoformat()

    query = f"""
        SELECT timestamp, symbol, price
        FROM {TABLE_NAME}
        WHERE symbol = ? AND timestamp BETWEEN ? AND ?
        ORDER BY timestamp ASC
    """

    with sqlite3.connect(DB_FILE) as conn:
        df = pd.read_sql_query(query, conn, params=(symbol, from_ts, to_ts))
    
    # Parse timestamp column to datetime with UTC timezone
    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.tz_convert("UTC")

    return df
