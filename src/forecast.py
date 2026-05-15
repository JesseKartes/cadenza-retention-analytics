"""Forecasting metric calculations for pipeline-snapshot analytics.

All functions are pure: they take pandas DataFrames matching the schema of
`data/generated/pipeline_snapshots.csv` and `opportunities.csv`, and return
scalars or aggregated DataFrames.

Schema reminder:
    pipeline_snapshots: snapshot_date, opportunity_id, stage_at_snapshot,
                        amount, forecast_category, expected_close_date
        - forecast_category in {Commit, Best Case, Pipeline}
"""
from __future__ import annotations

import pandas as pd

from src.pipeline import STAGE_PROBABILITY


def forecast_buckets(snapshots: pd.DataFrame, snapshot_date: str) -> dict[str, float]:
    """Sum amounts by forecast_category for the given snapshot_date.

    Returns dict with keys 'commit', 'best_case', 'pipeline' (lowercase,
    snake_case). Zero-defaults if a category has no rows for the date.
    """
    rows = snapshots[snapshots["snapshot_date"] == snapshot_date]
    result = {"commit": 0.0, "best_case": 0.0, "pipeline": 0.0}
    if len(rows) == 0:
        return result
    by_cat = rows.groupby("forecast_category")["amount"].sum().to_dict()
    result["commit"] = float(by_cat.get("Commit", 0.0))
    result["best_case"] = float(by_cat.get("Best Case", 0.0))
    result["pipeline"] = float(by_cat.get("Pipeline", 0.0))
    return result


def forecast_accuracy(snapshots: pd.DataFrame, opps: pd.DataFrame,
                      snapshot_date: str) -> float | None:
    """Forecast accuracy = weighted pipeline at snapshot ÷ actual closed-won
    in the 3 months starting at snapshot_date.

    Returns None if no closed-won deals exist in the window (can't compute
    a ratio against zero).

    Interpretation: 1.0 = perfect, >1.0 = over-forecasted, <1.0 = under-forecasted.
    """
    snap = snapshots[snapshots["snapshot_date"] == snapshot_date].copy()
    if len(snap) == 0:
        return None
    snap["weight"] = snap["stage_at_snapshot"].map(STAGE_PROBABILITY).fillna(0.0)
    weighted = float((snap["amount"] * snap["weight"]).sum())

    window_end = (pd.Timestamp(snapshot_date) + pd.DateOffset(months=3)).strftime("%Y-%m-%d")
    actual = opps[
        (opps["status"] == "closed_won")
        & (opps["close_date"] >= snapshot_date)
        & (opps["close_date"] < window_end)
    ]
    actual_total = float(actual["amount"].sum())
    if actual_total == 0:
        return None
    return weighted / actual_total


def forecast_accuracy_trend(snapshots: pd.DataFrame, opps: pd.DataFrame) -> pd.DataFrame:
    """Build a row-per-snapshot DataFrame with forecast, actual, and accuracy.

    Columns: snapshot_date, weighted_forecast, actual_closed_won, accuracy
    `accuracy` is None for snapshots where no closed-won deals fall in the
    3-month window after the snapshot date.
    """
    rows = []
    for snap_date in sorted(snapshots["snapshot_date"].unique()):
        snap = snapshots[snapshots["snapshot_date"] == snap_date].copy()
        snap["weight"] = snap["stage_at_snapshot"].map(STAGE_PROBABILITY).fillna(0.0)
        weighted = float((snap["amount"] * snap["weight"]).sum())

        window_end = (pd.Timestamp(snap_date) + pd.DateOffset(months=3)).strftime("%Y-%m-%d")
        actual = opps[
            (opps["status"] == "closed_won")
            & (opps["close_date"] >= snap_date)
            & (opps["close_date"] < window_end)
        ]
        actual_total = float(actual["amount"].sum())
        accuracy = (weighted / actual_total) if actual_total > 0 else None

        rows.append({
            "snapshot_date": snap_date,
            "weighted_forecast": weighted,
            "actual_closed_won": actual_total,
            "accuracy": accuracy,
        })
    return pd.DataFrame(rows)
