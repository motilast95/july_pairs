#!/usr/bin/env python3
"""
Standalone benchmark analysis script for pairs trading strategy.
Compares strategy performance against market benchmarks and alternative strategies.
"""

import sys
import os
import argparse
import logging
import pandas as pd
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, os.path.abspath('.'))

from src.analysis.benchmark_analysis import run_benchmark_analysis
from src.data.data_loader import load_prices_for_universe

def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def load_existing_results(results_file: str = "results/data/trades_data.csv") -> pd.Series:
    """Load existing backtest results and convert to daily returns."""
    if not os.path.exists(results_file):
        raise FileNotFoundError(f"Results file not found: {results_file}")
    
    # Load trades data
    trades_df = pd.read_csv(results_file)
    
    if trades_df.empty:
        raise ValueError("No trades data found in results file")
    
    # Convert to datetime
    trades_df['entry_date'] = pd.to_datetime(trades_df['entry_date'])
    trades_df['exit_date'] = pd.to_datetime(trades_df['exit_date'])
    
    # Create daily PnL series
    daily_pnl = pd.Series(0.0, index=pd.date_range(
        start=trades_df['entry_date'].min(),
        end=trades_df['exit_date'].max(),
        freq='D'
    ))
    
    # Aggregate PnL by date
    for _, trade in trades_df.iterrows():
        # Add net PnL to exit date (when position is closed)
        daily_pnl.loc[trade['exit_date']] += trade['net_pnl']
    
    return daily_pnl

def run_benchmark_analysis_script(
    start_date: str,
    end_date: str,
    universe: str = 'mega_cap',
    initial_capital: float = 100000,
    risk_free_rate: float = 0.02,
    results_file: str = None
):
    """Run comprehensive benchmark analysis."""
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 80)
    logger.info("PAIRS TRADING BENCHMARK ANALYSIS")
    logger.info("=" * 80)
    logger.info(f"Analysis Period: {start_date} to {end_date}")
    logger.info(f"Universe: {universe}")
    logger.info(f"Initial Capital: ${initial_capital:,.0f}")
    logger.info(f"Risk-Free Rate: {risk_free_rate*100:.1f}%")
    
    try:
        # Load strategy results
        if results_file and os.path.exists(results_file):
            logger.info(f"Loading results from: {results_file}")
            portfolio_pnl = load_existing_results(results_file)
        else:
            logger.warning("No existing results file found. Please run a backtest first.")
            return False
        
        # Convert PnL to returns
        strategy_returns = portfolio_pnl / initial_capital
        
        # Load universe prices for equal-weighted comparison
        logger.info(f"Loading {universe} universe prices...")
        universe_prices = load_prices_for_universe(
            universe=universe,
            start_date=start_date,
            end_date=end_date
        )
        
        if universe_prices.empty:
            logger.error("Failed to load universe prices")
            return False
        
        # Run benchmark analysis
        logger.info("Running benchmark comparison...")
        benchmark_results = run_benchmark_analysis(
            strategy_returns=strategy_returns,
            universe_prices=universe_prices,
            start_date=start_date,
            end_date=end_date,
            risk_free_rate=risk_free_rate
        )
        
        if benchmark_results and 'report' in benchmark_results:
            # Print the report
            print("\n" + benchmark_results['report'])
            
            # Save results
            import json
            results_dir = Path("results")
            results_dir.mkdir(exist_ok=True)
            
            benchmark_file = results_dir / "benchmark_comparison.json"
            with open(benchmark_file, 'w') as f:
                json.dump(benchmark_results['comparison'], f, indent=2, default=str)
            
            report_file = results_dir / "benchmark_report.txt"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(benchmark_results['report'])
            
            logger.info(f"Results saved to:")
            logger.info(f"  - {benchmark_file}")
            logger.info(f"  - {report_file}")
            
            return True
        else:
            logger.error("Benchmark analysis failed")
            return False
            
    except Exception as e:
        logger.error(f"Benchmark analysis failed: {e}")
        return False

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Pairs Trading Benchmark Analysis")
    
    parser.add_argument('--start-date', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--universe', default='mega_cap', 
                       choices=['mega_cap', 'mid_cap', 'custom'],
                       help='Trading universe')
    parser.add_argument('--initial-capital', type=float, default=100000,
                       help='Initial capital for return calculation')
    parser.add_argument('--risk-free-rate', type=float, default=0.02,
                       help='Risk-free rate for Sharpe ratio calculation')
    parser.add_argument('--results-file', 
                       help='Path to results file (default: results/data/trades_data.csv)')
    
    args = parser.parse_args()
    
    setup_logging()
    
    success = run_benchmark_analysis_script(
        start_date=args.start_date,
        end_date=args.end_date,
        universe=args.universe,
        initial_capital=args.initial_capital,
        risk_free_rate=args.risk_free_rate,
        results_file=args.results_file
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 