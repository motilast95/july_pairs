import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from data_loader import load_prices, load_sector_tickers
from walk_forward import walk_forward
from portfolio_analysis import aggregate_portfolio_pnl, compute_portfolio_metrics
from model_fitting import fit_spread
from signal_generation import generate_signals, generate_rolling_signals, generate_rolling_stepwise_signals, generate_rolling_stepwise_scaled_signals, generate_tiered_signals
from config.data_params import sector_tickers
# ---- Config ----
config = {
    'train_size': 504,
    'test_size': 126,
    'entry_z': 1.0,
    'exit_z': 0.25,
    'prototype': True,
    'tickers': list(set(sum(sector_tickers.values(), []))),
    'start_date': '2020-01-01',
    'end_date': '2025-07-01',
    'signal_method': 'tiered',
    'rolling_window': 60,
    'scaling_factor': 1.0,
    'position_size': 14,  # Dollar PnL per 1 spread point
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
plt.show()

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

# --- Per-pair performance table ---
pair_perf = results_df.groupby('pair')['total_return'].agg(['count', 'sum', 'mean', 'std'])
pair_perf = pair_perf.sort_values('sum', ascending=False)
pair_perf.to_csv('per_pair_performance.csv')
print("\nPer-pair performance:")
print(pair_perf)

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
    plt.show()

# --- Per-period (window) performance ---
window_perf = results_df[['test_start', 'total_return']]
window_perf = window_perf.groupby('test_start')['total_return'].sum()
window_perf.to_csv('per_window_performance.csv')
plt.figure(figsize=(10,4))
window_perf.plot()
plt.title('Per-Window Total Return')
plt.xlabel('Test Window Start Date')
plt.ylabel('Total Return ($)')
plt.savefig('per_window_total_return.png')
plt.show()

# def plot_zscore_grid(results, prices, config, period='test', ncols=2, max_plots=8, show=True, save_path=None):
#     import math
#     pairs_to_plot = results[:max_plots]
#     n = len(pairs_to_plot)
#     nrows = math.ceil(n / ncols)
#     fig, axes = plt.subplots(nrows, ncols, figsize=(6 * ncols, 3 * nrows), squeeze=False)
#     for idx, res in enumerate(pairs_to_plot):
#         pair = res['pair']
#         train_start = res['train_start']
#         test_start = res['test_start']
#         train_window = slice(train_start, test_start)
#         model_params = fit_spread(pair, prices, train_window)
#         if not model_params:
#             continue
#         beta = model_params['beta']
#         spread_mean = model_params['spread_mean']
#         spread_std = model_params['spread_std']
#         if period == 'test':
#             window = slice(test_start, prices.index[min(prices.index.get_loc(test_start) + config['test_size'] - 1, len(prices.index)-1)])
#             spread = prices.loc[window, pair[0]] - beta * prices.loc[window, pair[1]]
#         else:
#             window = train_window
#             spread = prices.loc[window, pair[0]] - beta * prices.loc[window, pair[1]]
#         # Compute z-score according to signal method
#         if config.get('signal_method', 'static') == 'rolling':
#             rolling_window = config.get('rolling_window', 60)
#             rolling_mean = spread.rolling(window=rolling_window, min_periods=rolling_window).mean()
#             rolling_std = spread.rolling(window=rolling_window, min_periods=rolling_window).std()
#             zscore = (spread - rolling_mean) / rolling_std
#         else:
#             zscore = (spread - spread_mean) / spread_std
#         # Add horizontal lines for every step size
#         step = config.get('step', 0.25)
#         max_z = max(6, int(np.ceil(np.nanmax(np.abs(zscore))) + 1))  # ensure at least 6
#         steps = np.arange(-max_z, max_z + step, step)
#         for s in steps:
#             if abs(s) < 1e-8:  # skip zero line (already plotted)
#                 continue
#             ax.axhline(s, color='gray', linestyle=':', linewidth=0.7, alpha=0.5)
#         if config.get('signal_method') == 'tiered':
#             signals = generate_tiered_signals(
#                 spread,
#                 entry_z=config['entry_z'],
#                 exit_z=config['exit_z'],
#                 rolling_window=config['rolling_window'],
#                 scaling_factor=config.get('scaling_factor', 1.0)
#             )
#         # Ensure signals is a pandas Series for .index access
#         if not isinstance(signals, pd.Series):
#             signals = pd.Series(signals, index=spread.index)
#         entries_mask = (signals.shift(1) == 0) & (signals != 0)
#         exits_mask = (signals.shift(1) != 0) & (signals == 0)
#         entries = signals.index[entries_mask]
#         exits = signals.index[exits_mask]
#         ax = axes[idx // ncols][idx % ncols]
#         ax.plot(zscore.index, zscore.values, label='Z-score')
#         ax.axhline(config['entry_z'], color='green', linestyle='--')
#         ax.axhline(-config['entry_z'], color='green', linestyle='--')
#         ax.axhline(config['exit_z'], color='red', linestyle='--')
#         ax.axhline(-config['exit_z'], color='red', linestyle='--')
#         ax.axhline(0, color='black', linestyle='-')
#         ax.scatter(entries, zscore.loc[entries], marker='^', color='blue', label='Entry', zorder=5)
#         ax.scatter(exits, zscore.loc[exits], marker='v', color='orange', label='Exit', zorder=5)
#         ax.set_title(f"{period.capitalize()} Z-score: {pair[0]} - {beta:.2f}*{pair[1]}")
#         ax.set_xlabel('Date')
#         ax.set_ylabel('Z-score')
#         ax.legend()
#     # Hide unused subplots
#     for idx in range(n, nrows * ncols):
#         fig.delaxes(axes[idx // ncols][idx % ncols])
#     plt.tight_layout()
#     if save_path:
#         plt.savefig(save_path)
#         print(f"Saved plot grid to {save_path}")
#     if show:
#         plt.show()
#     else:
#         plt.close(fig)

# # ---- Plot grid of z-score subplots for test and train periods ----
# # Save all test windows as subplots in a single large PNG file
# import math
# ncols = 3
# max_plots = len(results)
# nrows = math.ceil(max_plots / ncols)
# fig, axes = plt.subplots(nrows, ncols, figsize=(6 * ncols, 3 * nrows), squeeze=False)
# for idx, res in enumerate(results[:max_plots]):
#     pair = res['pair']
#     train_start = res['train_start']
#     test_start = res['test_start']
#     train_window = slice(train_start, test_start)
#     model_params = fit_spread(pair, prices, train_window)
#     if not model_params:
#         continue
#     beta = model_params['beta']
#     test_window = slice(test_start, prices.index[min(prices.index.get_loc(test_start) + config['test_size'] - 1, len(prices.index)-1)])
#     spread = prices.loc[test_window, pair[0]] - beta * prices.loc[test_window, pair[1]]
#     rolling_window = config.get('rolling_window', 60)
#     rolling_mean = spread.rolling(window=rolling_window, min_periods=rolling_window).mean()
#     rolling_std = spread.rolling(window=rolling_window, min_periods=rolling_window).std()
#     zscore = (spread - rolling_mean) / rolling_std
#     if config.get('signal_method') == 'tiered':
#         signals = generate_tiered_signals(
#             spread,
#             entry_z=config['entry_z'],
#             exit_z=config['exit_z'],
#             rolling_window=rolling_window,
#             scaling_factor=config.get('scaling_factor', 1.0)
#         )
#     entries_mask = (signals.shift(1) == 0) & (signals != 0)
#     exits_mask = (signals.shift(1) != 0) & (signals == 0)
#     entries = signals.index[entries_mask]
#     exits = signals.index[exits_mask]
#     ax = axes[idx // ncols][idx % ncols]
#     total_return = res['metrics']['total_return']
#     title_color = 'green' if total_return > 0 else 'red'
#     if total_return > 0:
#         ax.set_facecolor('#eaffea')  # light green
#     else:
#         ax.set_facecolor('#ffeaea')  # light red
#     # Plot z-score and entry/exit lines only (restore previous visual)
#     ax.plot(zscore.index, zscore.values, label='Z-score', color='blue')
#     ax.axhline(config['entry_z'], color='green', linestyle='--')
#     ax.axhline(-config['entry_z'], color='green', linestyle='--')
#     ax.axhline(config['exit_z'], color='red', linestyle='--')
#     ax.axhline(-config['exit_z'], color='red', linestyle='--')
#     ax.axhline(0, color='black', linestyle='-')
#     ax.scatter(entries, zscore.loc[entries], marker='^', color='blue', label='Entry', zorder=5)
#     ax.scatter(exits, zscore.loc[exits], marker='v', color='orange', label='Exit', zorder=5)
#     ax.set_title(f"{pair[0]} - {beta:.2f}*{pair[1]}\nTest start: {test_start}\nReturn: {total_return:.2f}", color=title_color)
#     ax.set_xlabel('Date')
#     ax.set_ylabel('Z-score')
#     ax.legend()
# plt.tight_layout()
# plt.savefig("all_test_windows_grid.png")
# plt.close(fig)
# print("Saved all test windows to all_test_windows_grid.png")

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
plt.show()

# --- Quantitative Drawdown and Volatility Analysis ---
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

# --- Highlight max drawdown period on the plot ---
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
plt.show()

# --- Diagnostic: Compare trade PnL sum to portfolio PnL ---
trade_pnl_sum = trades_df['pnl'].sum()
portfolio_pnl_sum = portfolio_pnl.sum()
print(f"Sum of trade PnLs: {trade_pnl_sum}")
print(f"Sum of portfolio daily PnL: {portfolio_pnl_sum}")

# Print first and last 20 values of daily and cumulative PnL
print("\nFirst 20 daily PnL values:")
print(portfolio_pnl.head(20))
print("\nLast 20 daily PnL values:")
print(portfolio_pnl.tail(20))
print("\nFirst 20 cumulative PnL values:")
print(portfolio_pnl.cumsum().head(20))
print("\nLast 20 cumulative PnL values:")
print(portfolio_pnl.cumsum().tail(20))

# Plot daily and cumulative PnL for visual inspection
plt.figure(figsize=(12,4))
plt.plot(portfolio_pnl.index, portfolio_pnl.values, label='Daily PnL')
plt.title('Portfolio Daily PnL')
plt.legend()
plt.show()

plt.figure(figsize=(12,4))
plt.plot(portfolio_pnl.index, portfolio_pnl.cumsum().values, label='Cumulative PnL')
plt.title('Portfolio Cumulative PnL')
plt.legend()
plt.show()