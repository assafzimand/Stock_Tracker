"""
This module initializes the analysis package by exposing key functions for

detecting patterns and plotting.

Exports:
- detect_cup_and_handle: Function to detect the 'cup and handle' pattern in

stock prices.
- plot_prices: Function to plot stock prices.
"""

from .detector import detect_cup_and_handle
from .plotting import plot_prices

__all__ = ["detect_cup_and_handle", "plot_prices"]
