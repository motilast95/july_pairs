import pandas as pd
from typing import List, Dict

def aggregate_portfolio_pnl(results: List[Dict]) -> pd.Series:
    """
    Aggregate daily PnL across all pairs and windows to get portfolio-level PnL.
    Assumes each result dict contains a 'backtest_results' key with 'daily_pnl' (pd.Series).
    Returns a single pd.Series of portfolio daily PnL indexed by date.
    """
    pnl_series = []
    for res in results:
        # Support both possible structures: backtest_results or daily_pnl directly
        if 'backtest_results' in res and 'daily_pnl' in res['backtest_results']:
            pnl_series.append(res['backtest_results']['daily_pnl'])
        elif 'daily_pnl' in res:
            pnl_series.append(res['daily_pnl'])
    if not pnl_series:
        return pd.Series(dtype=float)
    pnl_df = pd.concat(pnl_series, axis=1).fillna(0)
    portfolio_pnl = pnl_df.sum(axis=1)
    return portfolio_pnl

def compute_portfolio_metrics(portfolio_pnl: pd.Series, initial_capital: float = None) -> Dict:
    """
    Compute performance metrics for the aggregated portfolio PnL.
    If initial_capital is provided, compute metrics based on returns (normalized), otherwise use raw PnL.
    """
    if initial_capital is not None:
        returns = portfolio_pnl / initial_capital
        total_return = (1 + returns).prod() - 1
        sharpe = returns.mean() / returns.std() * (252 ** 0.5) if returns.std() > 0 else float('nan')
        max_drawdown = (returns.cumsum().cummax() - returns.cumsum()).max()
    else:
        total_return = portfolio_pnl.sum()
        sharpe = portfolio_pnl.mean() / portfolio_pnl.std() * (252 ** 0.5) if portfolio_pnl.std() > 0 else float('nan')
        max_drawdown = (portfolio_pnl.cumsum().cummax() - portfolio_pnl.cumsum()).max()
    return {
        'total_return': total_return,
        'sharpe_ratio': sharpe,
        'max_drawdown': max_drawdown,
    }
