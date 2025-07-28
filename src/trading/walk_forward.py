import pandas as pd
import numpy as np
from typing import Dict, List
import logging
from src.data.pair_selection import select_pairs, select_pairs_fast, select_pairs_ultra_fast
from src.models.model_fitting import fit_spread
from src.models.signal_generation import generate_signals, generate_rolling_signals, generate_rolling_scaled_signals, generate_rolling_stepwise_signals, generate_rolling_stepwise_scaled_signals, generate_tiered_signals
from src.trading.backtest import run_backtest, compute_performance_metrics
from src.trading.risk_management import PortfolioRiskManager
from src.analysis.performance import time_function, time_block, print_performance_summary, export_performance_metrics

# Set up logging
logger = logging.getLogger(__name__)

@time_function("walk_forward_analysis")
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
    all_trades = []  # Collect all trades for export
    total_windows = (len(prices) - train_size - test_size) // test_size

    logger.info(f"Starting walk-forward analysis: {total_windows} windows")

    for window_idx, start in enumerate(range(0, len(prices) - train_size - test_size, test_size)):
        try:
            train_window = slice(prices.index[start], prices.index[start + train_size - 1])
            test_window = slice(prices.index[start + train_size], prices.index[start + train_size + test_size - 1])

            logger.debug(f"Processing window {window_idx + 1}/{total_windows}: {train_window.start} to {test_window.stop}")

            # Select pairs with risk validation (using configurable pair selection method)
            adf_alpha = config.get('adf_alpha', 0.05)
            distance_threshold = config.get('distance_threshold', 0.1)
            pair_selection_method = config.get('pair_selection_method', 'fast')
            
            # Choose pair selection method
            if pair_selection_method == 'original':
                pairs = select_pairs(prices, sector_tickers, train_window, adf_alpha=adf_alpha)
            elif pair_selection_method == 'fast':
                pairs = select_pairs_fast(prices, sector_tickers, train_window, adf_alpha=adf_alpha, distance_threshold=distance_threshold)
            elif pair_selection_method == 'ultra_fast':
                pairs = select_pairs_ultra_fast(prices, sector_tickers, train_window, distance_threshold=distance_threshold)
            else:
                # Default to fast method
                pairs = select_pairs_fast(prices, sector_tickers, train_window, adf_alpha=adf_alpha, distance_threshold=distance_threshold)
            
            valid_pairs = []

            # Check if risk management is enabled
            risk_management_enabled = config.get('enable_pair_validation', True)
            
            for pair in pairs:
                if risk_manager.validate_pair_risk(pair, prices, train_window):
                    valid_pairs.append(pair)
                else:
                    if risk_management_enabled:
                        logger.debug(f"Pair {pair} failed risk validation")

            # Only log risk validation results if risk management is enabled
            if risk_management_enabled:
                logger.info(f"Window {window_idx + 1}: {len(valid_pairs)}/{len(pairs)} pairs passed risk validation")
            else:
                logger.info(f"Window {window_idx + 1}: {len(valid_pairs)} pairs selected (risk validation disabled)")

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

                    # Collect trades with additional context
                    for trade in backtest_results.get('trades', []):
                        trade.update({
                            'pair1': pair[0],
                            'pair2': pair[1],
                            'window_idx': window_idx,
                            'train_start': prices.index[start],
                            'test_start': prices.index[start + train_size],
                            'beta': model_params['beta'],
                        })
                        all_trades.append(trade)

                    results.append({
                        'pair': pair,
                        'train_start': prices.index[start],
                        'test_start': prices.index[start + train_size],
                        'window_idx': window_idx,
                        'metrics': metrics,
                        'daily_pnl': backtest_results['daily_pnl'],
                        'daily_pnl_gross': backtest_results['daily_pnl_gross'],
                    })
                except Exception as e:
                    logger.error(f"Error processing pair {pair} in window {window_idx + 1}: {e}")
                    continue
        except Exception as e:
            logger.error(f"Error in window {window_idx + 1}: {e}")
            continue

    # Save all trades to CSV for later analysis
    if all_trades:
        trades_df = pd.DataFrame(all_trades)
        trades_df.to_csv('results/data/trades_data.csv', index=False)
        logger.info(f"Saved all trades to results/data/trades_data.csv ({len(trades_df)} trades)")

    # Save daily portfolio data for visualizations
    if results:
        # Combine all daily P&L series
        all_daily_pnl = pd.Series(dtype=float)
        for result in results:
            if 'daily_pnl' in result:
                daily_pnl = result['daily_pnl']
                # Align dates and add P&L
                for date, pnl in daily_pnl.items():
                    if date in all_daily_pnl.index:
                        all_daily_pnl[date] += pnl
                    else:
                        all_daily_pnl[date] = pnl
        
        # Calculate portfolio metrics (outside the loop)
        if not all_daily_pnl.empty:
            # Sort by date
            all_daily_pnl = all_daily_pnl.sort_index()
            
            # Filter to only include trading periods (when there are actual trades)
            if all_trades:
                trades_df_temp = pd.DataFrame(all_trades)
                trades_df_temp['entry_date'] = pd.to_datetime(trades_df_temp['entry_date'])
                trades_df_temp['exit_date'] = pd.to_datetime(trades_df_temp['exit_date'])
                
                # Get the actual trading date range
                trading_start = trades_df_temp['entry_date'].min()
                trading_end = trades_df_temp['exit_date'].max()
                
                # Filter daily P&L to only include trading periods
                all_daily_pnl = all_daily_pnl[trading_start:trading_end]
            
            # Calculate cumulative P&L
            cumulative_pnl = all_daily_pnl.cumsum()
            
            # Calculate portfolio value (assuming $100k initial capital)
            initial_capital = 100000
            portfolio_value = initial_capital + cumulative_pnl
            
            # Calculate daily returns (matching main backtest method)
            daily_returns = all_daily_pnl / initial_capital
            
            # Calculate total return using geometric returns (matching main backtest)
            total_return = (1 + daily_returns).prod() - 1
            
            # Calculate cumulative returns as percentage
            cumulative_returns = (portfolio_value / initial_capital - 1) * 100
            
            # Save daily portfolio data
            portfolio_data = pd.DataFrame({
                'date': portfolio_value.index,
                'daily_pnl': all_daily_pnl.values,
                'portfolio_value': portfolio_value.values,
                'daily_return': daily_returns.values,
                'cumulative_return_pct': cumulative_returns.values
            })
            
            portfolio_data.to_csv('results/data/portfolio_daily.csv', index=False)
            logger.info(f"Saved daily portfolio data to results/data/portfolio_daily.csv")
            
            # Also save summary metrics (matching main backtest calculation)
            summary_metrics = {
                'initial_capital': initial_capital,
                'final_portfolio_value': portfolio_value.iloc[-1],
                'total_return_pct': total_return * 100,  # Use geometric return
                'total_pnl': cumulative_pnl.iloc[-1],
                'max_portfolio_value': portfolio_value.max(),
                'min_portfolio_value': portfolio_value.min(),
                'volatility': daily_returns.std() * np.sqrt(252) * 100,
                'sharpe_ratio': daily_returns.mean() / daily_returns.std() * np.sqrt(252) if daily_returns.std() > 0 else 0
            }
            
            import json
            with open('results/data/portfolio_summary.json', 'w') as f:
                json.dump(summary_metrics, f, indent=2)
            logger.info(f"Saved portfolio summary to results/data/portfolio_summary.json")

    return results