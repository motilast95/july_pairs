import pandas as pd
import numpy as np
from typing import Dict, List
import logging
from src.data.pair_selection import select_pairs
from src.models.model_fitting import fit_spread
from src.models.signal_generation import generate_signals, generate_rolling_signals, generate_rolling_scaled_signals, generate_rolling_stepwise_signals, generate_rolling_stepwise_scaled_signals, generate_tiered_signals
from src.trading.backtest import run_backtest, compute_performance_metrics
from src.trading.risk_management import PortfolioRiskManager

# Set up logging
logger = logging.getLogger(__name__)

def walk_forward(prices: pd.DataFrame, sector_tickers: Dict[str, list], config: Dict):
    """
    Run walk-forward analysis with enhanced risk management and error handling.
    
    Args:
        prices: Price data DataFrame
        sector_tickers: Dictionary of sector tickers
        config: Configuration dictionary
        
    Returns:
        List of results for each pair and test period
    """
    # Extract configuration parameters
    train_size = config.get('train_size', 504)
    test_size = config.get('test_size', 126)
    entry_z = config.get('entry_z', 1.0)
    exit_z = config.get('exit_z', 0.25)
    signal_method = config.get('signal_method', 'tiered')
    rolling_window = config.get('rolling_window', 60)
    position_size = config.get('position_size', 14)
    transaction_cost_bps = config.get('transaction_cost_bps', 5.0)
    
    # Initialize risk manager
    risk_manager = PortfolioRiskManager(config)
    
    results = []
    total_windows = (len(prices) - train_size - test_size) // test_size
    
    logger.info(f"Starting walk-forward analysis: {total_windows} windows")
    
    for window_idx, start in enumerate(range(0, len(prices) - train_size - test_size, test_size)):
        try:
            train_window = slice(prices.index[start], prices.index[start + train_size - 1])
            test_window = slice(prices.index[start + train_size], prices.index[start + train_size + test_size - 1])
            
            logger.debug(f"Processing window {window_idx + 1}/{total_windows}: {train_window.start} to {test_window.stop}")
            
            # Select pairs with risk validation
            adf_alpha = config.get('adf_alpha', 0.05)
            pairs = select_pairs(prices, sector_tickers, train_window, adf_alpha=adf_alpha)
            valid_pairs = []
            
            for pair in pairs:
                if risk_manager.validate_pair_risk(pair, prices, train_window):
                    valid_pairs.append(pair)
                else:
                    logger.debug(f"Pair {pair} failed risk validation")
            
            logger.info(f"Window {window_idx + 1}: {len(valid_pairs)}/{len(pairs)} pairs passed risk validation")
            
            for pair in valid_pairs:
                try:
                    model_params = fit_spread(pair, prices, train_window)
                    if not model_params:
                        continue
                    
                    spread_test = prices.loc[test_window, pair[0]] - model_params['beta'] * prices.loc[test_window, pair[1]]
                    
                    # Generate signals based on method
                    if signal_method == 'rolling':
                        signals = generate_rolling_signals(
                            spread_test, entry_z, exit_z, rolling_window=rolling_window
                        )
                    elif signal_method == 'rolling_scaled':
                        signals = generate_rolling_scaled_signals(
                            spread_test, entry_z=entry_z, exit_z=exit_z, rolling_window=rolling_window
                        )
                    elif signal_method == 'rolling_stepwise':
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
                    
                    # Apply risk management scaling
                    if len(signals) > 0:
                        # Calculate pair volatility for scaling
                        pair_volatility = spread_test.pct_change().std() * np.sqrt(252)
                        
                        # Apply volatility scaling
                        scaled_signals = signals.copy()
                        for i, signal in enumerate(signals):
                            if signal != 0:
                                scaled_signal = risk_manager.calculate_volatility_scaled_position(
                                    signal, pair_volatility, 0.15  # Default portfolio volatility
                                )
                                scaled_signals.iloc[i] = scaled_signal
                        
                        signals = scaled_signals
                    
                    # Run backtest with transaction costs
                    backtest_results = run_backtest(
                        spread_test, 
                        signals, 
                        position_size=position_size,
                        transaction_cost_bps=transaction_cost_bps
                    )
                    
                    metrics = compute_performance_metrics(backtest_results['daily_pnl'])
                    
                    results.append({
                        'pair': pair,
                        'train_start': prices.index[start],
                        'test_start': prices.index[start + train_size],
                        'window_idx': window_idx,
                        'metrics': metrics,
                        'daily_pnl': backtest_results['daily_pnl'],
                        'daily_pnl_gross': backtest_results['daily_pnl_gross'],
                        'daily_transaction_costs': backtest_results['daily_transaction_costs'],
                        'trades': backtest_results['trades'],
                        'model_params': model_params
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing pair {pair} in window {window_idx + 1}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error processing window {window_idx + 1}: {e}")
            continue
    
    logger.info(f"Walk-forward analysis completed: {len(results)} results")
    return results

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