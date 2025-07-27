# Performance Monitoring Usage Guide

## Overview

The pairs trading system includes an optional performance monitoring system that tracks execution times and memory usage of different functions and code blocks. This system is **disabled by default** for faster execution but can be enabled when needed for optimization and debugging.

## Quick Start

### Enable Performance Monitoring

```bash
# Enable performance monitoring for a backtest
python main.py backtest --enable-performance --start-date 2020-01-01 --end-date 2025-07-01 --signal-method rolling --entry-z 1.5 --exit-z 0.5 --risk-management-mode disabled
```

### Disable Performance Monitoring (Default)

```bash
# Performance monitoring is disabled by default for faster execution
python main.py backtest --start-date 2020-01-01 --end-date 2025-07-01 --signal-method rolling --entry-z 1.5 --exit-z 0.5 --risk-management-mode disabled
```

## Performance Monitoring Features

### What Gets Tracked
- **Function execution times** for all major components
- **Memory usage** (if psutil is available)
- **Call counts** and statistics
- **Detailed breakdowns** by component

### Key Components Monitored
1. **Pair Selection**: `fast_pair_selection` - Distance-based pre-screening
2. **Model Fitting**: `model_fitting` - Spread model estimation
3. **Signal Generation**: `signal_generation_rolling` - Trading signal generation
4. **Backtesting**: `backtest` - Trade execution and PnL calculation
5. **Walk-Forward Analysis**: `walk_forward_analysis` - Overall process

## Performance Analysis Results

When enabled, you'll see output like:

```
📊 Performance Summary:
  Total execution time: 15.9643s
  Total function calls: 146

  fast_pair_selection:
    Calls: 16
    Total: 6.1153s (38.3%)
    Avg: 0.3822s (min: 0.1395s, max: 0.8698s)
    Memory: +1.23MB avg, 145.61MB peak

  model_fitting:
    Calls: 43
    Total: 0.8657s (5.4%)
    Avg: 0.0201s (min: 0.0092s, max: 0.0303s)
    Memory: +0.01MB avg, 145.62MB peak
```

## API Usage

### Enable/Disable Programmatically
```python
from src.analysis.performance import (
    enable_performance_monitoring,
    disable_performance_monitoring,
    is_performance_monitoring_enabled
)

# Enable monitoring
enable_performance_monitoring()

# Check if enabled
if is_performance_monitoring_enabled():
    print("Performance monitoring is active")

# Disable monitoring
disable_performance_monitoring()
```

### Get Performance Data
```python
from src.analysis.performance import (
    get_performance_summary,
    print_performance_summary,
    export_performance_metrics
)

# Get summary as dictionary
summary = get_performance_summary()

# Print formatted summary
print_performance_summary()

# Export to CSV
export_performance_metrics("my_performance.csv")
```

## Performance Impact

### Speed Comparison
- **Disabled**: ~13-15 seconds (baseline)
- **Enabled**: ~15-17 seconds (+10-15% overhead)

### Memory Impact
- **Disabled**: No additional memory overhead
- **Enabled**: ~20-30MB additional memory for tracking

## Best Practices

### When to Enable
- **Development**: When optimizing specific components
- **Debugging**: When investigating performance bottlenecks
- **Analysis**: When comparing different algorithms
- **Profiling**: When preparing for production optimization

### When to Disable
- **Production**: For fastest execution
- **Batch Processing**: When running many backtests
- **Parameter Sweeps**: When testing many configurations
- **Regular Testing**: For daily development work

## Configuration

The performance monitoring is controlled by a global flag:
- **Default**: `PERFORMANCE_MONITORING_ENABLED = False`
- **Can be changed**: At runtime via API calls
- **Persists**: For the duration of the Python session

## Troubleshooting

### No Performance Data
If you see "Performance monitoring is disabled" messages:
1. Make sure you called `enable_performance_monitoring()`
2. Check that you're using the `--enable-performance` flag
3. Verify the monitoring was enabled before running your code

### Memory Tracking Issues
If memory tracking shows 0MB:
1. Install psutil: `pip install psutil`
2. Check if psutil is available in your environment
3. Memory tracking will be automatically disabled if psutil is unavailable

## Example Workflow

```python
# 1. Quick iteration (fast)
for params in parameter_sweep:
    run_simple_test(enable_performance=False)

# 2. Detailed analysis (with timing)
enable_performance_monitoring()
run_simple_test(enable_performance=True)
print_performance_summary()

# 3. Export for analysis
export_performance_metrics("parameter_sweep_performance.csv")
```

This approach gives you the best of both worlds: fast iteration when you need it, and detailed performance analysis when you want it. 