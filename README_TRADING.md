# Trading and evaluation (Group 3)

Put `strategy.py`, `backtest.py`, `evaluation.py` in the repository root. Use the team's existing `data/prepared/forecasts.csv`, `stock_targets.csv`, and `clean_prices.csv`.

From the repository root run:

```bash
python evaluation.py
```

This does **not** retrain the model. It evaluates the exported LASSO forecasts. If the LASSO forecasts change, regenerate `forecasts.csv` from the modelling notebook first.

The code searches 12 predefined combinations of threshold (0, 0.001, 0.002), scale (50, 100), and per-stock cap (0.2, 0.3). It selects the highest validation-period Sharpe, then applies the selected parameters once to the test period. Validation: 2012–2017; test: 2018–2025. Validation returns are required to be realized by the end of 2017. The periods are treated as independent backtests, each starting in cash and liquidating at the end.

Trading uses next-open to following-open adjusted returns, long-only, at most 100% total equity exposure, zero return on idle cash, and 0.1% fee per traded notional. Fee calculations use a simplified wealth deduction and proportional rescaling of target holdings. SPY is an adjusted-open buy-and-hold comparison without brokerage fees. Sharpe assumes risk-free rate zero. This is a research backtest, not a detailed execution simulator.

Outputs under `results/`: `validation_grid.csv`, `performance.csv`, validation/test daily returns, weights and cumulative wealth charts.

**Research integrity:** The test period was inspected before this parameter search was finalized. The final report should disclose this as exploratory work and avoid claiming the parameter search was fully pre-registered or that the resulting test is a pristine untouched holdout. Do not use test performance to change the grid or selection criterion.

## Selected Parameters and Results

The trading parameters were selected by maximizing the Sharpe ratio
over 12 predefined combinations on the 2012–2017 validation period.

Selected parameters:

| Parameter | Value |
|---|---:|
| Prediction threshold | 0 |
| Proportional scale | 100 |
| Maximum weight per stock | 0.30 |
| Transaction fee | 0.001 |

The selected parameters were kept fixed for the 2018–2025 test period.

### Performance Summary

| Metric | Strategy | SPY Buy & Hold |
|---|---:|---:|
| Annualized return | 26.14% | 14.26% |
| Annualized volatility | 26.28% | 18.67% |
| Sharpe ratio (rf = 0) | 1.0157 | 0.8080 |
| Maximum drawdown | -35.21% | -32.05% |
| Cumulative return | 536.94% | 189.47% |

These results are calculated using the provided historical data
and the stated backtesting assumptions. The strategy achieves
higher returns and Sharpe ratio than SPY, but also exhibits
higher volatility and a larger maximum drawdown.