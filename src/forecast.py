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
