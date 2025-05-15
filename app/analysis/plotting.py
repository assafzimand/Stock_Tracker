import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

from .preprocessing import smooth_prices
from ..config.constants import DATA_RETENTION_DAYS
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


def plot_prices(company: str, prices: pd.DataFrame, title: str = None, pattern_points: dict = None) -> [plt.Figure]:
    """
    Plots the price data for a given company over the last N days.
    Pattern overlay is colored: green if detected, red if not.

    Returns:
        matplotlib Figure or None if no data
    """
    if prices.empty or "price" not in prices.columns:
        print(f"[ERROR] No data to plot for {company}.")
        return None

    smoothing_window = auto_adjust_params(prices["price"])
    series = smooth_prices(prices["price"], window=smoothing_window)
    series = series.reindex(prices.index)  # Ensure alignment

    plt.figure(figsize=(12, 6))
    plt.plot(prices["timestamp"], prices["price"],
             label=f"{company} Original Price", linestyle='--', alpha=0.6)
    plt.plot(prices["timestamp"], series,
             label=f"{company} Smoothed", linewidth=1.5)

    # Overlay pattern if available
    if pattern_points:
        print(f"[DEBUG] Pattern points for {company}: {pattern_points}")

        key_order = ["left_rim", "left_min", "right_rim", "right_min", "current"]
        overlay_x = []
        overlay_y = []
        seen_idxs = set()

        for key in key_order:
            ts = pattern_points.get(key)
            if ts is None:
                continue

            print(f"[DEBUG] Matching timestamp: {ts}")
            closest_idx = prices["timestamp"].sub(ts).abs().idxmin()

            if closest_idx in seen_idxs:
                continue
            seen_idxs.add(closest_idx)

            if closest_idx not in series.index:
                print(f"[ERROR] Index mismatch: {closest_idx} not in smoothed series index")
                continue

            overlay_x.append(prices["timestamp"].loc[closest_idx])
            overlay_y.append(series.loc[closest_idx])

        if len(overlay_x) >= 2:
            color = "green" if pattern_points.get("pattern_detected") else "red"
            plt.plot(overlay_x, overlay_y, label="Detected Pattern",
                     color=color, linestyle="-", linewidth=2, marker='o')

    plt.title(title or f"{company} - Last {DATA_RETENTION_DAYS} Days")
    plt.xlabel("Time")
    plt.ylabel("Price")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    return plt.gcf()
