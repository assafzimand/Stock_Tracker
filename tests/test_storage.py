from datetime import datetime, timedelta
import random
import time

from app.data.storage import (
    load_existing_data_if_available,
    store_prices_and_save_file,
    get_prices,
    delete_old_prices,
)
from app.config.constants import STOCK_SYMBOLS

def simulate_price_data():
    """
    Simulates a price fetch using random prices.
    Returns a dictionary in the form {ticker: price}.
    """
    return {ticker: round(random.uniform(100, 500), 2) for ticker in STOCK_SYMBOLS}

def test_load_and_trim():
    """
    Test loading existing data and trimming old rows.
    """
    print("🔄 Loading existing data...")
    try:
        load_existing_data_if_available()
        print("✅ Data loaded and old rows trimmed.\n")
    except Exception as e:
        print(f"Error loading and trimming data: {e}")

def test_store_and_save():
    """
    Test storing and saving simulated price data.
    """
    print("💾 Simulating data store...")
    prices = simulate_price_data()
    try:
        store_prices_and_save_file(prices)
        print(f"✅ Stored prices: {prices}\n")
    except Exception as e:
        print(f"Error storing prices: {e}")

def test_query():
    """
    Test querying recent data for each ticker.
    """
    print("🔍 Testing query on recent data...")
    now = datetime.utcnow()
    one_hour_ago = now - timedelta(hours=1)

    for ticker in STOCK_SYMBOLS:
        try:
            df = get_prices(ticker, one_hour_ago, now)
            print(f"{ticker} - {len(df)} entries from the last hour.")
        except Exception as e:
            print(f"Error querying prices for {ticker}: {e}")
    print()

def test_manual_trim():
    """
    Test manually trimming old rows.
    """
    print("🧹 Manually trimming old rows (if any)...")
    try:
        delete_old_prices()
        print("✅ Trim complete.\n")
    except Exception as e:
        print(f"Error trimming old prices: {e}")

def run_all_tests():
    """
    Run all storage-related tests.
    """
    test_load_and_trim()
    test_store_and_save()
    test_query()
    test_manual_trim()

if __name__ == "__main__":
    run_all_tests()
