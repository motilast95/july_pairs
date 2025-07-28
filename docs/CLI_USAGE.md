# CLI Usage Guide

The enhanced `main.py` now supports comprehensive command-line configuration for all aspects of the pairs trading system.

## Basic Usage

```bash
python main.py backtest [OPTIONS]
```

## Quick Examples

### 1. Simple Diagnostic Test (No Risk Management)
```bash
python main.py backtest \
  --signal-method rolling \
  --entry-z 2.0 \
  --exit-z 0.5 \
  --risk-management-mode disabled \
  --start-date 2023-01-01 \
  --end-date 2024-12-31 \
  --train-size 252 \
  --test-size 63
```

### 2. Production Backtest with Full Risk Management
```bash
python main.py backtest \
  --signal-method rolling \
  --entry-z 2.0 \
  --exit-z 0.5 \
  --risk-management-mode full \
  --start-date 2020-01-01 \
  --end-date 2024-12-31 \
  --train-size 252 \
  --test-size 63
```

### 3. Optimal Performance Configuration (1.170 Sharpe Ratio)
```bash
python main.py backtest \
  --signal-method rolling \
  --entry-z 1.5 \
  --exit-z 0.5 \
  --risk-management-mode disabled \
  --start-date 2020-01-01 \
  --end-date 2025-07-01 \
  --benchmark
```
**Results:** 23.99% total return, 1.170 Sharpe ratio, 6.07% max drawdown

### 4. Performance Analysis with Timing
```bash
python main.py backtest \
  --signal-method rolling \
  --entry-z 2.0 \
  --exit-z 0.5 \
  --risk-management-mode disabled \
  --enable-performance
```

## Command-Line Options

### Basic Parameters
- `--start-date YYYY-MM-DD` - Start date for backtest
- `--end-date YYYY-MM-DD` - End date for backtest
- `--train-size INT` - Training window size in days
- `--test-size INT` - Testing window size in days

### Signal Generation Parameters
- `--signal-method {static,rolling,rolling_scaled,tiered}` - Signal generation method
- `--entry-z FLOAT` - Entry z-score threshold
- `--exit-z FLOAT` - Exit z-score threshold
- `--rolling-window INT` - Rolling window size for signal calculation
- `--position-size FLOAT` - Position size multiplier
- `--transaction-cost-bps FLOAT` - Transaction cost in basis points

### Pair Selection Parameters
- `--distance-threshold FLOAT` - Distance threshold for pair selection (lower = more similar)
- `--adf-alpha FLOAT` - ADF test significance level
- `--pair-selection-method {original,fast,ultra_fast}` - Pair selection method

| Method | Description | Speed | Quality |
|--------|-------------|-------|---------|
| `original` | Full ADF tests on all pairs | Slowest | Highest |
| `fast` | Distance pre-screening + ADF tests | Fast | High |
| `ultra_fast` | Distance only (no ADF tests) | Fastest | Good |

### Risk Management

#### Risk Management Modes
- `--risk-management-mode {disabled,minimal,moderate,full}` - Predefined risk management configurations

| Mode | Volatility Scaling | Position Limits | Pair Validation | Description |
|------|-------------------|-----------------|-----------------|-------------|
| `disabled` | ❌ | ❌ | ❌ | No risk management (for diagnosis) |
| `minimal` | ❌ | ✅ | ✅ | Basic position limits and pair validation |
| `moderate` | ✅ | ✅ | ✅ | Full risk management with volatility scaling |
| `full` | ✅ | ✅ | ✅ | Full risk management (same as moderate) |

#### Individual Risk Management Toggles
- `--disable-volatility-scaling` - Disable volatility-based position scaling
- `--disable-position-limits` - Disable position size limits
- `--disable-pair-validation` - Disable pair risk validation

#### Risk Management Thresholds
- `--max-pair-volatility FLOAT` - Maximum pair volatility (default: 0.5)
- `--max-daily-move FLOAT` - Maximum daily price move (default: 0.2)
- `--min-data-days INT` - Minimum data days required (default: 60)

### Performance Monitoring
- `--enable-performance` - Enable performance monitoring (slower but provides timing data)

## Advanced Examples

### 1. Custom Risk Management
```bash
python main.py backtest \
  --signal-method rolling \
  --entry-z 2.0 \
  --exit-z 0.5 \
  --disable-volatility-scaling \
  --max-pair-volatility 0.3 \
  --max-daily-move 0.15
```

### 2. Different Signal Methods
```bash
# Static z-score
python main.py backtest --signal-method static --entry-z 2.0 --exit-z 0.5

# Rolling z-score with custom window
python main.py backtest --signal-method rolling --rolling-window 120 --entry-z 2.0 --exit-z 0.5

# Tiered signals
python main.py backtest --signal-method tiered --entry-z 2.0 --exit-z 0.5
```

### 3. Pair Selection Tuning
```bash
# More selective pairs (lower distance threshold)
python main.py backtest --distance-threshold 0.05

# Less selective pairs (higher distance threshold)
python main.py backtest --distance-threshold 0.2

# Stricter ADF test
python main.py backtest --adf-alpha 0.01

# Different pair selection methods
python main.py backtest --pair-selection-method original  # Full ADF tests
python main.py backtest --pair-selection-method fast      # Distance + ADF
python main.py backtest --pair-selection-method ultra_fast  # Distance only
```

### 4. Transaction Cost Analysis
```bash
# High transaction costs
python main.py backtest --transaction-cost-bps 5.0

# Low transaction costs
python main.py backtest --transaction-cost-bps 0.5
```

## Configuration Summary

The system will display a configuration summary at the start of each run:

```
============================================================
CONFIGURATION SUMMARY
============================================================
Signal Method: rolling
Entry Z-Score: 2.0
Exit Z-Score: 0.5
Risk Management Mode: disabled
Volatility Scaling: False
Position Limits: False
Pair Validation: False
Pair Selection Method: ultra_fast
Distance Threshold: 0.1
Date Range: 2023-01-01 to 2024-12-31
Train/Test: 252/63 days
============================================================
```

## Performance Monitoring

When `--enable-performance` is used, you'll get detailed timing information:

```
============================================================
PERFORMANCE BENCHMARKING RESULTS
============================================================
📊 Performance Summary:
  Total execution time: 32.4711s
  Total function calls: 832

  walk_forward_analysis:
    Calls: 1
    Total: 16.6982s (51.4%)
    Avg: 16.6982s
    Memory: +22.80MB avg, 148.55MB peak

  fast_pair_selection:
    Calls: 33
    Total: 10.7767s (33.2%)
    Avg: 0.3266s
    Memory: +0.62MB avg, 148.43MB peak
...
```

## Tips for Diagnosis

1. **Start with risk management disabled** to isolate signal generation issues
2. **Use performance monitoring** to identify bottlenecks
3. **Try different signal methods** to see which works best
4. **Adjust pair selection parameters** to find optimal pair sets
5. **Test different time periods** to check for regime changes

## Output Files

- `results/data/trades_data.csv` - All generated trades
- `results/performance_metrics.csv` - Performance timing data (if enabled)
- `results/logs/pairs_trading.log` - Detailed execution log 