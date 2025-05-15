import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from .preprocessing import smooth_prices
from ..config.constants import (
    STOCK_SYMBOLS,
    DATA_RETENTION_DAYS,
    CUP_HANDLE_WIDTH_RATIO,
    HANDLE_RETRACEMENT_MIN,
    HANDLE_RETRACEMENT_MAX,
    CUP_MIN_POSITION_MIN,
    CUP_MIN_POSITION_MAX,
    MAX_CUP_PEAK_ABOVE_RIM,
    MAX_HANDLE_PEAK_ABOVE_RIM
)
from ..data.storage import get_prices


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
    for i in range(len(smoothed) - 2, 10, -1):
        val = smoothed.iloc[i]
        if not (val <= current_value and val >= current_value * (1 - tolerance)):
            continue

        window = smoothed.iloc[max(i - 2, 0):min(i + 3, len(smoothed))]
        if val != window.max():
            continue

        segment = smoothed.iloc[i:]
        min_idx = segment.idxmin()
        if min_idx > smoothed.index[i] and smoothed.iloc[-1] > segment[min_idx]:
            return i
    return None


def validate_left_rim(smoothed: pd.Series, left_rim_idx: int, right_rim_idx: int) -> tuple:
    """
    Checks if the given left rim index forms a valid cup pattern with the right rim.
    Returns a tuple (is_valid: bool, data: dict).
    """
    segment = smoothed.iloc[left_rim_idx:right_rim_idx + 1]
    min_idx = segment.idxmin()
    if not (min_idx > smoothed.index[left_rim_idx] and segment.iloc[-1] > segment[min_idx]):
        return False, {}

    cup_section = smoothed.iloc[left_rim_idx:right_rim_idx + 1]
    handle_section = smoothed.iloc[right_rim_idx:]
    
    rim_avg = (smoothed.iloc[left_rim_idx] + smoothed.iloc[right_rim_idx]) / 2
    cup_max = cup_section.max()

    if cup_max > rim_avg * (1 + MAX_CUP_PEAK_ABOVE_RIM):
        return False, {}

    handle_max = handle_section.max()
    if handle_max > smoothed.iloc[right_rim_idx] * (1 + MAX_HANDLE_PEAK_ABOVE_RIM):
        return False, {}


    cup_width = right_rim_idx - left_rim_idx
    handle_width = len(handle_section)
    cup_rise = smoothed.iloc[right_rim_idx] - cup_section.min()
    handle_dip = smoothed.iloc[right_rim_idx] - handle_section.min()
    retracement = handle_dip / cup_rise if cup_rise > 0 else 0

    min_pos = smoothed.index.get_loc(cup_section.idxmin())
    min_rel = (min_pos - left_rim_idx) / (right_rim_idx - left_rim_idx)

    is_valid = (
        cup_width >= handle_width * CUP_HANDLE_WIDTH_RATIO and
        HANDLE_RETRACEMENT_MIN <= retracement <= HANDLE_RETRACEMENT_MAX and
        CUP_MIN_POSITION_MIN <= min_rel <= CUP_MIN_POSITION_MAX
    )

    data = {
        "cup_section": cup_section,
        "handle_section": handle_section,
        "left_min_idx": cup_section.idxmin(),
        "right_min_idx": handle_section.idxmin()
    } if is_valid else {}

    return is_valid, data


def detect_cup_and_handle(company: str):
    """
    Detects a cup and handle pattern for a given company.
    Scans for a valid right rim, then iterates through possible left rim candidates,
    validating each for pattern structure until a match is found.

    Returns:
        bool: whether a valid pattern was found
        dict: key timestamps and detection metadata
    """
    symbol = get_symbol(company)
    df = get_price_data(symbol)

    result_info = {
        "left_rim": None,
        "left_min": None,
        "right_rim": None,
        "right_min": None,
        "current": None,
        "pattern_detected": False
    }

    if df.empty or 'price' not in df.columns:
        print(f"[DEBUG] {company}: No price data available.")
        return False, result_info

    prices = df['price']
    timestamps = df['timestamp']
    result_info["current"] = timestamps.iloc[-1]

    smoothing_window, tolerance = auto_adjust_params(prices)
    smoothed = smooth_prices(prices, window=smoothing_window)
    current_value = smoothed.iloc[-1]

    right_rim_idx = find_right_rim(smoothed, current_value, tolerance)
    if right_rim_idx is None:
        print(f"[DEBUG] {company}: No valid right rim found.")
        return False, result_info
    result_info["right_rim"] = timestamps.iloc[right_rim_idx]

    for j in range(right_rim_idx - 1, 5, -1):
        val = smoothed.iloc[j]
        if not (val >= smoothed.iloc[right_rim_idx] * (1 - tolerance) and val <= smoothed.iloc[right_rim_idx] * (1 + tolerance)):
            continue

        is_valid, pattern_data = validate_left_rim(smoothed, j, right_rim_idx)
        if is_valid:
            result_info["left_rim"] = timestamps.iloc[j]
            result_info["left_min"] = timestamps.loc[pattern_data["left_min_idx"]]
            result_info["right_min"] = timestamps.loc[pattern_data["right_min_idx"]]
            print(f"[INFO] {company}: Pattern detected.")
            result_info["pattern_detected"] = True
            return True, result_info

    print(f"[DEBUG] {company}: No valid left rim candidate formed a complete pattern.")
    return False, result_info
