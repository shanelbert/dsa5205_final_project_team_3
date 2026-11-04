"""Long-only, thresholded proportional target weights."""
import numpy as np
import pandas as pd


def make_weights(predictions: pd.DataFrame, threshold: float = 0.001,
                 max_weight: float = 0.30, scale: float = 100.0) -> pd.DataFrame:
    """Predictions indexed by signal date, ticker columns; uninvested cash earns 0.

    No shorting, per-stock cap, and total stock exposure <= 100%.
    Parameters must be fixed using validation data, never test results.
    """
    if threshold < 0 or max_weight <= 0 or max_weight > 1 or scale <= 0:
        raise ValueError('Invalid strategy parameters')
    p = predictions.astype(float).replace([np.inf, -np.inf], np.nan)
    raw = (p.where(p > threshold, 0.0).fillna(0.0) * scale).clip(0, max_weight)
    totals = raw.sum(axis=1)
    weights = raw.div(totals.where(totals > 1, 1), axis=0)
    return weights
