from typing import List, Tuple, Dict
import pandas as pd
import itertools
#from statsmodels.tsa.stattools import coint
#from config.screening import COINTEGRATION_SIGNIFICANCE
from src.models.model_fitting import is_spread_stationary

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