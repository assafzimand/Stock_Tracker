import os
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict

from app.config.constants import (
    STOCK_SYMBOLS,
    MAX_SAMPLES,
    DATA_RETENTION_DAYS
)

# === Configuration ===
DATA_FILE = os.path.join(os.path.dirname(__file__), "stock_data.csv")
COLUMNS = ["timestamp", "symbol", "price"]

# === Global in-memory store ===
_data: pd.DataFrame = pd.DataFrame(columns=COLUMNS)


def make_new_file_if_needed():
    """
    Creates a new empty CSV file with headers if it doesn't exist.
    """
    if not os.path.exists(DATA_FILE):
        print(f"[INFO] Creating new data file at: {DATA_FILE}")
        empty_df = pd.DataFrame(columns=COLUMNS)
        empty_df.to_csv(DATA_FILE, index=False)


def load_existing_data_if_available():
    """
    Loads existing data into memory from the persistent file and trims old rows.
    """
    global _data
    if os.path.exists(DATA_FILE):
        _data = pd.read_csv(DATA_FILE, parse_dates=["timestamp"])
        print(f"[INFO] Loaded existing data: {_data.shape[0]} rows from {DATA_FILE}")
        delete_old_prices()
    else:
        make_new_file_if_needed()



def delete_old_prices():
    """
    Truncates data older than the retention period (e.g., 3 days) from memory.
    """
    global _data
    cutoff_time = datetime.utcnow() - timedelta(days=DATA_RETENTION_DAYS)
    _data = _data[_data["timestamp"] >= cutoff_time]


def store_prices_and_save_file(prices: Dict[str, float]):
    """
    Adds new prices to the in-memory data and overwrites the CSV file.
    Assumes the in-memory data was loaded earlier at startup.
    """
    global _data

    # Ensure directory exists
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

    now = datetime.utcnow()
    new_entries = [
        {"timestamp": now, "symbol": ticker, "price": price}
        for ticker, price in prices.items()
    ]
    new_df = pd.DataFrame(new_entries, columns=COLUMNS)

    # Append new data to in-memory store
    _data = pd.concat([_data, new_df], ignore_index=True)

    # Trim outdated entries
    delete_old_prices()

    # Overwrite the existing file
    _data.to_csv(DATA_FILE, index=False)
    print(f"[INFO] Data updated and saved to {DATA_FILE}")



def get_prices(symbol: str, from_ts: datetime, to_ts: datetime) -> pd.DataFrame:
    """
    Returns price records for a specific stock in the given time range.
    """
    global _data
    return _data[
        (_data["symbol"] == symbol) &
        (_data["timestamp"] >= from_ts) &
        (_data["timestamp"] <= to_ts)
    ].copy()
