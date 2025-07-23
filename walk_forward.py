import pandas as pd
from typing import Dict
from pair_selection import select_pairs
from model_fitting import fit_spread
from signal_generation import generate_signals, generate_rolling_signals, generate_rolling_scaled_signals, generate_rolling_stepwise_signals, generate_rolling_stepwise_scaled_signals, generate_tiered_signals
from backtest import run_backtest, compute_performance_metrics

def walk_forward(prices: pd.DataFrame, sector_tickers: Dict[str, list], config: Dict):
    train_size = config.get('train_size', 120)  # days
    test_size = config.get('test_size', 20)     # days
    entry_z = config.get('entry_z', 1.0)
    exit_z = config.get('exit_z', 0.5)
    signal_method = config.get('signal_method', 'static')
    rolling_window = config.get('rolling_window', 60)
    position_size = config.get('position_size', 100)

    results = []

    for start in range(0, len(prices) - train_size - test_size, test_size):
        train_window = slice(prices.index[start], prices.index[start + train_size - 1])
        test_window = slice(prices.index[start + train_size], prices.index[start + train_size + test_size - 1])

        pairs = select_pairs(prices, sector_tickers, train_window)
        for pair in pairs:
            model_params = fit_spread(pair, prices, train_window)
            if not model_params:
                continue
            spread_test = prices.loc[test_window, pair[0]] - model_params['beta'] * prices.loc[test_window, pair[1]]
            if signal_method == 'rolling':
                signals = generate_rolling_signals(
                    spread_test,
                    entry_z,
                    exit_z,
                    rolling_window=rolling_window
                )
            elif signal_method == 'rolling_scaled':
                # Scaled position sizing using rolling z-score
                signals = generate_rolling_scaled_signals(
                    spread_test,
                    entry_z=entry_z,
                    exit_z=exit_z,
                    rolling_window=rolling_window
                )
            elif signal_method == 'rolling_stepwise':
                # Stepwise position sizing using rolling z-score (with scaling)
                signals = generate_rolling_stepwise_scaled_signals(
                    spread_test,
                    entry_z=entry_z,
                    exit_z=exit_z,
                    step=config.get('step', 0.25),
                    rolling_window=rolling_window,
                    scaling_factor=config.get('scaling_factor', 1.0)
                )
            elif signal_method == 'tiered':
                signals = generate_tiered_signals(
                    spread_test,
                    entry_z=entry_z,
                    exit_z=exit_z,
                    rolling_window=rolling_window,
                    scaling_factor=config.get('scaling_factor', 1.0)
                )
            else:
                signals = generate_signals(
                    spread_test,
                    model_params['spread_mean'],
                    model_params['spread_std'],
                    entry_z,
                    exit_z
                )
            backtest_results = run_backtest(spread_test, signals, position_size=position_size)
            metrics = compute_performance_metrics(backtest_results['daily_pnl'])
            results.append({
                'pair': pair,
                'train_start': prices.index[start],
                'test_start': prices.index[start + train_size],
                'metrics': metrics,
                'daily_pnl': backtest_results['daily_pnl'],
                'trades': backtest_results['trades']
            })

    return results