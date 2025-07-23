# Pairs Trading Pipeline

This repository implements a modular pipeline for pairs trading research and backtesting. The codebase is organized for flexibility and extensibility, supporting data loading, pair selection, model fitting, signal generation, backtesting, and portfolio analysis.

## Overview

### 1. Data Loading

- **`data_loader.py`**: Loads price data from CSV and sector tickers from config files.

### 2. Pair Selection

- **`pair_selection.py`**: Selects cointegrated pairs within each sector using the Engle-Granger test.

### 3. Model Fitting

- **`model_fitting.py`**: Fits a linear regression to estimate the hedge ratio (beta) for each pair.

### 4. Signal Generation

- **`signal_generation.py`**: Generates trading signals based on the z-score of the spread, supporting static, rolling, continuous (scaled), and stepwise position sizing approaches.

### 5. Backtesting

- **`backtest.py`**: Simulates trading based on generated signals, calculates daily and cumulative PnL, and logs trades.

### 6. Walk-Forward Analysis

- **`walk_forward.py`**: Runs the full pipeline in a walk-forward fashion, splitting data into train/test windows and aggregating results.

### 7. Portfolio Analysis

- **`portfolio_analysis.py`**: Aggregates PnL across all pairs and computes portfolio-level performance metrics.

### 8. Testing

- **`tests/`**: Contains unit tests for key modules, including signal generation.

---

## Recent Additions

### 1. Rolling Mean/Std Signal Generation

Signal generation now supports using a rolling window to compute the mean and standard deviation for z-score calculation. This allows for more adaptive signals that respond to changing market conditions.

- **Function:** `generate_rolling_signals`  
- **Usage:**  

  ```python
  signals = generate_rolling_signals(spread, entry_z, exit_z, rolling_window=60)
  ```

### 2. Scaled (Continuous) Signals

In addition to binary entry/exit signals, the codebase now supports position sizing proportional to the z-score. This means the position size can be fractional (e.g., 0.75, 1.5, etc.), and is set to zero when the z-score is within the exit threshold.

- **Function:** `generate_rolling_scaled_signals`  
- **Usage:**  

  ```python
  positions = generate_rolling_scaled_signals(spread, entry_z=1.0, exit_z=0.5, rolling_window=60)
  ```

### 3. Stepwise Position Sizing Signals

The codebase also supports stepwise position sizing, where the position size increases or decreases in discrete steps (e.g., every 0.25 z-score units) as the z-score moves further from zero. This provides a middle ground between binary and fully continuous scaling.

- **Function:** `generate_rolling_stepwise_signals`  
- **Usage:**  

  ```python
  positions = generate_rolling_stepwise_signals(spread, entry_z=1.0, exit_z=0.5, step=0.25, rolling_window=60)
  ```

---

## Running Tests

To run the unit tests:

```bash
pip install pytest
pytest tests/
```

---

## Customization

- Adjust parameters (e.g., window sizes, z-score thresholds, step size) in your config files or directly in the function calls.
- Add new signal generation or backtesting logic as needed.

---

## Explore Folder Experiment Log

This project includes an `explore` folder where various strategy experiments and diagnostics have been performed. Key activities include:

- **Signal-based backtests:** Iterative development and testing of rolling, tiered, and other signal generation methods for pairs trading.
- **Trade-level diagnostics:** Analysis of trade PnL distributions, win/loss rates, and per-pair and per-period performance to identify sources of risk and return.
- **Stop-loss/take-profit experiments:** Implemented and tested per-trade stop-loss and take-profit logic. Found that, in a signal-based always-exposed backtest, these controls had limited effect on portfolio-level risk/return. Logic was removed for clarity and robustness.
- **Portfolio-level risk analysis:** Focused on returns-based Sharpe ratio, drawdown, and volatility as primary metrics. Added diagnostics to compare trade log PnL to portfolio PnL, and to visualize daily/cumulative PnL.
- **Fat tail risk investigation:** Explored the causes of large losses and the limitations of per-trade stops in a signal-driven framework. Planning to address fat tails with alternative risk controls (e.g., volatility filters, regime detection, or portfolio-level constraints).

This log will be updated as new experiments and diagnostics are added.
