"""
Data handling modules for the pairs trading system.

This module contains:
- data_loader: Price data loading and preprocessing
- pair_selection: Cointegration-based pair selection
"""

from .data_loader import load_prices, load_sector_tickers
from .pair_selection import select_pairs

__all__ = ['load_prices', 'load_sector_tickers', 'select_pairs'] 