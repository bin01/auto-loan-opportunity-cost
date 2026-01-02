"""Tests for data loading utilities."""

import sqlite3
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from car_loan_sim.data import load_sp500_series, next_trading_day


class TestLoadSp500Series:
    """Tests for load_sp500_series function."""

    def test_loads_data_from_real_db(self):
        """Test loading from the actual sp500_daily_close.db file."""
        db_path = Path(__file__).parent.parent / "sp500_daily_close.db"
        if not db_path.exists():
            pytest.skip("sp500_daily_close.db not found")

        series = load_sp500_series(db_path)

        # Check basic properties
        assert isinstance(series, pd.Series)
        assert series.name == "close"
        assert isinstance(series.index, pd.DatetimeIndex)
        assert series.index.is_monotonic_increasing
        assert not series.isnull().any()
        assert len(series) > 0

    def test_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            load_sp500_series("/nonexistent/path/to/db.db")

    def test_validates_null_close_values(self):
        """Test that null close values raise ValueError."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE sp500_daily_close (date TEXT UNIQUE NOT NULL, close REAL)")
        conn.execute("INSERT INTO sp500_daily_close VALUES ('2024-01-01', NULL)")
        conn.commit()
        conn.close()

        with pytest.raises(ValueError, match="null values"):
            load_sp500_series(db_path)

        Path(db_path).unlink()

    def test_validates_duplicate_dates(self):
        """Test that duplicate dates raise ValueError."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        conn = sqlite3.connect(db_path)
        # Create table without UNIQUE constraint for testing
        conn.execute("CREATE TABLE sp500_daily_close (date TEXT NOT NULL, close REAL NOT NULL)")
        conn.execute("INSERT INTO sp500_daily_close VALUES ('2024-01-01', 100.0)")
        conn.execute("INSERT INTO sp500_daily_close VALUES ('2024-01-01', 101.0)")
        conn.commit()
        conn.close()

        with pytest.raises(ValueError, match="duplicate dates"):
            load_sp500_series(db_path)

        Path(db_path).unlink()


class TestNextTradingDay:
    """Tests for next_trading_day function."""

    @pytest.fixture
    def trading_days(self):
        """Create a sample trading day index."""
        # Simulate trading days (weekdays only, with some gaps)
        dates = pd.to_datetime(
            ["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05", "2024-01-08"]
        )
        return pd.DatetimeIndex(dates)

    def test_exact_match_returns_same_date(self, trading_days):
        """Test that if ts equals an index date, it returns ts."""
        ts = pd.Timestamp("2024-01-03")
        result = next_trading_day(trading_days, ts)
        assert result == ts

    def test_between_dates_returns_next(self, trading_days):
        """Test that if ts is between dates, it returns the next trading day."""
        # Saturday between Jan 5 and Jan 8
        ts = pd.Timestamp("2024-01-06")
        result = next_trading_day(trading_days, ts)
        assert result == pd.Timestamp("2024-01-08")

    def test_after_last_date_raises(self, trading_days):
        """Test that if ts is after last date, it raises ValueError."""
        ts = pd.Timestamp("2024-01-10")
        with pytest.raises(ValueError, match="after the last trading day"):
            next_trading_day(trading_days, ts)

    def test_before_first_date_returns_first(self, trading_days):
        """Test that if ts is before first date, it returns the first trading day."""
        ts = pd.Timestamp("2024-01-01")
        result = next_trading_day(trading_days, ts)
        assert result == pd.Timestamp("2024-01-02")

    def test_empty_index_raises(self):
        """Test that empty index raises ValueError."""
        empty_index = pd.DatetimeIndex([])
        ts = pd.Timestamp("2024-01-01")
        with pytest.raises(ValueError, match="empty"):
            next_trading_day(empty_index, ts)
