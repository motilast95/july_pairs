#!/usr/bin/env python3
"""
Pair Quality Analysis Script

Analyzes the mean-reversion characteristics of selected pairs to identify
why our Sharpe ratio is only 0.4 instead of 1.0+.
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
from src.trading.walk_forward import walk_forward
from config.trading_config import create_default_config

def calculate_half_life(spread: pd.Series) -> float:
    """Calculate mean reversion half-life."""
    try:
        spread_lag = spread.shift(1)
        spread_ret = spread - spread_lag
        spread_lag = spread_lag.dropna()
        spread_ret = spread_ret.dropna()
        
        if len(spread_lag) < 10:
            return np.nan
            
        beta = np.corrcoef(spread_lag, spread_ret)[0, 1] * spread_ret.std() / spread_lag.std()
        
        if beta >= 0:  # Not mean-reverting
            return np.nan
        else:
            half_life = np.log(2) / abs(beta)
            return half_life
    except:
        return np.nan

def analyze_pair_quality(pair: Tuple[str, str], prices: pd.DataFrame, 
                        window: slice) -> Dict:
    """Analyze a single pair's quality."""
    try:
        price1 = prices.loc[window, pair[0]]
        price2 = prices.loc[window, pair[1]]
        
        model_params = fit_spread(pair, prices, window)
        if not model_params:
            return None
            
        spread = price1 - model_params['beta'] * price2
        half_life = calculate_half_life(spread)
        
        # Calculate z-score stability
        rolling_mean = spread.rolling(window=60).mean()
        rolling_std = spread.rolling(window=60).std()
        zscore = (spread - rolling_mean) / rolling_std
        zscore_stability = np.sqrt(np.mean(zscore.dropna()**2))
        
        return {
            'pair': pair,
            'half_life': half_life,
            'zscore_stability': zscore_stability,
            'spread_std': spread.std(),
            'beta': model_params['beta'],
            'spread_data': spread
        }
    except Exception as e:
        return None

def run_analysis():
    """Run the pair quality analysis."""
    print("🔍 Starting Pair Quality Analysis...")
    
    # Load data
    prices = load_prices("data/prices.csv")
    sector_tickers = load_sector_tickers("config/data_params.py")
    
    # Filter to recent period for analysis
    prices = prices.loc["2020-01-01":"2024-06-30"]
    
    # Run walk-forward to get selected pairs
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
    
    print("Running walk-forward to identify selected pairs...")
    results = walk_forward(prices, sector_tickers, config.to_dict())
    
    # Extract unique pairs
    unique_pairs = set()
    for result in results:
        unique_pairs.add(result['pair'])
    
    print(f"Found {len(unique_pairs)} unique pairs to analyze")
    
    # Analyze each pair
    pair_analyses = []
    for pair in unique_pairs:
        train_window = slice(prices.index[0], prices.index[503])  # 504 days
        analysis = analyze_pair_quality(pair, prices, train_window)
        if analysis:
            pair_analyses.append(analysis)
    
    # Convert to DataFrame
    df = pd.DataFrame(pair_analyses)
    
    # Add performance metrics
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

def create_visualizations(df):
    """Create visualizations of the analysis."""
    plt.style.use('seaborn-v0_8')
    
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    
    # 1. Half-life distribution
    valid_half_life = df['half_life'].dropna()
    axes[0,0].hist(valid_half_life, bins=15, alpha=0.7)
    axes[0,0].axvline(valid_half_life.median(), color='red', linestyle='--')
    axes[0,0].set_title('Half-life Distribution')
    axes[0,0].set_xlabel('Half-life (days)')
    
    # 2. Z-score stability vs performance
    axes[0,1].scatter(df['zscore_stability'], df['avg_return'], alpha=0.6)
    axes[0,1].set_title('Z-score Stability vs Performance')
    axes[0,1].set_xlabel('Z-score Stability')
    axes[0,1].set_ylabel('Average Return')
    
    # 3. Half-life vs performance
    valid_data = df[df['half_life'].notna()]
    axes[0,2].scatter(valid_data['half_life'], valid_data['avg_return'], alpha=0.6)
    axes[0,2].set_title('Half-life vs Performance')
    axes[0,2].set_xlabel('Half-life (days)')
    axes[0,2].set_ylabel('Average Return')
    
    # 4. Performance distribution
    axes[1,0].hist(df['avg_return'], bins=15, alpha=0.7)
    axes[1,0].axvline(df['avg_return'].median(), color='red', linestyle='--')
    axes[1,0].set_title('Performance Distribution')
    axes[1,0].set_xlabel('Average Return')
    
    # 5. Sharpe ratio distribution
    axes[1,1].hist(df['sharpe_ratio'], bins=15, alpha=0.7)
    axes[1,1].axvline(df['sharpe_ratio'].median(), color='red', linestyle='--')
    axes[1,1].set_title('Sharpe Ratio Distribution')
    axes[1,1].set_xlabel('Sharpe Ratio')
    
    # 6. Correlation matrix
    corr_data = df[['half_life', 'zscore_stability', 'avg_return', 'sharpe_ratio']].corr()
    sns.heatmap(corr_data, annot=True, cmap='coolwarm', center=0, ax=axes[1,2])
    axes[1,2].set_title('Correlation Matrix')
    
    plt.tight_layout()
    plt.savefig('results/pair_quality_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

def print_summary(df):
    """Print summary statistics."""
    print("\n" + "="*80)
    print("PAIR QUALITY ANALYSIS SUMMARY")
    print("="*80)
    
    print(f"Total Pairs Analyzed: {len(df)}")
    print(f"Profitable Pairs: {(df['avg_return'] > 0).sum()} ({(df['avg_return'] > 0).mean()*100:.1f}%)")
    print(f"Mean Return: {df['avg_return'].mean():.4f}")
    print(f"Mean Sharpe: {df['sharpe_ratio'].mean():.3f}")
    print(f"Mean Half-life: {df['half_life'].mean():.1f} days")
    print(f"Mean Z-score Stability: {df['zscore_stability'].mean():.3f}")
    
    print("\nTOP 5 PERFORMING PAIRS:")
    top_pairs = df.nlargest(5, 'avg_return')
    for _, row in top_pairs.iterrows():
        print(f"  {row['pair']}: Return={row['avg_return']:.4f}, Sharpe={row['sharpe_ratio']:.3f}, Half-life={row['half_life']:.1f}")
    
    print("\nBOTTOM 5 PERFORMING PAIRS:")
    bottom_pairs = df.nsmallest(5, 'avg_return')
    for _, row in bottom_pairs.iterrows():
        print(f"  {row['pair']}: Return={row['avg_return']:.4f}, Sharpe={row['sharpe_ratio']:.3f}, Half-life={row['half_life']:.1f}")

if __name__ == "__main__":
    df = run_analysis()
    create_visualizations(df)
    print_summary(df)
    
    # Save results
    df.to_csv('results/pair_quality_analysis.csv', index=False)
    print(f"\nResults saved to results/pair_quality_analysis.csv") 