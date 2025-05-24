import yfinance as yf
from typing import Dict
import logging
from datetime import datetime, timezone
from app.config.constants import STOCK_SYMBOLS
from app.data.storage import store_prices_and_save_file  # Assumes a stub exists for now

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def get_stock_prices() -> Dict[str, float]:
    """
    Fetch current stock prices for predefined ticker symbols.

    Returns:
        Dict[str, float]: Dictionary mapping each ticker to its latest price.
    """
    prices = {}
    for ticker in STOCK_SYMBOLS:
        try:
            stock = yf.Ticker(ticker)
            current_price = stock.info.get("regularMarketPrice")
            if current_price is not None:
                prices[ticker] = round(current_price, 2)
            else:
                logging.warning(f"No price available for {ticker}")
        except Exception as e:
            logging.error(f"Failed to fetch data for {ticker}: {e}")
    return prices


def fetch_and_store_stock_prices() -> None:
    """
    High-level wrapper that:
    1. Gets current stock prices.
    2. Stores them via the storage module.
    """
    prices = get_stock_prices()
    now = datetime.now(timezone.utc).isoformat()
    store_prices_and_save_file(prices, now)
