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
# For testing -  STOCK_SYMBOLS = {i: i for i in range(1, 101)}

# Constants related to time intervals
SAMPLE_INTERVAL_MINUTES = 5
DATA_RETENTION_DAYS = 3
SAMPLES_PER_DAY = (60 // SAMPLE_INTERVAL_MINUTES) * 6.5  # Trading hours: 9:30–16:00 = 6.5 hrs
MAX_SAMPLES = int(SAMPLES_PER_DAY * DATA_RETENTION_DAYS)  # Total points to store per stock

# Pattern validation hyperparameters

# Width of the cup relative to total samples
CUP_WIDTH_MIN_RATIO = 0.085    # Between 0.07 and 0.10
CUP_WIDTH_MAX_RATIO = 0.70     # Between 0.65 and 0.75

# Handle width constraints
HANDLE_WIDTH_MIN = 4           # Between 3 and 5 bars
HANDLE_WIDTH_MAX_RATIO = 0.6   # Between 0.5 and 0.7

# Cup-to-handle width ratio
CUP_HANDLE_WIDTH_RATIO = 1.75  # Between 1.5 and 2

# Handle depth relative to cup depth
HANDLE_DEPTH_RATIO_MIN = 0.075  # Between 0.05 and 0.1
HANDLE_DEPTH_RATIO_MAX = 0.4    # Between 0.33 and 0.5

# Cup minimum relative position between rims
CUP_MIN_POSITION_MIN = 0.15    # Between 0.1 and 0.2
CUP_MIN_POSITION_MAX = 0.85    # Between 0.8 and 0.9

# Spike control: limits on extreme peaks within segments
MAX_CUP_PEAK_ABOVE_RIM = 0.025        # Between 0.02 and 0.03
MAX_HANDLE_PEAK_OVER_CEILING = 0.025  # Between 0.02 and 0.03

# Cup depth ratio (absolute)
MIN_CUP_DEPTH = 0.075          # Between 0.05 and 0.1
MAX_CUP_DEPTH = 0.55           # Between 0.5 and 0.6

# Handle dip (absolute)
MIN_HANDLE_DEPTH = 0.0035      # Between 0.002 and 0.005

# Structural placement constraints
MIN_LEFT_RIM_ABOVE_HANDLE_MIN = 0.0015   # Between 0.001 and 0.002
MAX_RIGHT_RIM_DROP_FROM_LEFT = 0.04      # Between 0.03 and 0.05
MAX_RIGHT_RIM_ABOVE_LEFT = 0.06          # Between 0.05 and 0.07

# Breakout validation
BREAKOUT_TOLERANCE = 0.015      # Between 0.01 and 0.02

# Tolerance for height similarity between left and right rims
LEFT_RIGHT_RIM_HEIGHT_TOLERANCE = 0.06  # Between 0.05 and 0.07


