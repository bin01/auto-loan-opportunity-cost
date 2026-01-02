# Car Loan vs Investment Simulator

A Python simulation tool that analyzes the opportunity cost of financing a car versus paying cash and investing the difference in the S&P 500.

## What It Does

This tool answers the question: **Should I take a car loan and invest the cash, or pay upfront?**

It simulates two strategies over 95+ years of S&P 500 historical data:

| Strategy | Description |
|----------|-------------|
| **Pay Cash** | Pay full car price upfront, invest monthly payment equivalent |
| **Take Loan + Invest** | Make down payment, invest remaining cash, pay monthly loan |

Both strategies have identical total cash outflows. The difference is *when* money is invested.

## Key Findings

- **Loan+Invest wins ~57% of the time** historically
- **Average advantage: ~$1,800** on a $50K car with 6% APR over 5 years
- **Worst case: -$48K** (investing lump sum before 1929 crash)
- **Best case: +$87K** (investing during strong bull markets)

## Key Configuration Toggles

| Parameter | Options | Description |
|-----------|---------|-------------|
| `cash_invest_monthly_payment` | `True`/`False` | Should cash buyer invest monthly? (True for fair comparison) |
| `loan_lump_sum_invest_mode` | `"lump_sum"` / `"dca_weekly"` | Invest all at once or spread over weeks |
| `loan_dca_weeks` | Integer (default: 52) | Weeks to spread DCA investment |
| `car_price` | Float | Total car price |
| `down_payment` | Float | Down payment amount |
| `loan_apr` | Float | Annual percentage rate (0.06 = 6%) |
| `term_months` | Integer | Loan term in months |

## Installation

```bash
# Clone the repository
git clone https://github.com/bin01/auto-loan-opportunity-cost.git
cd auto-loan-opportunity-cost

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```

## Providing S&P 500 Data

The simulator requires a SQLite database with S&P 500 daily closing prices.

**Expected schema:**
```sql
CREATE TABLE sp500_daily_close (
    id INTEGER PRIMARY KEY,
    date TEXT UNIQUE NOT NULL,
    close REAL NOT NULL,
    created_at TEXT
);
```

**Place the database file at the project root:**
```
auto-loan-opportunity-cost/
├── sp500_daily_close.db   <-- Your data file here
├── car_loan_sim/
├── notebooks/
└── ...
```

> **Note:** The database file is excluded from git via `.gitignore`. You must provide your own data.

## Running the Notebook

```bash
# Start Jupyter
jupyter notebook

# Open notebooks/car_loan_vs_invest.ipynb
```

The notebook provides:
1. Single scenario analysis for a specific start date
2. Batch backtest across all historical start dates
3. Win rate comparison (Lump Sum vs DCA)
4. Distribution visualizations (histogram, CDF)
5. Summary statistics and worst-case scenarios

## Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file (uses synthetic data, no DB required)
pytest tests/test_dca.py
```

Tests include synthetic data scenarios that don't require the database.

## Linting and Formatting

```bash
# Check code style
ruff check car_loan_sim/ tests/

# Auto-fix issues
ruff check car_loan_sim/ tests/ --fix

# Format code
ruff format car_loan_sim/ tests/
```

## Project Structure

```
auto-loan-opportunity-cost/
├── car_loan_sim/           # Main package
│   ├── __init__.py
│   ├── data.py             # Data loading utilities
│   ├── loan.py             # Loan amortization calculations
│   ├── portfolio.py        # Portfolio tracking
│   ├── plots.py            # Visualization utilities
│   └── simulator.py        # Core simulation logic
├── notebooks/
│   └── car_loan_vs_invest.ipynb  # Main analysis notebook
├── tests/                  # Test suite
│   ├── test_data.py
│   ├── test_dca.py         # DCA tests with synthetic data
│   ├── test_loan.py
│   └── test_simulator.py
├── pyproject.toml          # Project configuration
├── .gitignore
├── LICENSE
└── README.md
```

## Important Caveats

1. **Price-Only Returns**: The S&P 500 data uses price returns only, excluding dividends (~2%/year). Including dividends would slightly favor the loan strategy.

2. **No Taxes**: The simulation doesn't account for capital gains taxes or potential loan interest deductions.

3. **Past ≠ Future**: Historical performance doesn't guarantee future results.

4. **Behavioral Assumptions**: Assumes the cash buyer actually invests monthly (behavioral discipline matters).

5. **Single Interest Rate**: Results vary significantly with different loan APRs.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.
