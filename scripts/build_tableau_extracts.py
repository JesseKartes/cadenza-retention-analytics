"""Build flat, Tableau-friendly CSV extracts from data/generated/.

Outputs five pre-aggregated long-format CSVs plus three raw passthroughs into
data/tableau/. The pre-aggregated metrics are computed using the existing pure
functions in src/*.py so the Tableau workbook tells the same numerical story
as the Streamlit dashboard.

Run from repo root:
    python -m scripts.build_tableau_extracts
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd

from src import cohorts, forecast, metrics, quota

GENERATED = Path("data/generated")
TABLEAU = Path("data/tableau")


def load_inputs() -> dict[str, pd.DataFrame]:
    """Load every CSV the pre-aggregation needs."""
    return {
        "customers": pd.read_csv(GENERATED / "customers.csv"),
        "subscriptions": pd.read_csv(GENERATED / "subscriptions.csv"),
        "events": pd.read_csv(GENERATED / "events.csv"),
        "opportunities": pd.read_csv(GENERATED / "opportunities.csv"),
        "snapshots": pd.read_csv(GENERATED / "pipeline_snapshots.csv"),
        "reps": pd.read_csv(GENERATED / "reps.csv"),
    }


def copy_raw_files() -> None:
    """Copy raw CSVs that Tableau reads directly (opportunities, stage history, reps)."""
    for name in ["opportunities.csv", "opportunity_stage_history.csv", "reps.csv"]:
        shutil.copy(GENERATED / name, TABLEAU / name)


def main() -> None:
    TABLEAU.mkdir(parents=True, exist_ok=True)
    data = load_inputs()

    # Task 2-6 will add build_* function calls here.
    copy_raw_files()
    print(f"Wrote outputs to {TABLEAU.resolve()}")


if __name__ == "__main__":
    main()
