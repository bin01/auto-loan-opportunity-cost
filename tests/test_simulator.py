"""Tests for the simulator module."""

from pathlib import Path

import pandas as pd
import pytest

from car_loan_sim.simulator import simulate_one


class TestSimulateOne:
    """Tests for simulate_one function."""

    @pytest.fixture
    def db_path(self):
        """Path to the S&P 500 database."""
        path = Path(__file__).parent.parent / "sp500_daily_close.db"
        if not path.exists():
            pytest.skip("sp500_daily_close.db not found")
        return path

    def test_smoke_test_outputs_exist(self, db_path):
        """Smoke test: run one scenario and verify outputs exist."""
        result = simulate_one(
            start_date="2020-01-01",
            car_price=30000,
            down_payment=5000,
            loan_apr=0.06,
            term_months=60,
            cash_invest_monthly_payment=True,
            db_path=db_path,
        )

        # Verify result is a DataFrame
        assert isinstance(result, pd.DataFrame)

        # Verify expected columns exist
        expected_columns = [
            "date",
            "month",
            "portfolio_cash",
            "portfolio_loan",
            "balance_loan",
            "networth_cash",
            "networth_loan",
            "diff",
        ]
        assert list(result.columns) == expected_columns

    def test_output_length_matches_term(self, db_path):
        """Test that output length matches term_months + 1 (includes month 0)."""
        term_months = 60
        result = simulate_one(
            start_date="2020-01-01",
            car_price=30000,
            down_payment=5000,
            loan_apr=0.06,
            term_months=term_months,
            cash_invest_monthly_payment=True,
            db_path=db_path,
        )

        # Should have term_months + 1 rows (month 0 through month 60)
        assert len(result) == term_months + 1

    def test_month_column_values(self, db_path):
        """Test that month column has correct values."""
        term_months = 60
        result = simulate_one(
            start_date="2020-01-01",
            car_price=30000,
            down_payment=5000,
            loan_apr=0.06,
            term_months=term_months,
            cash_invest_monthly_payment=True,
            db_path=db_path,
        )

        assert list(result["month"]) == list(range(term_months + 1))

    def test_loan_balance_starts_at_loan_amount(self, db_path):
        """Test that loan balance starts at car_price - down_payment."""
        car_price = 30000
        down_payment = 5000
        result = simulate_one(
            start_date="2020-01-01",
            car_price=car_price,
            down_payment=down_payment,
            loan_apr=0.06,
            term_months=60,
            cash_invest_monthly_payment=True,
            db_path=db_path,
        )

        # First row (month 0) should have loan balance = loan amount
        assert result.iloc[0]["balance_loan"] == car_price - down_payment

    def test_loan_balance_ends_near_zero(self, db_path):
        """Test that loan balance ends near zero."""
        result = simulate_one(
            start_date="2020-01-01",
            car_price=30000,
            down_payment=5000,
            loan_apr=0.06,
            term_months=60,
            cash_invest_monthly_payment=True,
            db_path=db_path,
        )

        # Final loan balance should be essentially zero
        assert result.iloc[-1]["balance_loan"] < 1

    def test_portfolio_loan_starts_with_investment(self, db_path):
        """Test that loan portfolio has value from day 1 (lump sum invested)."""
        result = simulate_one(
            start_date="2020-01-01",
            car_price=30000,
            down_payment=5000,
            loan_apr=0.06,
            term_months=60,
            cash_invest_monthly_payment=True,
            db_path=db_path,
        )

        # Portfolio loan should have positive value at month 0
        assert result.iloc[0]["portfolio_loan"] > 0

    def test_portfolio_cash_starts_at_zero_when_not_investing(self, db_path):
        """Test that cash portfolio is zero when not investing monthly payment."""
        result = simulate_one(
            start_date="2020-01-01",
            car_price=30000,
            down_payment=5000,
            loan_apr=0.06,
            term_months=60,
            cash_invest_monthly_payment=False,
            db_path=db_path,
        )

        # All cash portfolio values should be zero
        assert all(result["portfolio_cash"] == 0)
        assert all(result["networth_cash"] == 0)
