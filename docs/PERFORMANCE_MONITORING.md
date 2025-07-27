# Performance Monitoring System

## 🎯 Overview

The performance monitoring system provides comprehensive tracking of execution times, memory usage, and performance metrics across the pairs trading system. This helps identify bottlenecks, optimize performance, and ensure the system scales efficiently.

## 🚀 Features

### **1. Function Timing**
- Automatic timing of function execution
- Memory usage tracking (requires `psutil`)
- Peak memory monitoring
- Detailed logging with customizable levels

### **2. Code Block Timing**
- Context manager for timing specific code blocks
- Nested timing support
- Flexible block naming

### **3. Performance Analysis**
- Statistical summaries (mean, min, max, std)
- Percentage breakdown of total execution time
- Memory usage analysis
- CSV export for further analysis

### **4. Integration**
- Seamless integration with existing codebase
- Minimal code changes required
- Global monitoring instance

## 📊 Usage Examples

### **Basic Function Timing**

```python
from src.analysis.performance import time_function

@time_function("my_function")
def my_function(data):
    # Your code here
    result = process_data(data)
    return result
```

### **Code Block Timing**

```python
from src.analysis.performance import time_block

def process_large_dataset():
    with time_block("data_loading"):
        data = load_data()
    
    with time_block("data_processing"):
        processed_data = process_data(data)
    
    with time_block("results_export"):
        export_results(processed_data)
```

### **Performance Summary**

```python
from src.analysis.performance import print_performance_summary, export_performance_metrics

# Print summary to console
print_performance_summary()

# Export to CSV for analysis
export_performance_metrics("performance_report.csv")
```

## 🔧 Integration with Pairs Trading System

### **Automatically Monitored Functions**

The following functions are now automatically monitored:

1. **`walk_forward_analysis`** - Main walk-forward analysis
2. **`pair_selection`** - Pair selection process
3. **`model_fitting`** - Spread model fitting
4. **`signal_generation_*`** - All signal generation methods:
   - `signal_generation_static`
   - `signal_generation_rolling`
   - `signal_generation_scaled`
   - `signal_generation_stepwise`
   - `signal_generation_tiered`
5. **`backtest`** - Backtesting execution

### **Performance Output**

When running the main system, you'll see output like:

```
2024-01-15 10:30:15 - INFO - ⏱️ walk_forward_analysis: 45.2341s, Memory: +12.34MB (Peak: 156.78MB)
2024-01-15 10:30:15 - INFO - ⏱️ pair_selection: 12.4567s, Memory: +2.45MB (Peak: 45.67MB)
2024-01-15 10:30:15 - INFO - ⏱️ model_fitting: 8.9012s, Memory: +1.23MB (Peak: 23.45MB)
2024-01-15 10:30:15 - INFO - ⏱️ signal_generation_tiered: 5.6789s, Memory: +0.89MB (Peak: 12.34MB)
2024-01-15 10:30:15 - INFO - ⏱️ backtest: 3.4567s, Memory: +0.45MB (Peak: 8.90MB)
```

### **Performance Summary**

At the end of execution, you'll see a detailed summary:

```
============================================================
PERFORMANCE BENCHMARKING RESULTS
============================================================
📊 Performance Summary:
  Total execution time: 75.7276s
  Total function calls: 156

  walk_forward_analysis:
    Calls: 1
    Total: 45.2341s (59.7%)
    Avg: 45.2341s (min: 45.2341s, max: 45.2341s)
    Memory: +12.34MB avg, 156.78MB peak

  pair_selection:
    Calls: 12
    Total: 12.4567s (16.4%)
    Avg: 1.0381s (min: 0.8234s, max: 1.4567s)
    Memory: +2.45MB avg, 45.67MB peak

  model_fitting:
    Calls: 89
    Total: 8.9012s (11.8%)
    Avg: 0.1000s (min: 0.0234s, max: 0.3456s)
    Memory: +1.23MB avg, 23.45MB peak
```

## 📈 Performance Metrics

### **Execution Time Metrics**
- **Total Time**: Cumulative execution time
- **Average Time**: Mean execution time per call
- **Min/Max Time**: Range of execution times
- **Standard Deviation**: Variability in execution time

### **Memory Metrics**
- **Memory Used**: Change in memory during execution
- **Peak Memory**: Maximum memory usage reached
- **Memory Efficiency**: Memory usage per operation

### **Call Count Metrics**
- **Function Calls**: Number of times each function was called
- **Frequency Analysis**: Most/least called functions

## 🎛️ Configuration

### **Memory Tracking**

Memory tracking requires the `psutil` package. If not available, timing will still work:

```python
# Memory tracking enabled (default)
performance_monitor = PerformanceMonitor(enable_memory_tracking=True)

# Memory tracking disabled
performance_monitor = PerformanceMonitor(enable_memory_tracking=False)
```

### **Logging Levels**

Control the verbosity of performance messages:

```python
@time_function("my_function", log_level="DEBUG")  # Only shows in debug mode
@time_function("my_function", log_level="INFO")   # Shows in info mode (default)
```

## 📁 Output Files

### **CSV Export**

Performance metrics are automatically exported to:
- `results/performance_metrics.csv` - Main system runs
- `test_performance_metrics.csv` - Test runs

**CSV Format:**
```csv
function_name,execution_time,memory_used_mb,memory_peak_mb,timestamp
walk_forward_analysis,45.2341,12.34,156.78,2024-01-15 10:30:15
pair_selection,12.4567,2.45,45.67,2024-01-15 10:30:15
model_fitting,8.9012,1.23,23.45,2024-01-15 10:30:15
```

## 🔍 Performance Analysis

### **Identifying Bottlenecks**

1. **High Total Time**: Functions consuming most execution time
2. **High Average Time**: Functions that are slow per call
3. **High Call Count**: Functions called frequently
4. **High Memory Usage**: Memory-intensive operations

### **Optimization Targets**

Based on typical pairs trading workloads:

1. **Pair Selection** - Often the biggest bottleneck
2. **Model Fitting** - Can be slow with many pairs
3. **Signal Generation** - Rolling calculations can be expensive
4. **Walk-Forward Analysis** - Overall orchestration

### **Scalability Analysis**

Monitor how performance changes with:
- **Data Size**: More tickers, longer time periods
- **Window Size**: Larger training/testing windows
- **Signal Complexity**: More sophisticated signal methods

## 🧪 Testing

### **Run Performance Tests**

```bash
# Activate virtual environment
.venv\Scripts\activate

# Run performance test
python scripts/test_performance.py
```

### **Expected Output**

```
🚀 Starting Performance Monitoring Test
⏱️ sample_function: 0.1234s, Memory: +0.12MB (Peak: 15.67MB)
⏱️ data_processing: 0.5678s, Memory: +2.34MB (Peak: 23.45MB)
⏱️ manual_calculation: 0.2345s, Memory: +0.45MB (Peak: 12.34MB)

📊 Performance Summary:
  Total execution time: 0.9257s
  Total function calls: 3
```

## 🚀 Advanced Usage

### **Custom Performance Monitoring**

```python
from src.analysis.performance import PerformanceMonitor

# Create custom monitor
custom_monitor = PerformanceMonitor(enable_memory_tracking=True)

@custom_monitor.time_function("custom_function")
def my_custom_function():
    # Your code here
    pass

# Get custom summary
summary = custom_monitor.get_summary()
custom_monitor.print_summary()
```

### **Performance Comparison**

```python
# Compare different approaches
with time_block("approach_1"):
    result1 = approach_1(data)

with time_block("approach_2"):
    result2 = approach_2(data)

# Compare in summary
print_performance_summary()
```

## 📊 Best Practices

### **1. Strategic Monitoring**
- Focus on high-impact functions
- Monitor during development and testing
- Track performance over time

### **2. Memory Management**
- Monitor memory usage for large datasets
- Identify memory leaks
- Optimize data structures

### **3. Scalability Planning**
- Test with different data sizes
- Monitor performance trends
- Plan for production scaling

### **4. Continuous Monitoring**
- Integrate into CI/CD pipeline
- Set performance thresholds
- Alert on performance regressions

## 🔧 Troubleshooting

### **Common Issues**

1. **psutil Import Error**
   ```
   pip install psutil
   ```

2. **Memory Tracking Disabled**
   - Check if psutil is installed
   - Verify memory tracking is enabled

3. **No Performance Data**
   - Ensure functions are decorated
   - Check logging level

### **Performance Tips**

1. **Vectorize Operations**: Use NumPy/Pandas vectorized operations
2. **Reduce Function Calls**: Minimize overhead in tight loops
3. **Memory Efficiency**: Use generators for large datasets
4. **Caching**: Cache expensive calculations

## 📈 Future Enhancements

### **Planned Features**
1. **Real-time Monitoring**: Live performance dashboard
2. **Performance Alerts**: Automatic alerts for performance issues
3. **Historical Tracking**: Performance trends over time
4. **Profiling Integration**: Integration with cProfile
5. **Distributed Monitoring**: Support for distributed processing

### **Integration Opportunities**
1. **Web Dashboard**: Real-time performance visualization
2. **Alerting System**: Performance threshold alerts
3. **CI/CD Integration**: Automated performance testing
4. **Production Monitoring**: Live trading performance tracking 