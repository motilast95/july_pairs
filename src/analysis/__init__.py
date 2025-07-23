"""
Analysis and performance evaluation modules.

This module contains:
- portfolio_analysis: Portfolio-level performance metrics
- performance: Performance calculation utilities
- diagnostic_analysis: Strategy diagnostic tools
"""

from .portfolio_analysis import aggregate_portfolio_pnl, compute_portfolio_metrics
from .performance import evaluate_performance

__all__ = ['aggregate_portfolio_pnl', 'compute_portfolio_metrics', 
           'evaluate_performance'] 