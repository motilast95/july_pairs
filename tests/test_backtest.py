import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pandas as pd
import numpy as np
from src.trading.backtest import run_backtest, compute_performance_metrics

def test_run_backtest_and_metrics():
    spread = pd.Series(np.cumsum(np.random.normal(0, 1, 100)))
    signals = pd.Series([0]*50 + [1]*50)
    results = run_backtest(spread, signals)
    assert 'daily_pnl' in results
    assert 'cumulative_pnl' in results
    metrics = compute_performance_metrics(results['daily_pnl'])
    assert 'total_return' in metrics
    assert 'sharpe_ratio' in metrics
    assert 'max_drawdown' in metrics 