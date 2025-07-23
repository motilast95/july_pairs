import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pandas as pd
from pair_selection import select_pairs

def test_select_pairs_basic():
    prices = pd.DataFrame({
        'A': [1,2,3,4,5],
        'B': [2,3,4,5,6],
        'C': [1,1,1,1,1]
    }, index=pd.date_range('2020-01-01', periods=5))
    sector_tickers = {'sector1': ['A', 'B', 'C']}
    window = slice(prices.index[0], prices.index[-1])
    pairs = select_pairs(prices, sector_tickers, window)
    assert isinstance(pairs, list) 