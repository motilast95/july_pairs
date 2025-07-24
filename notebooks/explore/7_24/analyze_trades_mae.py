# %% [markdown]
"""
# Trade Path and MAE Analysis

This script samples random trades from the backtest and visualizes their entry-to-exit PnL paths, highlighting maximum adverse excursion (MAE).
"""

# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Load trades data
trades = pd.read_csv('../../../results/data/trades_data.csv', parse_dates=['entry_date', 'exit_date'])
print(trades.head())

# %%
# Load price data
prices = pd.read_csv('../../../data/prices.csv', index_col=0, parse_dates=True)
print(prices.head())

# %%
def plot_trade_path(trade, prices):
    t1, t2 = trade['pair1'], trade['pair2']
    beta = trade.get('beta', 1.0)
    entry_date = pd.to_datetime(trade['entry_date'])
    exit_date = pd.to_datetime(trade['exit_date'])
    # Get price data for the trade period
    price_slice = prices.loc[entry_date:exit_date, [t1, t2]].copy()
    spread = price_slice[t1] - beta * price_slice[t2]
    pnl_path = spread - spread.iloc[0]
    adverse = pnl_path.cummin()
    mae = adverse.min()
    mae_idx = adverse.idxmin()
    plt.figure(figsize=(10, 4))
    plt.plot(pnl_path, label='PnL Path (Spread)')
    plt.scatter([pnl_path.index[0]], [0], color='green', label='Entry')
    plt.scatter([pnl_path.index[-1]], [pnl_path.iloc[-1]], color='blue', label='Exit')
    plt.scatter([mae_idx], [mae], color='red', label='MAE')
    plt.axhline(0, color='gray', linestyle='--')
    plt.title(f"Trade: {t1} - {beta:.2f}*{t2} | Entry: {entry_date.date()} | Exit: {exit_date.date()}")
    plt.xlabel('Date')
    plt.ylabel('Spread PnL (relative to entry)')
    plt.legend()
    plt.tight_layout()
    plt.show()

# %%
# Sample N random trades and plot
N = 5  # Number of trades to plot
sampled_trades = trades.sample(N, random_state=42)
for idx, trade in sampled_trades.iterrows():
    plot_trade_path(trade, prices)

# %%
# (Optional) Compute and plot MAE distribution for all trades
def compute_mae(trade, prices):
    t1, t2 = trade['pair1'], trade['pair2']
    beta = trade.get('beta', 1.0)
    entry_date = pd.to_datetime(trade['entry_date'])
    exit_date = pd.to_datetime(trade['exit_date'])
    price_slice = prices.loc[entry_date:exit_date, [t1, t2]].copy()
    spread = price_slice[t1] - beta * price_slice[t2]
    pnl_path = spread - spread.iloc[0]
    mae = pnl_path.cummin().min()
    return mae

trades['mae'] = trades.apply(lambda row: compute_mae(row, prices), axis=1)
print(trades['mae'].describe())
plt.hist(trades['mae'], bins=30)
plt.title('Distribution of Maximum Adverse Excursion (MAE)')
plt.xlabel('MAE')
plt.ylabel('Number of Trades')
plt.show() 
# %%
