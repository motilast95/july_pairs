import numpy as np
import pandas as pd
import itertools
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

# Import your modules
from config.trading_config import create_default_config
from src.data.data_loader import load_prices, load_sector_tickers
from src.data.pair_selection import select_pairs
from src.models.model_fitting import fit_spread
from src.trading.walk_forward import walk_forward
from src.analysis.portfolio_analysis import aggregate_portfolio_pnl

def run_diagnostic_analysis():
    print("=" * 80)
    print("PAIRS TRADING DIAGNOSTIC REPORT")
    print("=" * 80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Load data
    print("Loading data...")
    prices = load_prices("data/prices.csv")
    sector_tickers = load_sector_tickers("config/data_params.py")
    config = create_default_config()
    
    print(f"Data loaded: {len(prices)} days, {len(prices.columns)} tickers")
    print(f"Date range: {prices.index[0]} to {prices.index[-1]}")
    print()
    
    # 1. Data Quality Analysis
    print("1. DATA QUALITY ANALYSIS")
    print("-" * 40)
    
    # Check missing data
    missing_pct = (prices.isnull().sum() / len(prices)) * 100
    print(f"Missing data: {missing_pct.mean():.1f}% average, {missing_pct.max():.1f}% max")
    
    # Check for price anomalies
    returns = prices.pct_change().dropna()
    extreme_returns = (returns.abs() > 0.1).sum()
    print(f"Extreme moves (>10%): {extreme_returns.sum()} total")
    print()
    
    # 2. Pair Selection Analysis
    print("2. PAIR SELECTION ANALYSIS")
    print("-" * 40)
    
    # Test cointegration for all possible pairs
    all_pairs = []
    cointegrated_pairs = []
    
    for sector, tickers in sector_tickers.items():
        sector_prices = prices[tickers].dropna(axis=1, how="any")
        sector_pairs = list(itertools.combinations(sector_prices.columns, 2))
        all_pairs.extend(sector_pairs)
        
        sector_cointegrated = []
        for t1, t2 in sector_pairs:
            series1 = sector_prices[t1]
            series2 = sector_prices[t2]
            
            if len(series1) < 252:  # Need at least 1 year
                continue
                
            try:
                from statsmodels.tsa.stattools import coint
                score, pvalue, _ = coint(series1, series2)
                
                if pvalue < config.cointegration_significance:
                    sector_cointegrated.append((t1, t2, pvalue))
                    cointegrated_pairs.append((t1, t2, pvalue))
                    
            except Exception as e:
                continue
        
        print(f"{sector}: {len(sector_cointegrated)}/{len(sector_pairs)} pairs cointegrated ({len(sector_cointegrated)/len(sector_pairs)*100:.1f}%)")
    
    print(f"\nOverall: {len(cointegrated_pairs)}/{len(all_pairs)} pairs cointegrated ({len(cointegrated_pairs)/len(all_pairs)*100:.1f}%)")
    
    # Analyze cointegration quality
    if cointegrated_pairs:
        pvalues = [p[2] for p in cointegrated_pairs]
        strong_pairs = len([p for p in pvalues if p < 0.01])
        weak_pairs = len([p for p in pvalues if p > 0.02])
        print(f"Strong pairs (p<0.01): {strong_pairs}")
        print(f"Weak pairs (p>0.02): {weak_pairs}")
    print()
    
    # 3. Model Fitting Analysis
    print("3. MODEL FITTING ANALYSIS")
    print("-" * 40)
    
    # Test model fitting on sample pairs
    sample_pairs = []
    for sector, tickers in sector_tickers.items():
        sector_prices = prices[tickers].dropna(axis=1, how="any")
        if len(sector_prices.columns) >= 2:
            sample_pairs.extend(list(itertools.combinations(sector_prices.columns, 2))[:2])
    
    fitted_models = []
    for t1, t2 in sample_pairs[:10]:  # Test 10 pairs
        try:
            end_idx = len(prices) - 1
            start_idx = max(0, end_idx - 504)  # 2 years
            window = slice(start_idx, end_idx)
            
            model_result = fit_spread((t1, t2), prices, window)
            if model_result:
                fitted_models.append({
                    "pair": (t1, t2),
                    "beta": model_result["beta"],
                    "r_squared": model_result.get("r_squared", 0),
                    "spread_std": model_result["spread_std"]
                })
                
        except Exception as e:
            continue
    
    print(f"Models fitted: {len(fitted_models)}")
    
    if fitted_models:
        r_squared_values = [m["r_squared"] for m in fitted_models]
        beta_values = [m["beta"] for m in fitted_models]
        
        print(f"Average R²: {np.mean(r_squared_values):.3f}")
        print(f"Poor fits (R²<0.3): {len([r for r in r_squared_values if r < 0.3])}")
        print(f"Good fits (R²>0.7): {len([r for r in r_squared_values if r > 0.7])}")
        print(f"Beta range: {min(beta_values):.2f} to {max(beta_values):.2f}")
        print(f"Extreme betas (|β|>3): {len([b for b in beta_values if abs(b) > 3])}")
    print()
    
    # 4. Performance Analysis
    print("4. PERFORMANCE ANALYSIS")
    print("-" * 40)
    
    try:
        # Use shorter period for analysis
        test_config = config.update(
            start_date="2023-01-01",
            end_date="2024-06-30",
            train_size=252,
            test_size=126
        )
        
        results = walk_forward(prices, sector_tickers, test_config.to_dict())
        
        if results:
            all_trades = []
            for res in results:
                all_trades.extend(res.get("trades", []))
            
            if all_trades:
                trades_df = pd.DataFrame(all_trades)
                
                print(f"Total trades: {len(trades_df)}")
                print(f"Win rate: {len(trades_df[trades_df['net_pnl'] > 0]) / len(trades_df) * 100:.1f}%")
                print(f"Average holding period: {trades_df['holding_period'].mean():.1f} days")
                print(f"Quick exits (1 day): {len(trades_df[trades_df['holding_period'] <= 1])}")
                
                winning_trades = trades_df[trades_df["net_pnl"] > 0]
                losing_trades = trades_df[trades_df["net_pnl"] < 0]
                
                if len(winning_trades) > 0 and len(losing_trades) > 0:
                    profit_factor = abs(winning_trades["net_pnl"].sum() / losing_trades["net_pnl"].sum())
                    print(f"Profit factor: {profit_factor:.2f}")
                
                # Portfolio performance
                portfolio_pnl = aggregate_portfolio_pnl(results)
                if len(portfolio_pnl) > 0:
                    total_return = portfolio_pnl.sum()
                    daily_returns = portfolio_pnl / config.initial_capital
                    volatility = daily_returns.std() * np.sqrt(252)
                    sharpe_ratio = (daily_returns.mean() * 252) / volatility if volatility > 0 else 0
                    
                    print(f"Total return: ${total_return:,.2f}")
                    print(f"Sharpe ratio: {sharpe_ratio:.2f}")
                    print(f"Annualized volatility: {volatility:.1%}")
    
    except Exception as e:
        print(f"Performance analysis failed: {e}")
    
    print()
    
    # 5. Key Issues and Recommendations
    print("5. KEY ISSUES AND RECOMMENDATIONS")
    print("-" * 40)
    
    issues = []
    
    # Check cointegration rate
    if len(cointegrated_pairs) / len(all_pairs) < 0.1:
        issues.append("Low cointegration rate - consider relaxing significance threshold")
    
    # Check model quality
    if fitted_models and np.mean([m["r_squared"] for m in fitted_models]) < 0.5:
        issues.append("Poor model fits - consider longer training periods or alternative models")
    
    # Check trade frequency
    if all_trades and len(all_trades) < 50:
        issues.append("Very few trades - consider adjusting entry/exit thresholds")
    
    # Check holding periods
    if all_trades and trades_df["holding_period"].mean() < 3:
        issues.append("Very short holding periods - consider longer exit criteria")
    
    # Check win rate
    if all_trades and len(trades_df[trades_df["net_pnl"] > 0]) / len(trades_df) < 0.4:
        issues.append("Low win rate - consider adjusting signal generation")
    
    for i, issue in enumerate(issues, 1):
        print(f"{i}. {issue}")
    
    if not issues:
        print("No major issues identified. Strategy may need parameter tuning.")
    
    print()
    print("=" * 80)

# Run the diagnostic
if __name__ == "__main__":
    run_diagnostic_analysis() 