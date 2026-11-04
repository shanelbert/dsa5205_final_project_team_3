# Data and Features

This repository provides the data prepared for our team's modelling and backtesting work. The trading assets are Apple (`AAPL`), NVIDIA (`NVDA`), Microsoft (`MSFT`), and Tesla (`TSLA`). `SPY` is the buy-and-hold benchmark and is not included in the stock prediction datasets.

The downloaded snapshot covers **2011-01-03 to 2025-12-31**, at daily frequency. Prices are in USD, and dates refer to New York trading days.

- **For modelling:** use `train.csv`, `validation.csv`, and `test.csv` in `data/prepared/`.
- **For backtesting:** use `stock_targets.csv` for the entry and exit prices and `clean_prices.csv` for the full price history and SPY benchmark.

## Files

| File | What it contains or does |
|---|---|
| [`download_data.py`](download_data.py) | Downloads daily prices, volume, dividends, and stock splits for all five assets using yfinance. |
| [`prepare_data.py`](prepare_data.py) | Cleans the downloaded records and creates the open-to-open return labels. |
| [`build_features.py`](build_features.py) | Builds seven historical features for each stock and creates the chronological data splits. |
| [`requirements.txt`](requirements.txt) | Package versions used by these scripts. |
| `data/{TICKER}_2011_2025.csv` | The downloaded snapshot, before project cleaning: one CSV per asset, with 3,772 rows each. |
| [`data/prepared/clean_prices.csv`](data/prepared/clean_prices.csv) | Cleaned daily prices and corporate actions for all five assets: 18,860 rows. |
| [`data/prepared/stock_targets.csv`](data/prepared/stock_targets.csv) | Entry prices, exit prices, and return labels for the four stocks: 15,080 rows. |
| [`data/prepared/model_data.csv`](data/prepared/model_data.csv) | Features joined with labels and split assignments: 15,000 rows, including 16 rows marked `excluded`. |
| `data/prepared/train.csv`, `validation.csv`, `test.csv` | The ready-to-use modelling subsets, described under Time splits below. |

Stock datasets use a long format: each row represents one **`(Date, Ticker)`** observation. The files combine all four stocks, so they can also be filtered by `Ticker` for separate stock models.

## What one prediction means

For a row dated `t`:

1. Use information available after the close of trading day `t` to generate a signal.
2. Enter at the open of the next trading day, `t+1`.
3. Hold overnight and exit at the open of the following trading day, `t+2`.

The prediction target is:

```text
target_return[t] = AdjOpen[t+2] / AdjOpen[t+1] - 1,   where AdjOpen = Open * Adj Close / Close
```

Returns are decimals: `0.01` means a 1% return. This is the stock's gross long return, including dividends, before transaction costs or any portfolio position rule. `t+1` and `t+2` are the next two trading days, including across weekends and holidays.

| Column | Meaning |
|---|---|
| `Date` | The signal date in target and modelling tables. In price tables, it is the date of the price record. |
| `Ticker` | The asset identifier. |
| `entry_date` | The next trading day, `t+1`; entry takes place at its open. |
| `exit_date` | The trading day after `entry_date`, `t+2`; exit takes place at its open. |
| `entry_open` | The `Open` on `entry_date`, available in `stock_targets.csv`. |
| `exit_open` | The `Open` on `exit_date`, available in `stock_targets.csv`. |
| `target_return` | The return from `entry_open` to `exit_open`, plus any dividend whose ex-dividend date is `exit_date`. On those days (167 of the 15,080 targets) it is slightly higher than `exit_open / entry_open - 1`. |
| `split` | `train`, `validation`, `test`, or `excluded`. Present in the modelling tables. |

For backtesting, join predictions to `stock_targets.csv` on **`Date` and `Ticker`**. Execute on `entry_date` and `exit_date`; `Date` itself is the earlier signal date. Holdings are back to back: signal `t` holds from the open of `t+1` to the open of `t+2`, and signal `t+1` takes over at that same open. A stock held for both signals is not sold and bought again; only the change in its weight is traded. For a SPY buy-and-hold benchmark over the same holding periods, compute SPY's open-to-open returns the same way, from `Open * Adj Close / Close` in `clean_prices.csv`.

## Price fields and cleaning

The download uses `auto_adjust=False`. Yahoo's `Open`, `High`, `Low`, and `Close` already account for stock splits. `Adj Close` additionally accounts for dividends. Historical return and moving-average features use `Adj Close`. The label needs opens that account for dividends too: Yahoo applies one adjustment factor to all prices of a day, so `Open * Adj Close / Close` is the dividend-adjusted open (the same price yfinance returns with `auto_adjust=True`). See the [yfinance price-adjustment documentation](https://ranaroussi.github.io/yfinance/advanced/price_adjustment.html).

- `Volume` is the share volume returned by Yahoo.
- `Dividends` records the supplier's dividend amount per share on the ex-dividend date, using its historical split-adjusted units; zero means no dividend event.
- `Stock Splits` records new shares divided by old shares. For example, `4` means a four-for-one split; zero means no split event.

Cleaning sorts dates, keeps the last record for duplicate dates, and removes records with missing or non-finite values, non-positive prices or volume, or inconsistent OHLC prices. Dates are aligned to the downloaded SPY trading calendar. Values are not filled or winsorized. No price records needed removal in the included snapshot.

## Features

Let `A[t]` be `Adj Close` and `r[t] = A[t] / A[t-1] - 1`. `mean20` is the mean of the latest 20 trading-day observations, including day `t`.

| Feature | Definition | Purpose |
|---|---|---|
| `return_1d` | `A[t] / A[t-1] - 1` | Captures the latest price move, for studying short-term continuation or reversal. |
| `return_5d` | `A[t] / A[t-5] - 1` | Captures the recent weekly trend. |
| `return_20d` | `A[t] / A[t-20] - 1` | Captures the recent monthly trend. |
| `ma_gap_20d` | `A[t] / mean20(A)[t] - 1` | Measures the price's position relative to its recent trend. |
| `volatility_20d` | Sample standard deviation of the latest 20 daily returns, with `ddof=1` | Describes the recent risk state; this is daily volatility, not annualized. |
| `intraday_range` | `(High[t] - Low[t]) / Close[t]` | Describes the current day's trading range. |
| `volume_ratio_20d` | `Volume[t] / mean20(Volume)[t] - 1` | Describes trading activity relative to its recent level. |

Features are calculated separately for each stock, using information through the close of `Date`. Windows follow the shared trading calendar, so a missing record does not turn a five-day window into a longer one. Features are stored without standardization.

## Time splits

The configured periods are **2011-2018 for training**, **2019-2021 for validation**, and **2022-2025 for testing**. Actual signal dates and row counts are:

| File | Signal date range | Rows | Rows per stock |
|---|---|---:|---:|
| [`train.csv`](data/prepared/train.csv) | 2011-02-01 to 2018-12-27 | 7,960 | 1,990 |
| [`validation.csv`](data/prepared/validation.csv) | 2019-01-02 to 2021-12-29 | 3,020 | 755 |
| [`test.csv`](data/prepared/test.csv) | 2022-01-03 to 2025-12-29 | 4,004 | 1,001 |

The first 20 trading days per stock are used for feature warm-up, and the final two source dates have no label, because their exit open falls after the snapshot. A sample enters a split only if its signal date belongs to that period and its label is realized by the period end. The 16 signals dated on the last two trading days of 2018 and 2021 (`2018-12-28`, `2018-12-31`, `2021-12-30`, `2021-12-31`) are therefore marked `excluded` in `model_data.csv` and omitted from the three split files.

## Using the prepared data

The scripts were run with Python 3.12. From the repository root, install the dependencies:

```bash
python -m pip install -r requirements.txt
```

A minimal modelling input example:

```python
import pandas as pd
from build_features import FEATURE_COLUMNS

train = pd.read_csv(
    "data/prepared/train.csv",
    parse_dates=["Date", "entry_date", "exit_date"],
)
X_train = train[FEATURE_COLUMNS]
y_train = train["target_return"]
```

Load the validation and test files in the same way. Use validation for model selection and test for the final evaluation. Fit preprocessing on the training observations. For rolling refits on signal date `t`, only historical samples with `exit_date <= t` have an observed label; the label of signal `t-1` is not known until the open of `t+1`.

## Rebuilding the data

The prepared CSVs are included, so teammates can use them directly. To rebuild them from the included downloaded snapshot:

```bash
python prepare_data.py
python build_features.py
```

To refresh the downloaded snapshot, run `python download_data.py` first. This replaces the five downloaded CSVs; Yahoo may revise historical prices, so a fresh download can differ from the included snapshot. Use the same snapshot for shared experiments.
