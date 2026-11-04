"""Select trading parameters on validation only; evaluate frozen strategy on test."""

from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from strategy import make_weights
from backtest import load_targets, run_backtest, spy_benchmark, DATA_DIR

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "results"
VALIDATION = ("2012-02-01", "2017-12-31")
TEST = ("2018-01-01", "2025-12-31")
FEE = 0.001  # 0.1% of traded notional, per side
THRESHOLDS = (0.0, 0.001, 0.002)
SCALES = (50.0, 100.0)
MAX_WEIGHTS = (0.20, 0.30)


def metrics(returns):
    r = returns.dropna().astype(float)
    if r.empty:
        raise ValueError("No returns for performance evaluation")

    wealth = pd.concat(
        [pd.Series([1.0]), (1 + r).cumprod().reset_index(drop=True)], ignore_index=True
    )

    years = len(r) / 252
    annual = float(wealth.iloc[-1] ** (1 / years) - 1)
    vol = float(r.std(ddof=1) * np.sqrt(252))
    sharpe = float(r.mean() * 252 / vol) if vol > 0 else np.nan

    drawdown = wealth / wealth.cummax() - 1
    return {
        "annual_return": annual,
        "annual_volatility": vol,
        "sharpe_rf0": sharpe,
        "max_drawdown": float(drawdown.min()),
        "cumulative_return": float(wealth.iloc[-1] - 1),
    }


def evaluate(predictions, targets, prices, name, params, last_exit=None):
    start, end = VALIDATION if name == "validation" else TEST
    p = predictions.loc[start:end].copy()
    if last_exit is not None:
        exit_dates = targets.groupby("Date")["exit_date"].first().reindex(p.index)
        p = p.loc[exit_dates.le(pd.Timestamp(last_exit)).fillna(False)]

    if p.empty:
        raise ValueError(f"No eligible predictions for {name}")

    weights = make_weights(p, **params)
    bt = run_backtest(weights, targets, fee=FEE, liquidate_last=True)

    spy = spy_benchmark(prices, bt["entry_date"], bt["exit_date"])
    bt["spy_return"] = spy
    return weights, bt


def main():
    OUTPUT.mkdir(exist_ok=True)

    fpath = DATA_DIR / "forecasts.csv"
    if not fpath.exists():
        raise FileNotFoundError(f"Missing {fpath}; export LASSO forecasts first")

    forecasts = pd.read_csv(fpath, parse_dates=["Date"])
    required = {"Date", "Ticker", "predicted_return"}
    if not required.issubset(forecasts.columns):
        raise ValueError(
            f"Missing forecast columns: {required - set(forecasts.columns)}"
        )
    if forecasts.duplicated(["Date", "Ticker"]).any():
        raise ValueError("Duplicate date/ticker predictions")

    predictions = forecasts.pivot(
        index="Date", columns="Ticker", values="predicted_return"
    ).sort_index()

    targets = load_targets()
    prices = pd.read_csv(DATA_DIR / "clean_prices.csv", parse_dates=["Date"])

    # All validation holding periods must be completed by the last trading day of 2017.
    # This prevents validation outcomes from crossing into the test calendar year.
    val_cutoff = pd.Timestamp("2017-12-31")
    candidates = []
    for threshold, scale, max_weight in product(THRESHOLDS, SCALES, MAX_WEIGHTS):
        params = dict(threshold=threshold, scale=scale, max_weight=max_weight)
        _, bt = evaluate(
            predictions, targets, prices, "validation", params, last_exit=val_cutoff
        )
        stat = metrics(bt["net_return"])
        candidates.append({**params, **stat})

    grid = pd.DataFrame(candidates).sort_values(
        ["sharpe_rf0", "threshold", "scale", "max_weight"],
        ascending=[False, True, True, True],
        kind="stable",
    )
    grid.to_csv(OUTPUT / "validation_grid.csv", index=False)

    best = grid.iloc[0]
    chosen = {k: float(best[k]) for k in ("threshold", "scale", "max_weight")}
    print("Validation-selected parameters:", chosen)
    print("Validation Sharpe:", round(float(best["sharpe_rf0"]), 4))

    rows = []
    for name in ("validation", "test"):
        weights, bt = evaluate(
            predictions,
            targets,
            prices,
            name,
            chosen,
            last_exit=val_cutoff if name == "validation" else None,
        )

        weights.to_csv(OUTPUT / f"{name}_weights.csv")
        bt.to_csv(OUTPUT / f"{name}_daily.csv")

        compare = pd.DataFrame(
            {"Strategy": bt["net_return"], "SPY Buy & Hold": bt["spy_return"]}
        )
        for label in compare.columns:
            rows.append({"period": name, "portfolio": label, **metrics(compare[label])})

        (1 + compare).cumprod().plot(
            title=f"{name.title()} cumulative wealth", figsize=(9, 5)
        )
        plt.ylabel("Wealth (initial = 1)")
        plt.tight_layout()
        plt.savefig(OUTPUT / f"{name}_cumulative.png", dpi=160)
        plt.close()

    summary = pd.DataFrame(rows)
    summary.to_csv(OUTPUT / "performance.csv", index=False)
    print(summary.round(4).to_string(index=False))
    print("Outputs saved to", OUTPUT)


if __name__ == "__main__":
    main()
