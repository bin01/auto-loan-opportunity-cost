"""Tests for DCA (Dollar Cost Averaging) functionality with synthetic data."""

import numpy as np
import pandas as pd

from car_loan_sim.simulator import _simulate_one_with_series


def create_synthetic_series(
    start_date: str,
    num_days: int,
    pattern: str = "flat",
    base_price: float = 100.0,
) -> pd.Series:
    """Create a synthetic S&P 500 series for testing.

    Args:
        start_date: Start date for the series.
        num_days: Number of trading days to generate.
        pattern: 'flat', 'increasing', or 'decreasing'.
        base_price: Starting price.

    Returns:
        pandas Series with DatetimeIndex and close prices.
    """
    dates = pd.bdate_range(start=start_date, periods=num_days)

    if pattern == "flat":
        prices = np.full(num_days, base_price)
    elif pattern == "increasing":
        # 0.5% daily increase
        prices = base_price * (1.005 ** np.arange(num_days))
    elif pattern == "decreasing":
        # 0.5% daily decrease
        prices = base_price * (0.995 ** np.arange(num_days))
    else:
        raise ValueError(f"Unknown pattern: {pattern}")

    return pd.Series(prices, index=dates, name="close")


class TestDCAFlatMarket:
    """Test that lump sum and DCA end equal in a flat market."""

    def test_flat_market_lump_equals_dca(self):
        """In a flat market, lump sum and DCA should end with equal values."""
        # Create flat market with enough days for 60-month term + 52 weeks DCA
        sp500 = create_synthetic_series(
            start_date="2020-01-01",
            num_days=2000,  # ~8 years of trading days
            pattern="flat",
            base_price=100.0,
        )

        result = _simulate_one_with_series(
            start_date=pd.Timestamp("2020-01-01"),
            sp500=sp500,
            car_price=30000,
            down_payment=5000,
            loan_apr=0.06,
            term_months=60,
            cash_invest_monthly_payment=True,
            loan_dca_weeks=52,
        )

        assert result is not None

        # In a flat market, both strategies invest the same total amount
        # and end at the same price, so they should be equal within tolerance
        lump_end = result["nw_loan_lump_end"]
        dca_end = result["nw_loan_dca_weekly_end"]

        # Both should equal the loan amount (since price never changed)
        loan_amount = 30000 - 5000
        assert abs(lump_end - loan_amount) < 0.01, f"Lump sum: {lump_end} != {loan_amount}"
        assert abs(dca_end - loan_amount) < 0.01, f"DCA: {dca_end} != {loan_amount}"
        assert abs(lump_end - dca_end) < 0.01, f"Lump {lump_end} != DCA {dca_end}"


class TestDCAIncreasingMarket:
    """Test that lump sum beats DCA in a monotonically increasing market."""

    def test_increasing_market_lump_beats_dca(self):
        """In an increasing market, lump sum should beat DCA."""
        sp500 = create_synthetic_series(
            start_date="2020-01-01",
            num_days=2000,
            pattern="increasing",
            base_price=100.0,
        )

        result = _simulate_one_with_series(
            start_date=pd.Timestamp("2020-01-01"),
            sp500=sp500,
            car_price=30000,
            down_payment=5000,
            loan_apr=0.06,
            term_months=60,
            cash_invest_monthly_payment=True,
            loan_dca_weeks=52,
        )

        assert result is not None

        lump_end = result["nw_loan_lump_end"]
        dca_end = result["nw_loan_dca_weekly_end"]

        # Lump sum should be >= DCA in rising market (invests all at lowest price)
        assert lump_end >= dca_end, f"Lump {lump_end} should >= DCA {dca_end} in rising market"

        # The difference should be meaningful (not just floating point noise)
        # In a strongly rising market, lump sum has a clear advantage
        assert lump_end > dca_end * 1.01, "Lump should significantly beat DCA in rising market"


class TestDCADecreasingMarket:
    """Test that DCA beats lump sum in a monotonically decreasing market."""

    def test_decreasing_market_dca_beats_lump(self):
        """In a decreasing market, DCA should beat lump sum."""
        sp500 = create_synthetic_series(
            start_date="2020-01-01",
            num_days=2000,
            pattern="decreasing",
            base_price=100.0,
        )

        result = _simulate_one_with_series(
            start_date=pd.Timestamp("2020-01-01"),
            sp500=sp500,
            car_price=30000,
            down_payment=5000,
            loan_apr=0.06,
            term_months=60,
            cash_invest_monthly_payment=True,
            loan_dca_weeks=52,
        )

        assert result is not None

        lump_end = result["nw_loan_lump_end"]
        dca_end = result["nw_loan_dca_weekly_end"]

        # DCA should be >= lump sum in falling market (buys at lower avg price)
        assert dca_end >= lump_end, f"DCA {dca_end} should >= Lump {lump_end} in falling market"

        # The difference should be meaningful
        assert dca_end > lump_end * 1.01, "DCA should significantly beat lump sum in falling market"


class TestDCAEdgeCases:
    """Test edge cases for DCA functionality."""

    def test_dca_weeks_1_equals_lump_sum(self):
        """DCA with 1 week should be equivalent to lump sum."""
        sp500 = create_synthetic_series(
            start_date="2020-01-01",
            num_days=2000,
            pattern="increasing",
            base_price=100.0,
        )

        result = _simulate_one_with_series(
            start_date=pd.Timestamp("2020-01-01"),
            sp500=sp500,
            car_price=30000,
            down_payment=5000,
            loan_apr=0.06,
            term_months=60,
            cash_invest_monthly_payment=True,
            loan_dca_weeks=1,  # Only 1 week = essentially lump sum
        )

        assert result is not None

        lump_end = result["nw_loan_lump_end"]
        dca_end = result["nw_loan_dca_weekly_end"]

        # Should be equal since DCA with 1 week invests all at once
        assert abs(lump_end - dca_end) < 0.01, "1-week DCA should equal lump sum"

    def test_dca_weeks_104_spreads_over_two_years(self):
        """DCA with 104 weeks should work (2 years of weekly investing)."""
        sp500 = create_synthetic_series(
            start_date="2020-01-01",
            num_days=2000,
            pattern="flat",
            base_price=100.0,
        )

        result = _simulate_one_with_series(
            start_date=pd.Timestamp("2020-01-01"),
            sp500=sp500,
            car_price=30000,
            down_payment=5000,
            loan_apr=0.06,
            term_months=60,
            cash_invest_monthly_payment=True,
            loan_dca_weeks=104,
        )

        assert result is not None

        # In flat market, should still invest full amount
        loan_amount = 30000 - 5000
        assert abs(result["nw_loan_dca_weekly_end"] - loan_amount) < 0.01
