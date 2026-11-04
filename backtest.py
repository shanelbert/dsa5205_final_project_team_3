"""Open-to-open backtest, with transaction fees on executed turnover."""

from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent / "data" / "prepared"


def load_targets(path=DATA_DIR / "stock_targets.csv"):
    return pd.read_csv(path, parse_dates=["Date", "entry_date", "exit_date"])


def run_backtest(
    weights: pd.DataFrame,
    targets: pd.DataFrame,
    fee: float = 0.001,
    initial_weights=None,
    liquidate_last: bool = True,
) -> pd.DataFrame:
    """Weights indexed by *signal* date. Costs charged at entry opens.

    Prior positions drift with returns before next rebalance. Fees paid from
    portfolio cash; after fees, exposures are proportionally scaled. Returns
    are gross open-to-open total returns supplied in stock_targets.csv.
    """
    if fee < 0 or fee >= 1:
        raise ValueError("fee must be between 0 and 1")
    if weights.empty:
        raise ValueError("No weights")

    weights = weights.sort_index().copy()
    weights.index = pd.to_datetime(weights.index)

    if weights.isna().any().any():
        raise ValueError("Missing portfolio weights")
    if weights.index.has_duplicates:
        raise ValueError("Duplicate signal dates")
    if (weights.fillna(0) < 0).any().any() or (
        weights.fillna(0).sum(axis=1) > 1 + 1e-8
    ).any():
        raise ValueError("Long-only weights must sum to at most 1")

    tickers = list(weights.columns)
    subset = targets[targets["Ticker"].isin(tickers)]
    returns = subset.pivot(
        index="Date", columns="Ticker", values="target_return"
    ).reindex(index=weights.index, columns=tickers)
    entries = subset.groupby("Date")["entry_date"].first().reindex(weights.index)
    exits = subset.groupby("Date")["exit_date"].first().reindex(weights.index)

    if returns.isna().any().any() or entries.isna().any() or exits.isna().any():
        raise ValueError("Missing actual return or trading date for some predictions")
    if not (
        entries.iloc[1:].reset_index(drop=True)
        == exits.iloc[:-1].reset_index(drop=True)
    ).all():
        raise ValueError(
            "Nonconsecutive holding periods: do not silently carry positions across gaps"
        )

    previous = (
        pd.Series(0.0, index=tickers)
        if initial_weights is None
        else pd.Series(initial_weights).reindex(tickers).fillna(0.0)
    )
    if (previous < 0).any() or previous.sum() > 1 + 1e-8:
        raise ValueError("Invalid initial positions")

    records = []
    for date in weights.index:
        target = weights.loc[date].fillna(0).astype(float)

        # Calculate trading costs on the pre-trade portfolio value.
        turnover = (target - previous).abs().sum()
        cost = fee * turnover
        if cost >= 1:
            raise ValueError("Trading costs exceed portfolio value")

        # Simplified fee convention: charge fee against wealth at each rebalance,
        # then invest the remaining wealth at the target portfolio weights.
        r = returns.loc[date].astype(float)
        gross = float((target * r).sum())
        net = (1 - cost) * (1 + gross) - 1
        wealth_factor = 1 + gross
        if wealth_factor <= 0:
            raise ValueError("Nonpositive portfolio wealth")

        # Drift target weights to next open; fee scales all assets and cash equally,
        # so it cancels from this normalized weight calculation.
        previous = target * (1 + r) / wealth_factor

        records.append(
            {
                "Date": date,
                "entry_date": entries.loc[date],
                "exit_date": exits.loc[date],
                "gross_return": gross,
                "turnover": turnover,
                "cost": cost,
                "net_return": net,
                "exposure": float(target.sum()),
            }
        )

    out = pd.DataFrame(records).set_index("Date")

    if liquidate_last:
        # Closing the positions at the final exit open costs one more turnover fee.
        final_turnover = float(previous.abs().sum())
        out.loc[out.index[-1], "exit_cost"] = fee * final_turnover
        out["exit_cost"] = out["exit_cost"].fillna(0.0)

        out.loc[out.index[-1], "net_return"] = (1 + out.iloc[-1]["net_return"]) * (
            1 - fee * final_turnover
        ) - 1
    else:
        out["exit_cost"] = 0.0

    out["wealth"] = (1 + out["net_return"]).cumprod()
    return out


def spy_benchmark(clean_prices: pd.DataFrame, entries, exits) -> pd.Series:
    """SPY adjusted-open total return for exactly the same holding intervals."""
    spy = clean_prices.loc[clean_prices["Ticker"].eq("SPY")].copy()
    spy["Date"] = pd.to_datetime(spy["Date"])
    spy = spy.set_index("Date").sort_index()

    adj_open = spy["Open"] * spy["Adj Close"] / spy["Close"]
    start = adj_open.reindex(pd.to_datetime(entries)).to_numpy()
    end = adj_open.reindex(pd.to_datetime(exits)).to_numpy()

    if np.isnan(start).any() or np.isnan(end).any():
        raise ValueError("SPY price missing at entry or exit")

    return pd.Series(end / start - 1, index=entries.index, name="SPY")
