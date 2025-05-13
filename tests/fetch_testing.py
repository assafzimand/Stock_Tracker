from app.data.fetcher import get_stock_prices
from app.config.constants import STOCK_SYMBOLS

def debug_fetch():
    print("Fetching current stock prices...\n")
    prices = get_stock_prices()
    
    for ticker, price in prices.items():
        company = STOCK_SYMBOLS[ticker]
        print(f"{company} ({ticker}): ${price}")

if __name__ == "__main__":
    debug_fetch()
