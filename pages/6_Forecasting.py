"""Cadenza Forecasting — commit/best-case/pipeline buckets, accuracy trend,
segment-level bias.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src import forecast as fc
from src import viz

st.set_page_config(page_title="Cadenza — Forecasting", layout="wide")

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "generated"


@st.cache_data
def load_data():
    opps = pd.read_csv(DATA_DIR / "opportunities.csv")
    snapshots = pd.read_csv(DATA_DIR / "pipeline_snapshots.csv")
    return opps, snapshots


def main():
    st.title("Forecasting")
    st.caption("Quarterly forecast buckets, accuracy trend, and segment-level "
               "bias. Forecast aggregates across new-business, renewal, and "
               "expansion motions — that's how real forecast calls work. For "
               "new-business stage analytics, see the Pipeline page.")

    opps, snapshots = load_data()

    snap_dates = sorted(snapshots["snapshot_date"].unique())
    snap_date = st.sidebar.selectbox("Snapshot quarter", snap_dates, index=len(snap_dates) - 1)

    target = st.sidebar.number_input("Quarter target ($)",
                                      min_value=0, value=20_000_000, step=1_000_000,
                                      help="Total booking target for the quarter "
                                           "(new business + renewals + expansion).")

    buckets = fc.forecast_buckets(snapshots, snap_date)
    last_completed = snap_dates[snap_dates.index(snap_date) - 1] if snap_dates.index(snap_date) > 0 else None
    last_acc = fc.forecast_accuracy(snapshots, opps, last_completed) if last_completed else None

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Commit", f"${buckets['commit']:,.0f}")
    c2.metric("Best Case", f"${buckets['best_case']:,.0f}")
    c3.metric("Pipeline", f"${buckets['pipeline']:,.0f}")
    c4.metric("Last-Quarter Accuracy",
              f"{last_acc:.1%}" if last_acc is not None else "n/a",
              help="Weighted forecast at last snapshot ÷ actual closed-won that quarter.")

    st.divider()

    st.subheader(f"Forecast Buckets — {snap_date}")
    st.plotly_chart(viz.forecast_buckets_figure(buckets, target=target), use_container_width=True)

    st.subheader("Forecast Accuracy Trend")
    st.caption("Per quarterly snapshot: weighted forecast vs. actual closed-won. "
               "100% = perfect; >100% = over-forecast.")
    trend = fc.forecast_accuracy_trend(snapshots, opps).dropna(subset=["accuracy"])
    if len(trend) > 0:
        st.plotly_chart(
            viz.trend_figure(trend, "snapshot_date", ["accuracy"],
                              "Forecast Accuracy Over Time", reference=1.0),
            use_container_width=True,
        )
    else:
        st.info("No snapshots with completed quarters yet.")

    st.subheader(f"Forecast Bias by Segment — {snap_date}")
    bias = fc.forecast_bias_by_segment(snapshots, opps, snap_date)
    st.plotly_chart(viz.forecast_bias_bar(bias), use_container_width=True)


if __name__ == "__main__":
    main()
