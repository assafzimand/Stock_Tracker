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

# Ratio of cup width to handle width (time-wise)
CUP_WIDTH_MIN_RATIO = 0.10   # At least 10% of available points
CUP_WIDTH_MAX_RATIO = 0.65   # At most 65% of available points
HANDLE_WIDTH_MIN = 5  # At least 5 bars (25 minutes)
HANDLE_WIDTH_MAX_RATIO = 0.5  # Max 50% of cup width

CUP_HANDLE_WIDTH_RATIO = 2

# Minimum ratio between handle and cup depth
HANDLE_DEPTH_RATIO_MIN = 0.1
HANDLE_DEPTH_RATIO_MAX = 0.33

# Where the cup's minimum should lie between the rims (as a fraction of width)
CUP_MIN_POSITION_MIN = 0.2
CUP_MIN_POSITION_MAX = 0.8

# Peak control within cup and handle
MAX_CUP_PEAK_ABOVE_RIM = 0.02               # 2% above average rim height in cup
MAX_HANDLE_PEAK_OVER_CEILING = 0.02         # 2% above handle ceiling (right rim + current)

# Minimum absolute depth requirements
MIN_CUP_DEPTH = 0.1                       # 0.5% dip from rim average
MAX_CUP_DEPTH = 0.50
MIN_HANDLE_DEPTH = 0.005                   # 0.5% dip from handle ceiling

# Structural checks for relative placement
MIN_LEFT_RIM_ABOVE_HANDLE_MIN = 0.002       # Left rim must be at least 0.2% above handle min
MAX_RIGHT_RIM_DROP_FROM_LEFT = 0.03      # Right rim can be max 3% below left rim
MAX_RIGHT_RIM_ABOVE_LEFT = 0.05  # Right rim must be no more than 5% above left rim

BREAKOUT_TOLERANCE = 0.01  # Current price must be ≥ 99% of right rim
LEFT_RIGHT_RIM_HEIGHT_TOLERANCE = 0.05  # 5% tolerance


