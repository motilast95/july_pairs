"""
Model fitting and signal generation modules.

This module contains:
- model_fitting: Spread modeling and beta estimation
- signal_generation: Trading signal generation logic
"""

from .model_fitting import fit_spread
from .signal_generation import generate_signals

__all__ = ['fit_spread', 'generate_signals'] 