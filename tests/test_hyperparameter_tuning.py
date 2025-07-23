import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pandas as pd
import numpy as np
from hyperparameter_tuning import tune_hyperparameters

def test_tune_hyperparameters_basic():
    prices = pd.DataFrame({
        'A': np.arange(10),
        'B': np.arange(10, 20)
    }, index=pd.date_range('2020-01-01', periods=10))
    pair = ('A', 'B')
    window = slice(prices.index[0], prices.index[-1])
    model_params = {
        'spread': prices['A'] - prices['B'],
        'spread_mean': 0,
        'spread_std': 1
    }
    result = tune_hyperparameters(pair, prices, window, model_params)
    assert isinstance(result, dict) 