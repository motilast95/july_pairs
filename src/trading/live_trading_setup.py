"""
Live Trading Setup - Phase 1
Initial 2-year training period for pair selection and hedge ratio calculation
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple


from src.data.pair_selection import select_pairs_fast
from src.models.model_fitting import fit_spread
from src.data.universe_manager import UniverseManager
from src.analysis.performance import time_function

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@time_function("live_trading_setup")
def setup_live_trading(
    start_date: str = "2023-07-01",
    end_date: str = "2025-07-01",
    universe: str = "mega_cap",
    adf_alpha: float = 0.05,
    distance_threshold: float = 0.1
) -> Dict:
    """
    Run the initial 2-year training period for live trading setup.
    
    Args:
        start_date: Start date for training period (2 years ago)
        end_date: End date for training period (today)
        universe: Universe to use ('mega_cap', 'mid_cap', 'custom')
        adf_alpha: Significance level for ADF tests
        distance_threshold: Distance threshold for pair pre-screening
        
    Returns:
        Dictionary containing selected pairs, hedge ratios, and training results
    """
    
    logger.info("🚀 Starting Live Trading Setup - Phase 1")
    logger.info(f"📅 Training Period: {start_date} to {end_date}")
    logger.info(f"🌍 Universe: {universe}")
    
    # Step 1: Get universe and sector information
    universe_manager = UniverseManager()
    sector_tickers = universe_manager.get_universe_sectors(universe)
    all_tickers = universe_manager.get_universe_tickers(universe)
    
    logger.info(f"📊 Universe: {len(all_tickers)} stocks across {len(sector_tickers)} sectors")
    
    # Step 2: Load existing price data
    logger.info("📥 Loading existing price data...")
    prices = load_existing_price_data(start_date, end_date)
    
    if prices is None or prices.empty:
        logger.error("❌ Failed to download price data")
        return {}
    
    logger.info(f"✅ Downloaded {len(prices)} days of price data for {len(prices.columns)} stocks")
    
    # Step 3: Run pair selection
    logger.info("🔍 Running pair selection...")
    training_window = slice(prices.index[0], prices.index[-1])
    
    selected_pairs = select_pairs_fast(
        prices=prices,
        sector_tickers=sector_tickers,
        window=training_window,
        adf_alpha=adf_alpha,
        distance_threshold=distance_threshold
    )
    
    logger.info(f"✅ Selected {len(selected_pairs)} pairs for trading")
    
    # Step 4: Calculate hedge ratios and model parameters
    logger.info("📈 Calculating hedge ratios and model parameters...")
    pair_models = {}
    valid_pairs = []
    
    for pair in selected_pairs:
        model_params = fit_spread(pair, prices, training_window)
        if model_params:
            pair_models[pair] = model_params
            valid_pairs.append(pair)
            logger.info(f"✅ {pair[0]}-{pair[1]}: β={model_params['beta']:.4f}, R²={model_params['rsquared']:.3f}")
        else:
            logger.warning(f"⚠️ Failed to fit model for {pair[0]}-{pair[1]}")
    
    logger.info(f"✅ Successfully fitted models for {len(valid_pairs)} pairs")
    
    # Step 5: Create training summary
    training_summary = {
        'training_period': {
            'start_date': start_date,
            'end_date': end_date,
            'days': len(prices)
        },
        'universe': {
            'name': universe,
            'total_stocks': len(all_tickers),
            'sectors': len(sector_tickers)
        },
        'pair_selection': {
            'total_pairs_selected': len(selected_pairs),
            'valid_pairs': len(valid_pairs),
            'adf_alpha': adf_alpha,
            'distance_threshold': distance_threshold
        },
        'pair_models': pair_models,
        'valid_pairs': valid_pairs,
        'sector_tickers': sector_tickers
    }
    
    # Step 6: Save results
    save_training_results(training_summary)
    
    logger.info("🎉 Live Trading Setup - Phase 1 Complete!")
    logger.info(f"📊 Ready to trade {len(valid_pairs)} pairs for the next 6 months")
    
    return training_summary


def load_existing_price_data(start_date: str, end_date: str) -> pd.DataFrame:
    """Load existing price data from data/prices.csv."""
    try:
        logger.info("📥 Loading existing price data from data/prices.csv...")
        
        # Load the CSV file
        prices = pd.read_csv('data/prices.csv', index_col=0, parse_dates=True)
        
        # Filter to the requested date range
        prices = prices.loc[start_date:end_date]
        
        logger.info(f"✅ Loaded {len(prices)} days of data for {len(prices.columns)} stocks")
        logger.info(f"📅 Date range: {prices.index[0]} to {prices.index[-1]}")
        
        return prices
        
    except Exception as e:
        logger.error(f"❌ Error loading price data: {e}")
        return pd.DataFrame()


def save_training_results(training_summary: Dict):
    """Save training results to files."""
    try:
        import json
        from datetime import datetime
        
        # Create results directory if it doesn't exist
        import os
        os.makedirs('results/live_trading', exist_ok=True)
        
        # Save training summary
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save pair models to JSON
        pair_models_simple = {}
        for pair, model in training_summary['pair_models'].items():
            pair_models_simple[f"{pair[0]}-{pair[1]}"] = {
                'beta': float(model['beta']),
                'spread_mean': float(model['spread_mean']),
                'spread_std': float(model['spread_std']),
                'rsquared': float(model['rsquared'])
            }
        
        training_summary['pair_models'] = pair_models_simple
        
        with open(f'results/live_trading/training_summary_{timestamp}.json', 'w') as f:
            json.dump(training_summary, f, indent=2, default=str)
        
        # Save valid pairs list
        valid_pairs = training_summary['valid_pairs']
        with open(f'results/live_trading/valid_pairs_{timestamp}.txt', 'w') as f:
            for pair in valid_pairs:
                f.write(f"{pair[0]},{pair[1]}\n")
        
        logger.info(f"💾 Saved training results to results/live_trading/")
        
    except Exception as e:
        logger.error(f"❌ Error saving training results: {e}")


def print_training_summary(training_summary: Dict):
    """Print a summary of the training results."""
    if not training_summary:
        logger.error("❌ No training summary to display")
        return
    
    print("\n" + "="*60)
    print("🎯 LIVE TRADING SETUP - TRAINING SUMMARY")
    print("="*60)
    
    # Training period
    period = training_summary['training_period']
    print(f"📅 Training Period: {period['start_date']} to {period['end_date']} ({period['days']} days)")
    
    # Universe
    universe = training_summary['universe']
    print(f"🌍 Universe: {universe['name']} ({universe['total_stocks']} stocks, {universe['sectors']} sectors)")
    
    # Pair selection
    selection = training_summary['pair_selection']
    print(f"🔍 Pair Selection: {selection['valid_pairs']}/{selection['total_pairs_selected']} pairs selected")
    print(f"📊 Parameters: ADF α={selection['adf_alpha']}, Distance threshold={selection['distance_threshold']}")
    
    # Valid pairs
    valid_pairs = training_summary['valid_pairs']
    print(f"\n📈 VALID PAIRS ({len(valid_pairs)}):")
    print("-" * 40)
    
    for i, pair in enumerate(valid_pairs, 1):
        pair_key = f"{pair[0]}-{pair[1]}"
        model = training_summary['pair_models'][pair_key]
        print(f"{i:2d}. {pair[0]:<6} - {pair[1]:<6} | β={model['beta']:7.4f} | R²={model['rsquared']:6.3f}")
    
    print("\n" + "="*60)
    print("✅ READY FOR 6-MONTH TRADING CYCLE")
    print("="*60)


def main():
    """Main function to run the live trading setup."""
    print("🚀 LIVE TRADING SETUP - PHASE 1")
    print("="*50)
    
    # Run the setup
    training_summary = setup_live_trading(
        start_date="2023-07-01",
        end_date="2025-07-01",
        universe="mega_cap",
        adf_alpha=0.05,
        distance_threshold=0.1
    )
    
    if training_summary:
        print_training_summary(training_summary)
    else:
        print("❌ Setup failed")


if __name__ == "__main__":
    main() 