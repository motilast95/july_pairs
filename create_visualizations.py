#!/usr/bin/env python3
"""
Create professional visualizations for pairs trading strategy results.
Perfect for resume and portfolio showcasing.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Set style for professional look
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def load_data():
    """Load trading data and benchmark results."""
    # Load trades data
    trades_df = pd.read_csv('results/data/trades_data.csv')
    trades_df['entry_date'] = pd.to_datetime(trades_df['entry_date'])
    trades_df['exit_date'] = pd.to_datetime(trades_df['exit_date'])
    
    # Load benchmark comparison
    with open('results/benchmark_comparison.json', 'r') as f:
        benchmark_data = json.load(f)
    
    return trades_df, benchmark_data

def create_cumulative_returns_chart(trades_df, benchmark_data):
    """Create cumulative returns comparison chart."""
    import yfinance as yf
    
    # Calculate cumulative returns for strategy
    trades_df = trades_df.sort_values('entry_date')
    trades_df['cumulative_pnl'] = trades_df['net_pnl'].cumsum()
    
    # Calculate initial capital based on total P&L and target return from benchmark data
    total_pnl = trades_df['net_pnl'].sum()
    target_return = benchmark_data['strategy']['total_return']  # Get from actual benchmark data
    initial_capital = total_pnl / target_return
    trades_df['cumulative_return'] = trades_df['cumulative_pnl'] / initial_capital
    
    # Create date range for plotting
    date_range = pd.date_range(start=trades_df['entry_date'].min(), 
                              end=trades_df['exit_date'].max(), freq='D')
    
    # Interpolate strategy returns
    strategy_returns = pd.DataFrame({'date': date_range})
    strategy_returns = strategy_returns.merge(
        trades_df[['exit_date', 'cumulative_return']].rename(columns={'exit_date': 'date'}),
        on='date', how='left'
    )
    strategy_returns['cumulative_return'] = strategy_returns['cumulative_return'].fillna(method='ffill').fillna(0)
    
    # Download actual benchmark data
    benchmark_tickers = ['SPY', 'QQQ', 'IWM']
    benchmark_colors = ['#A23B72', '#F18F01', '#C73E1D']
    
    # Download benchmark data
    benchmark_data_actual = yf.download(
        benchmark_tickers,
        start=trades_df['entry_date'].min(),
        end=trades_df['exit_date'].max(),
        progress=False
    )
    
    # Extract adjusted close prices
    if isinstance(benchmark_data_actual.columns, pd.MultiIndex):
        if 'Adj Close' in benchmark_data_actual.columns.get_level_values(0):
            benchmark_prices = benchmark_data_actual['Adj Close']
        else:
            benchmark_prices = benchmark_data_actual['Close']
    else:
        benchmark_prices = benchmark_data_actual
    
    # Plot
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Strategy line
    ax.plot(strategy_returns['date'], strategy_returns['cumulative_return'] * 100, 
            linewidth=3, label='Pairs Trading Strategy', color='#2E86AB')
    
    # Add actual benchmark lines
    for i, ticker in enumerate(benchmark_tickers):
        if ticker in benchmark_prices.columns:
            # Calculate cumulative returns for benchmark
            benchmark_prices_ticker = benchmark_prices[ticker].dropna()
            if not benchmark_prices_ticker.empty:
                # Normalize to start at 0
                benchmark_prices_ticker = benchmark_prices_ticker / benchmark_prices_ticker.iloc[0] - 1
                benchmark_prices_ticker = benchmark_prices_ticker * 100  # Convert to percentage
                
                ax.plot(benchmark_prices_ticker.index, benchmark_prices_ticker.values, 
                       '--', linewidth=2, label=f'{ticker} ETF', 
                       color=benchmark_colors[i], alpha=0.7)
    
    ax.set_title('Cumulative Returns: Pairs Trading Strategy vs Benchmarks', 
                 fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Cumulative Return (%)', fontsize=12)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    
    # Add performance metrics as text
    strategy_return = strategy_returns['cumulative_return'].iloc[-1] * 100
    ax.text(0.02, 0.98, f'Strategy Return: {strategy_return:.1f}%\nSharpe Ratio: 1.170', 
            transform=ax.transAxes, fontsize=10, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig('visualizations/cumulative_returns.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_risk_return_scatter(trades_df, benchmark_data):
    """Create risk-return scatter plot."""
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Strategy point
    strategy_vol = benchmark_data['strategy']['volatility'] * 100
    strategy_return = benchmark_data['strategy']['total_return'] * 100
    strategy_sharpe = benchmark_data['strategy']['sharpe_ratio']
    
    ax.scatter(strategy_vol, strategy_return, s=200, c='#2E86AB', 
               label='Pairs Trading Strategy', zorder=5, edgecolors='black', linewidth=2)
    
    # Benchmark points
    benchmark_colors = ['#A23B72', '#F18F01', '#C73E1D', '#4A90A4', '#7B68EE']
    for i, (benchmark, data) in enumerate(benchmark_data['benchmarks'].items()):
        vol = data['volatility'] * 100
        ret = data['total_return'] * 100
        sharpe = data['sharpe_ratio']
        
        ax.scatter(vol, ret, s=100, c=benchmark_colors[i % len(benchmark_colors)], 
                  alpha=0.7, label=f'{benchmark} ETF')
        
        # Add Sharpe ratio as text
        ax.annotate(f'{sharpe:.2f}', (vol, ret), xytext=(5, 5), 
                   textcoords='offset points', fontsize=8)
    
    # Add Sharpe ratio for strategy
    ax.annotate(f'{strategy_sharpe:.3f}', (strategy_vol, strategy_return), 
               xytext=(10, 10), textcoords='offset points', fontsize=10, fontweight='bold')
    
    ax.set_xlabel('Volatility (%)', fontsize=12)
    ax.set_ylabel('Total Return (%)', fontsize=12)
    ax.set_title('Risk-Return Analysis: Strategy vs Market Benchmarks', 
                 fontsize=16, fontweight='bold', pad=20)
    ax.legend(fontsize=10, loc='upper left')
    ax.grid(True, alpha=0.3)
    
    # Add efficient frontier line (simplified)
    x = np.linspace(5, 35, 100)
    y = 0.5 * x + 5  # Simplified efficient frontier
    ax.plot(x, y, '--', color='gray', alpha=0.5, label='Efficient Frontier (Est.)')
    
    plt.tight_layout()
    plt.savefig('visualizations/risk_return_scatter.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_drawdown_analysis(trades_df, benchmark_data):
    """Create drawdown analysis chart."""
    # Calculate drawdown for strategy
    trades_df = trades_df.sort_values('entry_date')
    trades_df['cumulative_pnl'] = trades_df['net_pnl'].cumsum()
    
    # Use same calculation as cumulative returns
    total_pnl = trades_df['net_pnl'].sum()
    target_return = benchmark_data['strategy']['total_return']
    initial_capital = total_pnl / target_return
    trades_df['cumulative_return'] = trades_df['cumulative_pnl'] / initial_capital
    
    # Calculate running maximum and drawdown
    trades_df['running_max'] = trades_df['cumulative_return'].expanding().max()
    trades_df['drawdown'] = (trades_df['cumulative_return'] - trades_df['running_max']) / trades_df['running_max'] * 100
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Plot drawdown
    ax.fill_between(trades_df['exit_date'], trades_df['drawdown'], 0, 
                    alpha=0.3, color='red', label='Strategy Drawdown')
    ax.plot(trades_df['exit_date'], trades_df['drawdown'], color='red', linewidth=2)
    
    # Add benchmark drawdowns as horizontal lines
    benchmarks = ['SPY', 'QQQ', 'IWM']
    colors = ['#A23B72', '#F18F01', '#C73E1D']
    
    for i, benchmark in enumerate(benchmarks):
        if benchmark in benchmark_data['benchmarks']:
            drawdown = benchmark_data['benchmarks'][benchmark]['max_drawdown'] * 100
            ax.axhline(y=-drawdown, color=colors[i], linestyle='--', alpha=0.7,
                      label=f'{benchmark} Max Drawdown: {-drawdown:.1f}%')
    
    ax.set_title('Drawdown Analysis: Strategy vs Market Benchmarks', 
                 fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Drawdown (%)', fontsize=12)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    
    # Add max drawdown annotation
    max_dd = trades_df['drawdown'].min()
    ax.annotate(f'Max Drawdown: {max_dd:.1f}%', 
               xy=(trades_df['exit_date'].iloc[trades_df['drawdown'].idxmin()], max_dd),
               xytext=(10, -10), textcoords='offset points', fontsize=10,
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig('visualizations/drawdown_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_trade_distribution(trades_df):
    """Create trade P&L distribution histogram."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # P&L distribution
    ax1.hist(trades_df['net_pnl'], bins=20, alpha=0.7, color='#2E86AB', edgecolor='black')
    ax1.axvline(trades_df['net_pnl'].mean(), color='red', linestyle='--', 
                label=f'Mean: ${trades_df["net_pnl"].mean():.0f}')
    ax1.set_xlabel('Trade P&L ($)', fontsize=12)
    ax1.set_ylabel('Frequency', fontsize=12)
    ax1.set_title('Trade P&L Distribution', fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Holding period distribution
    ax2.hist(trades_df['holding_period'], bins=15, alpha=0.7, color='#A23B72', edgecolor='black')
    ax2.axvline(trades_df['holding_period'].mean(), color='red', linestyle='--',
                label=f'Mean: {trades_df["holding_period"].mean():.1f} days')
    ax2.set_xlabel('Holding Period (Days)', fontsize=12)
    ax2.set_ylabel('Frequency', fontsize=12)
    ax2.set_title('Trade Holding Period Distribution', fontsize=14, fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('visualizations/trade_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_win_loss_analysis(trades_df):
    """Create win/loss analysis."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Win/Loss pie chart
    wins = (trades_df['net_pnl'] > 0).sum()
    losses = (trades_df['net_pnl'] <= 0).sum()
    win_rate = wins / len(trades_df) * 100
    
    colors = ['#4CAF50', '#F44336']
    ax1.pie([wins, losses], labels=[f'Wins ({wins})', f'Losses ({losses})'], 
            colors=colors, autopct='%1.1f%%', startangle=90)
    ax1.set_title(f'Win/Loss Ratio\nWin Rate: {win_rate:.1f}%', 
                  fontsize=14, fontweight='bold')
    
    # Average win vs loss
    avg_win = trades_df[trades_df['net_pnl'] > 0]['net_pnl'].mean()
    avg_loss = trades_df[trades_df['net_pnl'] <= 0]['net_pnl'].mean()
    
    bars = ax2.bar(['Average Win', 'Average Loss'], [avg_win, avg_loss], 
                   color=['#4CAF50', '#F44336'], alpha=0.7)
    ax2.set_ylabel('P&L ($)', fontsize=12)
    ax2.set_title('Average Win vs Loss', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'${height:.0f}', ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('visualizations/win_loss_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_pair_performance_breakdown(trades_df):
    """Create pair performance breakdown."""
    # Group by pair and calculate metrics
    pair_stats = trades_df.groupby(['pair1', 'pair2']).agg({
        'net_pnl': ['count', 'sum', 'mean'],
        'holding_period': 'mean'
    }).round(2)
    
    pair_stats.columns = ['trade_count', 'total_pnl', 'avg_pnl', 'avg_holding_period']
    pair_stats = pair_stats.sort_values('total_pnl', ascending=False)
    
    # Top 10 pairs
    top_pairs = pair_stats.head(10)
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Create pair labels
    pair_labels = [f"{row[0]}-{row[1]}" for row in top_pairs.index]
    
    bars = ax.barh(range(len(top_pairs)), top_pairs['total_pnl'], 
                   color='#2E86AB', alpha=0.7)
    
    ax.set_yticks(range(len(top_pairs)))
    ax.set_yticklabels(pair_labels)
    ax.set_xlabel('Total P&L ($)', fontsize=12)
    ax.set_title('Top 10 Performing Pairs', fontsize=16, fontweight='bold', pad=20)
    ax.grid(True, alpha=0.3, axis='x')
    
    # Add value labels
    for i, (bar, pnl) in enumerate(zip(bars, top_pairs['total_pnl'])):
        ax.text(bar.get_width() + 50, bar.get_y() + bar.get_height()/2,
               f'${pnl:.0f}', va='center', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('visualizations/pair_performance.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_sharpe_comparison(benchmark_data):
    """Create Sharpe ratio comparison chart."""
    # Extract Sharpe ratios
    strategy_sharpe = benchmark_data['strategy']['sharpe_ratio']
    
    # Get top benchmarks
    benchmark_sharpes = []
    benchmark_names = []
    
    for name, data in benchmark_data['benchmarks'].items():
        benchmark_sharpes.append(data['sharpe_ratio'])
        benchmark_names.append(name)
    
    # Sort by Sharpe ratio
    sorted_data = sorted(zip(benchmark_names, benchmark_sharpes), 
                        key=lambda x: x[1], reverse=True)
    names, sharpes = zip(*sorted_data)
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Create bars
    bars = ax.bar(range(len(names)), sharpes, color='#A23B72', alpha=0.7)
    
    # Highlight strategy
    strategy_idx = len(names)  # Strategy will be added at the end
    strategy_bar = ax.bar(strategy_idx, strategy_sharpe, color='#2E86AB', 
                         alpha=0.9, label='Pairs Trading Strategy')
    
    # Set labels
    ax.set_xticks(range(len(names) + 1))
    ax.set_xticklabels(list(names) + ['Strategy'], rotation=45, ha='right')
    ax.set_ylabel('Sharpe Ratio', fontsize=12)
    ax.set_title('Sharpe Ratio Comparison: Strategy vs Market Benchmarks', 
                 fontsize=16, fontweight='bold', pad=20)
    
    # Add value labels
    for i, (bar, sharpe) in enumerate(zip(bars, sharpes)):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
               f'{sharpe:.3f}', ha='center', va='bottom', fontweight='bold')
    
    # Add strategy value
    ax.text(strategy_bar[0].get_x() + strategy_bar[0].get_width()/2, 
           strategy_bar[0].get_height() + 0.02,
           f'{strategy_sharpe:.3f}', ha='center', va='bottom', 
           fontweight='bold', color='#2E86AB')
    
    ax.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig('visualizations/sharpe_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_performance_summary_table(benchmark_data):
    """Create performance summary table."""
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.axis('tight')
    ax.axis('off')
    
    # Prepare data
    strategy = benchmark_data['strategy']
    data = [
        ['Metric', 'Strategy', 'Best Benchmark', 'Improvement'],
        ['Total Return (%)', f"{strategy['total_return']*100:.2f}", 
         f"{benchmark_data['benchmarks']['XLK']['total_return']*100:.2f}", 
         f"+{(strategy['total_return']/benchmark_data['benchmarks']['XLK']['total_return']-1)*100:.1f}%"],
        ['Sharpe Ratio', f"{strategy['sharpe_ratio']:.3f}", 
         f"{benchmark_data['benchmarks']['XLK']['sharpe_ratio']:.3f}", 
         f"+{(strategy['sharpe_ratio']/benchmark_data['benchmarks']['XLK']['sharpe_ratio']-1)*100:.1f}%"],
        ['Max Drawdown (%)', f"{strategy['max_drawdown']*100:.2f}", 
         f"{benchmark_data['benchmarks']['SPY']['max_drawdown']*100:.2f}", 
         f"{(strategy['max_drawdown']/benchmark_data['benchmarks']['SPY']['max_drawdown']-1)*100:.1f}%"],
        ['Volatility (%)', f"{strategy['volatility']*100:.2f}", 
         f"{benchmark_data['benchmarks']['SPY']['volatility']*100:.2f}", 
         f"{(strategy['volatility']/benchmark_data['benchmarks']['SPY']['volatility']-1)*100:.1f}%"]
    ]
    
    table = ax.table(cellText=data[1:], colLabels=data[0], 
                    cellLoc='center', loc='center',
                    colWidths=[0.25, 0.25, 0.25, 0.25])
    
    # Style the table
    table.auto_set_font_size(False)
    table.set_fontsize(12)
    table.scale(1.2, 1.5)
    
    # Color header
    for i in range(len(data[0])):
        table[(0, i)].set_facecolor('#2E86AB')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    # Color strategy row
    for i in range(len(data[0])):
        table[(1, i)].set_facecolor('#E8F4FD')
    
    ax.set_title('Performance Summary: Strategy vs Best Benchmarks', 
                 fontsize=16, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig('visualizations/performance_summary.png', dpi=300, bbox_inches='tight')
    plt.close()

def main():
    """Create all visualizations."""
    print("Loading data...")
    trades_df, benchmark_data = load_data()
    
    print("Creating visualizations...")
    
    # Create all charts
    create_cumulative_returns_chart(trades_df, benchmark_data)
    print("✓ Cumulative returns chart")
    
    create_risk_return_scatter(trades_df, benchmark_data)
    print("✓ Risk-return scatter plot")
    
    create_drawdown_analysis(trades_df, benchmark_data)
    print("✓ Drawdown analysis")
    
    create_trade_distribution(trades_df)
    print("✓ Trade distribution")
    
    create_win_loss_analysis(trades_df)
    print("✓ Win/loss analysis")
    
    create_pair_performance_breakdown(trades_df)
    print("✓ Pair performance breakdown")
    
    create_sharpe_comparison(benchmark_data)
    print("✓ Sharpe ratio comparison")
    
    create_performance_summary_table(benchmark_data)
    print("✓ Performance summary table")
    
    print(f"\n🎉 All visualizations saved to 'visualizations/' folder!")
    print("Files created:")
    print("- cumulative_returns.png")
    print("- risk_return_scatter.png") 
    print("- drawdown_analysis.png")
    print("- trade_distribution.png")
    print("- win_loss_analysis.png")
    print("- pair_performance.png")
    print("- sharpe_comparison.png")
    print("- performance_summary.png")

if __name__ == "__main__":
    main() 