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

def compute_portfolio_metrics(portfolio_pnl: pd.Series, initial_capital: float = None, results: List[Dict] = None) -> Dict:
    """
    Compute performance metrics for the aggregated portfolio PnL.
    If initial_capital is provided, compute metrics based on returns (normalized), otherwise use raw PnL.
    
    IMPORTANT: This function now calculates metrics based on the actual trading period only,
    starting from the first test window date (when strategy goes live) rather than first non-zero PnL day.
    """
    if len(portfolio_pnl) == 0:
        return {
            'total_return': 0.0,
            'annualized_return': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'trading_days': 0,
            'total_days': 0,
            'first_test_date': None
        }
    
    # Find the first test window date (when strategy goes live)
    first_test_date = None
    if results and len(results) > 0:
        # Get the earliest test_start date from all results
        test_dates = []
        for res in results:
            if 'test_start' in res:
                test_dates.append(res['test_start'])
        if test_dates:
            first_test_date = min(test_dates)
    
    if first_test_date is None:
        # Fallback: find the first non-zero PnL day
        for i, pnl in enumerate(portfolio_pnl):
            if pnl != 0:
                first_test_date = portfolio_pnl.index[i]
                break
    
    if first_test_date is None:
        # No trading occurred at all
        return {
            'total_return': 0.0,
            'annualized_return': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'trading_days': 0,
            'total_days': len(portfolio_pnl),
            'first_test_date': None
        }
    
    # Use the entire period from first test window date onwards (including zero PnL days)
    trading_period_pnl = portfolio_pnl[portfolio_pnl.index >= first_test_date]
    
    # Calculate metrics based on the trading period (including zero PnL days)
    if initial_capital is not None:
        returns = trading_period_pnl / initial_capital
        total_return = (1 + returns).prod() - 1
        sharpe = returns.mean() / returns.std() * (252 ** 0.5) if returns.std() > 0 else float('nan')
        max_drawdown = (returns.cumsum().cummax() - returns.cumsum()).max()
    else:
        total_return = trading_period_pnl.sum()
        sharpe = trading_period_pnl.mean() / trading_period_pnl.std() * (252 ** 0.5) if trading_period_pnl.std() > 0 else float('nan')
        max_drawdown = (trading_period_pnl.cumsum().cummax() - trading_period_pnl.cumsum()).max()
    
    # Calculate annualized return based on actual trading period
    if len(trading_period_pnl) > 0:
        # Calculate the number of years in the trading data
        start_date = trading_period_pnl.index[0]
        end_date = trading_period_pnl.index[-1]
        years = (end_date - start_date).days / 365.25
        
        if years > 0:
            if initial_capital is not None:
                # For return-based calculation
                annualized_return = (1 + total_return) ** (1 / years) - 1
            else:
                # For PnL-based calculation, assume initial capital of 1
                annualized_return = (1 + total_return) ** (1 / years) - 1
        else:
            annualized_return = float('nan')
    else:
        annualized_return = float('nan')
    
    # Calculate training days removed (days before first test window)
    training_days_removed = 0
    if first_test_date is not None:
        training_days_removed = len(portfolio_pnl[portfolio_pnl.index < first_test_date])
    
    return {
        'total_return': total_return,
        'annualized_return': annualized_return,
        'sharpe_ratio': sharpe,
        'max_drawdown': max_drawdown,
        'trading_days': len(trading_period_pnl),
        'total_days': len(portfolio_pnl),
        'training_days_removed': training_days_removed,
        'first_test_date': first_test_date
    }
