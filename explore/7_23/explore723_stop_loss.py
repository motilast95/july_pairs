import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sys
import os
import time
start_time = time.time()  # Start timer at the very top
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from data_loader import load_prices, load_sector_tickers
from walk_forward import walk_forward
from portfolio_analysis import aggregate_portfolio_pnl, compute_portfolio_metrics
from model_fitting import fit_spread
from signal_generation import generate_signals, generate_rolling_signals, generate_rolling_stepwise_signals, generate_rolling_stepwise_scaled_signals, generate_tiered_signals
from config.data_params import sector_tickers
# ---- Config ----
selected_sectors = list(sector_tickers.keys())
tickers = list(set(sum([sector_tickers[sector] for sector in selected_sectors], [])))
config = {
    'train_size': 504,
    'test_size': 126,
    'entry_z': 1.0,
    'exit_z': 0.25,
    'prototype': True,
    'tickers': tickers,
    'start_date': '2021-01-01',
    'end_date': '2025-07-01',
    'signal_method': 'tiered',
    'rolling_window': 60,
    'scaling_factor': 1.0,
    'position_size': 14,  # Dollar PnL per 1 spread point
    # 'stop_loss': None,
    # 'shutdown_on_stop_loss': True,
}

# ---- Load Data ----
prices = load_prices('data/prices.csv')
# Filter prices by config start/end date
prices = prices.loc[config['start_date']:config['end_date']]
sector_tickers = load_sector_tickers('config/data_params.py')

# ---- Run Walkforward ----
results = walk_forward(prices, sector_tickers, config)

# ---- Portfolio Analysis ----
initial_capital = 10000  # Set your starting capital
portfolio_pnl = aggregate_portfolio_pnl(results)
metrics = compute_portfolio_metrics(portfolio_pnl, initial_capital=initial_capital)
print('Portfolio Metrics (returns-based):')
for k, v in metrics.items():
    print(f'{k}: {v}')

# --- Returns-based analysis ---
returns = portfolio_pnl / initial_capital
cumulative_returns = (1 + returns).cumprod() - 1
mean_return = returns.mean()
std_return = returns.std()
sharpe = mean_return / std_return if std_return != 0 else float('nan')
annualization_factor = 252 ** 0.5
sharpe_annual = sharpe * annualization_factor if std_return != 0 else float('nan')
print(f"\nReturns-based metrics:")
print(f"Mean daily return: {mean_return:.4%}")
print(f"Std daily return: {std_return:.4%}")
print(f"Sharpe ratio (returns, daily): {sharpe:.2f}")
print(f"Sharpe ratio (returns, annualized): {sharpe_annual:.2f}")

# Plot cumulative returns
plt.figure(figsize=(10, 4))
plt.plot(cumulative_returns.index, cumulative_returns.values, label='Cumulative Return')
plt.ylabel('Cumulative Return')
plt.title('Portfolio Cumulative Return')
plt.legend()
plt.savefig('cumulative_return.png')
plt.close()

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
    if config.get('signal_method') == 'tiered':
        signals = generate_tiered_signals(
            spread_test,
            entry_z=config['entry_z'],
            exit_z=config['exit_z'],
            rolling_window=config['rolling_window'],
            scaling_factor=config.get('scaling_factor', 1.0)
        )
    n_trades, avg_holding = trade_stats(signals)
    res['n_trades'] = n_trades
    res['avg_holding'] = avg_holding

# Convert results to DataFrame for analysis
results_df = pd.DataFrame(results)
results_df['total_return'] = results_df['metrics'].apply(lambda m: m['total_return'])
results_df['sharpe_ratio'] = results_df['metrics'].apply(lambda m: m['sharpe_ratio'])

# Remove per-pair and per-period analysis and output
# (Removed: per_pair_performance.csv, per_window_performance.csv, related print statements and plots)

# --- Per-trade PnL distribution ---
all_trades = []
for res in results:
    all_trades.extend(res['trades'])
import pandas as pd
trades_df = pd.DataFrame(all_trades)
if not trades_df.empty:
    trades_df.to_csv('all_trades.csv', index=False)
    print("\nTrade PnL summary:")
    print(trades_df['pnl'].describe())
    plt.figure(figsize=(8,4))
    trades_df['pnl'].hist(bins=50)
    plt.title('Histogram of Trade PnL')
    plt.xlabel('Trade PnL ($)')
    plt.ylabel('Frequency')
    plt.savefig('trade_pnl_histogram.png')
    plt.close()

# --- Cumulative trade PnL ---
trades_df['exit_date'] = pd.to_datetime(trades_df['exit_date'])
trades_df = trades_df.sort_values('exit_date')
trades_df['cumulative_trade_pnl'] = trades_df['pnl'].cumsum()
plt.figure(figsize=(10, 4))
plt.plot(trades_df['exit_date'], trades_df['cumulative_trade_pnl'], label='Cumulative Trade PnL')
plt.ylabel('Cumulative Trade PnL')
plt.title('Cumulative Sum of Trade PnLs')
plt.legend()
plt.savefig('cumulative_trade_pnl.png')
plt.close()

# --- Portfolio cumulative return vs. cumulative trade PnL ---
plt.figure(figsize=(10, 4))
plt.plot(cumulative_returns.index, cumulative_returns.values, label='Portfolio Cumulative Return')
plt.plot(trades_df['exit_date'], trades_df['cumulative_trade_pnl'] / initial_capital, label='Cumulative Trade PnL (normalized)')
plt.ylabel('Cumulative Return')
plt.title('Portfolio Cumulative Return vs. Cumulative Trade PnL')
plt.legend()
plt.savefig('cum_return_vs_trade_pnl.png')
plt.close()

# --- Plot Equity Curve and Drawdowns ---
# Compute cumulative returns (equity curve)
equity_curve = portfolio_pnl.cumsum()
# Compute running max
running_max = equity_curve.cummax()
drawdown = equity_curve - running_max
drawdown_pct = drawdown / running_max

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
# Plot equity curve
ax1.plot(equity_curve.index, equity_curve.values, label='Equity Curve', color='blue')
ax1.set_ylabel('Cumulative PnL')
ax1.set_title('Portfolio Equity Curve')
ax1.legend()
# Plot drawdown
ax2.plot(drawdown.index, drawdown.values, label='Drawdown', color='red')
ax2.fill_between(drawdown.index, drawdown.values, 0, color='red', alpha=0.3)
ax2.set_ylabel('Drawdown')
ax2.set_title('Portfolio Drawdown')
ax2.legend()
plt.xlabel('Date')
plt.tight_layout()
plt.savefig('equity_curve_and_drawdown.png')
plt.close()

# --- Highlight max drawdown period on the plot ---
# 1. Maximum drawdown and its date
import numpy as np
running_max = equity_curve.cummax()
drawdown = equity_curve - running_max
max_dd_idx = np.argmin(drawdown)
max_drawdown = drawdown.iloc[max_dd_idx]
max_drawdown_date = drawdown.index[max_dd_idx]

# Find the peak before the max drawdown
peak_idx = np.argmax(equity_curve[:max_drawdown_date+pd.Timedelta(days=1)])
dd_start = equity_curve.index[peak_idx]

# Find the first recovery after the max drawdown
recovery_idx = None
for i in range(max_dd_idx, len(equity_curve)):
    if equity_curve.iloc[i] >= equity_curve.iloc[peak_idx]:
        recovery_idx = i
        break
if recovery_idx is not None:
    dd_end = equity_curve.index[recovery_idx]
else:
    dd_end = equity_curve.index[-1]

print(f"Maximum drawdown: {max_drawdown:.2f} on {max_drawdown_date}")
print(f"Drawdown period: {dd_start} to {dd_end} (duration: {(pd.to_datetime(dd_end) - pd.to_datetime(dd_start)).days} days)")

# 3. Volatility (standard deviation) of daily PnL
pnl_volatility = portfolio_pnl.std()
print(f"Daily PnL volatility (std): {pnl_volatility:.2f}")

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
ax1.plot(equity_curve.index, equity_curve.values, label='Equity Curve', color='blue')
ax1.axvspan(dd_start, dd_end, color='orange', alpha=0.2, label='Max Drawdown Period')
ax1.set_ylabel('Cumulative PnL')
ax1.set_title('Portfolio Equity Curve (Max Drawdown Highlighted)')
ax1.legend()
ax2.plot(drawdown.index, drawdown.values, label='Drawdown', color='red')
ax2.fill_between(drawdown.index, drawdown.values, 0, color='red', alpha=0.3)
ax2.axvspan(dd_start, dd_end, color='orange', alpha=0.2, label='Max Drawdown Period')
ax2.set_ylabel('Drawdown')
ax2.set_title('Portfolio Drawdown')
ax2.legend()
plt.xlabel('Date')
plt.tight_layout()
plt.savefig('max_drawdown_highlight.png')
plt.close()

# # --- Diagnostic: Compare trade PnL sum to portfolio PnL ---
# trade_pnl_sum = trades_df['pnl'].sum()
# portfolio_pnl_sum = portfolio_pnl.sum()
# print(f"Sum of trade PnLs: {trade_pnl_sum}")
# print(f"Sum of portfolio daily PnL: {portfolio_pnl_sum}")

# # Print first and last 20 values of daily and cumulative PnL
# print("\nFirst 20 daily PnL values:")
# print(portfolio_pnl.head(20))
# print("\nLast 20 daily PnL values:")
# print(portfolio_pnl.tail(20))
# print("\nFirst 20 cumulative PnL values:")
# print(portfolio_pnl.cumsum().head(20))
# print("\nLast 20 cumulative PnL values:")
# print(portfolio_pnl.cumsum().tail(20))

# --- Daily and cumulative PnL plots ---
plt.figure(figsize=(12,4))
plt.plot(portfolio_pnl.index, portfolio_pnl.values, label='Daily PnL')
plt.title('Portfolio Daily PnL')
plt.legend()
plt.savefig('portfolio_daily_pnl.png')
plt.close()

plt.figure(figsize=(12,4))
plt.plot(portfolio_pnl.index, portfolio_pnl.cumsum().values, label='Cumulative PnL')
plt.title('Portfolio Cumulative PnL')
plt.legend()
plt.savefig('portfolio_cumulative_pnl.png')
plt.close()

end_time = time.time()
print(f"\nTotal runtime: {end_time - start_time:.2f} seconds")