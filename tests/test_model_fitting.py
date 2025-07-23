import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pandas as pd
from src.models.model_fitting import fit_spread

def test_fit_spread_basic():
    prices = pd.DataFrame({
        'A': [1,2,3,4,5],
        'B': [2,3,4,5,6]
    }, index=pd.date_range('2020-01-01', periods=5))
    pair = ('A', 'B')
    window = slice(prices.index[0], prices.index[-1])
    result = fit_spread(pair, prices, window)
    assert isinstance(result, dict)
    assert 'beta' in result 