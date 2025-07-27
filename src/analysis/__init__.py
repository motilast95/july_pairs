"""
Analysis and performance evaluation modules.

This module contains:
- portfolio_analysis: Portfolio-level performance metrics
- performance: Performance calculation utilities
- diagnostic_analysis: Strategy diagnostic tools
"""

from .portfolio_analysis import aggregate_portfolio_pnl, compute_portfolio_metrics
from .performance import (
    time_function, 
    time_block, 
    print_performance_summary, 
    export_performance_metrics,
    performance_monitor
)

__all__ = [
    'aggregate_portfolio_pnl', 
    'compute_portfolio_metrics',
    'time_function',
    'time_block', 
    'print_performance_summary',
    'export_performance_metrics',
    'performance_monitor'
] 