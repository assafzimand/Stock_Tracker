import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

from .preprocessing import smooth_prices
from ..config.constants import STOCK_SYMBOLS, DATA_RETENTION_DAYS
from ..data.storage import get_prices


def auto_adjust_params(prices: pd.Series) -> tuple:
    """
    Adjust smoothing window and tolerance based on volatility (copied from detector logic).
    """
    variance = prices.pct_change().rolling(window=5).std().mean()
    volatility = variance if not np.isnan(variance) else 0.01

    if volatility < 0.005:
        smoothing_window = 5
    elif volatility < 0.015:
        smoothing_window = 7
    else:
        smoothing_window = 10

    return smoothing_window


def plot_prices(company: str, title: str = None, pattern_points: dict = None) -> None:
    """
    Plots the price data for a given company over the last N days, with optional cup-and-handle pattern overlay.

    Args:
        company (str): Company name (e.g., 'Apple')
        title (str): Optional plot title
        pattern_points (dict): Dictionary of timestamps for ['left_rim', 'left_min', 'right_rim', 'right_min', 'current']
    """
    # Resolve ticker symbol
    reverse_lookup = {v: k for k, v in STOCK_SYMBOLS.items()}
    symbol = reverse_lookup.get(company)

    if symbol is None:
        raise ValueError(f"Company name '{company}' is not recognized.")

    # Time window
    to_ts = datetime.utcnow()
    from_ts = to_ts - timedelta(days=DATA_RETENTION_DAYS)

    # Fetch price data
    prices = get_prices(symbol, from_ts, to_ts)
    if prices.empty or "price" not in prices.columns:
        print(f"No data to plot for {company}.")
        return

    # Apply matching smoothing logic
    smoothing_window = auto_adjust_params(prices["price"])
    series = smooth_prices(prices['price'], window=smoothing_window)

    # Plot original and smoothed series
    plt.figure(figsize=(12, 6))
    plt.plot(prices["timestamp"], prices["price"],
             label=f"{company} Original Price", linestyle='--', alpha=0.7)
    plt.plot(prices["timestamp"], series,
             label=f"{company} Smoothed Price", linewidth=1.5)

    # Optional: overlay pattern points
    if pattern_points:
        key_order = ["left_rim", "left_min", "right_rim", "right_min", "current"]
        overlay_x = []
        overlay_y = []
        seen_idxs = set()

        for key in key_order:
            ts = pattern_points.get(key)
            if ts is None:
                continue
            # Get unique smoothed price value at this timestamp
            closest_idx = prices["timestamp"].sub(ts).abs().idxmin()
            if closest_idx in seen_idxs:
                continue
            seen_idxs.add(closest_idx)

            overlay_x.append(prices["timestamp"].loc[closest_idx])
            overlay_y.append(series.loc[closest_idx])

        if len(overlay_x) >= 2:
            plt.plot(overlay_x, overlay_y, label="Detected Pattern",
                     color="black", linestyle="-", linewidth=2, marker='o')

    # Finalize plot
    plt.title(title or f"{company} - Last {DATA_RETENTION_DAYS} Days")
    plt.xlabel("Time")
    plt.ylabel("Price")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    fig = plt.gcf()
    return fig
