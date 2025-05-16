import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from .preprocessing import smooth_prices
from .patterns import CUP_AND_HANDLE_CONFIG as CH
from ..config.constants import (
    STOCK_SYMBOLS,
    DATA_RETENTION_DAYS
)
from ..data.storage import get_prices
import base64
from io import BytesIO
from app.analysis.plotting import plot_prices


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
        return 5
    elif volatility < 0.015:
        return 7
    return 10


def passes_handle_checks(smoothed: pd.Series, right_rim_idx: int) -> bool:
    current_price = smoothed.iloc[-1]

    if current_price < smoothed.iloc[right_rim_idx] * (1 - CH.breakout_tolerance):
        print("[DEBUG] Right rim test - Breakout condition not met.")
        return False

    handle_section = smoothed.iloc[right_rim_idx:]
    middle_handle = handle_section.iloc[1:-1]
    handle_avg_ceiling = (smoothed.iloc[right_rim_idx] + current_price) / 2
    handle_max = middle_handle.max()
    handle_min = middle_handle.min()

    if handle_max > handle_avg_ceiling * (1 + CH.max_handle_peak_over_ceiling):
        print("[DEBUG] Right rim test - Handle peak exceeds allowed spike limit.")
        return False

    if (handle_avg_ceiling - handle_min) / handle_avg_ceiling < CH.min_handle_depth:
        print("[DEBUG] Right rim test - Handle depth too shallow.")
        return False

    handle_width = len(handle_section)
    total_length = len(smoothed)

    if handle_width < int(total_length * CH.handle_width_min_ratio_total) or handle_width > int(total_length * CH.handle_width_max_ratio_total):
        print("[DEBUG] Right rim test - Handle width out of bounds.")
        return False
    
    if current_price < (handle_min + (handle_avg_ceiling - handle_min)*CH.min_handle_recovery_ratio):
        print("[DEBUG] Right rim test - Not enough recovery from handle.")
        return False
    
    return True


def validate_full_pattern(smoothed: pd.Series, left_rim_idx: int, right_rim_idx: int) -> tuple:
    cup_section = smoothed.iloc[left_rim_idx:right_rim_idx + 1]
    handle_section = smoothed.iloc[right_rim_idx:]
    middle_cup = cup_section.iloc[1:-1]
    middle_handle = handle_section.iloc[1:-1]
    
    pattern_data = {
        "cup_section": cup_section,
        "handle_section": handle_section,
        "left_min_idx": cup_section.idxmin(),
        "right_min_idx": handle_section.idxmin()
    }

    rim_avg = (smoothed.iloc[left_rim_idx] + smoothed.iloc[right_rim_idx]) / 2
    cup_max = middle_cup.max()
    if cup_max > rim_avg * (1 + CH.max_cup_peak_above_rim):
        print("[DEBUG] Cup peak exceeds allowed spike limit.")
        return False, pattern_data

    cup_min = middle_cup.min()
    handle_min = middle_handle.min()

    if (rim_avg - cup_min) / rim_avg < CH.min_cup_depth:
        print("[DEBUG] Cup depth too shallow.")
        return False, pattern_data

    cup_width = right_rim_idx - left_rim_idx
    handle_width = len(handle_section)
    total_length = len(smoothed)

    if not (CH.cup_width_min_ratio <= cup_width / total_length <= CH.cup_width_max_ratio):
        print("[DEBUG] Cup width out of range.")
        return False, pattern_data

    if not (cup_width >= handle_width * CH.cup_handle_width_ratio):
        print("[DEBUG] Cup not wide enough relative to handle.")
        return False, pattern_data

    cup_depth = rim_avg - cup_min
    cup_depth_ratio = cup_depth / rim_avg if rim_avg > 0 else 0
    handle_depth = (smoothed.iloc[right_rim_idx] + smoothed.iloc[-1]) / 2 - handle_min
    cup_handle_depth_ratio = handle_depth / cup_depth if cup_depth > 0 else 0

    if cup_depth_ratio < CH.min_cup_depth or cup_depth_ratio > CH.max_cup_depth:
        print("[DEBUG] Cup depth ratio out of range.")
        return False, pattern_data

    if not (CH.handle_depth_ratio_min_vs_cup <= cup_handle_depth_ratio <= CH.handle_depth_ratio_max_vs_cup):
        print("[DEBUG] Handle depth ratio out of range.")
        return False, pattern_data

    min_idx = middle_cup.idxmin()
    min_pos = smoothed.index.get_loc(min_idx)
    min_rel = (min_pos - left_rim_idx) / (right_rim_idx - left_rim_idx)
    if not (CH.cup_min_position_min <= min_rel <= CH.cup_min_position_max):
        print("[DEBUG] Cup min position out of range.")
        return False, pattern_data

    return True, pattern_data


def find_next_right_rim(smoothed: pd.Series, start: int) -> int:
    min_right_rim_idx = int(len(smoothed)/2)
    for i in range(start, min_right_rim_idx, -1):
        val = smoothed.iloc[i]

        window = smoothed.iloc[max(i - 2, 0):min(i + 3, len(smoothed))]
        if val != window.max():
            continue

        if not passes_handle_checks(smoothed, i):
            continue

        return i
    return None


def detect_cup_and_handle(company: str):
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

    if df.empty or len(df) < 5 or 'price' not in df.columns:
        print(f"[Error] Not enough data to analyze pattern for company: {company}")
        raise ValueError(f"Not enough data to analyze pattern for company: {company}")

    prices = df['price']
    timestamps = df['timestamp']
    result_info["current"] = timestamps.iloc[-1]

    smoothing_window = auto_adjust_params(prices)
    smoothed = smooth_prices(prices, window=smoothing_window)

    start_idx = len(smoothed) - 2
    while True:
        right_rim_idx = find_next_right_rim(smoothed, start=start_idx)
        if right_rim_idx is None:
            print(f"[DEBUG] {company}: No valid right rim candidate.")
            return False, result_info, df

        result_info["right_rim"] = timestamps.iloc[right_rim_idx]

        for left_rim_idx in range(right_rim_idx - 2, 0, -1):
            val = smoothed.iloc[left_rim_idx]
            right_val = smoothed.iloc[right_rim_idx]
            if not (val >= right_val * (1 - CH.max_right_rim_drop_from_left) and val <= right_val * (1 + CH.max_right_rim_above_left)):
                continue
            
            result_info["left_rim"] = timestamps.iloc[left_rim_idx]
            
            is_valid, pattern_data = validate_full_pattern(smoothed, left_rim_idx, right_rim_idx)
            result_info["left_min"] = timestamps.loc[pattern_data["left_min_idx"]]
            result_info["right_min"] = timestamps.loc[pattern_data["right_min_idx"]]
            if is_valid:
                print(f"[INFO] {company}: Pattern detected.")
                result_info["pattern_detected"] = True
                return True, result_info, df

        start_idx = right_rim_idx - 1


def detect_cup_and_handle_wrapper(company: str, include_plot: bool = False):
    result, pattern_points, prices = detect_cup_and_handle(company)

    plot_b64 = None
    if include_plot:
        fig = plot_prices(
            company,
            prices=prices,
            title=f"{company} - Pattern Detected: {pattern_points.get('pattern_detected', False)}",
            pattern_points=pattern_points
        )
        if fig is None:
            raise ValueError(f"Not enough data to generate plot for company: {company}")

        buf = BytesIO()
        fig.savefig(buf, format="png")
        buf.seek(0)
        plot_b64 = base64.b64encode(buf.read()).decode("utf-8")
        buf.close()

    return result, plot_b64
