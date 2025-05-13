# Dict of ticker symbols to company names
STOCK_SYMBOLS = {
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "GOOGL": "Alphabet",
    "AMZN": "Amazon",
    "NVDA": "Nvidia",
    "META": "Meta",
    "TSLA": "Tesla",
}

# Constants related to time intervals
SAMPLE_INTERVAL_MINUTES = 5
DATA_RETENTION_DAYS = 3
SAMPLES_PER_DAY = (60 // SAMPLE_INTERVAL_MINUTES) * 6.5  # Trading hours: 9:30–16:00 = 6.5 hrs
MAX_SAMPLES = int(SAMPLES_PER_DAY * DATA_RETENTION_DAYS)  # Total points to store per stock
