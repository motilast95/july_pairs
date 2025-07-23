import pandas as pd
import numpy as np

def run_backtest(spread: pd.Series, signals: pd.Series, position_size: float = 100) -> dict:
    """
    Run a simple backtest using spread and trading signals.
    Returns daily and cumulative PnL in dollars, and a trade log.
    """
    positions = signals.shift(1).fillna(0)
    spread_diff = spread.diff().fillna(0)
    daily_pnl = positions * spread_diff * position_size  # Convert to dollars
    cumulative_pnl = daily_pnl.cumsum()

    # Trade log
    trades = []
    position = 0
    entry_idx = None
    entry_price = None
    entry_date = None
    for t, (date, sig) in enumerate(signals.items()):
        if position == 0 and sig != 0:
            # Enter trade
            position = sig
            entry_idx = t
            entry_price = spread.iloc[t]
            entry_date = date
        elif position != 0 and sig == 0:
            # Exit trade
            exit_price = spread.iloc[t]
            exit_date = date
            pnl = (exit_price - entry_price) * position * position_size
            trades.append({
                'entry_date': entry_date,
                'exit_date': exit_date,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'direction': 'long' if position == 1 else 'short',
                'pnl': pnl,
                'holding_period': t - entry_idx
            })
            position = 0
            entry_idx = None
            entry_price = None
            entry_date = None
    # Force close at end if still open
    if position != 0 and entry_idx is not None:
        exit_price = spread.iloc[-1]
        exit_date = spread.index[-1]
        pnl = (exit_price - entry_price) * position * position_size
        trades.append({
            'entry_date': entry_date,
            'exit_date': exit_date,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'direction': 'long' if position == 1 else 'short',
            'pnl': pnl,
            'holding_period': len(spread) - int(entry_idx) - 1
        })

    return {
        'daily_pnl': daily_pnl,
        'cumulative_pnl': cumulative_pnl,
        'trades': trades
    }

def compute_performance_metrics(pnl: pd.Series) -> dict:
    """
    Compute basic performance metrics from daily PnL.
    """
    total_return = pnl.sum()
    sharpe = pnl.mean() / pnl.std() * np.sqrt(252) if pnl.std() > 0 else np.nan
    max_drawdown = (pnl.cumsum().cummax() - pnl.cumsum()).max()
    return {
        'total_return': total_return,
        'sharpe_ratio': sharpe,
        'max_drawdown': max_drawdown,
    } 