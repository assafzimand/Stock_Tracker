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
    print("🔄 Loading existing data...")
    load_existing_data_if_available()
    print("✅ Data loaded and old rows trimmed.\n")

def test_store_and_save():
    print("💾 Simulating data store...")
    prices = simulate_price_data()
    store_prices_and_save_file(prices)
    print(f"✅ Stored prices: {prices}\n")

def test_query():
    print("🔍 Testing query on recent data...")
    now = datetime.utcnow()
    one_hour_ago = now - timedelta(hours=1)

    for ticker in STOCK_SYMBOLS:
        df = get_prices(ticker, one_hour_ago, now)
        print(f"{ticker} - {len(df)} entries from the last hour.")
    print()

def test_manual_trim():
    print("🧹 Manually trimming old rows (if any)...")
    delete_old_prices()
    print("✅ Trim complete.\n")

def run_all_tests():
    test_load_and_trim()
    test_store_and_save()
    test_query()
    test_manual_trim()

if __name__ == "__main__":
    run_all_tests()
