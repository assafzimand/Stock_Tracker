import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from .preprocessing import smooth_prices
from ..config.constants import STOCK_SYMBOLS, DATA_RETENTION_DAYS
from ..data.storage import get_prices
from ..config.constants import CUP_HANDLE_WIDTH_RATIO, MINIMA_DEPTH_RATIO



def get_symbol(company: str) -> str:
    reverse_lookup = {v: k for k, v in STOCK_SYMBOLS.items()}
    symbol = reverse_lookup.get(company)
    if symbol is None:
        raise ValueError(f"Unknown company name: {company}")
    return symbol


def get_price_data(symbol: str) -> pd.DataFrame:
    to_ts = datetime.utcnow()
    from_ts = to_ts - timedelta(days=DATA_RETENTION_DAYS)
    return get_prices(symbol, from_ts, to_ts)


def auto_adjust_params(prices: pd.Series) -> tuple:
    variance = prices.pct_change().rolling(window=5).std().mean()
    volatility = variance if not np.isnan(variance) else 0.01

    if volatility < 0.005:
        smoothing_window = 5
        tolerance = 0.02
    elif volatility < 0.015:
        smoothing_window = 7
        tolerance = 0.03
    else:
        smoothing_window = 10
        tolerance = 0.04

    print(f"[INFO] Adjusted parameters: smoothing_window={smoothing_window}, tolerance={tolerance:.2%}, volatility={volatility:.2%}")
    return smoothing_window, tolerance


def find_right_rim(smoothed: pd.Series, current_value: float, tolerance: float) -> int:
    """
    Finds the right rim candidate that:
    - Is within tolerance of the current value
    - Is a local maximum in a 5-point window
    - Starts a U-shaped segment ending at the current value
    """
    for i in range(len(smoothed) - 2, 10, -1):
        val = smoothed.iloc[i]

        # 1. Must be within tolerance of current value
        if not (val <= current_value and val >= current_value * (1 - tolerance)):
            continue

        # 2. Must be a local maximum (robust: 5-point window)
        window = smoothed.iloc[max(i - 2, 0):min(i + 3, len(smoothed))]
        if val != window.max():
            continue

        # 3. Must form a U-shape: dip and recover
        segment = smoothed.iloc[i:]
        min_idx = segment.idxmin()

        if min_idx > smoothed.index[i] and smoothed.iloc[-1] > segment[min_idx]:
            return i

    return None



def find_left_rim(smoothed: pd.Series, right_rim_idx: int, tolerance: float) -> int:
    """
    Finds the left rim candidate that:
    - Is within tolerance of the right rim
    - Starts a U-shaped dip that ends at the right rim
    """
    for j in range(right_rim_idx - 1, 5, -1):
        val = smoothed.iloc[j]

        if not (val >= smoothed.iloc[right_rim_idx] * (1 - tolerance) and
                val <= smoothed.iloc[right_rim_idx] * (1 + tolerance)):
            continue

        # Check for U-shape from left rim to right rim
        segment = smoothed.iloc[j:right_rim_idx + 1]
        min_idx = segment.idxmin()

        if min_idx > smoothed.index[j] and segment.iloc[-1] > segment[min_idx]:
            return j

    return None



def validate_handle(smoothed: pd.Series, right_rim_idx: int, handle_noise_margin: float) -> bool:
    handle = smoothed.iloc[right_rim_idx + 1:]
    too_deep = handle < smoothed.iloc[right_rim_idx] * (1 - handle_noise_margin)
    if too_deep.any():
        print(f"[DEBUG] Handle dips too deep: rim={smoothed.iloc[right_rim_idx]:.4f}, handle_min={handle.min():.4f}")
        return False
    return True


def detect_cup_and_handle(company: str, handle_noise_margin: float = 0.01):
    symbol = get_symbol(company)
    df = get_price_data(symbol)

    if df.empty or 'price' not in df.columns:
        print(f"[DEBUG] {company}: No price data available.")
        return False, {}

    prices = df['price']
    timestamps = df['timestamp']
    smoothing_window, tolerance = auto_adjust_params(prices)
    smoothed = smooth_prices(prices, window=smoothing_window)
    current_value = smoothed.iloc[-1]

    result_info = {
        "left_rim": None,
        "left_min": None,
        "right_rim": None,
        "right_min": None,
        "current": timestamps.iloc[-1]
    }

    right_rim_idx = find_right_rim(smoothed, current_value, tolerance)
    if right_rim_idx is None:
        print(f"[DEBUG] {company}: No valid right rim found (current_value={current_value:.4f})")
        return False, result_info
    result_info["right_rim"] = timestamps.iloc[right_rim_idx]

    if not validate_handle(smoothed, right_rim_idx, handle_noise_margin):
        print(f"[DEBUG] {company}: Handle validation failed.")
        return False, result_info

    left_rim_idx = find_left_rim(smoothed, right_rim_idx, tolerance)
    if left_rim_idx is None:
        print(f"[DEBUG] {company}: No valid left rim found.")
        return False, result_info
    result_info["left_rim"] = timestamps.iloc[left_rim_idx]

    cup_section = smoothed.iloc[left_rim_idx:right_rim_idx + 1]
    handle_section = smoothed.iloc[right_rim_idx:]

    left_min_idx = cup_section.idxmin()
    right_min_idx = handle_section.idxmin()

    if left_min_idx == right_min_idx or timestamps.loc[left_min_idx] in [result_info["left_rim"], result_info["right_rim"]]:
        print(f"[DEBUG] {company}: Duplicate timestamp for minima and rim.")
        return False, result_info

    result_info["left_min"] = timestamps.loc[left_min_idx]
    result_info["right_min"] = timestamps.loc[right_min_idx]

    cup_width = right_rim_idx - left_rim_idx
    handle_width = len(handle_section)

    cup_min = cup_section.min()
    handle_min = handle_section.min()

    if (
        cup_width >= handle_width * CUP_HANDLE_WIDTH_RATIO and
        handle_min / cup_min >= MINIMA_DEPTH_RATIO
    ):
        print(f"[INFO] {company}: Pattern detected.")
        return True, result_info

    print(f"[DEBUG] {company}: Failed width/depth test — cup_width={cup_width}, handle_width={handle_width}, ratio={handle_min / cup_min:.4f}")
    return False, result_info
