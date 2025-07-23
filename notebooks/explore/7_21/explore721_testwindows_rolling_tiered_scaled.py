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

# ---- Load Data ----
prices = load_prices('data/prices.csv')
sector_tickers = load_sector_tickers('config/data_params.py')

# ---- Config ----
config = {
    'train_size': 504,
    'test_size': 126,
    'entry_z': 1.0,
    'exit_z': 0.25,
    'prototype': True,
    'tickers': prices.columns.tolist(),
    'start_date': '2016-01-01',
    'end_date': '2025-07-01',
    'signal_method': 'tiered',
    'rolling_window': 60,
    'scaling_factor': 1.0
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

def plot_zscore_grid(results, prices, config, period='test', ncols=2, max_plots=8, show=True, save_path=None):
    import math
    pairs_to_plot = results[:max_plots]
    n = len(pairs_to_plot)
    nrows = math.ceil(n / ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(6 * ncols, 3 * nrows), squeeze=False)
    for idx, res in enumerate(pairs_to_plot):
        pair = res['pair']
        train_start = res['train_start']
        test_start = res['test_start']
        train_window = slice(train_start, test_start)
        model_params = fit_spread(pair, prices, train_window)
        if not model_params:
            continue
        beta = model_params['beta']
        spread_mean = model_params['spread_mean']
        spread_std = model_params['spread_std']
        if period == 'test':
            window = slice(test_start, prices.index[min(prices.index.get_loc(test_start) + config['test_size'] - 1, len(prices.index)-1)])
            spread = prices.loc[window, pair[0]] - beta * prices.loc[window, pair[1]]
        else:
            window = train_window
            spread = prices.loc[window, pair[0]] - beta * prices.loc[window, pair[1]]
        # Compute z-score according to signal method
        if config.get('signal_method', 'static') == 'rolling':
            rolling_window = config.get('rolling_window', 60)
            rolling_mean = spread.rolling(window=rolling_window, min_periods=rolling_window).mean()
            rolling_std = spread.rolling(window=rolling_window, min_periods=rolling_window).std()
            zscore = (spread - rolling_mean) / rolling_std
        else:
            zscore = (spread - spread_mean) / spread_std
        # Add horizontal lines for every step size
        step = config.get('step', 0.25)
        max_z = max(6, int(np.ceil(np.nanmax(np.abs(zscore))) + 1))  # ensure at least 6
        steps = np.arange(-max_z, max_z + step, step)
        for s in steps:
            if abs(s) < 1e-8:  # skip zero line (already plotted)
                continue
            ax.axhline(s, color='gray', linestyle=':', linewidth=0.7, alpha=0.5)
        if config.get('signal_method') == 'tiered':
            signals = generate_tiered_signals(
                spread,
                entry_z=config['entry_z'],
                exit_z=config['exit_z'],
                rolling_window=config['rolling_window'],
                scaling_factor=config.get('scaling_factor', 1.0)
            )
        # Ensure signals is a pandas Series for .index access
        if not isinstance(signals, pd.Series):
            signals = pd.Series(signals, index=spread.index)
        entries_mask = (signals.shift(1) == 0) & (signals != 0)
        exits_mask = (signals.shift(1) != 0) & (signals == 0)
        entries = signals.index[entries_mask]
        exits = signals.index[exits_mask]
        ax = axes[idx // ncols][idx % ncols]
        ax.plot(zscore.index, zscore.values, label='Z-score')
        ax.axhline(config['entry_z'], color='green', linestyle='--')
        ax.axhline(-config['entry_z'], color='green', linestyle='--')
        ax.axhline(config['exit_z'], color='red', linestyle='--')
        ax.axhline(-config['exit_z'], color='red', linestyle='--')
        ax.axhline(0, color='black', linestyle='-')
        ax.scatter(entries, zscore.loc[entries], marker='^', color='blue', label='Entry', zorder=5)
        ax.scatter(exits, zscore.loc[exits], marker='v', color='orange', label='Exit', zorder=5)
        ax.set_title(f"{period.capitalize()} Z-score: {pair[0]} - {beta:.2f}*{pair[1]}")
        ax.set_xlabel('Date')
        ax.set_ylabel('Z-score')
        ax.legend()
    # Hide unused subplots
    for idx in range(n, nrows * ncols):
        fig.delaxes(axes[idx // ncols][idx % ncols])
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path)
        print(f"Saved plot grid to {save_path}")
    if show:
        plt.show()
    else:
        plt.close(fig)

# ---- Plot grid of z-score subplots for test and train periods ----
# Save all test windows as subplots in a single large PNG file
import math
ncols = 3
max_plots = len(results)
nrows = math.ceil(max_plots / ncols)
fig, axes = plt.subplots(nrows, ncols, figsize=(6 * ncols, 3 * nrows), squeeze=False)
for idx, res in enumerate(results[:max_plots]):
    pair = res['pair']
    train_start = res['train_start']
    test_start = res['test_start']
    train_window = slice(train_start, test_start)
    model_params = fit_spread(pair, prices, train_window)
    if not model_params:
        continue
    beta = model_params['beta']
    test_window = slice(test_start, prices.index[min(prices.index.get_loc(test_start) + config['test_size'] - 1, len(prices.index)-1)])
    spread = prices.loc[test_window, pair[0]] - beta * prices.loc[test_window, pair[1]]
    rolling_window = config.get('rolling_window', 60)
    rolling_mean = spread.rolling(window=rolling_window, min_periods=rolling_window).mean()
    rolling_std = spread.rolling(window=rolling_window, min_periods=rolling_window).std()
    zscore = (spread - rolling_mean) / rolling_std
    if config.get('signal_method') == 'tiered':
        signals = generate_tiered_signals(
            spread,
            entry_z=config['entry_z'],
            exit_z=config['exit_z'],
            rolling_window=rolling_window,
            scaling_factor=config.get('scaling_factor', 1.0)
        )
    entries_mask = (signals.shift(1) == 0) & (signals != 0)
    exits_mask = (signals.shift(1) != 0) & (signals == 0)
    entries = signals.index[entries_mask]
    exits = signals.index[exits_mask]
    ax = axes[idx // ncols][idx % ncols]
    total_return = res['metrics']['total_return']
    title_color = 'green' if total_return > 0 else 'red'
    if total_return > 0:
        ax.set_facecolor('#eaffea')  # light green
    else:
        ax.set_facecolor('#ffeaea')  # light red
    # Plot z-score and entry/exit lines only (restore previous visual)
    ax.plot(zscore.index, zscore.values, label='Z-score', color='blue')
    ax.axhline(config['entry_z'], color='green', linestyle='--')
    ax.axhline(-config['entry_z'], color='green', linestyle='--')
    ax.axhline(config['exit_z'], color='red', linestyle='--')
    ax.axhline(-config['exit_z'], color='red', linestyle='--')
    ax.axhline(0, color='black', linestyle='-')
    ax.scatter(entries, zscore.loc[entries], marker='^', color='blue', label='Entry', zorder=5)
    ax.scatter(exits, zscore.loc[exits], marker='v', color='orange', label='Exit', zorder=5)
    ax.set_title(f"{pair[0]} - {beta:.2f}*{pair[1]}\nTest start: {test_start}\nReturn: {total_return:.2f}", color=title_color)
    ax.set_xlabel('Date')
    ax.set_ylabel('Z-score')
    ax.legend()
plt.tight_layout()
plt.savefig("all_test_windows_grid.png")
plt.close(fig)
print("Saved all test windows to all_test_windows_grid.png")