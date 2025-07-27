#!/usr/bin/env python3
"""
Data loading utilities for the pairs trading system.
Supports loading price data and sector information for different universes.
"""

import pandas as pd
import yfinance as yf
from typing import Dict, List
import logging
import os
import pickle
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def get_cache_path(universe: str, start_date: str, end_date: str) -> str:
    """Generate cache file path for universe data."""
    cache_dir = "data/cache"
    os.makedirs(cache_dir, exist_ok=True)
    
    # Create a filename based on universe and date range
    filename = f"{universe}_{start_date}_{end_date}.pkl"
    return os.path.join(cache_dir, filename)

def is_cache_valid(cache_path: str, max_age_days: int = 7) -> bool:
    """Check if cached data is still valid (not too old)."""
    if not os.path.exists(cache_path):
        return False
    
    # Check file modification time
    file_time = datetime.fromtimestamp(os.path.getmtime(cache_path))
    age = datetime.now() - file_time
    
    return age.days < max_age_days

def load_cached_data(cache_path: str) -> pd.DataFrame:
    """Load data from cache file."""
    try:
        with open(cache_path, 'rb') as f:
            data = pickle.load(f)
        logger.info(f"Loaded cached data from {cache_path}")
        return data
    except Exception as e:
        logger.warning(f"Failed to load cached data: {e}")
        return None

def save_cached_data(cache_path: str, data: pd.DataFrame):
    """Save data to cache file."""
    try:
        with open(cache_path, 'wb') as f:
            pickle.dump(data, f)
        logger.info(f"Saved data to cache: {cache_path}")
    except Exception as e:
        logger.warning(f"Failed to save cached data: {e}")

def load_prices_for_universe(universe: str, start_date: str = None, end_date: str = None, use_cache: bool = True) -> pd.DataFrame:
    """
    Load price data for a specific universe with optional caching.
    
    Args:
        universe: 'mega_cap', 'mid_cap', or 'custom'
        start_date: Start date for data (optional)
        end_date: End date for data (optional)
        use_cache: Whether to use cached data if available
    
    Returns:
        DataFrame with price data for the universe
    """
    from src.data.universe_manager import UniverseManager
    
    universe_manager = UniverseManager()
    tickers = universe_manager.get_universe_tickers(universe)
    
    logger.info(f"Loading price data for {universe} universe ({len(tickers)} tickers)")
    
    # Check cache first
    if use_cache:
        cache_path = get_cache_path(universe, start_date or "2016-01-01", end_date or "2025-12-31")
        if is_cache_valid(cache_path):
            cached_data = load_cached_data(cache_path)
            if cached_data is not None:
                return cached_data
    
    # Download data using yfinance
    logger.info("Downloading fresh data from Yahoo Finance...")
    data = yf.download(tickers, start=start_date, end=end_date, progress=False)
    
    # Handle different data structures from yfinance
    if isinstance(data.columns, pd.MultiIndex):
        # Multi-level columns (multiple tickers)
        if 'Adj Close' in data.columns.get_level_values(0):
            prices = data['Adj Close']
        elif 'Close' in data.columns.get_level_values(0):
            prices = data['Close']
        else:
            # If no Adj Close or Close, use the first available price column
            price_cols = [col for col in data.columns.get_level_values(0) if col in ['Open', 'High', 'Low', 'Close']]
            if price_cols:
                prices = data[price_cols[0]]
            else:
                raise ValueError("No price columns found in downloaded data")
    else:
        # Single ticker case
        if 'Adj Close' in data.columns:
            prices = data[['Adj Close']]
        elif 'Close' in data.columns:
            prices = data[['Close']]
        else:
            # If no Adj Close or Close, use the first available price column
            price_cols = [col for col in data.columns if col in ['Open', 'High', 'Low', 'Close']]
            if price_cols:
                prices = data[[price_cols[0]]]
            else:
                raise ValueError("No price columns found in downloaded data")
    
    # Remove any tickers that failed to download
    failed_tickers = [col for col in prices.columns if prices[col].isna().all()]
    if failed_tickers:
        logger.warning(f"Failed to download data for tickers: {failed_tickers}")
        prices = prices.drop(columns=failed_tickers)
    
    # Cache the successful data
    if use_cache and len(prices.columns) > 0:
        cache_path = get_cache_path(universe, start_date or "2016-01-01", end_date or "2025-12-31")
        save_cached_data(cache_path, prices)
    
    logger.info(f"Successfully loaded data for {len(prices.columns)} tickers")
    return prices

def load_sector_tickers_for_universe(universe: str) -> Dict[str, List[str]]:
    """
    Load sector groupings for a specific universe.
    
    Args:
        universe: 'mega_cap', 'mid_cap', or 'custom'
    
    Returns:
        Dictionary mapping sector names to lists of tickers
    """
    from src.data.universe_manager import UniverseManager
    
    universe_manager = UniverseManager()
    return universe_manager.get_universe_sectors(universe)

def load_universe_parameters(universe: str) -> Dict:
    """
    Load universe-specific parameters (transaction costs, position sizes, etc.).
    
    Args:
        universe: 'mega_cap', 'mid_cap', or 'custom'
    
    Returns:
        Dictionary of universe-specific parameters
    """
    from src.data.universe_manager import UniverseManager
    
    universe_manager = UniverseManager()
    return universe_manager.get_universe_parameters(universe)

def clear_cache(universe: str = None):
    """
    Clear cached data files.
    
    Args:
        universe: Specific universe to clear, or None to clear all
    """
    cache_dir = "data/cache"
    if not os.path.exists(cache_dir):
        logger.info("No cache directory found")
        return
    
    if universe:
        # Clear specific universe cache
        pattern = f"{universe}_*.pkl"
        import glob
        files = glob.glob(os.path.join(cache_dir, pattern))
        for file in files:
            os.remove(file)
            logger.info(f"Removed cache file: {file}")
    else:
        # Clear all cache
        import shutil
        shutil.rmtree(cache_dir)
        logger.info("Cleared all cached data")

# Legacy functions for backward compatibility
def load_prices(file_path: str) -> pd.DataFrame:
    """Legacy function - loads prices from CSV file."""
    logger.warning("Using legacy load_prices function. Consider using load_prices_for_universe instead.")
    return pd.read_csv(file_path, index_col=0, parse_dates=True)

def load_sector_tickers(file_path: str) -> Dict[str, List[str]]:
    """Legacy function - loads sector tickers from Python file."""
    logger.warning("Using legacy load_sector_tickers function. Consider using load_sector_tickers_for_universe instead.")
    import importlib.util
    spec = importlib.util.spec_from_file_location("data_params", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.sector_tickers 