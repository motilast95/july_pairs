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
    'entry_z': 1.5,
    'exit_z': 0.5,
    'prototype': True,
    'tickers': prices.columns.tolist(),
    'start_date': '2016-01-01',
    'end_date': '2018-01-01',
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
    epsilon = 1e-8
    entries = (signals.shift(1).abs() < epsilon) & (signals.abs() >= epsilon)
    exits = (signals.shift(1).abs() >= epsilon) & (signals.abs() < epsilon)
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
    signals = generate_rolling_scaled_signals(
        spread_test,
        entry_z=config['entry_z'],
        exit_z=config['exit_z'],
        rolling_window=config['rolling_window']
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
        if config.get('signal_method', 'static') == 'static':
            signals = generate_signals(spread, spread_mean, spread_std, config['entry_z'], config['exit_z'])
        elif config.get('signal_method') == 'rolling_scaled':
            signals = generate_rolling_scaled_signals(
                spread,
                entry_z=config['entry_z'],
                exit_z=config['exit_z'],
                rolling_window=config.get('rolling_window', 60)
            )
        else:
            signals = generate_rolling_signals(
                spread,
                config['entry_z'],
                config['exit_z'],
                config.get('rolling_window', 60)
            )
        # Ensure signals is a pandas Series for .index access
        if not isinstance(signals, pd.Series):
            signals = pd.Series(signals, index=spread.index)
        epsilon = 1e-8
        entries_mask = (signals.shift(1).abs() < epsilon) & (signals.abs() >= epsilon)
        exits_mask = (signals.shift(1).abs() >= epsilon) & (signals.abs() < epsilon)
        entries = signals.index[entries_mask]
        exits = signals.index[exits_mask]
        # Debug print for exits
        for exit_idx in exits:
            print(f"Exit at {exit_idx}: z-score={zscore.loc[exit_idx]}, signal={signals.loc[exit_idx]}")
            # Print a window around the exit
            window = signals.index.get_loc(exit_idx)
            print('Signal window:')
            print(signals.iloc[max(0, window-3):window+4])
            print('Z-score window:')
            print(zscore.iloc[max(0, window-3):window+4])
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

# Sort by total_return descending for most profitable, ascending for most losing
top_profitable_df = results_df.sort_values('total_return', ascending=False).head(10)
top_losing_df = results_df.sort_values('total_return', ascending=True).head(10)

top_profitable_results = top_profitable_df.to_dict(orient='records')
top_losing_results = top_losing_df.to_dict(orient='records')

print('Top 10 most profitable windows:')
plot_zscore_grid(top_profitable_results, prices, config, period='test', ncols=2, max_plots=10, show=True, save_path="top_profitable_zscore_grid.png")

print('Top 10 most losing windows:')
plot_zscore_grid(top_losing_results, prices, config, period='test', ncols=2, max_plots=10, show=True, save_path="top_losing_zscore_grid.png")