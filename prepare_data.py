import pandas as pd

from download_data import COLUMNS, OUTPUT_DIR as DATA_DIR, SYMBOLS


OUTPUT_DIR = DATA_DIR / "prepared"
PRICE_COLUMNS = ["Open", "High", "Low", "Close", "Adj Close"]


def clean_prices(frame: pd.DataFrame, calendar: pd.DatetimeIndex) -> pd.DataFrame:
    frame = frame.loc[:, ["Date", *COLUMNS]]
    frame["Date"] = pd.to_datetime(frame["Date"], errors="coerce")
    frame = frame.sort_values("Date", kind="stable").drop_duplicates(
        "Date", keep="last"
    )
    frame[COLUMNS] = frame[COLUMNS].apply(pd.to_numeric, errors="coerce")
    frame = frame.replace([float("inf"), float("-inf")], float("nan"))
    frame = frame.dropna().set_index("Date")

    valid = (
        frame.index.isin(calendar)
        & frame[PRICE_COLUMNS].gt(0).all(axis=1)
        & frame["Volume"].gt(0)
        & frame["High"].ge(frame[["Open", "Close"]].max(axis=1))
        & frame["Low"].le(frame[["Open", "Close"]].min(axis=1))
    )
    return frame.loc[valid]


def make_targets(
    symbol: str, frame: pd.DataFrame, calendar: pd.DatetimeIndex
) -> pd.DataFrame:
    next_date = pd.Series(calendar, index=calendar).shift(-1)
    next_prices = frame[["Open", "Close"]].reindex(calendar).shift(-1)
    targets = pd.DataFrame(
        {
            "Ticker": symbol,
            "entry_date": next_date,
            "exit_date": next_date,
            "entry_open": next_prices["Open"],
            "exit_close": next_prices["Close"],
            "target_return": next_prices["Close"] / next_prices["Open"] - 1,
        },
        index=calendar,
    )
    targets = targets.loc[targets.index.isin(frame.index)].dropna()
    return targets.reset_index()


def main() -> None:
    raw_frames = {
        symbol: pd.read_csv(DATA_DIR / f"{symbol}_2011_2025.csv") for symbol in SYMBOLS
    }
    calendar = pd.DatetimeIndex(
        pd.to_datetime(raw_frames["SPY"]["Date"], errors="coerce").dropna().unique(),
        name="Date",
    ).sort_values()

    clean_frames = []
    target_frames = []
    for symbol, raw in raw_frames.items():
        frame = clean_prices(raw, calendar)
        clean_frames.append(frame.assign(Ticker=symbol).reset_index())
        print(
            f"{symbol}: {len(raw)} downloaded rows, {len(frame)} cleaned rows",
            flush=True,
        )

        if symbol != "SPY":
            targets = make_targets(symbol, frame, calendar)
            target_frames.append(targets)
            print(f"  Valid targets: {len(targets)} rows", flush=True)

    prices = pd.concat(clean_frames, ignore_index=True)
    prices = prices.loc[:, ["Date", "Ticker", *COLUMNS]].sort_values(["Date", "Ticker"])
    targets = pd.concat(target_frames, ignore_index=True).sort_values(
        ["Date", "Ticker"]
    )

    OUTPUT_DIR.mkdir(exist_ok=True)
    prices.to_csv(OUTPUT_DIR / "clean_prices.csv", index=False, date_format="%Y-%m-%d")
    targets.to_csv(
        OUTPUT_DIR / "stock_targets.csv", index=False, date_format="%Y-%m-%d"
    )
    print(
        f"Completed: {len(prices)} clean price rows, {len(targets)} stock targets, "
        f"saved to {OUTPUT_DIR.relative_to(DATA_DIR.parent)}/"
    )


if __name__ == "__main__":
    main()
