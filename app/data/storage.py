import os
import pandas as pd
from datetime import datetime, timedelta, timezone
from typing import Dict
import logging

from app.config.constants import DATA_RETENTION_DAYS

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# === Configuration ===
DATA_FILE = os.path.join(os.path.dirname(__file__), "stock_data.csv")
COLUMNS = ["timestamp", "symbol", "price"]

# === Global in-memory store ===
_data: pd.DataFrame = None


def make_new_file_if_needed():
    """
    Create a new empty CSV file with headers if it doesn't exist.
    """
    if not os.path.exists(DATA_FILE):
        logging.info(f"Creating new data file at: {DATA_FILE}")
        empty_df = pd.DataFrame(columns=COLUMNS)
        empty_df.to_csv(DATA_FILE, index=False)


def delete_old_prices():
    """
    Truncate data older than the retention period (e.g., 3 days) from memory.
    """
    global _data
    cutoff_time = datetime.now(timezone.utc) - timedelta(days=DATA_RETENTION_DAYS)
    
    # Convert to UTC if needed
    if _data["timestamp"].dt.tz is None:
        _data["timestamp"] = _data["timestamp"].dt.tz_localize(timezone.utc)

    rows_before = len(_data)
    _data = _data[_data["timestamp"] >= cutoff_time]
    rows_after = len(_data)

    if rows_before > rows_after:
        logging.info(f"Deleted {rows_before - rows_after} old price records.")


def load_existing_data_if_available():
    """
    Load existing data into memory from the persistent file and trim old rows.
    """
    global _data
    if not os.path.exists(DATA_FILE):
        make_new_file_if_needed()

    _data = pd.read_csv(DATA_FILE, parse_dates=["timestamp"])

    # Ensure timestamp column is timezone-aware (UTC)
    if _data["timestamp"].dt.tz is None:
        _data["timestamp"] = _data["timestamp"].dt.tz_localize(timezone.utc)

    logging.info(f"Loaded existing data: {_data.shape[0]} rows from {DATA_FILE}")
    delete_old_prices()

    try:
        _data.to_csv(DATA_FILE, index=False)
        logging.info(f"Data updated and saved to {DATA_FILE}")
    except Exception as e:
        logging.error(f"Failed to save data to {DATA_FILE}: {e}")


load_existing_data_if_available()


def store_prices_and_save_file(prices: Dict[str, float]):
    """
    Add new prices to the in-memory data and overwrite the CSV file.
    """
    global _data

    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

    now = datetime.now(timezone.utc)
    new_entries = [
        {"timestamp": now, "symbol": ticker, "price": price}
        for ticker, price in prices.items()
    ]
    new_df = pd.DataFrame(new_entries, columns=COLUMNS)

    _data = pd.concat([_data, new_df], ignore_index=True)

    delete_old_prices()

    try:
        _data.to_csv(DATA_FILE, index=False)
        logging.info(f"Data updated and saved to {DATA_FILE}")
    except Exception as e:
        logging.error(f"Failed to save data to {DATA_FILE}: {e}")


def get_prices(symbol: str, from_ts: datetime, to_ts: datetime) -> pd.DataFrame:
    """
    Retrieve price data for a given stock symbol within a specified time range.
    """
    global _data

    if _data is None:
        logging.info("_data is None — loading from disk.")
        load_existing_data_if_available()

    if _data.empty:
        logging.info("Data is empty. Triggering fetch and retrying.")
        from app.data.fetcher import fetch_and_store_stock_prices
        fetch_and_store_stock_prices()
        load_existing_data_if_available()

    # Ensure filter bounds are timezone-aware
    if from_ts.tzinfo is None:
        from_ts = from_ts.replace(tzinfo=timezone.utc)
    if to_ts.tzinfo is None:
        to_ts = to_ts.replace(tzinfo=timezone.utc)

    return _data[
        (_data["symbol"] == symbol) &
        (_data["timestamp"] >= from_ts) &
        (_data["timestamp"] <= to_ts)
    ].copy()
