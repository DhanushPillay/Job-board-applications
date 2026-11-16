"""Statistical helpers: Wilson intervals and the Newcombe difference."""

from __future__ import annotations

import numpy as np
import pandas as pd


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson score interval for a proportion, returned in percent."""
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, 100 * (centre - half)), min(100.0, 100 * (centre + half)))


def add_wilson(df: pd.DataFrame, k_col: str, n_col: str) -> pd.DataFrame:
    df = df.copy()
    intervals = [wilson_ci(int(k), int(n)) for k, n in zip(df[k_col], df[n_col], strict=True)]
    df["ci_low"], df["ci_high"] = zip(*intervals, strict=True)
    return df


def newcombe_diff(k1: int, n1: int, k2: int, n2: int) -> tuple[float, float]:
    """Newcombe hybrid score interval for p1 - p2, returned in proportion units."""
    p1, p2 = k1 / n1, k2 / n2
    low1, high1 = (value / 100 for value in wilson_ci(k1, n1))
    low2, high2 = (value / 100 for value in wilson_ci(k2, n2))
    diff = p1 - p2
    lower = diff - np.sqrt((p1 - low1) ** 2 + (high2 - p2) ** 2)
    upper = diff + np.sqrt((high1 - p1) ** 2 + (p2 - low2) ** 2)
    return float(max(-1.0, lower)), float(min(1.0, upper))
