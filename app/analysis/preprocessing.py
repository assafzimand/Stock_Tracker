import pandas as pd

def smooth_prices(prices: pd.Series, window: int = 7) -> pd.Series:
    """
    Combines median + mean smoothing for noise-resistant signal.
    """
    median = prices.rolling(window=window, min_periods=1, center=True).median()
    return median.rolling(window=window, min_periods=1, center=True).mean()
