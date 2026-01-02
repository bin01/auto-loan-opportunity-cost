"""Data loading utilities for S&P 500 historical data."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


def load_sp500_series(db_path: str | Path) -> pd.Series:
    """Load S&P 500 daily close prices from SQLite database.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        pd.Series with DatetimeIndex and close prices, named 'close'.

    Raises:
        ValueError: If data validation fails (null values, unsorted, duplicates).
        FileNotFoundError: If database file doesn't exist.
    """
    db_path = Path(db_path)
    if not db_path.exists():
        raise FileNotFoundError(f"Database file not found: {db_path}")

    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query(
            "SELECT date, close FROM sp500_daily_close ORDER BY date ASC",
            conn,
            parse_dates=["date"],
        )
    finally:
        conn.close()

    # Validate: non-null close values
    if df["close"].isnull().any():
        raise ValueError("Found null values in close prices")

    # Validate: unique dates
    if df["date"].duplicated().any():
        raise ValueError("Found duplicate dates in data")

    # Create series with datetime index
    series = pd.Series(df["close"].values, index=df["date"], name="close")

    # Validate: sorted index
    if not series.index.is_monotonic_increasing:
        raise ValueError("Date index is not sorted in ascending order")

    return series


def next_trading_day(index: pd.DatetimeIndex, ts: pd.Timestamp) -> pd.Timestamp:
    """Find the next trading day on or after the given timestamp.

    Uses searchsorted to efficiently find the first trading day >= ts.

    Args:
        index: DatetimeIndex of trading days (must be sorted).
        ts: Timestamp to search from.

    Returns:
        The first trading day on or after ts.

    Raises:
        ValueError: If ts is after the last trading day in the index.
    """
    if len(index) == 0:
        raise ValueError("Index is empty")

    # searchsorted with side='left' finds the insertion point for ts
    # This gives us the index of the first element >= ts
    pos = index.searchsorted(ts, side="left")

    if pos >= len(index):
        raise ValueError(f"Timestamp {ts} is after the last trading day in the index ({index[-1]})")

    return index[pos]
