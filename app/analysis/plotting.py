import matplotlib
matplotlib.use("Agg")  # Use non-interactive backend for headless rendering
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import logging

from .preprocessing import smooth_prices
from ..config.constants import DATA_RETENTION_DAYS

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


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


def plot_prices(company: str, prices: pd.DataFrame, title: str = None, pattern_points: dict = None) -> plt.Figure:
    """
    Plots the price data for a given company over the last N days.

    Args:
        company (str): The name of the company.
        prices (pd.DataFrame): A DataFrame containing the price data with
        'timestamp' and 'price' columns.
        title (str, optional): The title of the plot. Defaults to None.
        pattern_points (dict, optional): A dictionary containing pattern
        points for overlay. Defaults to None.

    Returns:
        plt.Figure: The matplotlib Figure object of the plot, or None if
        no data is available.
    """
    if prices.empty or "price" not in prices.columns:
        logging.error(f"No data to plot for {company}.")
        return None

    # Ensure sorted timestamps
    prices = prices.sort_values("timestamp").reset_index(drop=True)

    smoothing_window = auto_adjust_params(prices["price"])
    series = smooth_prices(prices["price"], window=smoothing_window)
    series = series.reindex(prices.index)  # Ensure alignment

    # Use evenly spaced x-values
    x_vals = np.arange(len(prices))
    timestamps = pd.to_datetime(prices["timestamp"])

    plt.figure(figsize=(12, 6))
    plt.plot(x_vals, prices["price"],
             label=f"{company} Original Price", linestyle='--', alpha=0.6)
    plt.plot(x_vals, series,
             label=f"{company} Smoothed", linewidth=1.5)

    # Overlay pattern if provided
    if pattern_points:
        logging.debug(f"Pattern points for {company}: {pattern_points}")
        key_order = ["left_rim", "left_min", "right_rim", "right_min", "current"]
        overlay_x = []
        overlay_y = []
        seen_idxs = set()

        for key in key_order:
            ts = pattern_points.get(key)
            if ts is None:
                continue

            # Find index closest to timestamp
            closest_idx = (timestamps - pd.to_datetime(ts)).abs().idxmin()

            if closest_idx in seen_idxs:
                continue
            seen_idxs.add(closest_idx)

            if closest_idx not in series.index:
                logging.error(f"Index mismatch: {closest_idx} not in smoothed series index")
                continue

            overlay_x.append(closest_idx)
            overlay_y.append(series.loc[closest_idx])

        if len(overlay_x) >= 2:
            color = "green" if pattern_points.get("pattern_detected") else "red"
            plt.plot(overlay_x, overlay_y,
                     label="Detected Pattern" if pattern_points.get("pattern_detected") else "No Pattern",
                     color=color, linestyle="-", linewidth=2, marker='o')

    # Use formatted tick labels
    tick_spacing = max(1, len(prices) // 10)
    tick_indices = np.arange(0, len(prices), tick_spacing)
    tick_labels = [timestamps.iloc[i].strftime("%m-%d %H:%M") for i in tick_indices]

    plt.xticks(tick_indices, tick_labels, rotation=45)

    plt.title(title or f"{company} - Last {DATA_RETENTION_DAYS} Days")
    plt.xlabel("Time")
    plt.ylabel("Price")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    return plt.gcf()