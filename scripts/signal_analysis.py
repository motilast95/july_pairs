#!/usr/bin/env python3
"""
Signal Analysis Script

Investigates signal generation, trade frequency, and why many pairs have zero return variance.
This will help us understand why the Sharpe ratio is only 0.4 instead of 1.0+.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple
import logging
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

from src.data.data_loader import load_prices, load_sector_tickers
from src.models.model_fitting import fit_spread
from src.models.signal_generation import generate_rolling_signals
from src.trading.backtest import run_backtest
from src.trading.walk_forward import walk_forward
from config.trading_config import create_default_config

def analyze_signal_generation(pair: Tuple[str, str], prices: pd.DataFrame, 
                            train_window: slice, test_window: slice,
                            entry_z: float = 2.0, exit_z: float = 0.5,
                            rolling_window: int = 60) -> Dict:
    """Analyze signal generation for a single pair."""
    try:
        # Fit spread model
        model_params = fit_spread(pair, prices, train_window)
        if not model_params:
            return None
            
        # Calculate spread for test period
        spread_test = prices.loc[test_window, pair[0]] - model_params['beta'] * prices.loc[test_window, pair[1]]
        
        # Generate signals
        signals = generate_rolling_signals(spread_test, entry_z, exit_z, rolling_window=rolling_window)
        
        # Count signal types
        long_signals = (signals == 1).sum()
        short_signals = (signals == -1).sum()
        no_position = (signals == 0).sum()
        total_days = len(signals)
        
        # Calculate signal frequency
        signal_frequency = (long_signals + short_signals) / total_days
        
        # Find signal transitions
        signal_changes = signals.diff().abs()
        num_trades = (signal_changes > 0).sum()
        
        # Calculate average holding period
        if num_trades > 0:
            avg_holding_period = total_days / num_trades
        else:
            avg_holding_period = np.nan
        
        # Analyze z-score distribution
        rolling_mean = spread_test.rolling(window=rolling_window).mean()
        rolling_std = spread_test.rolling(window=rolling_window).std()
        zscore = (spread_test - rolling_mean) / rolling_std
        zscore = zscore.dropna()
        
        # Count extreme z-scores
        extreme_high = (zscore > entry_z).sum()
        extreme_low = (zscore < -entry_z).sum()
        moderate_high = ((zscore > exit_z) & (zscore <= entry_z)).sum()
        moderate_low = ((zscore < -exit_z) & (zscore >= -entry_z)).sum()
        neutral = ((zscore >= -exit_z) & (zscore <= exit_z)).sum()
        
        return {
            'pair': pair,
            'total_days': total_days,
            'long_signals': long_signals,
            'short_signals': short_signals,
            'no_position': no_position,
            'signal_frequency': signal_frequency,
            'num_trades': num_trades,
            'avg_holding_period': avg_holding_period,
            'extreme_high_z': extreme_high,
            'extreme_low_z': extreme_low,
            'moderate_high_z': moderate_high,
            'moderate_low_z': moderate_low,
            'neutral_z': neutral,
            'zscore_mean': zscore.mean(),
            'zscore_std': zscore.std(),
            'zscore_min': zscore.min(),
            'zscore_max': zscore.max(),
            'spread_std': spread_test.std(),
            'beta': model_params['beta'],
            'signals': signals,
            'zscore': zscore,
            'spread': spread_test
        }
    except Exception as e:
        print(f"Error analyzing pair {pair}: {e}")
        return None

def run_signal_analysis():
    """Run comprehensive signal analysis."""
    print("🔍 Starting Signal Analysis...")
    
    # Load data
    prices = load_prices("data/prices.csv")
    sector_tickers = load_sector_tickers("config/data_params.py")
    
    # Filter to recent period for analysis
    prices = prices.loc["2020-01-01":"2024-06-30"]
    
    # Run walk-forward to get selected pairs and their results
    config = create_default_config()
    config = config.update(
        start_date="2020-01-01",
        end_date="2024-06-30",
        signal_method='rolling',
        entry_z=2.0,
        exit_z=0.5,
        enable_volatility_scaling=False,
        enable_position_limits=False,
        enable_pair_validation=False,
        max_position_per_pair=999999.0,
        max_portfolio_exposure=1.0
    )
    
    print("Running walk-forward to get pairs and results...")
    results = walk_forward(prices, sector_tickers, config.to_dict())
    
    # Extract unique pairs
    unique_pairs = set()
    for result in results:
        unique_pairs.add(result['pair'])
    
    print(f"Found {len(unique_pairs)} unique pairs to analyze")
    
    # Analyze signals for each pair
    signal_analyses = []
    for pair in unique_pairs:
        # Use first window for analysis
        train_window = slice(prices.index[0], prices.index[503])  # 504 days
        test_window = slice(prices.index[504], prices.index[629])  # 126 days
        
        analysis = analyze_signal_generation(
            pair, prices, train_window, test_window,
            entry_z=2.0, exit_z=0.5, rolling_window=60
        )
        if analysis:
            signal_analyses.append(analysis)
    
    # Convert to DataFrame
    df = pd.DataFrame(signal_analyses)
    
    # Add performance metrics from results
    performance_dict = {}
    for result in results:
        pair_key = str(result['pair'])
        if pair_key not in performance_dict:
            performance_dict[pair_key] = []
        performance_dict[pair_key].append(result['metrics']['total_return'])
    
    df['avg_return'] = df['pair'].apply(lambda p: np.mean(performance_dict.get(str(p), [0])))
    df['return_std'] = df['pair'].apply(lambda p: np.std(performance_dict.get(str(p), [0])))
    df['sharpe_ratio'] = df['avg_return'] / (df['return_std'] + 1e-8)
    
    return df

def create_signal_visualizations(df):
    """Create visualizations of signal analysis."""
    plt.style.use('seaborn-v0_8')
    
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    
    # 1. Signal frequency distribution
    axes[0,0].hist(df['signal_frequency'], bins=15, alpha=0.7)
    axes[0,0].axvline(df['signal_frequency'].median(), color='red', linestyle='--')
    axes[0,0].set_title('Signal Frequency Distribution')
    axes[0,0].set_xlabel('Signal Frequency')
    axes[0,0].set_ylabel('Number of Pairs')
    
    # 2. Number of trades vs performance
    axes[0,1].scatter(df['num_trades'], df['avg_return'], alpha=0.6)
    axes[0,1].set_title('Number of Trades vs Performance')
    axes[0,1].set_xlabel('Number of Trades')
    axes[0,1].set_ylabel('Average Return')
    
    # 3. Signal frequency vs performance
    axes[0,2].scatter(df['signal_frequency'], df['avg_return'], alpha=0.6)
    axes[0,2].set_title('Signal Frequency vs Performance')
    axes[0,2].set_xlabel('Signal Frequency')
    axes[0,2].set_ylabel('Average Return')
    
    # 4. Z-score distribution analysis
    extreme_signals = df['extreme_high_z'] + df['extreme_low_z']
    axes[1,0].scatter(extreme_signals, df['avg_return'], alpha=0.6)
    axes[1,0].set_title('Extreme Z-scores vs Performance')
    axes[1,0].set_xlabel('Number of Extreme Z-scores')
    axes[1,0].set_ylabel('Average Return')
    
    # 5. Average holding period vs performance
    valid_holding = df[df['avg_holding_period'].notna()]
    axes[1,1].scatter(valid_holding['avg_holding_period'], valid_holding['avg_return'], alpha=0.6)
    axes[1,1].set_title('Average Holding Period vs Performance')
    axes[1,1].set_xlabel('Average Holding Period (days)')
    axes[1,1].set_ylabel('Average Return')
    
    # 6. Z-score range vs performance
    zscore_range = df['zscore_max'] - df['zscore_min']
    axes[1,2].scatter(zscore_range, df['avg_return'], alpha=0.6)
    axes[1,2].set_title('Z-score Range vs Performance')
    axes[1,2].set_xlabel('Z-score Range (max - min)')
    axes[1,2].set_ylabel('Average Return')
    
    plt.tight_layout()
    plt.savefig('results/signal_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

def create_detailed_pair_analysis(df, num_pairs=5):
    """Create detailed analysis for top and bottom performing pairs."""
    plt.style.use('seaborn-v0_8')
    
    # Get top and bottom performers
    top_pairs = df.nlargest(num_pairs, 'avg_return')
    bottom_pairs = df.nsmallest(num_pairs, 'avg_return')
    
    fig, axes = plt.subplots(2, num_pairs, figsize=(4*num_pairs, 8))
    
    # Analyze top performers
    for i, (_, row) in enumerate(top_pairs.iterrows()):
        pair = row['pair']
        signals = row['signals']
        zscore = row['zscore']
        
        # Plot signals over time
        axes[0, i].plot(signals.index, signals, 'b-', alpha=0.7, linewidth=1)
        axes[0, i].set_title(f'Top: {pair}\nReturn: {row["avg_return"]:.2f}')
        axes[0, i].set_ylabel('Signal')
        axes[0, i].grid(True, alpha=0.3)
        
        # Plot z-score distribution
        axes[1, i].hist(zscore, bins=20, alpha=0.7, color='green')
        axes[1, i].axvline(2.0, color='red', linestyle='--', label='Entry')
        axes[1, i].axvline(-2.0, color='red', linestyle='--')
        axes[1, i].axvline(0.5, color='orange', linestyle='--', label='Exit')
        axes[1, i].axvline(-0.5, color='orange', linestyle='--')
        axes[1, i].set_xlabel('Z-score')
        axes[1, i].legend()
    
    plt.tight_layout()
    plt.savefig('results/top_performers_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # Analyze bottom performers
    fig, axes = plt.subplots(2, num_pairs, figsize=(4*num_pairs, 8))
    
    for i, (_, row) in enumerate(bottom_pairs.iterrows()):
        pair = row['pair']
        signals = row['signals']
        zscore = row['zscore']
        
        # Plot signals over time
        axes[0, i].plot(signals.index, signals, 'r-', alpha=0.7, linewidth=1)
        axes[0, i].set_title(f'Bottom: {pair}\nReturn: {row["avg_return"]:.2f}')
        axes[0, i].set_ylabel('Signal')
        axes[0, i].grid(True, alpha=0.3)
        
        # Plot z-score distribution
        axes[1, i].hist(zscore, bins=20, alpha=0.7, color='red')
        axes[1, i].axvline(2.0, color='red', linestyle='--', label='Entry')
        axes[1, i].axvline(-2.0, color='red', linestyle='--')
        axes[1, i].axvline(0.5, color='orange', linestyle='--', label='Exit')
        axes[1, i].axvline(-0.5, color='orange', linestyle='--')
        axes[1, i].set_xlabel('Z-score')
        axes[1, i].legend()
    
    plt.tight_layout()
    plt.savefig('results/bottom_performers_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

def print_signal_summary(df):
    """Print comprehensive signal analysis summary."""
    print("\n" + "="*80)
    print("SIGNAL ANALYSIS SUMMARY")
    print("="*80)
    
    print(f"Total Pairs Analyzed: {len(df)}")
    print(f"Profitable Pairs: {(df['avg_return'] > 0).sum()} ({(df['avg_return'] > 0).mean()*100:.1f}%)")
    
    print(f"\nSIGNAL GENERATION STATISTICS:")
    print(f"Mean Signal Frequency: {df['signal_frequency'].mean():.3f} ({df['signal_frequency'].mean()*100:.1f}%)")
    print(f"Mean Number of Trades: {df['num_trades'].mean():.1f}")
    print(f"Mean Holding Period: {df['avg_holding_period'].mean():.1f} days")
    
    print(f"\nZ-SCORE ANALYSIS:")
    print(f"Mean Z-score: {df['zscore_mean'].mean():.3f}")
    print(f"Mean Z-score Std: {df['zscore_std'].mean():.3f}")
    print(f"Mean Extreme Z-scores: {(df['extreme_high_z'] + df['extreme_low_z']).mean():.1f}")
    
    print(f"\nPERFORMANCE CORRELATIONS:")
    correlations = df[['signal_frequency', 'num_trades', 'avg_holding_period', 'avg_return']].corr()
    print(f"Signal Frequency vs Return: {correlations.loc['signal_frequency', 'avg_return']:.3f}")
    print(f"Number of Trades vs Return: {correlations.loc['num_trades', 'avg_return']:.3f}")
    print(f"Holding Period vs Return: {correlations.loc['avg_holding_period', 'avg_return']:.3f}")
    
    print(f"\nTOP 5 SIGNAL FREQUENCY PAIRS:")
    top_freq = df.nlargest(5, 'signal_frequency')
    for _, row in top_freq.iterrows():
        print(f"  {row['pair']}: Freq={row['signal_frequency']:.3f}, Trades={row['num_trades']}, Return={row['avg_return']:.4f}")
    
    print(f"\nBOTTOM 5 SIGNAL FREQUENCY PAIRS:")
    bottom_freq = df.nsmallest(5, 'signal_frequency')
    for _, row in bottom_freq.iterrows():
        print(f"  {row['pair']}: Freq={row['signal_frequency']:.3f}, Trades={row['num_trades']}, Return={row['avg_return']:.4f}")
    
    # Identify pairs with zero variance
    zero_var_pairs = df[df['return_std'] == 0]
    if len(zero_var_pairs) > 0:
        print(f"\n⚠️  PAIRS WITH ZERO RETURN VARIANCE ({len(zero_var_pairs)} pairs):")
        for _, row in zero_var_pairs.iterrows():
            print(f"  {row['pair']}: Signal Freq={row['signal_frequency']:.3f}, Trades={row['num_trades']}, Return={row['avg_return']:.4f}")

if __name__ == "__main__":
    df = run_signal_analysis()
    create_signal_visualizations(df)
    create_detailed_pair_analysis(df)
    print_signal_summary(df)
    
    # Save results
    df.to_csv('results/signal_analysis.csv', index=False)
    print(f"\nResults saved to results/signal_analysis.csv") 