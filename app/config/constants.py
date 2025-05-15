# Dict of ticker symbols to company names
# STOCK_SYMBOLS = {
#     "AAPL": "Apple",
#     "MSFT": "Microsoft",
#     "GOOGL": "Alphabet",
#     "AMZN": "Amazon",
#     "NVDA": "Nvidia",
#     "META": "Meta",
#     "TSLA": "Tesla",
# }
STOCK_SYMBOLS = {i: i for i in range(1, 101)}

# Constants related to time intervals
SAMPLE_INTERVAL_MINUTES = 5
DATA_RETENTION_DAYS = 3
SAMPLES_PER_DAY = (60 // SAMPLE_INTERVAL_MINUTES) * 6.5  # Trading hours: 9:30–16:00 = 6.5 hrs
MAX_SAMPLES = int(SAMPLES_PER_DAY * DATA_RETENTION_DAYS)  # Total points to store per stock

# Pattern validation hyperparameters
CUP_HANDLE_WIDTH_RATIO = 1.1
MINIMA_DEPTH_RATIO = 1.01

# Handle retracement must be between 30% and 50% of the cup rise
HANDLE_RETRACEMENT_MIN = 0.15
HANDLE_RETRACEMENT_MAX = 0.6

# Cup minimum should be between 30% and 70% of the distance from left to right rim
CUP_MIN_POSITION_MIN = 0.3
CUP_MIN_POSITION_MAX = 0.7

MAX_CUP_PEAK_ABOVE_RIM = 0.02     # 2% over rim (in cup section)
MAX_HANDLE_PEAK_ABOVE_RIM = 0.01  # 1% over right rim (in handle)

