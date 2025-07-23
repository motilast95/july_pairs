import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data_loader import load_prices, load_sector_tickers
from walk_forward import walk_forward
from portfolio_analysis import aggregate_portfolio_pnl, compute_portfolio_metrics
from model_fitting import fit_spread
from signal_generation import generate_signals, generate_rolling_signals, generate_rolling_scaled_signals

# ---- Load Data ----
prices = load_prices('data/prices.csv')
sector_tickers = load_sector_tickers('config/data_params.py')

# ---- Config ----
config = {
    'train_size': 504,
    'test_size': 126,
    'entry_z': 1.0,
    'exit_z': 0.5,
    'prototype': True,
    'tickers': prices.columns.tolist(),
    'start_date': '2016-01-01',
    'end_date': '2025-07-01',
    'signal_method': 'rolling_scaled',
    'rolling_window': 60
}
# ---- Run Walkforward ----
results = walk_forward(prices, sector_tickers, config)
# ---- Portfolio Analysis ----
portfolio_pnl = aggregate_portfolio_pnl(results)
metrics = compute_portfolio_metrics(portfolio_pnl)
print('Portfolio Metrics:')
for k, v in metrics.items():
    print(f'{k}: {v}')

def trade_stats(signals):
    entries = (signals.shift(1) == 0) & (signals != 0)
    exits = (signals.shift(1) != 0) & (signals == 0)
    n_trades = entries.sum()
    holding_periods = []
    entry_idx = None
    for i, (ent, ex) in enumerate(zip(entries, exits)):
        if ent:
            entry_idx = i
        if ex and entry_idx is not None:
            holding_periods.append(i - entry_idx)
            entry_idx = None
    avg_holding = sum(holding_periods) / len(holding_periods) if holding_periods else 0
    return int(n_trades), avg_holding
# ---- Add Trade Stats to All Results ----
for res in results:
    pair = res['pair']
    train_start = res['train_start']
    test_start = res['test_start']
    train_window = slice(train_start, test_start)
    model_params = fit_spread(pair, prices, train_window)
    if not model_params:
        res['n_trades'] = 0
        res['avg_holding'] = 0
        continue
    beta = model_params['beta']
    spread_mean = model_params['spread_mean']
    spread_std = model_params['spread_std']
    test_window = slice(test_start, prices.index[min(prices.index.get_loc(test_start) + config['test_size'] - 1, len(prices.index)-1)])
    spread_test = prices.loc[test_window, pair[0]] - beta * prices.loc[test_window, pair[1]]
    signals = generate_signals(spread_test, spread_mean, spread_std, config['entry_z'], config['exit_z'])
    n_trades, avg_holding = trade_stats(signals)
    res['n_trades'] = n_trades
    res['avg_holding'] = avg_holding

# Convert results to DataFrame for analysis
results_df = pd.DataFrame(results)
results_df['total_return'] = results_df['metrics'].apply(lambda m: m['total_return'])
results_df['sharpe_ratio'] = results_df['metrics'].apply(lambda m: m['sharpe_ratio'])

# Histogram of per-pair returns
results_df['total_return'].hist(bins=50)
plt.title('Distribution of Per-Pair Total Returns')
plt.xlabel('Total Return')
plt.ylabel('Number of Pairs')
plt.show()

# Total number of pairs/windows
total_windows = len(results_df)
# Total number of trades
total_trades = results_df['n_trades'].sum()
# Average and median holding period (only for windows with trades)
avg_holding = results_df.loc[results_df['n_trades'] > 0, 'avg_holding'].mean()
median_holding = results_df.loc[results_df['n_trades'] > 0, 'avg_holding'].median()
# Percentage of windows with at least one trade
pct_with_trades = (results_df['n_trades'] > 0).mean() * 100
# Number of profitable/unprofitable windows (using total_return from metrics)
results_df['total_return'] = results_df['metrics'].apply(lambda m: m['total_return'])
profitable = (results_df['total_return'] > 0).sum()
unprofitable = (results_df['total_return'] <= 0).sum()

print(f"\n==== Walkforward Strategy Summary ====")
print(f"Total windows (pair x test): {total_windows}")
print(f"Total trades: {total_trades}")
print(f"Average holding period (if traded): {avg_holding:.2f} days")
print(f"Median holding period (if traded): {median_holding:.2f} days")
print(f"% of windows with at least one trade: {pct_with_trades:.1f}%")
print(f"Profitable windows: {profitable}")
print(f"Unprofitable windows: {unprofitable}")
print(f"Portfolio Metrics:")
for k, v in metrics.items():
    print(f"  {k}: {v}")


# Aggregate all trades from all results
all_trades = []
for res in results:
    for trade in res.get('trades', []):
        trade_copy = trade.copy()
        trade_copy['pair'] = res['pair']
        trade_copy['train_start'] = res['train_start']
        trade_copy['test_start'] = res['test_start']
        all_trades.append(trade_copy)

trades_df = pd.DataFrame(all_trades)
print(trades_df.head())
if not trades_df.empty:
    print("Total trades:", len(trades_df))
    print("Total realized PnL:", trades_df['pnl'].sum())
    print("Average realized PnL per trade:", trades_df['pnl'].mean())
    print("Median holding period:", trades_df['holding_period'].median())
    print("Win rate:", (trades_df['pnl'] > 0).mean() * 100, "%")
    print("Average PnL by direction:")
    print(trades_df.groupby('direction')['pnl'].mean())
else:
    print("No trades found.")

if not trades_df.empty:
    trades_df['pnl'].hist(bins=50)
    plt.title('Distribution of Realized Trade PnL')
    plt.xlabel('Realized PnL')
    plt.ylabel('Number of Trades')
    plt.show()