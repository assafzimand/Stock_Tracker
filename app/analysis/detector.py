import pandas as pd
import numpy as np
from scipy.signal import argrelextrema
from datetime import datetime, timedelta, timezone
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
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def get_symbol(company: str) -> str:
    """
    Retrieve the stock symbol for a given company name.

    Args:
        company (str): The name of the company.

    Returns:
        str: The stock symbol associated with the company.

    Raises:
        ValueError: If the company name is not recognized.
    """
    reverse_lookup = {v: k for k, v in STOCK_SYMBOLS.items()}
    symbol = reverse_lookup.get(company)
    if symbol is None:
        raise ValueError(f"Unknown company name: {company}")
    return symbol


def get_price_data(symbol: str) -> pd.DataFrame:
    """
    Fetch historical price data for a given stock symbol.

    Args:
        symbol (str): The stock symbol.

    Returns:
        pd.DataFrame: A DataFrame containing the historical price data.
    """
    to_ts = datetime.now(timezone.utc)
    from_ts = to_ts - timedelta(days=DATA_RETENTION_DAYS)
    return get_prices(symbol, from_ts, to_ts)


def auto_adjust_params(prices: pd.Series) -> int:
    """
    Automatically adjust parameters based on price volatility.

    Args:
        prices (pd.Series): A series of stock prices.

    Returns:
        int: The adjusted parameter value.
    """
    variance = prices.pct_change().rolling(window=5).std().mean()
    volatility = variance if not np.isnan(variance) else 0.01

    if volatility < 0.005:
        return 5
    elif volatility < 0.015:
        return 7
    return 10


def passes_handle_checks(smoothed: pd.Series, right_rim_idx: int) -> bool:
    """
    Validate the handle section of the pattern.

    Args:
        smoothed (pd.Series): The smoothed price series.
        right_rim_idx (int): The index of the right rim.

    Returns:
        bool: True if the handle section passes all checks, False otherwise.
    """
    current_price = smoothed.iloc[-1]

    if current_price < smoothed.iloc[right_rim_idx] * (1 - CH.breakout_tolerance):
        logging.debug("Right rim test - Breakout condition not met.")
        return False
    
    if current_price > smoothed.iloc[right_rim_idx] * (1 + CH.max_breakout_extension_ratio):
        logging.debug("Right rim test - Breakout extension too large.")
        return False

    handle_section = smoothed.iloc[right_rim_idx:]
    middle_handle = handle_section.iloc[1:-1]
    handle_ceiling = smoothed.iloc[right_rim_idx]
    handle_min = middle_handle.min()

    local_maxima_idx = argrelextrema(middle_handle.values, np.greater)[0]
    if len(local_maxima_idx) > 0:
        middle_handle_max = middle_handle.iloc[local_maxima_idx].max()
        if middle_handle_max > handle_ceiling * (1 + CH.max_handle_peak_over_ceiling):
            logging.debug(
                "Right rim test - Handle peak exceeds allowed spike limit."
            )
            return False

    if (handle_ceiling - handle_min) / handle_ceiling < CH.min_handle_depth:
        logging.debug(
            f"Right rim test - Handle depth too shallow: handle_min: {handle_min}, "
            f"handle_ceiling: {handle_ceiling}, handle_depth: "
            f"{(handle_ceiling - handle_min) / handle_ceiling}"
        )
        return False

    handle_width = len(handle_section)
    total_length = len(smoothed)

    if (handle_width < int(total_length * CH.handle_width_min_ratio_total) or 
        handle_width > int(total_length * CH.handle_width_max_ratio_total)):
        logging.debug("Right rim test - Handle width out of bounds.")
        return False
    
    if current_price < (handle_min + (handle_ceiling - handle_min) * 
                        CH.min_handle_recovery_ratio):
        logging.debug("Right rim test - Not enough recovery from handle's minimum.")
        return False
    
    return True


def validate_full_pattern(smoothed: pd.Series, left_rim_idx: int, right_rim_idx: int) -> tuple:
    """
    Validate the full 'cup and handle' pattern.

    Args:
        smoothed (pd.Series): The smoothed price series.
        left_rim_idx (int): The index of the left rim.
        right_rim_idx (int): The index of the right rim.

    Returns:
        tuple: A tuple containing a boolean indicating if the pattern is valid and a dictionary
        with pattern data.
    """
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

    cup_ceiling = min(smoothed.iloc[left_rim_idx], smoothed.iloc[right_rim_idx])
    local_maxima_idx = argrelextrema(middle_cup.values, np.greater)[0]
    if len(local_maxima_idx) > 0:
        middle_cup_max = middle_cup.iloc[local_maxima_idx].max()
        if middle_cup_max > cup_ceiling * (1 + CH.max_cup_peak_above_rim):
            logging.debug(
                f"Cup peak exceeds allowed spike limit, ceiling value: {cup_ceiling}, "
                f"max local peak: {middle_cup_max}"
            )
            return False, pattern_data

    cup_min = middle_cup.min()
    handle_min = middle_handle.min()

    if (cup_ceiling - cup_min) / cup_ceiling < CH.min_cup_depth:
        logging.debug(
            f"Cup depth too shallow: cup_min: {cup_min}, cup_ceiling: {cup_ceiling}, "
            f"cup_depth: {(cup_ceiling - cup_min) / cup_ceiling}"
        )
        return False, pattern_data

    cup_width = right_rim_idx - left_rim_idx
    handle_width = len(handle_section)
    total_length = len(smoothed)

    if not (CH.cup_width_min_ratio <= cup_width / total_length <= \
            CH.cup_width_max_ratio):
        logging.debug("Cup width out of range.")
        return False, pattern_data

    if not (CH.min_cup_to_handle_width_ratio <= cup_width / handle_width <= \
            CH.max_cup_to_handle_width_ratio):
        logging.debug("Cup not wide enough relative to handle.")
        return False, pattern_data

    cup_depth = cup_ceiling - cup_min
    cup_depth_ratio = cup_depth / cup_ceiling if cup_ceiling > 0 else 0
    handle_ceiling = smoothed.iloc[right_rim_idx]
    handle_depth = handle_ceiling - handle_min
    cup_handle_depth_ratio = handle_depth / cup_depth if cup_depth > 0 else 0

    if cup_depth_ratio < CH.min_cup_depth or cup_depth_ratio > CH.max_cup_depth:
        logging.debug("Cup depth ratio out of range.")
        return False, pattern_data

    if not (CH.handle_depth_ratio_min_vs_cup <= cup_handle_depth_ratio <= \
            CH.handle_depth_ratio_max_vs_cup):
        logging.debug("Handle depth ratio out of range.")
        return False, pattern_data

    min_idx = middle_cup.idxmin()
    min_pos = smoothed.index.get_loc(min_idx)
    min_rel = (min_pos - left_rim_idx) / (right_rim_idx - left_rim_idx)
    if not (CH.cup_min_position_min <= min_rel <= CH.cup_min_position_max):
        logging.debug("Cup min position out of range.")
        return False, pattern_data

    avg_cup_value = middle_cup.mean()
    if (cup_ceiling - avg_cup_value) / cup_ceiling < CH.min_avg_cup_value_vs_ceiling_ratio:
        logging.debug("Cup depth ratio out of range.")
        return False, pattern_data

    return True, pattern_data


def find_next_right_rim(smoothed: pd.Series, start: int) -> int:
    """
    Find the next right rim candidate in the smoothed price series.

    Args:
        smoothed (pd.Series): The smoothed price series.
        start (int): The starting index for the search.

    Returns:
        int: The index of the next right rim candidate, or None if not found.
    """
    min_right_rim_idx = int(len(smoothed)/2)
    for i in range(start, min_right_rim_idx, -1):
        val = smoothed.iloc[i]
        logging.debug(f"Value at {i}: {val}")

        if not passes_handle_checks(smoothed, i):
            continue

        return i
    return None


def detect_cup_and_handle(company: str):
    """
    Detect the 'cup and handle' pattern for a given company.

    Args:
        company (str): The name of the company.

    Returns:
        tuple: A tuple containing a boolean indicating if the pattern is detected, a dictionary
        with pattern information, and a DataFrame with price data.

    Raises:
        ValueError: If there is not enough data to analyze the pattern.
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

    if df.empty or len(df) < 5 or 'price' not in df.columns:
        logging.error(
            f"Not enough data to analyze pattern for company: {company}"
        )
        raise ValueError(
            f"Not enough data to analyze pattern for company: {company}"
        )

    prices = df['price']
    timestamps = df['timestamp']
    result_info["current"] = timestamps.iloc[-1]

    smoothing_window = auto_adjust_params(prices)
    smoothed = smooth_prices(prices, window=smoothing_window)

    # Start searching for the right rim from the end of the smoothed data
    start_idx = len(smoothed) - 2
    while True:
        right_rim_idx = find_next_right_rim(smoothed, start=start_idx)
        if right_rim_idx is None:
            logging.debug(f"{company}: No valid right rim candidate.")
            return False, result_info, df

        result_info["right_rim"] = timestamps.iloc[right_rim_idx]

        # Validate left rim and full pattern
        if find_left_rim_and_validate_pattern(smoothed, timestamps, right_rim_idx, result_info):
            logging.info(f"{company}: Pattern detected.")
            result_info["pattern_detected"] = True
            return True, result_info, df

        # Move to the next potential right rim
        start_idx = right_rim_idx - 1


def validate_left_rim(smoothed, right_rim_idx, left_rim_idx):
    """
    Validate a specific left rim index.

    Args:
        smoothed (pd.Series): Smoothed price series.
        right_rim_idx (int): Index of the right rim.
        left_rim_idx (int): Index of the left rim candidate.

    Returns:
        bool: True if the left rim is valid, False otherwise.
    """
    right_val = smoothed.iloc[right_rim_idx]
    left_val = smoothed.iloc[left_rim_idx]

    if not (left_val >= right_val * (1 - CH.max_right_rim_drop_from_left) and 
            left_val <= right_val * (1 + CH.max_right_rim_above_left)):
        return False
    
    return True


def find_left_rim_and_validate_pattern(smoothed, timestamps, right_rim_idx, result_info):
    """
     Try all possible left rim candidates and validate the full pattern.

    Args:
        smoothed (pd.Series): The smoothed price series.
        timestamps (pd.Series): The timestamps corresponding to the price series.
        right_rim_idx (int): The index of the right rim.
        result_info (dict): Dictionary to store pattern information.

    Returns:
        bool: True if the pattern is valid, False otherwise.
    """
    for left_rim_idx in range(right_rim_idx - 2, 0, -1):
        if not validate_left_rim(smoothed, right_rim_idx, left_rim_idx):
            continue
        
        result_info["left_rim"] = timestamps.iloc[left_rim_idx]

        is_valid, pattern_data = validate_full_pattern(smoothed, left_rim_idx, right_rim_idx)
        result_info["left_min"] = timestamps.loc[pattern_data["left_min_idx"]]
        result_info["right_min"] = timestamps.loc[pattern_data["right_min_idx"]]
        if is_valid:
            return True

    return False


def detect_cup_and_handle_wrapper(company: str, include_plot: bool = False):
    """
    Wrapper function to detect the 'cup and handle' pattern and optionally generate a plot.

    Args:
        company (str): The name of the company.
        include_plot (bool): Whether to include a plot of the pattern.

    Returns:
        tuple: A tuple containing the detection result, the plot in base64 format if requested.

    Raises:
        ValueError: If there is not enough data to generate the plot.
    """
    result, pattern_points, prices = detect_cup_and_handle(company)

    plot_b64 = None
    if include_plot:
        fig = plot_prices(
            company,
            prices=prices,
            title=(
                f"{company} - Pattern Detected: "
                f"{pattern_points.get('pattern_detected', False)}"
            ),
            pattern_points=pattern_points
        )
        if fig is None:
            raise ValueError(
                f"Not enough data to generate plot for company: {company}"
            )

        buf = BytesIO()
        fig.savefig(buf, format="png")
        buf.seek(0)
        plot_b64 = base64.b64encode(buf.read()).decode("utf-8")
        buf.close()

    return result, plot_b64
