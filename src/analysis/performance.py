"""
Performance monitoring and benchmarking for the pairs trading system.
Tracks execution times, memory usage, and provides detailed performance analysis.
"""

import time
import logging
import psutil
import os
import functools
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# Global flag to enable/disable performance monitoring
PERFORMANCE_MONITORING_ENABLED = False

def enable_performance_monitoring():
    """Enable performance monitoring globally."""
    global PERFORMANCE_MONITORING_ENABLED
    PERFORMANCE_MONITORING_ENABLED = True
    logger.info("Performance monitoring enabled")

def disable_performance_monitoring():
    """Disable performance monitoring globally."""
    global PERFORMANCE_MONITORING_ENABLED
    PERFORMANCE_MONITORING_ENABLED = False
    logger.info("Performance monitoring disabled")

def is_performance_monitoring_enabled() -> bool:
    """Check if performance monitoring is enabled."""
    return PERFORMANCE_MONITORING_ENABLED

@dataclass
class PerformanceMetrics:
    """Container for performance metrics"""
    function_name: str
    execution_time: float
    memory_used_mb: float
    memory_peak_mb: float
    timestamp: datetime = field(default_factory=datetime.now)
    additional_info: Dict[str, Any] = field(default_factory=dict)

class PerformanceMonitor:
    """Comprehensive performance monitoring system"""
    
    def __init__(self, enable_memory_tracking: bool = True):
        """
        Initialize performance monitor.
        
        Args:
            enable_memory_tracking: Whether to track memory usage (requires psutil)
        """
        self.timings: Dict[str, List[PerformanceMetrics]] = {}
        self.enable_memory_tracking = enable_memory_tracking
        self.logger = logging.getLogger(__name__)
        
        # Track if psutil is available
        try:
            import psutil
            self.psutil_available = True
        except ImportError:
            self.psutil_available = False
            if enable_memory_tracking:
                self.logger.warning("psutil not available. Memory tracking disabled.")
                self.enable_memory_tracking = False
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        if not self.enable_memory_tracking or not self.psutil_available:
            return 0.0
        
        try:
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            return memory_info.rss / 1024 / 1024  # Convert to MB
        except Exception as e:
            self.logger.warning(f"Failed to get memory usage: {e}")
            return 0.0
    
    def _get_peak_memory(self) -> float:
        """Get peak memory usage in MB"""
        if not self.enable_memory_tracking or not self.psutil_available:
            return 0.0
        
        try:
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            return memory_info.peak_wset / 1024 / 1024  # Convert to MB
        except Exception as e:
            self.logger.warning(f"Failed to get peak memory usage: {e}")
            return 0.0
    
    def time_function(self, func_name: str, log_level: str = "DEBUG"):
        """
        Decorator to time function execution and track memory usage.
        
        Args:
            func_name: Name to use for tracking this function
            log_level: Logging level for performance messages
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                # Skip timing if performance monitoring is disabled
                if not PERFORMANCE_MONITORING_ENABLED:
                    return func(*args, **kwargs)
                
                # Initialize tracking
                if func_name not in self.timings:
                    self.timings[func_name] = []
                
                # Get initial memory state
                memory_before = self._get_memory_usage()
                start_time = time.time()
                
                try:
                    # Execute function
                    result = func(*args, **kwargs)
                    
                    # Calculate metrics
                    execution_time = time.time() - start_time
                    memory_after = self._get_memory_usage()
                    memory_used = memory_after - memory_before
                    memory_peak = self._get_peak_memory()
                    
                    # Store metrics
                    metrics = PerformanceMetrics(
                        function_name=func_name,
                        execution_time=execution_time,
                        memory_used_mb=memory_used,
                        memory_peak_mb=memory_peak
                    )
                    self.timings[func_name].append(metrics)
                    
                    # Log performance (optional) - only log at DEBUG level by default
                    if log_level.upper() == "DEBUG":
                        self.logger.debug(f"{func_name}: {execution_time:.4f}s, Memory: {memory_used:.2f}MB")
                    # Don't log at INFO level to avoid cluttering output
                    
                    return result
                    
                except Exception as e:
                    # Still track timing even if function fails
                    execution_time = time.time() - start_time
                    self.logger.error(f"{func_name} failed after {execution_time:.4f}s: {e}")
                    raise
            
            return wrapper
        return decorator
    
    def time_block(self, block_name: str, log_level: str = "DEBUG"):
        """
        Context manager for timing code blocks.
        
        Args:
            block_name: Name to use for tracking this block
            log_level: Logging level for performance messages
        """
        class TimeBlock:
            def __init__(self, monitor, name, log_level):
                self.monitor = monitor
                self.name = name
                self.log_level = log_level
            
            def __enter__(self):
                # Skip timing if performance monitoring is disabled
                if not PERFORMANCE_MONITORING_ENABLED:
                    return self
                
                self.memory_before = self.monitor._get_memory_usage()
                self.start_time = time.time()
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                # Skip timing if performance monitoring is disabled
                if not PERFORMANCE_MONITORING_ENABLED:
                    return
                
                execution_time = time.time() - self.start_time
                memory_after = self.monitor._get_memory_usage()
                memory_used = memory_after - self.memory_before
                memory_peak = self.monitor._get_peak_memory()
                
                # Store metrics
                if self.name not in self.monitor.timings:
                    self.monitor.timings[self.name] = []
                
                metrics = PerformanceMetrics(
                    function_name=self.name,
                    execution_time=execution_time,
                    memory_used_mb=memory_used,
                    memory_peak_mb=memory_peak
                )
                self.monitor.timings[self.name].append(metrics)
                
                # Log performance - only log at DEBUG level by default
                if self.log_level.upper() == "DEBUG":
                    self.monitor.logger.debug(f"{self.name}: {execution_time:.4f}s, Memory: {memory_used:.2f}MB")
                # Don't log at INFO level to avoid cluttering output
        
        return TimeBlock(self, block_name, log_level)
    
    def get_summary(self) -> Dict[str, Dict[str, float]]:
        """
        Get summary statistics for all tracked functions.
        
        Returns:
            Dictionary with function names as keys and summary stats as values
        """
        summary = {}
        
        for func_name, metrics_list in self.timings.items():
            if not metrics_list:
                continue
            
            execution_times = [m.execution_time for m in metrics_list]
            memory_used = [m.memory_used_mb for m in metrics_list]
            memory_peak = [m.memory_peak_mb for m in metrics_list]
            
            summary[func_name] = {
                'count': len(metrics_list),
                'total_time': sum(execution_times),
                'avg_time': np.mean(execution_times),
                'min_time': np.min(execution_times),
                'max_time': np.max(execution_times),
                'std_time': np.std(execution_times),
                'avg_memory_used': np.mean(memory_used),
                'max_memory_peak': np.max(memory_peak) if memory_peak else 0.0
            }
        
        return summary
    
    def print_summary(self, sort_by: str = 'total_time'):
        """
        Print formatted performance summary.
        
        Args:
            sort_by: Metric to sort by ('total_time', 'avg_time', 'count', etc.)
        """
        summary = self.get_summary()
        
        if not summary:
            self.logger.info("📊 No performance data collected")
            return
        
        # Calculate totals
        total_execution_time = sum(stats['total_time'] for stats in summary.values())
        total_calls = sum(stats['count'] for stats in summary.values())
        
        self.logger.info("📊 Performance Summary:")
        self.logger.info(f"  Total execution time: {total_execution_time:.4f}s")
        self.logger.info(f"  Total function calls: {total_calls}")
        self.logger.info("")
        
        # Sort and display
        sorted_items = sorted(summary.items(), key=lambda x: x[1][sort_by], reverse=True)
        
        for func_name, stats in sorted_items:
            percentage = (stats['total_time'] / total_execution_time) * 100
            self.logger.info(f"  {func_name}:")
            self.logger.info(f"    Calls: {stats['count']}")
            self.logger.info(f"    Total: {stats['total_time']:.4f}s ({percentage:.1f}%)")
            self.logger.info(f"    Avg: {stats['avg_time']:.4f}s (min: {stats['min_time']:.4f}s, max: {stats['max_time']:.4f}s)")
            if self.enable_memory_tracking and self.psutil_available:
                self.logger.info(f"    Memory: {stats['avg_memory_used']:+.2f}MB avg, {stats['max_memory_peak']:.2f}MB peak")
            self.logger.info("")
    
    def export_to_csv(self, filename: str = "performance_metrics.csv"):
        """
        Export performance metrics to CSV file.
        
        Args:
            filename: Output filename
        """
        if not self.timings:
            self.logger.warning("No performance data to export")
            return
        
        # Flatten all metrics
        all_metrics = []
        for func_name, metrics_list in self.timings.items():
            for metrics in metrics_list:
                all_metrics.append({
                    'function_name': metrics.function_name,
                    'execution_time': metrics.execution_time,
                    'memory_used_mb': metrics.memory_used_mb,
                    'memory_peak_mb': metrics.memory_peak_mb,
                    'timestamp': metrics.timestamp
                })
        
        # Create DataFrame and export
        df = pd.DataFrame(all_metrics)
        df.to_csv(filename, index=False)
        self.logger.info(f"📁 Performance metrics exported to {filename}")
    
    def clear(self):
        """Clear all stored performance data."""
        self.timings.clear()
        self.logger.info("🧹 Performance data cleared")

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

# Convenience functions for easy usage
def time_function(func_name: str, log_level: str = "DEBUG"):
    """Convenience decorator using global monitor."""
    return performance_monitor.time_function(func_name, log_level)

def time_block(block_name: str, log_level: str = "DEBUG"):
    """Convenience context manager using global monitor."""
    return performance_monitor.time_block(block_name, log_level)

def get_performance_summary() -> Dict[str, Dict[str, float]]:
    """Get performance summary from global monitor."""
    if not PERFORMANCE_MONITORING_ENABLED:
        logger.info("Performance monitoring is disabled. Enable it first with enable_performance_monitoring().")
        return {}
    return performance_monitor.get_summary()

def print_performance_summary(sort_by: str = 'total_time'):
    """Print performance summary from global monitor."""
    if not PERFORMANCE_MONITORING_ENABLED:
        logger.info("Performance monitoring is disabled. Enable it first with enable_performance_monitoring().")
        return
    performance_monitor.print_summary(sort_by)

def export_performance_metrics(filename: str = "performance_metrics.csv"):
    """Export performance metrics from global monitor."""
    if not PERFORMANCE_MONITORING_ENABLED:
        logger.info("Performance monitoring is disabled. Enable it first with enable_performance_monitoring().")
        return
    performance_monitor.export_to_csv(filename) 