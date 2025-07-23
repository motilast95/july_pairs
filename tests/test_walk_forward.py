import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pandas as pd
from walk_forward import walk_forward

def test_walk_forward_basic():
    # Create sample price data
    prices = pd.DataFrame({
        'A': [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30],
        'B': [2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31],
        'C': [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
    }, index=pd.date_range('2020-01-01', periods=30))
    sector_tickers = {'sector1': ['A', 'B', 'C']}
    config = {
        'train_size': 10,
        'test_size': 5,
        'entry_z': 1.0,
        'exit_z': 0.5
    }
    results = walk_forward(prices, sector_tickers, config)
    print('DEBUG walk_forward results:', results)
    assert isinstance(results, list)
    if results:
        assert 'pair' in results[0]
        assert 'metrics' in results[0] 