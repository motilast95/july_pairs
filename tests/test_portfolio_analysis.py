import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pandas as pd
import numpy as np
from src.analysis.portfolio_analysis import aggregate_portfolio_pnl, compute_portfolio_metrics

def test_portfolio_aggregation_and_metrics():
    # Create fake per-pair results with daily_pnl series
    idx1 = pd.date_range('2020-01-01', periods=5)
    idx2 = pd.date_range('2020-01-03', periods=5)
    res1 = {'daily_pnl': pd.Series([1, 2, 3, 4, 5], index=idx1)}
    res2 = {'daily_pnl': pd.Series([-1, -2, -1, 0, 1], index=idx2)}
    results = [res1, res2]
    portfolio_pnl = aggregate_portfolio_pnl(results)
    assert isinstance(portfolio_pnl, pd.Series)
    assert not portfolio_pnl.empty
    metrics = compute_portfolio_metrics(portfolio_pnl)
    assert 'total_return' in metrics
    assert 'sharpe_ratio' in metrics
    assert 'max_drawdown' in metrics 