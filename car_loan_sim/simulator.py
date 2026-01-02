"""Single-scenario simulation for car loan vs investing comparison."""

from pathlib import Path
from typing import Dict, List, Literal, Optional, Union

import numpy as np
import pandas as pd

from .data import load_sp500_series, next_trading_day
from .loan import amortization_schedule, monthly_payment
from .portfolio import Portfolio


def simulate_one(
    start_date: Union[str, pd.Timestamp],
    car_price: float,
    down_payment: float,
    loan_apr: float,
    term_months: int,
    cash_invest_monthly_payment: bool,
    db_path: Union[str, Path],
    contribution_timing: str = "end_of_month",
    loan_lump_sum_invest_mode: Literal["lump_sum", "dca_weekly"] = "lump_sum",
    loan_dca_weeks: int = 52,
) -> pd.DataFrame:
    """Simulate a single car purchase scenario comparing cash vs loan+invest.

    Strategy A (cash): Pay car_price upfront at t0. If cash_invest_monthly_payment
    is True, invest the equivalent monthly payment amount each month.

    Strategy B (loan+invest): Pay down_payment at t0, invest the remaining
    (car_price - down_payment) either as lump sum or via weekly DCA.
    Pay monthly loan payments. No extra monthly investing.

    Args:
        start_date: Date of car purchase (will be mapped to next trading day).
        car_price: Total price of the car.
        down_payment: Down payment for loan strategy.
        loan_apr: Annual percentage rate for the loan.
        term_months: Loan term in months.
        cash_invest_monthly_payment: If True, Strategy A invests monthly payment
            amount each month after paying cash for car.
        db_path: Path to the S&P 500 SQLite database.
        contribution_timing: When to make monthly contributions ('end_of_month').
        loan_lump_sum_invest_mode: 'lump_sum' to invest all at t0, 'dca_weekly' to
            spread investment over loan_dca_weeks weeks.
        loan_dca_weeks: Number of weeks to spread DCA investment (default 52).

    Returns:
        DataFrame with columns: date, portfolio_cash, portfolio_loan,
        balance_loan, networth_cash, networth_loan, diff.
    """
    # Load market data
    sp500 = load_sp500_series(db_path)
    start_ts = pd.Timestamp(start_date)

    # Find the first trading day on or after start_date
    t0 = next_trading_day(sp500.index, start_ts)
    t0_price = sp500[t0]

    # Calculate monthly payment
    loan_amount = car_price - down_payment
    pmt = monthly_payment(loan_amount, loan_apr, term_months)

    # Get amortization schedule for tracking loan balance
    schedule = amortization_schedule(loan_amount, loan_apr, term_months)

    # Initialize portfolios
    portfolio_cash = Portfolio()  # Strategy A
    portfolio_loan = Portfolio()  # Strategy B

    # Strategy B: Invest based on mode
    if loan_lump_sum_invest_mode == "lump_sum":
        portfolio_loan.buy(loan_amount, t0_price)
        weekly_dca_dates = []
    else:
        # DCA weekly: build list of weekly investment dates
        weekly_amount = loan_amount / loan_dca_weeks
        weekly_dca_dates = []
        for week in range(loan_dca_weeks):
            week_date_target = t0 + pd.Timedelta(days=7 * week)
            try:
                week_date = next_trading_day(sp500.index, week_date_target)
                weekly_dca_dates.append(week_date)
            except ValueError:
                break

    # Generate monthly dates for the term
    monthly_dates = []
    for month in range(term_months + 1):  # +1 to include final month
        if month == 0:
            monthly_dates.append(t0)
        else:
            next_month = t0 + pd.DateOffset(months=month)
            try:
                trade_date = next_trading_day(sp500.index, next_month)
                monthly_dates.append(trade_date)
            except ValueError:
                monthly_dates.append(sp500.index[-1])
                break

    # Build time series
    records = []
    dca_invested_weeks = 0

    for i, date in enumerate(monthly_dates):
        price = sp500[date] if date in sp500.index else sp500.iloc[-1]

        # Get loan balance for this month
        if i == 0:
            balance = loan_amount
        elif i <= len(schedule):
            balance = schedule.iloc[i - 1]["balance"]
        else:
            balance = 0.0

        # Strategy A: monthly contribution (after month 0)
        if cash_invest_monthly_payment and i > 0:
            portfolio_cash.buy(pmt, price)

        # Strategy B: DCA weekly investments that fall before or on this date
        if loan_lump_sum_invest_mode == "dca_weekly":
            while dca_invested_weeks < len(weekly_dca_dates):
                week_date = weekly_dca_dates[dca_invested_weeks]
                if week_date <= date:
                    week_price = sp500[week_date]
                    portfolio_loan.buy(weekly_amount, week_price)
                    dca_invested_weeks += 1
                else:
                    break

        # Calculate values
        portfolio_cash_value = portfolio_cash.value(price)
        portfolio_loan_value = portfolio_loan.value(price)

        # Net worth calculation
        networth_cash = portfolio_cash_value
        networth_loan = portfolio_loan_value - balance

        records.append(
            {
                "date": date,
                "month": i,
                "portfolio_cash": portfolio_cash_value,
                "portfolio_loan": portfolio_loan_value,
                "balance_loan": balance,
                "networth_cash": networth_cash,
                "networth_loan": networth_loan,
                "diff": networth_loan - networth_cash,
            }
        )

    return pd.DataFrame(records)


def _simulate_one_with_series(
    start_date: pd.Timestamp,
    sp500: pd.Series,
    car_price: float,
    down_payment: float,
    loan_apr: float,
    term_months: int,
    cash_invest_monthly_payment: bool,
    loan_lump_sum_invest_mode: Literal["lump_sum", "dca_weekly"] = "lump_sum",
    loan_dca_weeks: int = 52,
) -> Optional[Dict]:
    """Internal simulation function using pre-loaded series for batch processing.

    Returns dict with start_date, nw_cash_end, nw_loan_lump_end, nw_loan_dca_weekly_end, etc.
    """
    # Find the first trading day on or after start_date
    t0 = next_trading_day(sp500.index, start_date)
    t0_price = sp500[t0]

    # Calculate monthly payment
    loan_amount = car_price - down_payment
    pmt = monthly_payment(loan_amount, loan_apr, term_months)

    # Find the end date (term_months after t0)
    end_date_target = t0 + pd.DateOffset(months=term_months)
    try:
        end_date = next_trading_day(sp500.index, end_date_target)
    except ValueError:
        return None

    end_price = sp500[end_date]

    # Initialize portfolios
    portfolio_cash = Portfolio()
    portfolio_loan_lump = Portfolio()
    portfolio_loan_dca = Portfolio()

    # Strategy B lump sum: Invest all at t0
    portfolio_loan_lump.buy(loan_amount, t0_price)

    # Strategy B DCA weekly: Invest weekly over loan_dca_weeks
    weekly_amount = loan_amount / loan_dca_weeks
    for week in range(loan_dca_weeks):
        week_date_target = t0 + pd.Timedelta(days=7 * week)
        try:
            week_date = next_trading_day(sp500.index, week_date_target)
            week_price = sp500[week_date]
            portfolio_loan_dca.buy(weekly_amount, week_price)
        except ValueError:
            break

    # Simulate monthly contributions for cash strategy
    for month in range(1, term_months + 1):
        month_date_target = t0 + pd.DateOffset(months=month)
        try:
            month_date = next_trading_day(sp500.index, month_date_target)
            month_price = sp500[month_date]
            if cash_invest_monthly_payment:
                portfolio_cash.buy(pmt, month_price)
        except ValueError:
            break

    # Calculate final values
    nw_cash_end = portfolio_cash.value(end_price)
    nw_loan_lump_end = portfolio_loan_lump.value(end_price)
    nw_loan_dca_weekly_end = portfolio_loan_dca.value(end_price)

    return {
        "start_date": t0,
        "nw_cash_end": nw_cash_end,
        "nw_loan_lump_end": nw_loan_lump_end,
        "diff_loan_lump": nw_loan_lump_end - nw_cash_end,
        "nw_loan_dca_weekly_end": nw_loan_dca_weekly_end,
        "diff_loan_dca_weekly": nw_loan_dca_weekly_end - nw_cash_end,
    }


def run_backtest_all_start_dates(
    car_price: float,
    down_payment: float,
    loan_apr: float,
    term_months: int,
    cash_invest_monthly_payment: bool,
    db_path: Union[str, Path],
    loan_dca_weeks: int = 52,
) -> pd.DataFrame:
    """Run backtest across all possible start dates.

    Tests every trading day where the full term_months period fits within
    the available price data. Computes both lump sum and weekly DCA variants.

    Args:
        car_price: Total price of the car.
        down_payment: Down payment for loan strategy.
        loan_apr: Annual percentage rate for the loan.
        term_months: Loan term in months.
        cash_invest_monthly_payment: If True, cash strategy invests monthly payment.
        db_path: Path to the S&P 500 SQLite database.
        loan_dca_weeks: Number of weeks for DCA deployment (default 52).

    Returns:
        DataFrame with columns: start_date, nw_cash_end, nw_loan_lump_end,
        diff_loan_lump, nw_loan_dca_weekly_end, diff_loan_dca_weekly.
    """
    sp500 = load_sp500_series(db_path)

    # Determine the last valid start date (must have term_months of data after)
    last_data_date = sp500.index[-1]
    last_valid_start = last_data_date - pd.DateOffset(months=term_months)

    # Get all valid start dates
    valid_starts = sp500.index[sp500.index <= last_valid_start]

    results: List[Dict] = []
    for start_date in valid_starts:
        result = _simulate_one_with_series(
            start_date=start_date,
            sp500=sp500,
            car_price=car_price,
            down_payment=down_payment,
            loan_apr=loan_apr,
            term_months=term_months,
            cash_invest_monthly_payment=cash_invest_monthly_payment,
            loan_dca_weeks=loan_dca_weeks,
        )
        if result is not None:
            results.append(result)

    return pd.DataFrame(results)


def compute_summary_stats(results: pd.DataFrame, diff_column: str = "diff_loan_lump") -> Dict:
    """Compute summary statistics for backtest results.

    Args:
        results: DataFrame from run_backtest_all_start_dates.
        diff_column: Column name for the diff to analyze.

    Returns:
        Dictionary with summary statistics.
    """
    # Handle legacy column name for backward compatibility
    if diff_column == "diff" and "diff" not in results.columns:
        diff_column = "diff_loan_lump"

    diff = results[diff_column]

    stats = {
        "n_scenarios": len(results),
        "win_rate": (diff > 0).mean(),
        "mean_diff": diff.mean(),
        "median_diff": diff.median(),
        "std_diff": diff.std(),
        "min_diff": diff.min(),
        "max_diff": diff.max(),
        "percentile_5": np.percentile(diff, 5),
        "percentile_25": np.percentile(diff, 25),
        "percentile_75": np.percentile(diff, 75),
        "percentile_95": np.percentile(diff, 95),
    }

    return stats


def compute_comparison_stats(results: pd.DataFrame) -> Dict:
    """Compute comparison statistics for both lump sum and DCA strategies.

    Args:
        results: DataFrame from run_backtest_all_start_dates.

    Returns:
        Dictionary with comparison statistics for both strategies.
    """
    lump_stats = compute_summary_stats(results, "diff_loan_lump")
    dca_stats = compute_summary_stats(results, "diff_loan_dca_weekly")

    return {
        "lump_sum": lump_stats,
        "dca_weekly": dca_stats,
        "lump_beats_dca_rate": (results["diff_loan_lump"] > results["diff_loan_dca_weekly"]).mean(),
    }


def get_worst_scenarios(
    results: pd.DataFrame, n: int = 10, diff_column: str = "diff_loan_lump"
) -> pd.DataFrame:
    """Get the worst N scenarios (lowest diff).

    Args:
        results: DataFrame from run_backtest_all_start_dates.
        n: Number of worst scenarios to return.
        diff_column: Column name for the diff to sort by.

    Returns:
        DataFrame with the worst N scenarios sorted by diff ascending.
    """
    # Handle legacy column name
    if diff_column == "diff" and "diff" not in results.columns:
        diff_column = "diff_loan_lump"

    return results.nsmallest(n, diff_column)
