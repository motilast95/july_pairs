#!/usr/bin/env python3
"""
Main entry point for the Pairs Trading System.

This script provides a command-line interface to run various components
of the pairs trading system.
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
from src.analysis.performance import print_performance_summary, export_performance_metrics

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

def run_backtest(args):
    """Run a backtest with the specified configuration."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting pairs trading backtest...")
    
    try:
        # Load data
        prices = load_prices("data/prices.csv")
        sector_tickers = load_sector_tickers("config/data_params.py")
        
        # Create configuration
        config = create_default_config()
        if args.start_date:
            config = config.update(start_date=args.start_date)
        if args.end_date:
            config = config.update(end_date=args.end_date)
        if args.train_size:
            config = config.update(train_size=args.train_size)
        if args.test_size:
            config = config.update(test_size=args.test_size)
        
        logger.info(f"Configuration: {config.to_dict()}")
        
        # Run walk-forward analysis
        results = walk_forward(prices, sector_tickers, config.to_dict())
        
        if results:
            # Calculate portfolio metrics
            portfolio_pnl = aggregate_portfolio_pnl(results)
            metrics = compute_portfolio_metrics(portfolio_pnl, config.initial_capital)
            
            logger.info("Backtest completed successfully!")
            logger.info(f"Total results: {len(results)}")
            logger.info(f"Portfolio metrics: {metrics}")
            
            # Print performance summary
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

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Pairs Trading System")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Backtest command
    backtest_parser = subparsers.add_parser('backtest', help='Run a backtest')
    backtest_parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    backtest_parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    backtest_parser.add_argument('--train-size', type=int, help='Training window size')
    backtest_parser.add_argument('--test-size', type=int, help='Testing window size')
    
    # Diagnostic command
    diagnostic_parser = subparsers.add_parser('diagnostic', help='Run diagnostic analysis')
    
    args = parser.parse_args()
    
    if args.command == 'backtest':
        success = run_backtest(args)
        sys.exit(0 if success else 1)
    elif args.command == 'diagnostic':
        run_diagnostic(args)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main() 