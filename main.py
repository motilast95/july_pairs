#!/usr/bin/env python3
"""
Main entry point for the Pairs Trading System.

This script provides a command-line interface to run various components
of the pairs trading system with full configuration support.
"""

import argparse
import sys
import os
import logging
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, os.path.abspath('.'))

from config.trading_config import create_default_config
from src.data.data_loader import load_prices, load_sector_tickers
from src.trading.walk_forward import walk_forward
from src.analysis.portfolio_analysis import aggregate_portfolio_pnl, compute_portfolio_metrics
from src.analysis.performance import print_performance_summary, export_performance_metrics, enable_performance_monitoring
from src.analysis.benchmark_analysis import run_benchmark_analysis

def setup_logging(level=logging.INFO):
    """Set up logging configuration."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('results/logs/pairs_trading.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def create_config_from_args(args):
    """Create configuration from command line arguments."""
    config = create_default_config()
    
    # Basic parameters
    if args.start_date:
        config = config.update(start_date=args.start_date)
    if args.end_date:
        config = config.update(end_date=args.end_date)
    if args.train_size:
        config = config.update(train_size=args.train_size)
    if args.test_size:
        config = config.update(test_size=args.test_size)
    
    # Universe selection
    if args.universe:
        config = config.update(universe=args.universe)
        
        # Load universe-specific parameters
        from src.data.data_loader import load_universe_parameters
        universe_params = load_universe_parameters(args.universe)
        
        # Apply universe-specific parameters if not explicitly overridden
        if not args.transaction_cost_bps:
            config = config.update(transaction_cost_bps=universe_params['transaction_cost_bps'])
        if not args.position_size:
            config = config.update(position_size=universe_params['position_size'])
        if not args.distance_threshold:
            config = config.update(distance_threshold=universe_params['distance_threshold'])
    
    # Signal generation parameters
    if args.signal_method:
        config = config.update(signal_method=args.signal_method)
    if args.entry_z is not None:
        config = config.update(entry_z=args.entry_z)
    if args.exit_z is not None:
        config = config.update(exit_z=args.exit_z)
    if args.rolling_window:
        config = config.update(rolling_window=args.rolling_window)
    if args.position_size:
        config = config.update(position_size=args.position_size)
    if args.transaction_cost_bps:
        config = config.update(transaction_cost_bps=args.transaction_cost_bps)
    
    # Pair selection parameters
    if args.distance_threshold:
        config = config.update(distance_threshold=args.distance_threshold)
    if args.adf_alpha:
        config = config.update(adf_alpha=args.adf_alpha)
    if args.pair_selection_method:
        config = config.update(pair_selection_method=args.pair_selection_method)
    
    # Risk management configuration
    if args.risk_management_mode:
        if args.risk_management_mode == "disabled":
            config = config.update(
                enable_volatility_scaling=False,
                enable_position_limits=False,
                enable_pair_validation=False,
                max_position_per_pair=999999.0,
                max_portfolio_exposure=1.0
            )
        elif args.risk_management_mode == "minimal":
            config = config.update(
                enable_volatility_scaling=False,
                enable_position_limits=True,
                enable_pair_validation=True,
                max_position_per_pair=1.0,
                max_portfolio_exposure=0.5
            )
        elif args.risk_management_mode == "moderate":
            config = config.update(
                enable_volatility_scaling=True,
                enable_position_limits=True,
                enable_pair_validation=True,
                max_position_per_pair=1.0,
                max_portfolio_exposure=0.5
            )
        elif args.risk_management_mode == "full":
            config = config.update(
                enable_volatility_scaling=True,
                enable_position_limits=True,
                enable_pair_validation=True,
                max_position_per_pair=1.0,
                max_portfolio_exposure=0.5
            )
    
    # Individual risk management toggles (override mode if specified)
    if args.disable_volatility_scaling:
        config = config.update(enable_volatility_scaling=False)
    if args.disable_position_limits:
        config = config.update(enable_position_limits=False)
    if args.disable_pair_validation:
        config = config.update(enable_pair_validation=False)
    
    # Risk management thresholds
    if args.max_pair_volatility:
        config = config.update(max_pair_volatility=args.max_pair_volatility)
    if args.max_daily_move:
        config = config.update(max_daily_move=args.max_daily_move)
    if args.min_data_days:
        config = config.update(min_data_days=args.min_data_days)
    
    return config

def run_backtest(args):
    """Run a backtest with the specified configuration."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Enable performance monitoring if requested
    if hasattr(args, 'enable_performance') and args.enable_performance:
        enable_performance_monitoring()
        logger.info("Performance monitoring enabled")
    else:
        logger.info("Performance monitoring disabled (faster execution)")
    
    logger.info("Starting pairs trading backtest...")
    
    try:
        # Create configuration from arguments
        config = create_config_from_args(args)
        
        # Load data for specific universe (defaults to mega_cap)
        from src.data.data_loader import load_prices_for_universe, load_sector_tickers_for_universe
        
        prices = load_prices_for_universe(
            universe=config.universe,
            start_date=config.start_date,
            end_date=config.end_date
        )
        sector_tickers = load_sector_tickers_for_universe(universe=config.universe)
        
        logger.info(f"Using universe-aware data loading ({config.universe})")
        
        # Log configuration summary
        logger.info("=" * 60)
        logger.info("CONFIGURATION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Universe: {config.universe}")
        logger.info(f"Signal Method: {config.signal_method}")
        logger.info(f"Entry Z-Score: {config.entry_z}")
        logger.info(f"Exit Z-Score: {config.exit_z}")
        logger.info(f"Risk Management Mode: {getattr(args, 'risk_management_mode', 'default')}")
        logger.info(f"Volatility Scaling: {config.enable_volatility_scaling}")
        logger.info(f"Position Limits: {config.enable_position_limits}")
        logger.info(f"Pair Validation: {config.enable_pair_validation}")
        logger.info(f"Pair Selection Method: {getattr(config, 'pair_selection_method', 'fast')}")
        logger.info(f"Distance Threshold: {config.distance_threshold}")
        logger.info(f"Transaction Cost: {config.transaction_cost_bps} bps")
        logger.info(f"Position Size: {config.position_size}")
        logger.info(f"Date Range: {config.start_date} to {config.end_date}")
        logger.info(f"Train/Test: {config.train_size}/{config.test_size} days")
        logger.info("=" * 60)
        
        # Run walk-forward analysis
        results = walk_forward(prices, sector_tickers, config.to_dict())
        
        if results:
            # Calculate portfolio metrics
            portfolio_pnl = aggregate_portfolio_pnl(results)
            metrics = compute_portfolio_metrics(portfolio_pnl, config.initial_capital, results)
            
            # Print beautiful results summary
            logger.info("=" * 60)
            logger.info("🎉 BACKTEST COMPLETED SUCCESSFULLY!")
            logger.info("=" * 60)
            
            # Extract metrics for better formatting
            total_return = float(metrics['total_return'])
            annualized_return = float(metrics['annualized_return'])
            sharpe_ratio = float(metrics['sharpe_ratio'])
            max_drawdown = float(metrics['max_drawdown'])
            
            logger.info(f"📊 PORTFOLIO PERFORMANCE")
            logger.info(f"   Total Return:     {total_return:.4f} ({total_return*100:.2f}%)")
            logger.info(f"   Annualized Return: {annualized_return:.4f} ({annualized_return*100:.2f}%)")
            logger.info(f"   Sharpe Ratio:     {sharpe_ratio:.3f}")
            logger.info(f"   Max Drawdown:     {max_drawdown:.4f} ({max_drawdown*100:.2f}%)")
            logger.info("")
            logger.info(f"📈 TRADING SUMMARY")
            logger.info(f"   Total Results:    {len(results)} pair results")
            logger.info(f"   Date Range:       {config.start_date} to {config.end_date}")
            logger.info(f"   Train/Test:       {config.train_size}/{config.test_size} days")
            logger.info(f"   Trading Days:     {metrics.get('trading_days', 'N/A')} out of {metrics.get('total_days', 'N/A')} total days")
            logger.info(f"   Training Days Removed: {metrics.get('training_days_removed', 'N/A')} days")
            logger.info(f"   First Test Date:  {metrics.get('first_test_date', 'N/A')}")
            logger.info("=" * 60)
            
            # Run benchmark comparison if requested
            if hasattr(args, 'benchmark') and args.benchmark:
                logger.info("=" * 60)
                logger.info("📊 RUNNING BENCHMARK COMPARISON")
                logger.info("=" * 60)
                
                # Convert portfolio PnL to returns for comparison
                strategy_returns = portfolio_pnl / config.initial_capital
                
                # Run benchmark analysis
                benchmark_results = run_benchmark_analysis(
                    strategy_returns=strategy_returns,
                    universe_prices=prices,
                    start_date=config.start_date,
                    end_date=config.end_date,
                    risk_free_rate=config.risk_free_rate
                )
                
                if benchmark_results and 'report' in benchmark_results:
                    logger.info(benchmark_results['report'])
                    
                    # Save benchmark results
                    import json
                    benchmark_file = "results/benchmark_comparison.json"
                    with open(benchmark_file, 'w') as f:
                        json.dump(benchmark_results['comparison'], f, indent=2, default=str)
                    logger.info(f"Benchmark results saved to {benchmark_file}")
                else:
                    logger.warning("Benchmark analysis failed or returned no results")
             
            # Create visualizations if requested

            
            # Print performance summary (only if monitoring is enabled)
            if hasattr(args, 'enable_performance') and args.enable_performance:
                logger.info("=" * 60)
                logger.info("PERFORMANCE BENCHMARKING RESULTS")
                logger.info("=" * 60)
                print_performance_summary()
                
                # Export performance metrics
                export_performance_metrics("results/performance_metrics.csv")
            
            return True
        else:
            logger.warning("No results from walk-forward analysis")
            return False
            
    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        return False

def run_diagnostic(args):
    """Run the diagnostic analysis."""
    from scripts.diagnostic_analysis import run_diagnostic_analysis
    run_diagnostic_analysis()

def run_cache_clear(args):
    """Clear cached data."""
    from src.data.data_loader import clear_cache
    universe = getattr(args, 'universe', None)
    clear_cache(universe)
    logger = logging.getLogger(__name__)
    if universe:
        logger.info(f"Cleared cache for universe: {universe}")
    else:
        logger.info("Cleared all cached data")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Pairs Trading System")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Backtest command
    backtest_parser = subparsers.add_parser('backtest', help='Run a backtest')
    
    # Basic parameters
    backtest_parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    backtest_parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    backtest_parser.add_argument('--train-size', type=int, help='Training window size')
    backtest_parser.add_argument('--test-size', type=int, help='Testing window size')
    
    # Universe and pair selection parameters
    backtest_parser.add_argument('--universe', 
                                choices=['mega_cap', 'mid_cap', 'custom'],
                                help='Trading universe (if not specified, uses legacy data/prices.csv)')
    backtest_parser.add_argument('--distance-threshold', type=float, help='Distance threshold for pair selection')
    backtest_parser.add_argument('--adf-alpha', type=float, help='ADF test significance level')
    backtest_parser.add_argument('--pair-selection-method', 
                                choices=['original', 'fast', 'ultra_fast'],
                                help='Pair selection method')
    
    # Signal generation parameters
    backtest_parser.add_argument('--signal-method', 
                                choices=['static', 'rolling', 'rolling_scaled', 'tiered'],
                                help='Signal generation method')
    backtest_parser.add_argument('--entry-z', type=float, help='Entry z-score threshold')
    backtest_parser.add_argument('--exit-z', type=float, help='Exit z-score threshold')
    backtest_parser.add_argument('--rolling-window', type=int, help='Rolling window size')
    backtest_parser.add_argument('--position-size', type=float, help='Position size')
    backtest_parser.add_argument('--transaction-cost-bps', type=float, help='Transaction cost in basis points')
    
    # Risk management
    backtest_parser.add_argument('--risk-management-mode', 
                                choices=['disabled', 'minimal', 'moderate', 'full'],
                                help='Risk management mode')
    backtest_parser.add_argument('--disable-volatility-scaling', action='store_true',
                                help='Disable volatility-based position scaling')
    backtest_parser.add_argument('--disable-position-limits', action='store_true',
                                help='Disable position size limits')
    backtest_parser.add_argument('--disable-pair-validation', action='store_true',
                                help='Disable pair risk validation')
    backtest_parser.add_argument('--max-pair-volatility', type=float, help='Maximum pair volatility')
    backtest_parser.add_argument('--max-daily-move', type=float, help='Maximum daily price move')
    backtest_parser.add_argument('--min-data-days', type=int, help='Minimum data days required')
    
    # Performance monitoring
    backtest_parser.add_argument('--enable-performance', action='store_true', 
                                help='Enable performance monitoring (slower but provides timing data)')
    
    # Benchmark comparison
    backtest_parser.add_argument('--benchmark', action='store_true',
                                help='Run benchmark comparison against market indices and ETFs')
    

    
    # Diagnostic command
    diagnostic_parser = subparsers.add_parser('diagnostic', help='Run diagnostic analysis')
    
    # Cache management command
    cache_parser = subparsers.add_parser('cache', help='Manage cached data')
    cache_parser.add_argument('action', choices=['clear'], help='Cache action')
    cache_parser.add_argument('--universe', 
                             choices=['mega_cap', 'mid_cap', 'custom'],
                             help='Specific universe to clear (optional)')
    
    args = parser.parse_args()
    
    if args.command == 'backtest':
        success = run_backtest(args)
        sys.exit(0 if success else 1)
    elif args.command == 'diagnostic':
        run_diagnostic(args)
    elif args.command == 'cache':
        run_cache_clear(args)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main() 