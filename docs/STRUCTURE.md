# Pairs Trading System - Project Structure

This document describes the organized structure of the pairs trading system.

## Directory Structure

```
july_pairs/
├── src/                          # Core trading system modules
│   ├── __init__.py
│   ├── data/                     # Data handling modules
│   │   ├── __init__.py
│   │   ├── data_loader.py        # Price data loading and preprocessing
│   │   └── pair_selection.py     # Cointegration-based pair selection
│   ├── models/                   # Model fitting and signal generation
│   │   ├── __init__.py
│   │   ├── model_fitting.py      # Spread modeling and beta estimation
│   │   └── signal_generation.py  # Trading signal generation logic
│   ├── trading/                  # Trading execution and risk management
│   │   ├── __init__.py
│   │   ├── backtest.py           # Backtesting engine
│   │   ├── walk_forward.py       # Walk-forward analysis
│   │   └── risk_management.py    # Position sizing and risk controls
│   └── analysis/                 # Analysis and performance evaluation
│       ├── __init__.py
│       ├── portfolio_analysis.py # Portfolio-level performance metrics
│       └── performance.py        # Performance calculation utilities
├── config/                       # Configuration files
│   ├── __init__.py
│   ├── trading_config.py         # Main trading configuration
│   ├── data_params.py            # Data parameters and sector definitions
│   ├── signal_generation_config.py
│   └── screening.py              # Screening parameters
├── data/                         # Data files
│   └── prices.csv                # Price data
├── tests/                        # Test files
│   ├── __init__.py
│   ├── test_data_loader.py
│   ├── test_pair_selection.py
│   ├── test_model_fitting.py
│   ├── test_signal_generation.py
│   ├── test_backtest.py
│   ├── test_walk_forward.py
│   ├── test_portfolio_analysis.py
│   └── test_hyperparameter_tuning.py
├── scripts/                      # Utility and analysis scripts
│   ├── hyperparameter_tuning.py  # Hyperparameter optimization
│   ├── test_improvements.py      # System improvement tests
│   └── diagnostic_analysis.py    # Strategy diagnostic analysis
├── notebooks/                    # Jupyter notebooks and exploration
│   ├── all_trades.ipynb
│   └── explore/                  # Exploration notebooks by date
│       ├── 7_18/
│       ├── 7_20/
│       ├── 7_21/
│       ├── 7_22/
│       ├── 7_23/
│       └── 7_24/
├── results/                      # Output files
│   ├── plots/                    # Generated plots and charts
│   ├── logs/                     # Log files
│   └── data/                     # Output CSV files
├── docs/                         # Documentation
│   ├── README.md                 # Main README
│   ├── IMPROVEMENTS_SUMMARY.md   # Summary of improvements
│   └── STRUCTURE.md              # This file
├── requirements.txt              # Python dependencies
├── setup.py                      # Package setup
├── main.py                       # Main entry point
└── .gitignore
```

## Key Benefits

1. **Separation of Concerns**: Core logic, config, tests, and utilities are clearly separated
2. **Modularity**: Related functionality is grouped together
3. **Scalability**: Easy to add new modules without cluttering root
4. **Professional Structure**: Follows Python package conventions
5. **Clean Root**: Only essential files at root level

## Usage

### Running the System

```bash
# Run a backtest
python main.py backtest --start-date 2023-01-01 --end-date 2024-06-30

# Run diagnostic analysis
python main.py diagnostic

# Run tests
python -m pytest tests/

# Run specific script
python scripts/diagnostic_analysis.py
```

### Importing Modules

```python
# Import data modules
from src.data.data_loader import load_prices, load_sector_tickers
from src.data.pair_selection import select_pairs

# Import model modules
from src.models.model_fitting import fit_spread
from src.models.signal_generation import generate_signals

# Import trading modules
from src.trading.backtest import run_backtest
from src.trading.walk_forward import walk_forward
from src.trading.risk_management import PortfolioRiskManager

# Import analysis modules
from src.analysis.portfolio_analysis import aggregate_portfolio_pnl
from src.analysis.performance import calculate_returns
```

## Configuration

The system uses a centralized configuration system in `config/trading_config.py`:

```python
from config.trading_config import create_default_config

config = create_default_config()
config = config.update(
    start_date="2023-01-01",
    end_date="2024-06-30",
    train_size=252,
    test_size=126
)
```

## Testing

Tests are organized by module and can be run individually or together:

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_data_loader.py

# Run with coverage
python -m pytest tests/ --cov=src
```

## Development Workflow

1. **Core Logic**: Add new functionality in appropriate `src/` subdirectory
2. **Configuration**: Update `config/` files for new parameters
3. **Tests**: Add corresponding tests in `tests/`
4. **Scripts**: Create utility scripts in `scripts/`
5. **Documentation**: Update relevant docs in `docs/`

## File Naming Conventions

- **Modules**: snake_case (e.g., `data_loader.py`)
- **Classes**: PascalCase (e.g., `PortfolioRiskManager`)
- **Functions**: snake_case (e.g., `load_prices`)
- **Constants**: UPPER_CASE (e.g., `COINTEGRATION_SIGNIFICANCE`)
- **Directories**: snake_case (e.g., `data_loader/`)

This structure makes the codebase more maintainable, professional, and easier to navigate. 