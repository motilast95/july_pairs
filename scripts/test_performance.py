#!/usr/bin/env python3
"""
Test script to demonstrate performance monitoring functionality.
"""

import sys
import os
import logging
import pandas as pd
import numpy as np

# Add the project root to the path
sys.path.insert(0, os.path.abspath('..'))

from src.analysis.performance import (
    time_function, 
    time_block, 
    print_performance_summary, 
    export_performance_metrics,
    performance_monitor
)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@time_function("sample_function")
def sample_function(n: int) -> float:
    """Sample function to demonstrate timing."""
    result = 0.0
    for i in range(n):
        result += np.sqrt(i) * np.sin(i)
    return result

@time_function("data_processing")
def process_data(data_size: int) -> pd.DataFrame:
    """Sample data processing function."""
    # Create sample data
    dates = pd.date_range('2021-01-01', periods=data_size, freq='D')
    data = pd.DataFrame({
        'price1': np.random.randn(data_size).cumsum() + 100,
        'price2': np.random.randn(data_size).cumsum() + 100,
        'price3': np.random.randn(data_size).cumsum() + 100
    }, index=dates)
    
    # Simulate some processing
    data['spread'] = data['price1'] - data['price2']
    data['zscore'] = (data['spread'] - data['spread'].rolling(20).mean()) / data['spread'].rolling(20).std()
    
    return data

def test_performance_monitoring():
    """Test the performance monitoring system."""
    logger.info("🚀 Starting Performance Monitoring Test")
    
    # Test function timing
    logger.info("Testing function timing...")
    result1 = sample_function(1000)
    result2 = sample_function(10000)
    
    # Test data processing
    logger.info("Testing data processing...")
    data1 = process_data(1000)
    data2 = process_data(5000)
    
    # Test context manager
    logger.info("Testing context manager...")
    with time_block("manual_calculation"):
        # Simulate some manual calculations
        for i in range(1000):
            _ = np.random.randn(100).sum()
    
    # Test nested timing
    logger.info("Testing nested timing...")
    with time_block("outer_operation"):
        for i in range(5):
            with time_block(f"inner_operation_{i}"):
                sample_function(100)
    
    # Print performance summary
    logger.info("=" * 60)
    logger.info("PERFORMANCE SUMMARY")
    logger.info("=" * 60)
    print_performance_summary()
    
    # Export metrics
    export_performance_metrics("test_performance_metrics.csv")
    
    logger.info("✅ Performance monitoring test completed!")

def test_memory_tracking():
    """Test memory tracking functionality."""
    logger.info("🧠 Testing memory tracking...")
    
    # Create a large array to see memory usage
    with time_block("large_array_creation"):
        large_array = np.random.randn(1000000)  # ~8MB of data
        _ = large_array.sum()
    
    # Create multiple arrays
    with time_block("multiple_arrays"):
        arrays = []
        for i in range(10):
            arrays.append(np.random.randn(100000))  # ~800KB each
    
    print_performance_summary(sort_by='memory_peak_mb')
    
    logger.info("✅ Memory tracking test completed!")

if __name__ == "__main__":
    logger.info("Starting performance monitoring tests...")
    
    try:
        test_performance_monitoring()
        test_memory_tracking()
        
        logger.info("🎉 All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        sys.exit(1) 