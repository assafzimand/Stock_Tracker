import pandas as pd

def smooth_prices(prices: pd.Series, window: int = 7) -> pd.Series:
    """
    Applies a combination of median and mean smoothing to a series of prices
    for noise-resistant signal processing.

    Args:
        prices (pd.Series): A pandas Series containing the price data to be
        smoothed.
        window (int, optional): The window size for smoothing. Defaults to 7.

    Returns:
        pd.Series: A pandas Series containing the smoothed price data.

    Raises:
        ValueError: If the input is not a pandas Series.
    """
    if not isinstance(prices, pd.Series):
        raise ValueError("Input must be a pandas Series.")

    median = prices.rolling(window=window, min_periods=1, center=True).median()
    return median.rolling(window=window, min_periods=1, center=True).mean()
