from pathlib import Path
import yfinance as yf


SYMBOLS = {
    "AAPL": "Apple",
    "NVDA": "NVIDIA",
    "MSFT": "Microsoft",
    "TSLA": "Tesla",
    "SPY": "SPDR S&P 500 ETF Trust",
}
START = "2011-01-01"
END_EXCLUSIVE = "2026-01-01"
TIMEZONE = "America/New_York"
OUTPUT_DIR = Path(__file__).resolve().parent / "data"
COLUMNS = [
    "Open",
    "High",
    "Low",
    "Close",
    "Adj Close",
    "Volume",
    "Dividends",
    "Stock Splits",
]
HISTORY_OPTIONS = {
    "start": START,
    "end": END_EXCLUSIVE,
    "interval": "1d",
    "actions": True,
    "auto_adjust": False,
    "keepna": True,
    "timeout": 30,
}


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    total_rows = 0

    for symbol, company in SYMBOLS.items():
        print(f"Downloading {symbol} ({company}) ...", flush=True)
        frame = yf.Ticker(symbol).history(**HISTORY_OPTIONS)
        if frame.empty:
            raise RuntimeError(f"{symbol}: no data downloaded")

        frame = frame.loc[:, COLUMNS]
        frame.index = frame.index.tz_convert(TIMEZONE).tz_localize(None)
        frame.index.name = "Date"
        destination = OUTPUT_DIR / f"{symbol}_2011_2025.csv"
        frame.to_csv(
            destination, date_format="%Y-%m-%d", encoding="utf-8", lineterminator="\n"
        )
        total_rows += len(frame)
        print(f"Saved {destination.name}: {len(frame)} rows", flush=True)

    print(
        f"Completed: {len(SYMBOLS)} assets, {total_rows} rows, "
        f"saved to {OUTPUT_DIR.name}/"
    )


if __name__ == "__main__":
    main()
