"""Tests for loan amortization calculations."""

import pytest

from car_loan_sim.loan import amortization_schedule, monthly_payment


class TestMonthlyPayment:
    """Tests for monthly_payment function."""

    def test_apr_zero_equals_principal_divided_by_term(self):
        """Test that with apr=0, payment equals principal/term."""
        principal = 30000
        term_months = 60
        payment = monthly_payment(principal, apr=0, term_months=term_months)
        expected = principal / term_months
        assert payment == pytest.approx(expected)

    def test_known_calculation(self):
        """Test against a known correct calculation."""
        # $30,000 loan at 6% APR for 60 months = ~$579.98/month
        payment = monthly_payment(30000, 0.06, 60)
        assert payment == pytest.approx(579.98, rel=0.01)

    def test_negative_principal_raises(self):
        """Test that negative principal raises ValueError."""
        with pytest.raises(ValueError, match="Principal must be positive"):
            monthly_payment(-1000, 0.05, 12)

    def test_zero_principal_raises(self):
        """Test that zero principal raises ValueError."""
        with pytest.raises(ValueError, match="Principal must be positive"):
            monthly_payment(0, 0.05, 12)

    def test_negative_term_raises(self):
        """Test that negative term raises ValueError."""
        with pytest.raises(ValueError, match="Term must be positive"):
            monthly_payment(1000, 0.05, -12)

    def test_negative_apr_raises(self):
        """Test that negative APR raises ValueError."""
        with pytest.raises(ValueError, match="APR cannot be negative"):
            monthly_payment(1000, -0.05, 12)


class TestAmortizationSchedule:
    """Tests for amortization_schedule function."""

    def test_apr_zero_payment_equals_principal_divided_by_term(self):
        """Test that with apr=0, each payment equals principal/term."""
        principal = 30000
        term_months = 60
        schedule = amortization_schedule(principal, apr=0, term_months=term_months)
        expected_payment = principal / term_months

        # All payments should equal principal/term (no interest)
        for payment in schedule["payment"]:
            assert payment == pytest.approx(expected_payment)
        # All interest should be zero
        for interest in schedule["interest"]:
            assert interest == pytest.approx(0)

    def test_final_balance_near_zero_normal_apr(self):
        """Test that final balance is ~0 within tolerance for normal APR."""
        principal = 30000
        schedule = amortization_schedule(principal, apr=0.06, term_months=60)
        final_balance = schedule["balance"].iloc[-1]

        # Final balance should be essentially zero (within 1e-6 * principal)
        assert abs(final_balance) < 1e-6 * principal

    def test_payment_constant_each_month(self):
        """Test that payment is constant each month (except possibly final)."""
        schedule = amortization_schedule(30000, apr=0.06, term_months=60)

        # Exclude final payment which may be slightly adjusted
        payments = schedule["payment"].iloc[:-1]

        # All payments should be the same
        assert payments.std() < 1e-10

    def test_balance_decreases_monotonically(self):
        """Test that balance decreases with each payment."""
        schedule = amortization_schedule(30000, apr=0.06, term_months=60)

        balances = schedule["balance"].values
        for i in range(1, len(balances)):
            assert balances[i] <= balances[i - 1], f"Balance increased at month {i + 1}"

    def test_balance_never_negative(self):
        """Test that balance never goes negative."""
        schedule = amortization_schedule(30000, apr=0.06, term_months=60)
        assert all(schedule["balance"] >= 0)

    def test_dataframe_columns(self):
        """Test that schedule has correct columns."""
        schedule = amortization_schedule(30000, apr=0.06, term_months=60)
        expected_columns = ["month", "payment", "interest", "principal", "balance"]
        assert list(schedule.columns) == expected_columns

    def test_month_numbers_correct(self):
        """Test that month numbers are 1 to term_months."""
        term_months = 60
        schedule = amortization_schedule(30000, apr=0.06, term_months=term_months)
        assert list(schedule["month"]) == list(range(1, term_months + 1))

    def test_total_principal_equals_loan_amount(self):
        """Test that total principal payments equal the loan amount."""
        principal = 30000
        schedule = amortization_schedule(principal, apr=0.06, term_months=60)
        total_principal = schedule["principal"].sum()
        assert total_principal == pytest.approx(principal, rel=1e-6)

    def test_payment_equals_interest_plus_principal(self):
        """Test that payment = interest + principal for each row."""
        schedule = amortization_schedule(30000, apr=0.06, term_months=60)
        for _, row in schedule.iterrows():
            assert row["payment"] == pytest.approx(row["interest"] + row["principal"], rel=1e-10)
