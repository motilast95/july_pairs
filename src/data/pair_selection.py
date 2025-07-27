from typing import List, Tuple, Dict
import pandas as pd
import numpy as np
import itertools
#from statsmodels.tsa.stattools import coint
#from config.screening import COINTEGRATION_SIGNIFICANCE
from src.models.model_fitting import is_spread_stationary
from src.analysis.performance import time_function

@time_function("pair_selection")
def select_pairs(prices: pd.DataFrame, sector_tickers: Dict[str, list], window: slice, adf_alpha: float = 0.05) -> List[Tuple[str, str]]:
    """
    Select pairs of stocks whose spread is stationary (ADF test) within the given window.
    Returns a list of (ticker1, ticker2) tuples.
    Only considers pairs within the same sector.
    """
    selected_pairs = []
    for sector, tickers in sector_tickers.items():
        sector_prices = prices.loc[window, tickers].dropna(axis=1, how='any')
        for t1, t2 in itertools.combinations(sector_prices.columns, 2):
            series1 = sector_prices[t1]
            series2 = sector_prices[t2]
            if len(series1) < 2 or len(series2) < 2:
                continue
            is_stat, pvalue, beta = is_spread_stationary(series1, series2, adf_alpha=adf_alpha)
            if is_stat:
                selected_pairs.append((t1, t2))
    return selected_pairs

@time_function("fast_pair_selection")
def select_pairs_fast(prices: pd.DataFrame, sector_tickers: Dict[str, list], window: slice, 
                     adf_alpha: float = 0.05, distance_threshold: float = 0.1) -> List[Tuple[str, str]]:
    """
    Fast pair selection using distance-based pre-screening before ADF tests.
    
    Args:
        prices: DataFrame with price data
        sector_tickers: Dictionary mapping sectors to ticker lists
        window: Slice object defining the time window
        adf_alpha: Significance level for ADF test
        distance_threshold: Maximum normalized distance for pre-screening (default: 0.1)
    
    Returns:
        List of (ticker1, ticker2) tuples that pass both distance and ADF tests
    """
    selected_pairs = []
    
    for sector, tickers in sector_tickers.items():
        # Get sector prices for the window
        sector_prices = prices.loc[window, tickers].dropna(axis=1, how='any')
        
        if len(sector_prices.columns) < 2:
            continue
            
        # Normalize prices to [0,1] range for distance calculation
        normalized_prices = sector_prices.copy()
        for col in normalized_prices.columns:
            col_min = normalized_prices[col].min()
            col_max = normalized_prices[col].max()
            if col_max > col_min:
                normalized_prices[col] = (normalized_prices[col] - col_min) / (col_max - col_min)
        
        # Find pairs with low distance (similar price movements)
        low_distance_pairs = []
        for t1, t2 in itertools.combinations(sector_prices.columns, 2):
            # Calculate Euclidean distance between normalized price series
            distance = np.sqrt(np.mean((normalized_prices[t1] - normalized_prices[t2])**2))
            
            # Check if distance is below threshold (lower distance = more similar)
            if distance <= distance_threshold:
                low_distance_pairs.append((t1, t2, distance))
        
        # Sort by distance (lowest first) for better pairs
        low_distance_pairs.sort(key=lambda x: x[2])
        
        # Now do ADF tests only on low-distance pairs
        for t1, t2, distance in low_distance_pairs:
            series1 = sector_prices[t1]
            series2 = sector_prices[t2]
            
            # Skip if insufficient data
            if len(series1) < 30 or len(series2) < 30:
                continue
                
            # Perform ADF test
            is_stat, pvalue, beta = is_spread_stationary(series1, series2, adf_alpha=adf_alpha)
            
            if is_stat:
                selected_pairs.append((t1, t2))
    
    return selected_pairs

@time_function("ultra_fast_pair_selection")
def select_pairs_ultra_fast(prices: pd.DataFrame, sector_tickers: Dict[str, list], window: slice,
                          distance_threshold: float = 0.08, max_pairs_per_sector: int = 10) -> List[Tuple[str, str]]:
    """
    Ultra-fast pair selection using only distance (no ADF tests).
    Use this for very fast iteration when you want to test many parameters quickly.
    
    Args:
        prices: DataFrame with price data
        sector_tickers: Dictionary mapping sectors to ticker lists
        window: Slice object defining the time window
        distance_threshold: Maximum normalized distance for selection (default: 0.08)
        max_pairs_per_sector: Maximum pairs to select per sector (default: 10)
    
    Returns:
        List of (ticker1, ticker2) tuples with lowest distances
    """
    selected_pairs = []
    
    for sector, tickers in sector_tickers.items():
        # Get sector prices for the window
        sector_prices = prices.loc[window, tickers].dropna(axis=1, how='any')
        
        if len(sector_prices.columns) < 2:
            continue
            
        # Normalize prices to [0,1] range for distance calculation
        normalized_prices = sector_prices.copy()
        for col in normalized_prices.columns:
            col_min = normalized_prices[col].min()
            col_max = normalized_prices[col].max()
            if col_max > col_min:
                normalized_prices[col] = (normalized_prices[col] - col_min) / (col_max - col_min)
        
        # Find all pairs with low distance
        low_distance_pairs = []
        for t1, t2 in itertools.combinations(sector_prices.columns, 2):
            # Calculate Euclidean distance between normalized price series
            distance = np.sqrt(np.mean((normalized_prices[t1] - normalized_prices[t2])**2))
            
            # Check if distance is below threshold
            if distance <= distance_threshold:
                low_distance_pairs.append((t1, t2, distance))
        
        # Sort by distance and take top pairs
        low_distance_pairs.sort(key=lambda x: x[2])
        
        # Take top pairs per sector
        top_pairs = low_distance_pairs[:max_pairs_per_sector]
        
        for t1, t2, distance in top_pairs:
            selected_pairs.append((t1, t2))
    
    return selected_pairs

def compare_pair_selection_methods(prices: pd.DataFrame, sector_tickers: Dict[str, list], 
                                 window: slice, adf_alpha: float = 0.05) -> Dict:
    """
    Compare different pair selection methods for speed and results.
    
    Returns:
        Dictionary with comparison results
    """
    import time
    
    # Test original method
    start_time = time.time()
    original_pairs = select_pairs(prices, sector_tickers, window, adf_alpha)
    original_time = time.time() - start_time
    
    # Test fast method
    start_time = time.time()
    fast_pairs = select_pairs_fast(prices, sector_tickers, window, adf_alpha, distance_threshold=0.1)
    fast_time = time.time() - start_time
    
    # Test ultra-fast method
    start_time = time.time()
    ultra_pairs = select_pairs_ultra_fast(prices, sector_tickers, window, distance_threshold=0.08)
    ultra_time = time.time() - start_time
    
    return {
        'original': {
            'pairs': original_pairs,
            'count': len(original_pairs),
            'time': original_time
        },
        'fast': {
            'pairs': fast_pairs,
            'count': len(fast_pairs),
            'time': fast_time,
            'speedup': original_time / fast_time if fast_time > 0 else float('inf')
        },
        'ultra_fast': {
            'pairs': ultra_pairs,
            'count': len(ultra_pairs),
            'time': ultra_time,
            'speedup': original_time / ultra_time if ultra_time > 0 else float('inf')
        }
    } 