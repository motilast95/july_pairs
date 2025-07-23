import pandas as pd
import matplotlib.pyplot as plt
from data_loader import load_prices, load_sector_tickers
from walk_forward import walk_forward
from portfolio_analysis import aggregate_portfolio_pnl, compute_portfolio_metrics
from model_fitting import fit_spread
from signal_generation import generate_signals, generate_rolling_signals
import importlib.util
import sys
import os
import numpy as np

# ---- Load Data ----
prices = load_prices('data/prices.csv')
sector_tickers = load_sector_tickers('config/data_params.py')

# Load signal generation config
signal_config_path = os.path.join('config', 'signal_generation_config.py')
spec = importlib.util.spec_from_file_location("signal_generation_config", signal_config_path)
if spec is None or spec.loader is None:
    raise ImportError(f"Could not load spec or loader from {signal_config_path}")
signal_generation_config = importlib.util.module_from_spec(spec)
sys.modules["signal_generation_config"] = signal_generation_config
spec.loader.exec_module(signal_generation_config)

# ---- Config ----
config = {
    'train_size': 504,
    'test_size': 126,
    'entry_z': 1.5,
    'exit_z': 0.5,
    'prototype': True,
    'tickers': prices.columns.tolist(),
    'start_date': '2016-01-01',
    'end_date': '2025-07-01'
}

# Update main config with signal generation config values
config['rolling_window'] = signal_generation_config.rolling_window
config['entry_z'] = signal_generation_config.entry_z
config['exit_z'] = signal_generation_config.exit_z
config['signal_method'] = signal_generation_config.signal_method

# ---- Prototype Subsetting ----
if config.get('prototype', False):
    available_tickers = [t for t in config['tickers'] if t in prices.columns]
    prices = prices.loc[config['start_date']:config['end_date'], available_tickers]
    for sector in sector_tickers:
        sector_tickers[sector] = [t for t in sector_tickers[sector] if t in available_tickers]

# ---- Run Walkforward ----
results = walk_forward(prices, sector_tickers, config)

# ---- Portfolio Analysis ----
portfolio_pnl = aggregate_portfolio_pnl(results)
metrics = compute_portfolio_metrics(portfolio_pnl)
print('Portfolio Metrics:')
for k, v in metrics.items():
    print(f'{k}: {v}')

# ---- Plot Cumulative Portfolio PnL ----
plt.figure(figsize=(10, 5))
plt.plot(portfolio_pnl.cumsum())
plt.title('Portfolio Cumulative PnL')
plt.xlabel('Date')
plt.ylabel('Cumulative PnL')
plt.show()

# ---- Diagnostics: Plot Z-score with Entry/Exit Signals ----
def plot_zscore_with_signals(prices, pair, beta, spread_mean, spread_std, signals, window, entry_z, exit_z):
    spread = prices.loc[window, pair[0]] - beta * prices.loc[window, pair[1]]
    zscore = (spread - spread_mean) / spread_std
    plt.figure(figsize=(12, 5))
    plt.plot(zscore.index, zscore.values, label='Spread Z-score')
    plt.axhline(entry_z, color='green', linestyle='--', label='Entry/Exit Thresholds')
    plt.axhline(-entry_z, color='green', linestyle='--')
    plt.axhline(exit_z, color='red', linestyle='--', label='Exit Thresholds')
    plt.axhline(-exit_z, color='red', linestyle='--')
    plt.axhline(0, color='black', linestyle='-')
    entries = signals[(signals.shift(1) == 0) & (signals != 0)].index
    exits = signals[(signals.shift(1) != 0) & (signals == 0)].index
    plt.scatter(entries, zscore.loc[entries], marker='^', color='blue', label='Entry', zorder=5)
    plt.scatter(exits, zscore.loc[exits], marker='v', color='orange', label='Exit', zorder=5)
    plt.title(f"Z-score and Trades: {pair[0]} - {beta:.2f}*{pair[1]}")
    plt.xlabel('Date')
    plt.ylabel('Z-score')
    plt.legend()
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

# # ---- Analyze and Plot for a Sample Pair ----
# if results:
#     result = results[0]
#     pair = result['pair']
#     train_start = result['train_start']
#     test_start = result['test_start']
#     entry_z = config['entry_z']
#     exit_z = config['exit_z']
#     train_window = slice(train_start, test_start)
#     model_params = fit_spread(pair, prices, train_window)
#     if model_params:
#         beta = model_params['beta']
#         spread_mean = model_params['spread_mean']
#         spread_std = model_params['spread_std']
#         test_window = slice(test_start, prices.index[min(prices.index.get_loc(test_start) + config['test_size'] - 1, len(prices.index)-1)])
#         spread_test = prices.loc[test_window, pair[0]] - beta * prices.loc[test_window, pair[1]]
#         signals = generate_signals(spread_test, spread_mean, spread_std, entry_z, exit_z)
#         plot_zscore_with_signals(prices, pair, beta, spread_mean, spread_std, signals, test_window, entry_z, exit_z)
#         n_trades, avg_holding = trade_stats(signals)
#         print(f"Sample Pair: {pair}, Number of trades: {n_trades}, Average holding period: {avg_holding:.2f} days")

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

# ---- Save Results to DataFrame ----
results_df = pd.DataFrame(results)
print(results_df.head())


def plot_test_zscore(prices, pair, beta, spread_mean, spread_std, test_window, entry_z, exit_z):
    spread = prices.loc[test_window, pair[0]] - beta * prices.loc[test_window, pair[1]]
    zscore = (spread - spread_mean) / spread_std
    plt.figure(figsize=(10, 4))
    plt.plot(zscore.index, zscore.values, label='Test Z-score')
    plt.axhline(entry_z, color='green', linestyle='--', label='Entry/Exit')
    plt.axhline(-entry_z, color='green', linestyle='--')
    plt.axhline(exit_z, color='red', linestyle='--', label='Exit')
    plt.axhline(-exit_z, color='red', linestyle='--')
    plt.axhline(0, color='black', linestyle='-')
    plt.title(f"Test Z-score: {pair[0]} - {beta:.2f}*{pair[1]}")
    plt.xlabel('Date')
    plt.ylabel('Z-score')
    plt.legend()
    plt.show()

def plot_zscore_grid(results, prices, config, period='test', ncols=2, max_plots=8):
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
        signals = generate_signals(spread, spread_mean, spread_std, config['entry_z'], config['exit_z']) if config.get('signal_method', 'static') == 'static' else generate_rolling_signals(spread, config['entry_z'], config['exit_z'], config.get('rolling_window', 60))
        # Ensure signals is a pandas Series for .index access
        if not isinstance(signals, pd.Series):
            signals = pd.Series(signals, index=spread.index)
        entries_mask = pd.Series((signals.shift(1) == 0) & (signals != 0), index=signals.index)
        exits_mask = pd.Series((signals.shift(1) != 0) & (signals == 0), index=signals.index)
        entries = entries_mask[entries_mask].index if hasattr(entries_mask, 'index') else pd.Index(np.where(entries_mask)[0])
        exits = exits_mask[exits_mask].index if hasattr(exits_mask, 'index') else pd.Index(np.where(exits_mask)[0])
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
    plt.show()

# ---- Plot grid of z-score subplots for test and train periods ----
plot_zscore_grid(results, prices, config, period='test', ncols=5, max_plots=len(results_df))
# plot_zscore_grid(results, prices, config, period='train', ncols=2, max_plots=8)

# ---- Informative Walkforward Strategy Summary ----

# Ensure results_df is up to date
results_df = pd.DataFrame(results)

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

# ---- Pair Reliability Analysis ----
# Group by pair for reliability analysis
pair_stats = results_df.groupby('pair').agg(
    times_cointegrated=('pair', 'count'),
    median_test_sharpe=('metrics', lambda ms: np.median([m['sharpe_ratio'] for m in ms])),
    median_holding=('avg_holding', 'median'),
    pct_windows_traded=('n_trades', lambda x: (x > 0).mean() * 100)
).reset_index()

# Example reliability score (customize as you wish)
pair_stats['reliability_score'] = (
    pair_stats['median_test_sharpe'] * 2 +
    pair_stats['pct_windows_traded'] * 0.1 +
    pair_stats['times_cointegrated'] * 0.05
)

# Sort by reliability score
top_pairs = pair_stats.sort_values('reliability_score', ascending=False)

print("\n==== Pair Reliability Table ====")
print(top_pairs[['pair', 'times_cointegrated', 'median_test_sharpe', 'median_holding', 'pct_windows_traded', 'reliability_score']])


