# Pairs Trading System

A production-ready pairs trading system with excellent performance (1.170 Sharpe ratio) using a proven 60-stock universe across 6 balanced sectors, complete with a professional visualization suite.

## 🚀 Quick Start

### Default System (Your 60 Stocks)
```bash
python main.py backtest --start-date 2020-01-01 --end-date 2025-07-01 --signal-method rolling --entry-z 1.5 --exit-z 0.5 --risk-management-mode disabled
```

**Performance**: 23.99% total return, 1.170 Sharpe ratio, 6.07% max drawdown

### Generate Professional Visualizations
```bash
cd results
python visualize_strategy.py
```

**Output**: 8 high-quality PNG charts perfect for presentations

### Mid-Cap Experiment
```bash
python main.py backtest --universe mid_cap --start-date 2020-01-01 --end-date 2024-01-01 --signal-method rolling --entry-z 1.5 --exit-z 0.5 --risk-management-mode disabled
```

## 📊 System Overview

### Default Universe: 60 Mega-Cap Stocks (6 Sectors × 10 Stocks)

**Technology**: AAPL, MSFT, NVDA, GOOGL, META, ORCL, AVGO, ADBE, CSCO, INTC  
**Financials**: JPM, BAC, WFC, C, GS, MS, SCHW, BK, AXP, USB  
**Consumer Discretionary**: AMZN, HD, MCD, NKE, SBUX, LOW, TJX, TGT, GM, F  
**Healthcare**: JNJ, UNH, PFE, MRK, ABBV, ABT, LLY, BMY, TMO, AMGN  
**Industrials**: CAT, DE, HON, UNP, UPS, BA, GE, LMT, RTX, MMM  
**Energy**: XOM, CVX, COP, EOG, SLB, MPC, PSX, VLO, BKR, HAL  

### Key Features

- **Fresh Data**: Yahoo Finance with automatic caching
- **Fast Execution**: 10x speedup from optimized pair selection
- **Flexible CLI**: All parameters configurable via command line
- **Multiple Universes**: Mega-cap (default), mid-cap, custom
- **Risk Management**: Configurable from disabled to full
- **Performance Monitoring**: Optional timing and diagnostics
- **Professional Visualizations**: 8 high-quality charts for presentations

## 📈 Performance Results

### Default System (Mega-Cap Universe)
- **Total Return**: 23.99% over 5.5 years (2020-2025)
- **Sharpe Ratio**: 1.170 (excellent risk-adjusted returns)
- **Max Drawdown**: 6.07% (manageable risk)
- **Annualized Return**: 7.41%
- **Win Rate**: 70.7% (excellent trade quality)

### Signal Methods Available
- **`static`**: Fixed z-score thresholds
- **`rolling`**: Dynamic z-scores using rolling windows
- **`rolling_scaled`**: Continuous position sizing
- **`tiered`**: Multi-level position sizing

### Pair Selection Methods
- **`original`**: ADF test-based (slow but thorough)
- **`fast`**: Distance-based pre-screening (10x faster)
- **`ultra_fast`**: Distance-only (fastest)

## 📊 Visualization Suite

### Professional Charts Available
1. **`cumulative_returns.png`** - Strategy vs benchmark performance
2. **`sharpe_ratio_comparison.png`** - Risk-adjusted performance comparison
3. **`correlation_table.png`** - Strategy correlation with benchmarks
4. **`performance_summary_table.png`** - Comprehensive metrics table
5. **`trade_distribution_pnl.png`** - Trade PnL distribution histogram
6. **`price_spread_chart.png`** - Strategy mechanics demonstration
7. **`z_score_thresholds_chart.png`** - Signal generation visualization
8. **`trading_signals_chart.png`** - Trading positions over time

### Visualization Features
- **Cell-based development** script for easy customization
- **High-resolution PNG outputs** (300 DPI, print quality)
- **Professional color palette** and styling
- **Comprehensive data validation** and debugging
- **Perfect for presentations** and documentation

## 🏗️ System Architecture

### Core Modules

```
src/
├── data/                     # Data handling
│   ├── data_loader.py        # Price data loading and caching
│   ├── pair_selection.py     # Fast distance-based pair selection
│   └── universe_manager.py   # Universe management system
├── models/                   # Signal generation
│   ├── model_fitting.py      # Spread modeling and beta estimation
│   └── signal_generation.py  # Multiple signal methods
├── trading/                  # Trading execution
│   ├── backtest.py           # Backtesting engine
│   ├── walk_forward.py       # Walk-forward analysis
│   └── risk_management.py    # Position sizing and risk controls
└── analysis/                 # Performance evaluation
    ├── portfolio_analysis.py # Portfolio-level metrics
    └── performance.py        # Performance monitoring
```

### Configuration

- **`config/trading_config.py`**: Main trading configuration with validation
- **`config/data_params.py`**: Original 60-stock sector definitions
- **`main.py`**: Enhanced CLI with comprehensive parameter control
- **`results/visualize_strategy.py`**: Cell-based visualization script

## 🛠️ Advanced Usage

### CLI Options

```bash
# Basic parameters
--start-date YYYY-MM-DD
--end-date YYYY-MM-DD
--train-size 504
--test-size 126

# Signal generation
--signal-method [static|rolling|rolling_scaled|tiered]
--entry-z 1.5
--exit-z 0.5
```

### Visualization Development

```bash
# Generate all visualizations
cd results
python visualize_strategy.py

# Custom development
# Edit visualize_strategy.py to run specific cells
# Comment out unwanted cells and run:
python visualize_strategy.py
```

## 📋 Documentation

- **[Progress Report](PROGRESS_REPORT.md)**: Comprehensive system overview and performance analysis
- **[Visualization Guide](VISUALIZATION_GUIDE.md)**: Complete guide to the visualization suite
- **[CLI Usage](CLI_USAGE.md)**: Detailed command-line interface documentation
- **[Technical Guide](TECHNICAL_GUIDE.md)**: System architecture and technical details

## 🎯 Use Cases

### For Recruiters and Presentations
- Use `cumulative_returns.png` and `sharpe_ratio_comparison.png` for performance overview
- Use `performance_summary_table.png` for comprehensive metrics
- Use strategy mechanics charts for technical explanation

### For Technical Interviews
- Use strategy mechanics charts to explain methodology
- Use `trade_distribution_pnl.png` to show trade quality
- Use correlation table to demonstrate diversification

### For Investment Proposals
- Use all charts for comprehensive presentation
- Focus on risk-adjusted performance advantages
- Emphasize low correlation and diversification benefits

## 🚀 Next Steps

1. **Run the system**: Use the default configuration for optimal performance
2. **Generate visualizations**: Create professional charts for presentations
3. **Customize as needed**: Modify the visualization script for specific requirements
4. **Deploy to production**: Use the system for live trading with proper risk management

---

**Last Updated**: July 27, 2025  
**Performance**: 1.170 Sharpe ratio, 23.99% total return  
**Visualization Suite**: Complete with 8 professional charts
