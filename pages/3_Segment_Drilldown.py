"""Segment & Channel Deep-Dive — quantifies the cohort insight.

Shows NRR/GRR/Logo Churn split by segment and channel, plus an explorable
account table.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src import metrics

st.set_page_config(page_title="Cadenza — Segment & Channel", layout="wide")

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "generated"


@st.cache_data
def load_data():
    customers = pd.read_csv(DATA_DIR / "customers.csv")
    subs = pd.read_csv(DATA_DIR / "subscriptions.csv")
    return customers, subs


def metrics_by_group(customers: pd.DataFrame, subs: pd.DataFrame,
                     group_col: str, start_month: str, end_month: str) -> pd.DataFrame:
    rows = []
    for value in sorted(customers[group_col].unique()):
        group_ids = customers[customers[group_col] == value]["customer_id"]
        group_subs = subs[subs["customer_id"].isin(group_ids)]
        rows.append({
            group_col: value,
            "NRR": metrics.nrr(group_subs, start_month, end_month),
            "GRR": metrics.grr(group_subs, start_month, end_month),
            "Logo Churn": metrics.logo_churn(group_subs, start_month, end_month),
        })
    return pd.DataFrame(rows)


def main():
    st.title("Segment & Channel Deep-Dive")
    st.caption("This is where the headline numbers get decomposed. The engineered insight: "
               "Self-Serve Promo has noticeably worse retention than other channels.")

    customers, subs = load_data()

    months = sorted(subs["month"].unique())
    end_month = st.selectbox("Reporting month", months, index=len(months) - 1)
    start_month = (pd.Timestamp(end_month) - pd.DateOffset(months=12)).strftime("%Y-%m-01")
    st.caption(f"Trailing 12 months: {start_month} → {end_month}")

    st.subheader("By Segment")
    seg_df = metrics_by_group(customers, subs, "segment", start_month, end_month)
    st.dataframe(
        seg_df.style.format({"NRR": "{:.1%}", "GRR": "{:.1%}", "Logo Churn": "{:.1%}"}),
        use_container_width=True,
    )

    st.subheader("By Acquisition Channel")
    chan_df = metrics_by_group(customers, subs, "acquisition_channel", start_month, end_month)
    chan_df = chan_df.sort_values("GRR")
    st.dataframe(
        chan_df.style.format({"NRR": "{:.1%}", "GRR": "{:.1%}", "Logo Churn": "{:.1%}"})
                     .highlight_min(subset=["GRR", "NRR"], color="#FECACA")
                     .highlight_max(subset=["Logo Churn"], color="#FECACA"),
        use_container_width=True,
    )
    st.caption(
        "Red marks the worst-performing channel on each metric (lowest GRR/NRR, "
        "highest Logo Churn). The highlight follows the data — if a different "
        "channel becomes the laggard, the highlight moves with it."
    )

    st.divider()
    st.subheader("Account Explorer")
    st.caption("Filter to the channel/segment of interest and inspect individual customer trajectories.")

    col1, col2 = st.columns(2)
    seg_filter = col1.selectbox("Segment", ["All"] + sorted(customers["segment"].unique().tolist()))
    chan_filter = col2.selectbox("Channel", ["All"] + sorted(customers["acquisition_channel"].unique().tolist()))

    view = customers.copy()
    if seg_filter != "All":
        view = view[view["segment"] == seg_filter]
    if chan_filter != "All":
        view = view[view["acquisition_channel"] == chan_filter]

    # Add lifecycle status: active at end_month or churned
    active_end = set(subs[(subs["month"] == end_month) & (subs["status"] == "active")]["customer_id"])
    view = view.assign(status=view["customer_id"].apply(lambda x: "active" if x in active_end else "churned"))
    cur_mrr = subs[subs["month"] == end_month].set_index("customer_id")["mrr"]
    view = view.assign(current_mrr=view["customer_id"].map(cur_mrr).fillna(0).round(0))

    display_cols = ["customer_id", "company_name", "segment", "acquisition_channel",
                    "signup_cohort", "plan_tier_initial", "current_mrr", "status"]
    st.dataframe(view[display_cols], use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
