"""Loan amortization calculations."""

import pandas as pd


def monthly_payment(principal: float, apr: float, term_months: int) -> float:
    """Calculate the fixed monthly payment for a loan.

    Uses the standard amortization formula:
    M = P * [r(1+r)^n] / [(1+r)^n - 1]

    where:
    - M = monthly payment
    - P = principal
    - r = monthly interest rate (apr/12)
    - n = number of payments (term_months)

    Args:
        principal: Loan principal amount.
        apr: Annual percentage rate (e.g., 0.06 for 6%).
        term_months: Loan term in months.

    Returns:
        Fixed monthly payment amount.
    """
    if principal <= 0:
        raise ValueError("Principal must be positive")
    if term_months <= 0:
        raise ValueError("Term must be positive")
    if apr < 0:
        raise ValueError("APR cannot be negative")

    # Handle zero interest rate case
    if apr == 0:
        return principal / term_months

    monthly_rate = apr / 12
    # Standard amortization formula
    numerator = monthly_rate * (1 + monthly_rate) ** term_months
    denominator = (1 + monthly_rate) ** term_months - 1

    return principal * (numerator / denominator)


def amortization_schedule(principal: float, apr: float, term_months: int) -> pd.DataFrame:
    """Generate a full amortization schedule for a loan.

    Args:
        principal: Loan principal amount.
        apr: Annual percentage rate (e.g., 0.06 for 6%).
        term_months: Loan term in months.

    Returns:
        DataFrame with columns: month, payment, interest, principal, balance.
        - month: Payment number (1 to term_months)
        - payment: Fixed monthly payment amount
        - interest: Interest portion of payment
        - principal: Principal portion of payment
        - balance: Remaining balance after payment
    """
    payment = monthly_payment(principal, apr, term_months)
    monthly_rate = apr / 12

    schedule = []
    balance = principal

    for month in range(1, term_months + 1):
        interest_payment = balance * monthly_rate
        principal_payment = payment - interest_payment

        # For final payment, adjust to pay off exact balance
        if month == term_months:
            principal_payment = balance
            payment_actual = interest_payment + principal_payment
        else:
            payment_actual = payment

        balance = balance - principal_payment

        # Ensure balance never goes negative (handle floating point errors)
        if balance < 0:
            balance = 0.0

        schedule.append(
            {
                "month": month,
                "payment": payment_actual,
                "interest": interest_payment,
                "principal": principal_payment,
                "balance": balance,
            }
        )

    return pd.DataFrame(schedule)
