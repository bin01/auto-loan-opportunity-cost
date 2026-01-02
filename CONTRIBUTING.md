# Contributing

Thank you for your interest in contributing to the Car Loan vs Investment Simulator!

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/bin01/auto-loan-opportunity-cost.git
   cd auto-loan-opportunity-cost
   ```
3. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"
   ```

## Development Workflow

### Running Tests

```bash
pytest
```

### Code Style

We use [ruff](https://github.com/astral-sh/ruff) for linting and formatting:

```bash
# Check for issues
ruff check car_loan_sim/ tests/

# Auto-fix issues
ruff check car_loan_sim/ tests/ --fix

# Format code
ruff format car_loan_sim/ tests/
```

### Pre-commit Hooks (Optional)

Install pre-commit hooks to automatically check code before commits:

```bash
pip install pre-commit
pre-commit install
```

## Submitting Changes

1. Create a new branch for your feature or fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and ensure:
   - Tests pass (`pytest`)
   - Code is formatted (`ruff format`)
   - Linting passes (`ruff check`)

3. Commit your changes with a clear message:
   ```bash
   git commit -m "Add feature: description of your change"
   ```

4. Push to your fork and open a Pull Request

## Code of Conduct

Please be respectful and constructive in all interactions. We welcome contributors of all experience levels.

## Questions?

Open an issue if you have questions or need help getting started.
