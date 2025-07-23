"""
Test script to verify the improvements to the pairs trading system.
"""

import sys
import os
import logging
import pandas as pd
import numpy as np

# Add the project root to the path
sys.path.insert(0, os.path.abspath('.'))

from config.trading_config import create_default_config
from src.data.data_loader import load_prices, load_sector_tickers
from src.trading.walk_forward import walk_forward
from src.analysis.portfolio_analysis import aggregate_portfolio_pnl, compute_portfolio_metrics

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_configuration():
    """Test the new configuration system."""
    logger.info("Testing configuration system...")
    
    try:
        # Create default config
        config = create_default_config()
        logger.info("✓ Default configuration created successfully")
        
        # Test validation
        config_dict = config.to_dict()
        logger.info(f"✓ Configuration validation passed: {len(config_dict)} parameters")
        
        # Test parameter access
        assert config.train_size == 504
        assert config.signal_method == 'tiered'
        logger.info("✓ Configuration parameter access works")
        
        # Test invalid config
        try:
            invalid_config = config.update(train_size=-1)
            assert False, "Should have raised ValueError"
        except ValueError:
            logger.info("✓ Configuration validation catches invalid parameters")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Configuration test failed: {e}")
        return False

def test_transaction_costs():
    """Test transaction cost implementation."""
    logger.info("Testing transaction cost implementation...")
    
    try:
        from src.trading.backtest import run_backtest
        
        # Create test data
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        spread = pd.Series(np.random.randn(100).cumsum(), index=dates)
        signals = pd.Series([0, 1, 1, 0, -1, -1, 0] + [0] * 93, index=dates)
        
        # Test without transaction costs
        result_no_cost = run_backtest(spread, signals, position_size=100, transaction_cost_bps=0.0)
        
        # Test with transaction costs
        result_with_cost = run_backtest(spread, signals, position_size=100, transaction_cost_bps=5.0)
        
        # Verify transaction costs reduce net PnL
        total_pnl_no_cost = result_no_cost['daily_pnl'].sum()
        total_pnl_with_cost = result_with_cost['daily_pnl'].sum()
        
        assert total_pnl_with_cost <= total_pnl_no_cost
        logger.info("✓ Transaction costs correctly reduce net PnL")
        
        # Verify trade log includes transaction costs
        trades = result_with_cost['trades']
        if trades:
            assert 'transaction_cost' in trades[0]
            assert 'net_pnl' in trades[0]
            logger.info("✓ Trade log includes transaction cost information")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Transaction cost test failed: {e}")
        return False

def test_risk_management():
    """Test risk management functionality."""
    logger.info("Testing risk management...")
    
    try:
        from src.trading.risk_management import PortfolioRiskManager
        
        # Create test config
        config = {
            'max_position_per_pair': 1.0,
            'max_portfolio_exposure': 0.5,
            'volatility_lookback': 252,
            'volatility_target': 0.15
        }
        
        risk_manager = PortfolioRiskManager(config)
        logger.info("✓ Risk manager initialized")
        
        # Test volatility scaling
        scaled_pos = risk_manager.calculate_volatility_scaled_position(1.0, 0.2, 0.15)
        assert 0 <= scaled_pos <= 1.0
        logger.info("✓ Volatility scaling works")
        
        # Test position limits
        positions = pd.DataFrame({
            'pair1': [0.3, 0.4, 0.6],
            'pair2': [0.2, 0.3, 0.4]
        }, index=pd.date_range('2023-01-01', periods=3))
        
        constrained = risk_manager.apply_position_limits(positions)
        total_exposure = constrained.abs().sum(axis=1)
        assert (total_exposure <= 0.5).all()
        logger.info("✓ Position limits work")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Risk management test failed: {e}")
        return False

def test_error_handling():
    """Test error handling and logging."""
    logger.info("Testing error handling...")
    
    try:
        from src.models.model_fitting import fit_spread
        
        # Test with invalid pair
        prices = pd.DataFrame({
            'AAPL': [100, 101, 102],
            'MSFT': [200, 201, 202]
        }, index=pd.date_range('2023-01-01', periods=3))
        
        # Test invalid pair
        result = fit_spread(('INVALID', 'TICKER'), prices, slice(0, 2))
        assert result is None
        logger.info("✓ Invalid pair handling works")
        
        # Test insufficient data
        result = fit_spread(('AAPL', 'MSFT'), prices, slice(0, 1))
        assert result is None
        logger.info("✓ Insufficient data handling works")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Error handling test failed: {e}")
        return False

def test_full_pipeline():
    """Test the full pipeline with improvements."""
    logger.info("Testing full pipeline...")
    
    try:
        # Load data
        prices = load_prices('data/prices.csv')
        sector_tickers = load_sector_tickers('config/data_params.py')
        
        # Filter to recent data for faster testing
        prices = prices.loc['2023-01-01':'2023-06-30']
        
        # Create config
        config = create_default_config()
        config = config.update(
            start_date='2023-01-01',
            end_date='2023-06-30',
            train_size=60,  # Smaller for testing
            test_size=20,
            transaction_cost_bps=5.0
        )
        
        # Run walk-forward
        results = walk_forward(prices, sector_tickers, config.to_dict())
        
        if results:
            logger.info(f"✓ Full pipeline completed: {len(results)} results")
            
            # Test portfolio aggregation
            portfolio_pnl = aggregate_portfolio_pnl(results)
            metrics = compute_portfolio_metrics(portfolio_pnl, initial_capital=10000)
            
            logger.info(f"✓ Portfolio metrics calculated: Sharpe = {metrics.get('sharpe_ratio', 'N/A'):.2f}")
            
            return True
        else:
            logger.warning("No results from walk-forward analysis")
            return False
            
    except Exception as e:
        logger.error(f"✗ Full pipeline test failed: {e}")
        return False

def main():
    """Run all tests."""
    logger.info("Starting improvement tests...")
    
    tests = [
        test_configuration,
        test_transaction_costs,
        test_risk_management,
        test_error_handling,
        test_full_pipeline
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                logger.error(f"Test {test.__name__} failed")
        except Exception as e:
            logger.error(f"Test {test.__name__} crashed: {e}")
    
    logger.info(f"Tests completed: {passed}/{total} passed")
    
    if passed == total:
        logger.info("🎉 All improvements working correctly!")
    else:
        logger.error("❌ Some improvements need attention")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 