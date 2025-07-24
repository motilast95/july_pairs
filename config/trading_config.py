"""
Centralized configuration management for the pairs trading system.
Provides validation and type safety for all trading parameters.
"""

from typing import Dict, List, Optional, Union
from dataclasses import dataclass
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TradingConfig:
    """Configuration class for pairs trading parameters with validation."""
    
    # Data parameters
    start_date: str
    end_date: str
    tickers: List[str]
    
    # Walk-forward parameters
    train_size: int = 504  # days
    test_size: int = 126   # days
    adf_alpha: float = 0.05  # ADF significance level for spread stationarity
    
    # Signal generation parameters
    entry_z: float = 1.0
    exit_z: float = 0.25
    signal_method: str = 'tiered'  # 'static', 'rolling', 'rolling_scaled', 'rolling_stepwise', 'tiered'
    rolling_window: int = 60
    step: float = 0.25  # for stepwise signals
    scaling_factor: float = 1.0
    
    # Position sizing
    position_size: float = 14  # Dollar PnL per 1 spread point
    
    # Risk management
    max_position_per_pair: float = 1.0  # Maximum position size per pair
    max_portfolio_exposure: float = 0.5  # Maximum portfolio exposure (0.5 = 50%)
    volatility_lookback: int = 252  # Days for volatility calculation
    volatility_target: float = 0.15  # Target annual volatility (15%)
    
    # Transaction costs
    transaction_cost_bps: float = 5.0  # Transaction cost in basis points (0.05%)
    
    # Cointegration parameters
    cointegration_significance: float = 0.05
    
    # Performance calculation
    risk_free_rate: float = 0.02  # Annual risk-free rate for Sharpe calculation
    
    # Capital and sizing
    initial_capital: float = 100000  # Initial portfolio capital in dollars
    
    def __post_init__(self):
        """Validate configuration parameters after initialization."""
        self._validate()
    
    def _validate(self):
        """Validate all configuration parameters."""
        errors = []
        
        # Date validation
        try:
            from datetime import datetime
            datetime.strptime(self.start_date, '%Y-%m-%d')
            datetime.strptime(self.end_date, '%Y-%m-%d')
        except ValueError:
            errors.append("start_date and end_date must be in 'YYYY-MM-DD' format")
        
        # Size validation
        if self.train_size <= 0:
            errors.append("train_size must be positive")
        if self.test_size <= 0:
            errors.append("test_size must be positive")
        if self.rolling_window <= 0:
            errors.append("rolling_window must be positive")
        if self.volatility_lookback <= 0:
            errors.append("volatility_lookback must be positive")
        
        # Z-score validation
        if self.entry_z <= 0:
            errors.append("entry_z must be positive")
        if self.exit_z <= 0:
            errors.append("exit_z must be positive")
        if self.exit_z >= self.entry_z:
            errors.append("exit_z must be less than entry_z")
        
        # Signal method validation
        valid_methods = ['static', 'rolling', 'rolling_scaled', 'rolling_stepwise', 'tiered']
        if self.signal_method not in valid_methods:
            errors.append(f"signal_method must be one of {valid_methods}")
        
        # Position sizing validation
        if self.position_size <= 0:
            errors.append("position_size must be positive")
        if self.max_position_per_pair <= 0:
            errors.append("max_position_per_pair must be positive")
        if self.max_portfolio_exposure <= 0 or self.max_portfolio_exposure > 1:
            errors.append("max_portfolio_exposure must be between 0 and 1")
        
        # Transaction costs validation
        if self.transaction_cost_bps < 0:
            errors.append("transaction_cost_bps must be non-negative")
        
        # Cointegration validation
        if self.cointegration_significance <= 0 or self.cointegration_significance >= 1:
            errors.append("cointegration_significance must be between 0 and 1")
        
        # Risk-free rate validation
        if self.risk_free_rate < 0:
            errors.append("risk_free_rate must be non-negative")
        
        # Initial capital validation
        if self.initial_capital <= 0:
            errors.append("initial_capital must be positive")
        
        # Raise errors if any found
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors)
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info("Configuration validation passed")
    
    def to_dict(self) -> Dict:
        """Convert configuration to dictionary format."""
        return {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'tickers': self.tickers,
            'train_size': self.train_size,
            'test_size': self.test_size,
            'adf_alpha': self.adf_alpha,
            'entry_z': self.entry_z,
            'exit_z': self.exit_z,
            'signal_method': self.signal_method,
            'rolling_window': self.rolling_window,
            'step': self.step,
            'scaling_factor': self.scaling_factor,
            'position_size': self.position_size,
            'max_position_per_pair': self.max_position_per_pair,
            'max_portfolio_exposure': self.max_portfolio_exposure,
            'volatility_lookback': self.volatility_lookback,
            'volatility_target': self.volatility_target,
            'transaction_cost_bps': self.transaction_cost_bps,
            'cointegration_significance': self.cointegration_significance,
            'risk_free_rate': self.risk_free_rate,
            'initial_capital': self.initial_capital
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict) -> 'TradingConfig':
        """Create configuration from dictionary."""
        return cls(**config_dict)
    
    def update(self, **kwargs) -> 'TradingConfig':
        """Create a new configuration with updated parameters."""
        new_config = self.to_dict()
        new_config.update(kwargs)
        return self.from_dict(new_config)


def create_default_config() -> TradingConfig:
    """Create a default configuration for testing."""
    from config.data_params import sector_tickers
    
    # Get all tickers from sectors
    all_tickers = []
    for sector, tickers in sector_tickers.items():
        all_tickers.extend(tickers)
    
    return TradingConfig(
        start_date="2021-01-01",
        end_date="2025-07-01",
        tickers=all_tickers,
        train_size=504,
        test_size=126,
        adf_alpha=0.05,
        entry_z=1.0,
        exit_z=0.25,
        signal_method='tiered',
        rolling_window=60,
        scaling_factor=1.0,
        position_size=14,
        initial_capital=100000
    ) 