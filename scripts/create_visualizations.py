#!/usr/bin/env python3
"""
Standalone script to create comprehensive strategy visualizations.
Generates professional charts and reports for strategy showcasing.
"""

import sys
import os
import argparse
import logging
import pandas as pd
import json
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, os.path.abspath('..'))

from src.analysis.visualization import create_strategy_visualizations
from src.analysis.portfolio_analysis import aggregate_portfolio_pnl, compute_portfolio_metrics

def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def load_existing_results(results_file: str = "results/data/trades_data.csv",
                         benchmark_file: str = "results/benchmark_comparison.json") -> tuple:
    """
    Load existing backtest results and benchmark data.
    
    Args:
        results_file: Path to trades data CSV
        benchmark_file: Path to benchmark comparison JSON
    
    Returns:
        Tuple of (portfolio_pnl, benchmark_data, trades_data, metrics)
    """
    logger = logging.getLogger(__name__)
    
    # Load trades data
    trades_data = pd.DataFrame()
    if os.path.exists(results_file):
        trades_data = pd.read_csv(results_file)
        logger.info(f"Loaded trades data from {results_file}")
    else:
        logger.warning(f"Trades data file not found: {results_file}")
    
    # Load benchmark data
    benchmark_data = None
    if os.path.exists(benchmark_file):
        with open(benchmark_file, 'r') as f:
            benchmark_data = json.load(f)
        logger.info(f"Loaded benchmark data from {benchmark_file}")
    else:
        logger.warning(f"Benchmark data file not found: {benchmark_file}")
    
    # Calculate portfolio PnL and metrics
    portfolio_pnl = pd.Series(dtype=float)
    metrics = {}
    
    if not trades_data.empty:
        # Group by date and sum PnL
        if 'date' in trades_data.columns and 'pnl' in trades_data.columns:
            trades_data['date'] = pd.to_datetime(trades_data['date'])
            portfolio_pnl = trades_data.groupby('date')['pnl'].sum()
            portfolio_pnl = portfolio_pnl.sort_index()
            
            # Calculate metrics
            metrics = compute_portfolio_metrics(portfolio_pnl, initial_capital=100000)
            logger.info("Calculated portfolio metrics")
    
    return portfolio_pnl, benchmark_data, trades_data, metrics

def main():
    """Main function to create visualizations."""
    parser = argparse.ArgumentParser(description="Create strategy visualizations")
    parser.add_argument('--results-file', default="results/data/trades_data.csv",
                       help='Path to trades data CSV file')
    parser.add_argument('--benchmark-file', default="results/benchmark_comparison.json",
                       help='Path to benchmark comparison JSON file')
    parser.add_argument('--output-dir', default="results",
                       help='Output directory for visualizations')
    parser.add_argument('--format', choices=['png', 'pdf', 'svg'], default='png',
                       help='Output format for static charts')
    
    args = parser.parse_args()
    
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("🎨 Creating Strategy Visualizations")
    logger.info("=" * 50)
    
    # Load existing data
    portfolio_pnl, benchmark_data, trades_data, metrics = load_existing_results(
        args.results_file, args.benchmark_file
    )
    
    if portfolio_pnl.empty:
        logger.error("No portfolio data available. Please run a backtest first.")
        return False
    
    # Create visualizations
    try:
        viz_files = create_strategy_visualizations(
            portfolio_pnl=portfolio_pnl,
            benchmark_data=benchmark_data,
            trades_data=trades_data,
            metrics=metrics,
            output_dir=args.output_dir
        )
        
        if viz_files:
            logger.info("✅ Successfully created visualizations:")
            logger.info("=" * 50)
            for viz_type, file_path in viz_files.items():
                logger.info(f"📊 {viz_type.upper()}: {file_path}")
            
            logger.info("=" * 50)
            logger.info("🎯 Key Visualization Files:")
            logger.info(f"   📈 Interactive Dashboard: {viz_files.get('dashboard', 'N/A')}")
            logger.info(f"   📊 Performance Charts: {viz_files.get('performance_chart', 'N/A')}")
            logger.info(f"   📋 Summary Report: {viz_files.get('summary_report', 'N/A')}")
            logger.info(f"   📊 Benchmark Table: {viz_files.get('benchmark_table', 'N/A')}")
            
            if 'trading_analysis' in viz_files:
                logger.info(f"   📈 Trading Analysis: {viz_files['trading_analysis']}")
            
            return True
        else:
            logger.error("Failed to create any visualizations")
            return False
            
    except Exception as e:
        logger.error(f"Error creating visualizations: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 