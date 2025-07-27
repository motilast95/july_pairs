# Documentation Index

## 📚 Documentation Overview

This directory contains comprehensive documentation for the pairs trading system, organized for easy navigation and reference.

## 📖 Core Documentation

### [README.md](README.md) - Main System Overview
**Purpose**: High-level system overview and quick start guide  
**Content**: 
- Quick start commands
- System features and performance
- Default universe (60 stocks)
- Key insights and mission accomplished

**Best for**: New users, system overview, quick reference

### [TECHNICAL_GUIDE.md](TECHNICAL_GUIDE.md) - Technical Deep Dive
**Purpose**: Comprehensive technical documentation  
**Content**:
- System architecture and components
- Core modules and their functions
- Configuration system details
- Performance optimizations
- Signal generation methods
- Risk management system
- Development workflow

**Best for**: Developers, technical implementation, system understanding

## 🛠️ Usage Guides

### [CLI_USAGE.md](CLI_USAGE.md) - Command Line Interface Reference
**Purpose**: Complete CLI reference and examples  
**Content**:
- All CLI arguments and options
- Usage examples for different scenarios
- Parameter explanations
- Advanced usage patterns

**Best for**: Command line usage, parameter reference, examples

### [PERFORMANCE_MONITORING_USAGE.md](PERFORMANCE_MONITORING_USAGE.md) - Performance Monitoring Guide
**Purpose**: Performance monitoring system usage  
**Content**:
- How to enable/disable performance monitoring
- Understanding timing data
- Optimization workflow
- Best practices

**Best for**: Performance optimization, debugging, system tuning

### [STRATEGY_ADVANTAGES.md](STRATEGY_ADVANTAGES.md) - Strategy Advantages & Market Performance
**Purpose**: Comprehensive analysis of strategy advantages vs. market benchmarks  
**Content**:
- Risk-adjusted performance analysis
- Benchmark comparison results
- Strategic advantages and investment thesis
- Target applications and use cases

**Best for**: Strategy evaluation, investment decisions, performance presentation

### [VISUALIZATION_GUIDE.md](VISUALIZATION_GUIDE.md) - Strategy Visualization System
**Purpose**: Complete guide to creating professional strategy visualizations  
**Content**:
- Interactive dashboard creation
- Performance comparison charts
- Trading activity analysis
- Benchmark comparison tables
- HTML summary reports
- Best practices for showcasing

**Best for**: Strategy showcasing, client presentations, performance reporting

## 📈 Progress and Development

### [progress/2025-07-27.md](progress/2025-07-27.md) - Development Progress Log
**Purpose**: Complete development history and achievements  
**Content**:
- Day-by-day development progress
- Key breakthroughs and insights
- Performance benchmarks
- System evolution

**Best for**: Understanding system development, historical context

## 🎯 Quick Navigation

### For New Users
1. Start with [README.md](README.md) for system overview
2. Use [CLI_USAGE.md](CLI_USAGE.md) for command reference
3. Check [progress/2025-07-27.md](progress/2025-07-27.md) for latest achievements

### For Developers
1. Read [TECHNICAL_GUIDE.md](TECHNICAL_GUIDE.md) for system architecture
2. Reference [CLI_USAGE.md](CLI_USAGE.md) for implementation details
3. Use [PERFORMANCE_MONITORING_USAGE.md](PERFORMANCE_MONITORING_USAGE.md) for optimization

### For Performance Analysis
1. Review [progress/2025-07-27.md](progress/2025-07-27.md) for performance benchmarks
2. Use [PERFORMANCE_MONITORING_USAGE.md](PERFORMANCE_MONITORING_USAGE.md) for monitoring
3. Check [TECHNICAL_GUIDE.md](TECHNICAL_GUIDE.md) for optimization strategies

### For Strategy Evaluation
1. Read [STRATEGY_ADVANTAGES.md](STRATEGY_ADVANTAGES.md) for comprehensive analysis
2. Run benchmark comparisons with `--benchmark` flag
3. Create visualizations with `--visualize` flag
4. Use standalone analysis script for detailed comparisons

## 📊 System Performance Summary

### Default System (Mega-Cap Universe)
- **Total Return**: 25.04% over 5.5 years (2020-2025)
- **Sharpe Ratio**: 1.266 (excellent risk-adjusted returns)
- **Max Drawdown**: 7.38% (manageable risk)
- **Annualized Return**: 7.71%

### Key Features
- **60 Stocks**: 6 sectors × 10 stocks each
- **Fast Execution**: 10x speedup from optimizations
- **Flexible CLI**: Comprehensive parameter control
- **Multiple Universes**: Mega-cap, mid-cap, custom
- **Production Ready**: Robust, tested, documented

## 🚀 Quick Start Commands

### Default System
```bash
python main.py backtest --start-date 2020-01-01 --end-date 2025-07-01 --signal-method rolling --entry-z 1.5 --exit-z 0.5 --risk-management-mode disabled
```

### With Benchmark Comparison
```bash
python main.py backtest --start-date 2020-01-01 --end-date 2025-07-01 --signal-method rolling --entry-z 1.5 --exit-z 0.5 --risk-management-mode disabled --benchmark
```

### With Visualizations
```bash
python main.py backtest --start-date 2020-01-01 --end-date 2025-07-01 --signal-method rolling --entry-z 1.5 --exit-z 0.5 --risk-management-mode disabled --benchmark --visualize
```

### Mid-Cap Experiment
```bash
python main.py backtest --universe mid_cap --start-date 2020-01-01 --end-date 2024-01-01 --signal-method rolling --entry-z 1.5 --exit-z 0.5 --risk-management-mode disabled
```

### Cache Management
```bash
python main.py cache clear
```

## 📝 Documentation Maintenance

### Adding New Documentation
1. Create new markdown file in appropriate directory
2. Update this index with new entry
3. Cross-reference with existing documentation
4. Maintain consistent formatting and style

### Documentation Standards
- Use clear, descriptive titles
- Include purpose and content summary
- Cross-reference related documents
- Keep examples up-to-date with current system

---

**Last Updated**: July 27, 2025  
**System Version**: Production Ready  
**Performance**: 1.266 Sharpe Ratio Achieved 