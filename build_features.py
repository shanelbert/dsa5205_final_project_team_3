import pandas as pd

from download_data import OUTPUT_DIR as DATA_DIR


OUTPUT_DIR = DATA_DIR / "prepared"
FEATURE_COLUMNS = [
    "return_1d",
    "return_5d",
    "return_20d",
    "ma_gap_20d",
    "volatility_20d",
    "intraday_range",
    "volume_ratio_20d",
]
SPLIT_PERIODS = {
    "train": ("2011-01-01", "2018-12-31"),
    "validation": ("2019-01-01", "2021-12-31"),
    "test": ("2022-01-01", "2025-12-31"),
}


def make_features(frame: pd.DataFrame, calendar: pd.DatetimeIndex) -> pd.DataFrame:
    frame = frame.set_index("Date").reindex(calendar)
    close = frame["Adj Close"]
    features = pd.DataFrame({"return_1d": close / close.shift(1) - 1})

    for window in (5, 20):
        features[f"return_{window}d"] = close / close.shift(window) - 1

    features["ma_gap_20d"] = close / close.rolling(20).mean() - 1
    features["volatility_20d"] = features["return_1d"].rolling(20).std()
    features["intraday_range"] = (frame["High"] - frame["Low"]) / frame["Close"]
    features["volume_ratio_20d"] = (
        frame["Volume"] / frame["Volume"].rolling(20).mean() - 1
    )
    return features


def assign_splits(data: pd.DataFrame) -> pd.DataFrame:
    data = data.assign(split="excluded")
    for name, (start, end) in SPLIT_PERIODS.items():
        mask = data["Date"].between(start, end) & data["exit_date"].le(
            pd.Timestamp(end)
        )
        data.loc[mask, "split"] = name
    return data


def main() -> None:
    prices = pd.read_csv(OUTPUT_DIR / "clean_prices.csv", parse_dates=["Date"])
    targets = pd.read_csv(
        OUTPUT_DIR / "stock_targets.csv",
        parse_dates=["Date", "entry_date", "exit_date"],
    )
    calendar = pd.DatetimeIndex(
        pd.to_datetime(
            pd.read_csv(DATA_DIR / "SPY_2011_2025.csv", usecols=["Date"])["Date"]
        ),
        name="Date",
    ).sort_values()

    feature_frames = []
    for symbol, frame in prices.loc[prices["Ticker"].ne("SPY")].groupby("Ticker"):
        features = make_features(frame, calendar).assign(Ticker=symbol).reset_index()
        feature_frames.append(features)

    features = pd.concat(feature_frames, ignore_index=True).dropna(
        subset=FEATURE_COLUMNS
    )
    label_columns = ["Date", "Ticker", "entry_date", "exit_date", "target_return"]
    data = features.merge(targets[label_columns], on=["Date", "Ticker"])
    data = data.loc[
        :,
        [
            "Date",
            "Ticker",
            "entry_date",
            "exit_date",
            *FEATURE_COLUMNS,
            "target_return",
        ],
    ]
    data = assign_splits(data).sort_values(["Date", "Ticker"])
    data.to_csv(OUTPUT_DIR / "model_data.csv", index=False, date_format="%Y-%m-%d")

    for name, (start, end) in SPLIT_PERIODS.items():
        subset = data.loc[data["split"].eq(name)]
        subset.to_csv(OUTPUT_DIR / f"{name}.csv", index=False, date_format="%Y-%m-%d")
        print(f"{name}: {start} to {end}, {len(subset)} rows", flush=True)

    excluded = data["split"].eq("excluded").sum()
    print(
        f"Total samples with features and targets: {len(data)}; "
        f"excluded at split boundaries: {excluded}"
    )


if __name__ == "__main__":
    main()
