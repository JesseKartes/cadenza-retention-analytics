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
