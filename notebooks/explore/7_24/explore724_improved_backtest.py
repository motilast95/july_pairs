"""
Improved Pairs Trading Backtest - Showcasing All Enhancements
Date: 2024-07-24

This script demonstrates the improved pairs trading system with:
- Centralized configuration management
- Risk management and position scaling
- Transaction cost modeling
- Enhanced error handling and logging
- Look-ahead bias fixes
- Comprehensive performance analysis
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sys
import os
import time
import logging
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import improved modules
from config.trading_config import create_default_config
from data_loader import load_prices, load_sector_tickers
from walk_forward import walk_forward
from portfolio_analysis import aggregate_portfolio_pnl, compute_portfolio_metrics
from risk_management import PortfolioRiskManager, calculate_drawdown_limits

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('improved_backtest.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Run comprehensive backtest with all improvements."""
    start_time = time.time()
    logger.info("Starting improved pairs trading backtest...")
    
    # ============================================================================
    # 1. CONFIGURATION SETUP
    # ============================================================================
    logger.info("Setting up configuration...")
    
    # Create default configuration
    config = create_default_config()
    
    # Customize configuration for this backtest
    config = config.update(
        start_date="2022-01-01",
        end_date="2024-06-30",
        train_size=252,  # 1 year training
        test_size=63,    # ~3 months testing
        entry_z=1.0,
        exit_z=0.25,
        signal_method='tiered',
        rolling_window=60,
        scaling_factor=1.0,
        position_size=14,
        transaction_cost_bps=5.0,  # 5 basis points
        max_position_per_pair=1.0,
        max_portfolio_exposure=0.5,
        volatility_target=0.15
    )
    
    logger.info(f"Configuration: {config.signal_method} signals, {config.transaction_cost_bps}bps costs")
    
    # ============================================================================
    # 2. DATA LOADING
    # ============================================================================
    logger.info("Loading data...")
    
    try:
        prices = load_prices('data/prices.csv')
        sector_tickers = load_sector_tickers('config/data_params.py')
        
        # Filter to date range
        prices = prices.loc[config.start_date:config.end_date]
        
        logger.info(f"Loaded {len(prices)} days of data for {len(prices.columns)} tickers")
        logger.info(f"Date range: {prices.index[0]} to {prices.index[-1]}")
        
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        return
    
    # ============================================================================
    # 3. WALK-FORWARD ANALYSIS
    # ============================================================================
    logger.info("Running walk-forward analysis...")
    
    try:
        results = walk_forward(prices, sector_tickers, config.to_dict())
        logger.info(f"Walk-forward completed: {len(results)} results")
        
    except Exception as e:
        logger.error(f"Error in walk-forward analysis: {e}")
        return
    
    # ============================================================================
    # 4. PORTFOLIO ANALYSIS
    # ============================================================================
    logger.info("Analyzing portfolio performance...")
    
    try:
        # Aggregate portfolio PnL
        portfolio_pnl = aggregate_portfolio_pnl(results)
        
        # Calculate metrics
        metrics = compute_portfolio_metrics(portfolio_pnl, initial_capital=config.initial_capital)
        
        # Additional analysis
        total_return = portfolio_pnl.sum()
        avg_daily_return = portfolio_pnl.mean()
        daily_volatility = portfolio_pnl.std()
        sharpe_ratio = avg_daily_return / daily_volatility * np.sqrt(252) if daily_volatility > 0 else np.nan
        
        # Calculate drawdown
        cumulative_pnl = portfolio_pnl.cumsum()
        running_max = cumulative_pnl.cummax()
        drawdown = (cumulative_pnl - running_max) / running_max
        max_drawdown = drawdown.min()
        
        logger.info("Portfolio Performance Summary:")
        logger.info(f"  Total Return: ${total_return:,.2f}")
        logger.info(f"  Sharpe Ratio: {sharpe_ratio:.2f}")
        logger.info(f"  Max Drawdown: {max_drawdown:.2%}")
        logger.info(f"  Daily Volatility: ${daily_volatility:.2f}")
        win_rate_str = f"{metrics.get('win_rate', 0):.2%}" if metrics.get('win_rate') is not None else 'N/A'
        logger.info(f"  Win Rate: {win_rate_str}")
        
    except Exception as e:
        logger.error(f"Error in portfolio analysis: {e}")
        return
    
    # ============================================================================
    # 5. TRADE ANALYSIS
    # ============================================================================
    logger.info("Analyzing individual trades...")
    
    try:
        # Collect all trades
        all_trades = []
        for res in results:
            all_trades.extend(res['trades'])
        
        if all_trades:
            trades_df = pd.DataFrame(all_trades)
            
            # Trade statistics
            total_trades = len(trades_df)
            winning_trades = len(trades_df[trades_df['net_pnl'] > 0])
            losing_trades = len(trades_df[trades_df['net_pnl'] < 0])
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            
            avg_win = trades_df[trades_df['net_pnl'] > 0]['net_pnl'].mean() if winning_trades > 0 else 0
            avg_loss = trades_df[trades_df['net_pnl'] < 0]['net_pnl'].mean() if losing_trades > 0 else 0
            profit_factor = abs(avg_win * winning_trades / (avg_loss * losing_trades)) if losing_trades > 0 and avg_loss != 0 else float('inf')
            
            avg_holding_period = trades_df['holding_period'].mean()
            
            logger.info("Trade Statistics:")
            logger.info(f"  Total Trades: {total_trades}")
            logger.info(f"  Win Rate: {win_rate:.2%}")
            logger.info(f"  Profit Factor: {profit_factor:.2f}")
            logger.info(f"  Avg Win: ${avg_win:.2f}")
            logger.info(f"  Avg Loss: ${avg_loss:.2f}")
            logger.info(f"  Avg Holding Period: {avg_holding_period:.1f} days")
            
            # Save trade data
            trades_df.to_csv('improved_trades.csv', index=False)
            logger.info("Trade data saved to improved_trades.csv")
            
        else:
            logger.warning("No trades found in results")
            
    except Exception as e:
        logger.error(f"Error in trade analysis: {e}")
    
    # ============================================================================
    # 6. RISK ANALYSIS
    # ============================================================================
    logger.info("Performing risk analysis...")
    
    try:
        # Calculate Value at Risk
        returns = portfolio_pnl / config.initial_capital
        var_95 = np.percentile(returns, 5)  # 95% VaR
        var_99 = np.percentile(returns, 1)  # 99% VaR
        
        # Calculate maximum consecutive losses
        consecutive_losses = 0
        max_consecutive_losses = 0
        for pnl in portfolio_pnl:
            if pnl < 0:
                consecutive_losses += 1
                max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
            else:
                consecutive_losses = 0
        
        logger.info("Risk Metrics:")
        logger.info(f"  95% VaR: {var_95:.2%}")
        logger.info(f"  99% VaR: {var_99:.2%}")
        logger.info(f"  Max Consecutive Losses: {max_consecutive_losses} days")
        
    except Exception as e:
        logger.error(f"Error in risk analysis: {e}")
    
    # ============================================================================
    # 7. VISUALIZATION
    # ============================================================================
    logger.info("Creating visualizations...")
    
    try:
        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Improved Pairs Trading System - Performance Analysis', fontsize=16)
        
        # 1. Cumulative PnL
        cumulative_pnl = portfolio_pnl.cumsum()
        axes[0, 0].plot(cumulative_pnl.index, cumulative_pnl.values, linewidth=2, color='blue')
        axes[0, 0].set_title('Cumulative Portfolio PnL')
        axes[0, 0].set_ylabel('Cumulative PnL ($)')
        axes[0, 0].grid(True, alpha=0.3)
        
        # 2. Daily PnL
        axes[0, 1].plot(portfolio_pnl.index, portfolio_pnl.values, alpha=0.7, color='green')
        axes[0, 1].set_title('Daily Portfolio PnL')
        axes[0, 1].set_ylabel('Daily PnL ($)')
        axes[0, 1].grid(True, alpha=0.3)
        
        # 3. Drawdown
        axes[1, 0].fill_between(drawdown.index, drawdown.values, 0, color='red', alpha=0.3)
        axes[1, 0].plot(drawdown.index, drawdown.values, color='red', linewidth=1)
        axes[1, 0].set_title('Portfolio Drawdown')
        axes[1, 0].set_ylabel('Drawdown (%)')
        axes[1, 0].grid(True, alpha=0.3)
        
        # 4. Trade PnL Distribution
        if all_trades:
            trade_pnls = trades_df['net_pnl']
            axes[1, 1].hist(trade_pnls, bins=50, alpha=0.7, color='purple', edgecolor='black')
            axes[1, 1].set_title('Trade PnL Distribution')
            axes[1, 1].set_xlabel('Trade PnL ($)')
            axes[1, 1].set_ylabel('Frequency')
            axes[1, 1].grid(True, alpha=0.3)
            
            # Add mean line
            mean_pnl = trade_pnls.mean()
            axes[1, 1].axvline(mean_pnl, color='red', linestyle='--', label=f'Mean: ${mean_pnl:.2f}')
            axes[1, 1].legend()
        
        plt.tight_layout()
        plt.savefig('improved_backtest_performance.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info("Performance charts saved to improved_backtest_performance.png")
        
    except Exception as e:
        logger.error(f"Error creating visualizations: {e}")
    
    # ============================================================================
    # 8. COMPARISON WITH BASELINE
    # ============================================================================
    logger.info("Comparing with baseline (no transaction costs)...")
    
    try:
        # Create baseline config (no transaction costs)
        baseline_config = config.update(transaction_cost_bps=0.0)
        
        # Run baseline backtest
        baseline_results = walk_forward(prices, sector_tickers, baseline_config.to_dict())
        baseline_pnl = aggregate_portfolio_pnl(baseline_results)
        baseline_total = baseline_pnl.sum()
        
        # Calculate cost impact
        cost_impact = baseline_total - total_return
        cost_impact_pct = (cost_impact / baseline_total) * 100 if baseline_total != 0 else 0
        
        logger.info("Transaction Cost Impact:")
        logger.info(f"  Baseline Return: ${baseline_total:,.2f}")
        logger.info(f"  Net Return: ${total_return:,.2f}")
        logger.info(f"  Cost Impact: ${cost_impact:,.2f} ({cost_impact_pct:.2f}%)")
        
    except Exception as e:
        logger.error(f"Error in baseline comparison: {e}")
    
    # ============================================================================
    # 9. SUMMARY REPORT
    # ============================================================================
    end_time = time.time()
    runtime = end_time - start_time
    
    logger.info("=" * 60)
    logger.info("IMPROVED BACKTEST SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Runtime: {runtime:.2f} seconds")
    logger.info(f"Date Range: {config.start_date} to {config.end_date}")
    logger.info(f"Initial Capital: ${config.initial_capital:,.0f}")
    logger.info(f"Signal Method: {config.signal_method}")
    logger.info(f"Transaction Costs: {config.transaction_cost_bps} bps")
    logger.info(f"Risk Management: Enabled")
    logger.info(f"Total Return: ${total_return:,.2f}")
    logger.info(f"Sharpe Ratio: {sharpe_ratio:.2f}")
    logger.info(f"Max Drawdown: {max_drawdown:.2%}")
    logger.info(f"Total Trades: {len(all_trades) if all_trades else 0}")
    logger.info("=" * 60)
    
    # Save summary to file
    summary_data = {
        'runtime_seconds': runtime,
        'start_date': config.start_date,
        'end_date': config.end_date,
        'initial_capital': config.initial_capital,
        'signal_method': config.signal_method,
        'transaction_cost_bps': config.transaction_cost_bps,
        'total_return': total_return,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'total_trades': len(all_trades) if all_trades else 0,
        'win_rate': win_rate if all_trades else 0,
        'profit_factor': profit_factor if all_trades else 0
    }
    
    summary_df = pd.DataFrame([summary_data])
    summary_df.to_csv('improved_backtest_summary.csv', index=False)
    logger.info("Summary saved to improved_backtest_summary.csv")

if __name__ == "__main__":
    main() 