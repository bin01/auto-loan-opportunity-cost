"""Simple fractional-share portfolio model."""


class Portfolio:
    """A simple portfolio that tracks fractional shares.

    Supports buying shares at given prices and valuing the portfolio
    at any given close price.
    """

    def __init__(self):
        """Initialize an empty portfolio."""
        self.shares = 0.0
        self.cost_basis = 0.0

    def buy(self, amount: float, price: float) -> float:
        """Buy shares with a given dollar amount at a given price.

        Args:
            amount: Dollar amount to invest.
            price: Price per share at time of purchase.

        Returns:
            Number of shares purchased.
        """
        if amount <= 0:
            return 0.0
        if price <= 0:
            raise ValueError("Price must be positive")

        shares_bought = amount / price
        self.shares += shares_bought
        self.cost_basis += amount
        return shares_bought

    def value(self, price: float) -> float:
        """Calculate current portfolio value at given price.

        Args:
            price: Current price per share.

        Returns:
            Total portfolio value.
        """
        return self.shares * price

    def __repr__(self) -> str:
        return f"Portfolio(shares={self.shares:.6f}, cost_basis={self.cost_basis:.2f})"
