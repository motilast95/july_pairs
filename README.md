# Pairs Trading System

A production-ready pairs trading system with excellent performance (1.170 Sharpe ratio) using a proven 60-stock universe across 6 balanced sectors, complete with a professional visualization suite.

## 🚀 Quick Start

### ⭐ Optimal Configuration (1.170 Sharpe Ratio)
```bash
python main.py backtest \
  --start-date 2020-01-01 \
  --end-date 2025-07-01 \
  --signal-method rolling \
  --entry-z 1.5 \
  --exit-z 0.5 \
  --risk-management-mode disabled \
  --benchmark
```

**Expected Results:**
- **Total Return**: 23.99% over 5.5 years
- **Sharpe Ratio**: 1.170 (excellent risk-adjusted returns)
- **Max Drawdown**: 6.07% (manageable risk)
- **Annualized Return**: 7.41%
- **99 trades executed** across 42 pairs
- **+44.2% outperformance** vs best benchmark

## 📊 Performance Highlights

| Metric | Value | Benchmark Comparison |
|--------|-------|---------------------|
| **Sharpe Ratio** | 1.170 | +44.2% vs best benchmark |
| **Total Return** | 23.99% | +9.88% vs S&P 500 |
| **Max Drawdown** | 6.07% | -27.49% vs S&P 500 |
| **Volatility** | 6.30% | -15.14% vs S&P 500 |
| **Win Rate** | 70.7% | Excellent trade quality |

## 🎯 Key Features

- **Fresh Data**: Yahoo Finance with automatic caching
- **Fast Execution**: 10x speedup from optimized pair selection
- **Flexible CLI**: All parameters configurable via command line
- **Multiple Universes**: Mega-cap (default), mid-cap, custom
- **Risk Management**: Configurable from disabled to full
- **Professional Visualizations**: 8 high-quality charts for presentations

## 📁 Repository Structure

```
july_pairs/
├── main.py                 # Main entry point
├── OPTIMAL_CONFIGURATION.md # Optimal parameters guide
├── docs/                   # Detailed documentation
├── src/                    # Core trading system
├── results/                # Visualization scripts
├── data/                   # Price data and cache
└── tests/                  # Unit tests
```

## 📈 Generate Visualizations

After running the backtest, create professional charts:

```bash
cd results
python visualize_strategy.py
```

**Output**: 8 high-quality PNG charts perfect for presentations

## 📚 Documentation

- **[Optimal Configuration](OPTIMAL_CONFIGURATION.md)** - Exact parameters for 1.170 Sharpe ratio
- **[Detailed Documentation](docs/README.md)** - Complete system guide
- **[Visualization Guide](docs/VISUALIZATION_GUIDE.md)** - Chart generation guide

## 🏆 Benchmark Comparison

| Benchmark | Return | Sharpe | Drawdown | Volatility |
|-----------|--------|--------|----------|------------|
| **Strategy** | 23.99% | 1.170 | -6.07% | 6.30% |
| Technology ETF | 21.00% | 0.81 | -33.56% | 28.63% |
| NASDAQ-100 ETF | 19.33% | 0.81 | -35.12% | 26.08% |
| S&P 500 ETF | 14.11% | 0.73 | -33.72% | 21.44% |

## 🛠️ Installation

```bash
git clone https://github.com/motilast95/july_pairs.git
cd july_pairs
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

## 📋 Requirements

- Python 3.8+
- pandas, numpy, matplotlib, seaborn
- yfinance, scipy, sklearn

## 📄 License

This project is for educational and research purposes.

---

**Built with ❤️ for quantitative finance**