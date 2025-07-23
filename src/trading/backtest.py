import pandas as pd
import numpy as np

def run_backtest(
    spread: pd.Series, 
    signals: pd.Series, 
    position_size: float = 100,
    transaction_cost_bps: float = 5.0
) -> dict:
    """
    Run a backtest using spread and trading signals with transaction costs.
    
    Args:
        spread: Price spread series
        signals: Trading signals (-1, 0, 1 or fractional positions)
        position_size: Dollar PnL per 1 spread point
        transaction_cost_bps: Transaction cost in basis points (0.05% = 5.0)
        
    Returns:
        Dictionary containing daily_pnl, cumulative_pnl, and trades
    """
    positions = signals.shift(1).fillna(0)
    spread_diff = spread.diff().fillna(0)
    
    # Calculate PnL from spread changes
    daily_pnl = positions * spread_diff * position_size
    
    # Calculate transaction costs
    position_changes = positions.diff().abs().fillna(0)
    transaction_costs = position_changes * spread * (transaction_cost_bps / 10000) * position_size
    
    # Net PnL after transaction costs
    daily_pnl_net = daily_pnl - transaction_costs
    cumulative_pnl = daily_pnl_net.cumsum()

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
            # Calculate gross PnL
            gross_pnl = (exit_price - entry_price) * position * position_size
            
            # Calculate transaction costs for this trade
            entry_cost = abs(position) * entry_price * (transaction_cost_bps / 10000) * position_size
            exit_cost = abs(position) * exit_price * (transaction_cost_bps / 10000) * position_size
            total_transaction_cost = entry_cost + exit_cost
            
            # Net PnL after transaction costs
            net_pnl = gross_pnl - total_transaction_cost
            
            trades.append({
                'entry_date': entry_date,
                'exit_date': exit_date,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'direction': 'long' if position == 1 else 'short',
                'gross_pnl': gross_pnl,
                'transaction_cost': total_transaction_cost,
                'net_pnl': net_pnl,
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
        # Calculate gross PnL
        gross_pnl = (exit_price - entry_price) * position * position_size
        
        # Calculate transaction costs for this trade
        entry_cost = abs(position) * entry_price * (transaction_cost_bps / 10000) * position_size
        exit_cost = abs(position) * exit_price * (transaction_cost_bps / 10000) * position_size
        total_transaction_cost = entry_cost + exit_cost
        
        # Net PnL after transaction costs
        net_pnl = gross_pnl - total_transaction_cost
        
        trades.append({
            'entry_date': entry_date,
            'exit_date': exit_date,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'direction': 'long' if position == 1 else 'short',
            'gross_pnl': gross_pnl,
            'transaction_cost': total_transaction_cost,
            'net_pnl': net_pnl,
            'holding_period': len(spread) - int(entry_idx) - 1
        })

    return {
        'daily_pnl': daily_pnl_net,  # Net PnL after transaction costs
        'daily_pnl_gross': daily_pnl,  # Gross PnL before transaction costs
        'daily_transaction_costs': transaction_costs,  # Daily transaction costs
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