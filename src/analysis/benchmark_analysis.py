#!/usr/bin/env python3
"""
Benchmark analysis module for comparing pairs trading strategy performance
against market benchmarks and alternative strategies.
"""

import pandas as pd
import numpy as np
import yfinance as yf
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class BenchmarkAnalyzer:
    """Analyzes strategy performance against various market benchmarks."""
    
    def __init__(self):
        # Common benchmark tickers
        self.benchmarks = {
            'SPY': 'S&P 500 ETF',
            'QQQ': 'NASDAQ-100 ETF', 
            'IWM': 'Russell 2000 ETF',
            'VTI': 'Total Stock Market ETF',
            'XLK': 'Technology Sector ETF',
            'XLF': 'Financial Sector ETF',
            'XLV': 'Healthcare Sector ETF',
            'XLE': 'Energy Sector ETF',
            'XLI': 'Industrial Sector ETF',
            'XLY': 'Consumer Discretionary ETF'
        }
    
    def download_benchmark_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Download benchmark data for comparison period."""
        logger.info(f"Downloading benchmark data from {start_date} to {end_date}")
        
        try:
            # Download all benchmark data
            benchmark_data = yf.download(
                list(self.benchmarks.keys()), 
                start=start_date, 
                end=end_date, 
                progress=False
            )
            
            # Extract adjusted close prices
            if isinstance(benchmark_data.columns, pd.MultiIndex):
                if 'Adj Close' in benchmark_data.columns.get_level_values(0):
                    prices = benchmark_data['Adj Close']
                elif 'Close' in benchmark_data.columns.get_level_values(0):
                    prices = benchmark_data['Close']
                else:
                    # Use the first available price column
                    price_cols = [col for col in benchmark_data.columns.get_level_values(0) if col in ['Open', 'High', 'Low', 'Close']]
                    if price_cols:
                        prices = benchmark_data[price_cols[0]]
                    else:
                        raise ValueError("No price columns found in benchmark data")
            else:
                # Single ticker case
                if 'Adj Close' in benchmark_data.columns:
                    prices = benchmark_data['Adj Close']
                elif 'Close' in benchmark_data.columns:
                    prices = benchmark_data['Close']
                else:
                    # Use the first available price column
                    price_cols = [col for col in benchmark_data.columns if col in ['Open', 'High', 'Low', 'Close']]
                    if price_cols:
                        prices = benchmark_data[price_cols[0]]
                    else:
                        raise ValueError("No price columns found in benchmark data")
            
            logger.info(f"Successfully downloaded {len(prices.columns)} benchmarks")
            return prices
            
        except Exception as e:
            logger.error(f"Failed to download benchmark data: {e}")
            return pd.DataFrame()
    
    def calculate_benchmark_returns(self, benchmark_prices: pd.DataFrame) -> pd.DataFrame:
        """Calculate daily returns for all benchmarks."""
        if benchmark_prices.empty:
            return pd.DataFrame()
        
        # Calculate daily returns
        returns = benchmark_prices.pct_change().dropna()
        return returns
    
    def calculate_equal_weighted_portfolio(self, universe_prices: pd.DataFrame) -> pd.Series:
        """Calculate equal-weighted portfolio returns from universe stocks."""
        if universe_prices.empty:
            return pd.Series(dtype=float)
        
        # Calculate daily returns for all stocks
        returns = universe_prices.pct_change().dropna()
        
        # Equal-weighted portfolio (1/N allocation)
        n_stocks = len(returns.columns)
        equal_weight = 1.0 / n_stocks
        
        # Calculate portfolio returns
        portfolio_returns = returns.sum(axis=1) * equal_weight
        
        return portfolio_returns
    
    def calculate_benchmark_metrics(self, returns: pd.Series, risk_free_rate: float = 0.02) -> Dict:
        """Calculate performance metrics for a benchmark."""
        if returns.empty:
            return {}
        
        # Basic metrics - using same calculation as main system
        total_return = (1 + returns).prod() - 1
        
        # Calculate annualized return based on actual trading period
        if len(returns) > 0:
            start_date = returns.index[0]
            end_date = returns.index[-1]
            years = (end_date - start_date).days / 365.25
            
            if years > 0:
                annualized_return = (1 + total_return) ** (1 / years) - 1
            else:
                annualized_return = 0.0
        else:
            annualized_return = 0.0
        
        # Calculate Sharpe ratio using same method as main system
        volatility = returns.std() * np.sqrt(252)
        sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
        
        # Drawdown calculation
        cumulative_returns = (1 + returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Additional metrics
        positive_days = (returns > 0).sum()
        negative_days = (returns < 0).sum()
        win_rate = positive_days / len(returns) if len(returns) > 0 else 0
        
        return {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'positive_days': positive_days,
            'negative_days': negative_days,
            'total_days': len(returns)
        }
    
    def compare_strategy_to_benchmarks(
        self, 
        strategy_returns: pd.Series, 
        benchmark_prices: pd.DataFrame,
        universe_prices: pd.DataFrame,
        risk_free_rate: float = 0.02
    ) -> Dict:
        """Compare strategy performance against multiple benchmarks."""
        
        # Calculate strategy metrics
        strategy_metrics = self.calculate_benchmark_metrics(strategy_returns, risk_free_rate)
        
        # Calculate benchmark returns and metrics
        benchmark_returns = self.calculate_benchmark_returns(benchmark_prices)
        benchmark_metrics = {}
        
        for ticker in benchmark_returns.columns:
            if ticker in self.benchmarks:
                benchmark_metrics[ticker] = self.calculate_benchmark_metrics(
                    benchmark_returns[ticker], risk_free_rate
                )
        
        # Calculate equal-weighted portfolio metrics
        equal_weighted_returns = self.calculate_equal_weighted_portfolio(universe_prices)
        equal_weighted_metrics = self.calculate_benchmark_metrics(equal_weighted_returns, risk_free_rate)
        
        # Create comparison summary
        comparison = {
            'strategy': strategy_metrics,
            'benchmarks': benchmark_metrics,
            'equal_weighted': equal_weighted_metrics,
            'comparison_period': {
                'start_date': strategy_returns.index[0] if not strategy_returns.empty else None,
                'end_date': strategy_returns.index[-1] if not strategy_returns.empty else None,
                'total_days': len(strategy_returns)
            }
        }
        
        return comparison
    
    def generate_comparison_report(self, comparison: Dict) -> str:
        """Generate a formatted comparison report."""
        if not comparison or 'strategy' not in comparison:
            return "No comparison data available"
        
        strategy = comparison['strategy']
        benchmarks = comparison.get('benchmarks', {})
        equal_weighted = comparison.get('equal_weighted', {})
        
        report = []
        report.append("=" * 80)
        report.append("PAIRS TRADING STRATEGY vs MARKET BENCHMARKS")
        report.append("=" * 80)
        
        # Strategy performance
        report.append("\n📊 STRATEGY PERFORMANCE")
        report.append("-" * 40)
        report.append(f"Total Return:        {strategy.get('total_return', 0):.4f} ({strategy.get('total_return', 0)*100:.2f}%)")
        report.append(f"Annualized Return:   {strategy.get('annualized_return', 0):.4f} ({strategy.get('annualized_return', 0)*100:.2f}%)")
        report.append(f"Volatility:          {strategy.get('volatility', 0):.4f} ({strategy.get('volatility', 0)*100:.2f}%)")
        report.append(f"Sharpe Ratio:        {strategy.get('sharpe_ratio', 0):.3f}")
        report.append(f"Max Drawdown:        {strategy.get('max_drawdown', 0):.4f} ({strategy.get('max_drawdown', 0)*100:.2f}%)")
        report.append(f"Win Rate:            {strategy.get('win_rate', 0):.3f} ({strategy.get('win_rate', 0)*100:.1f}%)")
        
        # Benchmark comparison
        if benchmarks:
            report.append("\n📈 BENCHMARK COMPARISON")
            report.append("-" * 40)
            report.append(f"{'Benchmark':<15} {'Return':<10} {'Sharpe':<8} {'Drawdown':<10} {'Volatility':<12}")
            report.append("-" * 40)
            
            # Sort benchmarks by Sharpe ratio
            sorted_benchmarks = sorted(
                benchmarks.items(), 
                key=lambda x: x[1].get('sharpe_ratio', -999), 
                reverse=True
            )
            
            for ticker, metrics in sorted_benchmarks:
                name = self.benchmarks.get(ticker, ticker)
                report.append(
                    f"{name:<15} "
                    f"{metrics.get('annualized_return', 0)*100:>8.2f}% "
                    f"{metrics.get('sharpe_ratio', 0):>6.2f} "
                    f"{metrics.get('max_drawdown', 0)*100:>8.2f}% "
                    f"{metrics.get('volatility', 0)*100:>10.2f}%"
                )
        
        # Equal-weighted comparison
        if equal_weighted:
            report.append("\n⚖️ EQUAL-WEIGHTED UNIVERSE COMPARISON")
            report.append("-" * 40)
            report.append(f"Equal-Weighted Return: {equal_weighted.get('annualized_return', 0):.4f} ({equal_weighted.get('annualized_return', 0)*100:.2f}%)")
            report.append(f"Equal-Weighted Sharpe:  {equal_weighted.get('sharpe_ratio', 0):.3f}")
            report.append(f"Equal-Weighted Drawdown: {equal_weighted.get('max_drawdown', 0):.4f} ({equal_weighted.get('max_drawdown', 0)*100:.2f}%)")
            
            # Strategy vs Equal-weighted
            strategy_sharpe = strategy.get('sharpe_ratio', 0)
            equal_sharpe = equal_weighted.get('sharpe_ratio', 0)
            if equal_sharpe != 0:
                sharpe_improvement = (strategy_sharpe - equal_sharpe) / abs(equal_sharpe) * 100
                report.append(f"Sharpe Improvement:     {sharpe_improvement:+.1f}%")
        
        # Risk-adjusted performance summary
        report.append("\n🎯 RISK-ADJUSTED PERFORMANCE SUMMARY")
        report.append("-" * 40)
        
        if benchmarks:
            # Find best benchmark Sharpe
            best_benchmark_sharpe = max(
                [metrics.get('sharpe_ratio', -999) for metrics in benchmarks.values()]
            )
            strategy_sharpe = strategy.get('sharpe_ratio', 0)
            
            if best_benchmark_sharpe > 0:
                report.append(f"Strategy Sharpe Ratio: {strategy_sharpe:.3f}")
                report.append(f"Best Benchmark Sharpe: {best_benchmark_sharpe:.3f}")
                
                if strategy_sharpe > best_benchmark_sharpe:
                    improvement = (strategy_sharpe - best_benchmark_sharpe) / best_benchmark_sharpe * 100
                    report.append(f"✅ Strategy outperforms best benchmark by {improvement:+.1f}%")
                else:
                    underperformance = (best_benchmark_sharpe - strategy_sharpe) / best_benchmark_sharpe * 100
                    report.append(f"❌ Strategy underperforms best benchmark by {underperformance:+.1f}%")
        
        # Period information
        if 'comparison_period' in comparison:
            period = comparison['comparison_period']
            report.append(f"\n📅 COMPARISON PERIOD")
            report.append("-" * 40)
            report.append(f"Start Date: {period.get('start_date', 'N/A')}")
            report.append(f"End Date:   {period.get('end_date', 'N/A')}")
            report.append(f"Total Days: {period.get('total_days', 'N/A')}")
        
        report.append("\n" + "=" * 80)
        
        return "\n".join(report)
    
    def calculate_rolling_comparison(
        self, 
        strategy_returns: pd.Series, 
        benchmark_returns: pd.Series, 
        window: int = 252
    ) -> pd.DataFrame:
        """Calculate rolling Sharpe ratio comparison between strategy and benchmark."""
        if strategy_returns.empty or benchmark_returns.empty:
            return pd.DataFrame()
        
        # Align dates
        common_dates = strategy_returns.index.intersection(benchmark_returns.index)
        strategy_aligned = strategy_returns.loc[common_dates]
        benchmark_aligned = benchmark_returns.loc[common_dates]
        
        # Calculate rolling Sharpe ratios
        strategy_rolling_sharpe = strategy_aligned.rolling(window).mean() / strategy_aligned.rolling(window).std() * np.sqrt(252)
        benchmark_rolling_sharpe = benchmark_aligned.rolling(window).mean() / benchmark_aligned.rolling(window).std() * np.sqrt(252)
        
        # Create comparison DataFrame
        comparison_df = pd.DataFrame({
            'strategy_sharpe': strategy_rolling_sharpe,
            'benchmark_sharpe': benchmark_rolling_sharpe,
            'sharpe_difference': strategy_rolling_sharpe - benchmark_rolling_sharpe
        })
        
        return comparison_df


def run_benchmark_analysis(
    strategy_returns: pd.Series,
    universe_prices: pd.DataFrame,
    start_date: str,
    end_date: str,
    risk_free_rate: float = 0.02
) -> Dict:
    """
    Run comprehensive benchmark analysis for the pairs trading strategy.
    
    Args:
        strategy_returns: Daily returns of the pairs trading strategy
        universe_prices: Price data for the trading universe
        start_date: Start date for analysis
        end_date: End date for analysis
        risk_free_rate: Risk-free rate for Sharpe ratio calculation
    
    Returns:
        Dictionary containing comparison results and formatted report
    """
    analyzer = BenchmarkAnalyzer()
    
    # Download benchmark data
    benchmark_prices = analyzer.download_benchmark_data(start_date, end_date)
    
    if benchmark_prices.empty:
        logger.warning("Failed to download benchmark data")
        return {}
    
    # Run comparison
    comparison = analyzer.compare_strategy_to_benchmarks(
        strategy_returns, benchmark_prices, universe_prices, risk_free_rate
    )
    
    # Generate report
    report = analyzer.generate_comparison_report(comparison)
    
    return {
        'comparison': comparison,
        'report': report,
        'analyzer': analyzer
    } 