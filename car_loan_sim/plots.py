"""Plotting utilities for backtest results visualization."""

from typing import Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure


def plot_histogram(
    diff: pd.Series,
    bins: int = 50,
    figsize: Tuple[int, int] = (12, 6),
    title: Optional[str] = None,
    ax: Optional[Axes] = None,
) -> Tuple[Figure, Axes]:
    """Plot histogram of net worth differences.

    Args:
        diff: Series of diff values (loan strategy - cash strategy).
        bins: Number of histogram bins.
        figsize: Figure size (width, height).
        title: Optional custom title.
        ax: Optional existing axes to plot on.

    Returns:
        Tuple of (Figure, Axes).
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.figure

    # Plot histogram
    ax.hist(diff, bins=bins, edgecolor="black", alpha=0.7, color="steelblue")

    # Add vertical line at zero
    ax.axvline(x=0, color="red", linestyle="--", linewidth=2, label="Break-even")

    # Add vertical line at mean
    mean_val = diff.mean()
    ax.axvline(
        x=mean_val,
        color="green",
        linestyle="-",
        linewidth=2,
        label=f"Mean: ${mean_val:,.0f}",
    )

    # Add vertical line at median
    median_val = diff.median()
    ax.axvline(
        x=median_val,
        color="orange",
        linestyle="-",
        linewidth=2,
        label=f"Median: ${median_val:,.0f}",
    )

    ax.set_xlabel("Net Worth Difference ($)")
    ax.set_ylabel("Frequency")
    ax.set_title(title or "Distribution of Loan+Invest vs Cash Strategy Outcomes")
    ax.legend()
    ax.grid(True, alpha=0.3)

    return fig, ax


def plot_cdf(
    diff: pd.Series,
    figsize: Tuple[int, int] = (12, 6),
    title: Optional[str] = None,
    ax: Optional[Axes] = None,
) -> Tuple[Figure, Axes]:
    """Plot cumulative distribution function of net worth differences.

    Args:
        diff: Series of diff values (loan strategy - cash strategy).
        figsize: Figure size (width, height).
        title: Optional custom title.
        ax: Optional existing axes to plot on.

    Returns:
        Tuple of (Figure, Axes).
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.figure

    # Sort values for CDF
    sorted_diff = np.sort(diff.values)
    cdf = np.arange(1, len(sorted_diff) + 1) / len(sorted_diff)

    # Plot CDF
    ax.plot(sorted_diff, cdf, linewidth=2, color="steelblue")

    # Add horizontal line at 50%
    ax.axhline(y=0.5, color="gray", linestyle="--", alpha=0.5)

    # Add vertical line at zero to show win rate
    ax.axvline(x=0, color="red", linestyle="--", linewidth=2, label="Break-even")

    # Calculate and display win rate
    win_rate = (diff > 0).mean()
    ax.axhline(
        y=1 - win_rate,
        color="red",
        linestyle=":",
        alpha=0.7,
        label=f"Loan wins {win_rate:.1%} of scenarios",
    )

    # Mark percentiles
    for pct in [5, 25, 75, 95]:
        val = np.percentile(diff, pct)
        ax.plot(val, pct / 100, "o", markersize=8, label=f"P{pct}: ${val:,.0f}")

    ax.set_xlabel("Net Worth Difference ($)")
    ax.set_ylabel("Cumulative Probability")
    ax.set_title(title or "CDF of Loan+Invest vs Cash Strategy Outcomes")
    ax.legend(loc="lower right")
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1)

    return fig, ax
