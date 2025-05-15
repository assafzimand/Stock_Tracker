import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from .preprocessing import smooth_prices
from ..config.constants import (
    STOCK_SYMBOLS,
    DATA_RETENTION_DAYS,
    CUP_HANDLE_WIDTH_RATIO,
    HANDLE_DEPTH_RATIO_MIN,
    HANDLE_DEPTH_RATIO_MAX,
    CUP_MIN_POSITION_MIN,
    CUP_MIN_POSITION_MAX,
    MAX_CUP_PEAK_ABOVE_RIM,
    MAX_HANDLE_PEAK_OVER_CEILING,
    MIN_CUP_DEPTH,
    MAX_CUP_DEPTH,
    MIN_HANDLE_DEPTH,
    MIN_LEFT_RIM_ABOVE_HANDLE_MIN,
    MAX_RIGHT_RIM_DROP_FROM_LEFT,
    CUP_WIDTH_MIN_RATIO,
    CUP_WIDTH_MAX_RATIO,
    HANDLE_WIDTH_MIN,
    HANDLE_WIDTH_MAX_RATIO,
    BREAKOUT_TOLERANCE,
    LEFT_RIGHT_RIM_HEIGHT_TOLERANCE
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


def auto_adjust_params(prices: pd.Series) -> int:
    variance = prices.pct_change().rolling(window=5).std().mean()
    volatility = variance if not np.isnan(variance) else 0.01

    if volatility < 0.005:
        smoothing_window = 5
    elif volatility < 0.015:
        smoothing_window = 7
    else:
        smoothing_window = 10

    print(f"[INFO] Adjusted parameters: smoothing_window={smoothing_window}, volatility={volatility:.2%}")
    return smoothing_window


def validate_left_rim(smoothed: pd.Series, left_rim_idx: int, right_rim_idx: int) -> tuple:
    """
    Checks if the given left rim index forms a valid cup pattern with the right rim.
    Returns a tuple (is_valid: bool, data: dict).
    """
    segment = smoothed.iloc[left_rim_idx:right_rim_idx + 1]
    min_idx = segment.idxmin()
    min_pos = smoothed.index.get_loc(min_idx)
    min_rel = (min_pos - left_rim_idx) / (right_rim_idx - left_rim_idx)

    if not (
        min_pos > left_rim_idx and
        segment.iloc[0] > segment[min_idx] and
        segment.iloc[-1] > segment[min_idx]
    ):
        print("[DEBUG] U-shape condition failed.")
        return False, {}


    cup_section = smoothed.iloc[left_rim_idx:right_rim_idx + 1]
    handle_section = smoothed.iloc[right_rim_idx:]
    
    # Check that the cup recovered — right rim not too far below left rim
    if smoothed.iloc[right_rim_idx] < smoothed.iloc[left_rim_idx] * (1 - MAX_RIGHT_RIM_DROP_FROM_LEFT):
        print("[DEBUG] Right rim is too low relative to left rim — incomplete recovery.")
        return False, {}

    rim_avg = (smoothed.iloc[left_rim_idx] + smoothed.iloc[right_rim_idx]) / 2
    cup_max = cup_section.max()
    if cup_max > rim_avg * (1 + MAX_CUP_PEAK_ABOVE_RIM):
        print("[DEBUG] Cup peak exceeds allowed spike limit.")
        return False, {}

    handle_avg_ceiling = (smoothed.iloc[right_rim_idx] + smoothed.iloc[-1]) / 2
    handle_max = handle_section.max()
    if handle_max > handle_avg_ceiling * (1 + MAX_HANDLE_PEAK_OVER_CEILING):
        print("[DEBUG] Handle peak exceeds allowed spike limit.")
        return False, {}

    cup_min = cup_section.min()
    handle_min = handle_section.min()

    if (rim_avg - cup_min) / rim_avg < MIN_CUP_DEPTH:
        print(f"[DEBUG] Cup depth too shallow: depth ratio = {(rim_avg - cup_min) / rim_avg:.4f}")
        return False, {}

    if (handle_avg_ceiling - handle_min) / handle_avg_ceiling < MIN_HANDLE_DEPTH:
        print(f"[DEBUG] Handle depth too shallow: depth ratio = {(handle_avg_ceiling - handle_min) / handle_avg_ceiling:.4f}")
        return False, {}

    if smoothed.iloc[left_rim_idx] < handle_min * (1 + MIN_LEFT_RIM_ABOVE_HANDLE_MIN):
        print("[DEBUG] Left rim is too low relative to handle minimum.")
        return False, {}

    cup_width = right_rim_idx - left_rim_idx
    handle_width = len(handle_section)
    
    if handle_width < HANDLE_WIDTH_MIN or handle_width > cup_width * HANDLE_WIDTH_MAX_RATIO:
        print(f"[DEBUG] Handle width {handle_width} invalid: too short or too long for cup width {cup_width}.")
        return False, {}

    total_length = len(smoothed)
    if not (CUP_WIDTH_MIN_RATIO <= cup_width / total_length <= CUP_WIDTH_MAX_RATIO):
        print(f"[DEBUG] Cup width {cup_width} out of allowed range based on total samples {total_length}.")
        return False, {}


    cup_depth = rim_avg - cup_min
    handle_depth = handle_avg_ceiling - handle_min

    cup_depth_ratio = handle_depth / cup_depth if cup_depth > 0 else 0

    if cup_depth_ratio < MIN_CUP_DEPTH or cup_depth_ratio > MAX_CUP_DEPTH:
        print(f"[DEBUG] Cup depth ratio {cup_depth_ratio:.2f} out of range.")
        return False, {}

    if not (cup_width >= handle_width * CUP_HANDLE_WIDTH_RATIO):
        print("[DEBUG] Cup is not wide enough compared to handle.")
        return False, {}

    if not (HANDLE_DEPTH_RATIO_MIN <= cup_depth_ratio <= HANDLE_DEPTH_RATIO_MAX):
        print(f"[DEBUG] Handle depth ratio {cup_depth_ratio:.2f} out of range.")
        return False, {}
    
    if not (CUP_MIN_POSITION_MIN <= min_rel <= CUP_MIN_POSITION_MAX):
        print(f"[DEBUG] Cup min position {min_rel:.2f} out of range.")
        return False, {}


    data = {
        "cup_section": cup_section,
        "handle_section": handle_section,
        "left_min_idx": cup_section.idxmin(),
        "right_min_idx": handle_section.idxmin()
    }

    return True, data


def find_next_right_rim(smoothed: pd.Series, current_value: float, start: int) -> int:
    for i in range(start, 10, -1):
        val = smoothed.iloc[i]

        window = smoothed.iloc[max(i - 2, 0):min(i + 3, len(smoothed))]
        if val != window.max():
            continue
        
        current_price = smoothed.iloc[-1]
        if current_price < val * (1 - BREAKOUT_TOLERANCE):
            continue  # skip this right rim candidate


        segment = smoothed.iloc[i:]
        min_idx = segment.idxmin()
        if min_idx > smoothed.index[i] and smoothed.iloc[-1] > segment[min_idx]:
            return i
    return None


def detect_cup_and_handle(company: str):
    """
    Detects a cup and handle pattern for a given company.
    Scans through multiple right rim candidates and for each, iterates through
    possible left rim candidates, validating each for pattern structure.
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

    smoothing_window = auto_adjust_params(prices)
    smoothed = smooth_prices(prices, window=smoothing_window)
    current_value = smoothed.iloc[-1]

    start_idx = len(smoothed) - 2
    while True:
        right_rim_idx = find_next_right_rim(smoothed, current_value, start=start_idx)
        if right_rim_idx is None:
            print(f"[DEBUG] {company}: No valid right rim candidate formed a complete pattern.")
            return False, result_info

        result_info["right_rim"] = timestamps.iloc[right_rim_idx]

        for j in range(right_rim_idx - 1, 5, -1):
            val = smoothed.iloc[j]
            right_val = smoothed.iloc[right_rim_idx]
            if not (val >= right_val * (1 - LEFT_RIGHT_RIM_HEIGHT_TOLERANCE) and val <= right_val * (1 + LEFT_RIGHT_RIM_HEIGHT_TOLERANCE)):
                continue

            is_valid, pattern_data = validate_left_rim(smoothed, j, right_rim_idx)
            if is_valid:
                result_info["left_rim"] = timestamps.iloc[j]
                result_info["left_min"] = timestamps.loc[pattern_data["left_min_idx"]]
                result_info["right_min"] = timestamps.loc[pattern_data["right_min_idx"]]
                print(f"[INFO] {company}: Pattern detected.")
                result_info["pattern_detected"] = True
                return True, result_info

        start_idx = right_rim_idx - 1  # move to the next older right rim
