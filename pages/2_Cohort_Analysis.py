"""Cohort Analysis page — the hero visualization.

Flipping the acquisition-channel filter to 'Self-Serve Promo' should make
the Q3 2024 cohort visibly underperform — that's the engineered insight.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src import cohorts, viz

st.set_page_config(page_title="Cadenza — Cohort Analysis", layout="wide")

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "generated"


@st.cache_data
def load_data():
    customers = pd.read_csv(DATA_DIR / "customers.csv")
    subs = pd.read_csv(DATA_DIR / "subscriptions.csv")
    return customers, subs


def main():
    st.title("Cohort Analysis")
    st.markdown(
        """
        **How to read this heatmap:** each **row** is a group of customers who
        signed up in the same month (the *cohort*). Each **column** is months
        since signup. Cells show what share of the cohort is still active at
        that age. **Read across a row** to see how a cohort decays over time;
        **read down a column** to compare cohorts at the same age. Blank cells
        mean the cohort hasn't reached that age yet (its M12 is still in the
        future, for example).
        """
    )

    customers, subs = load_data()

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        view = st.radio("View", ["Logo retention", "Revenue retention"], horizontal=True)
    with col2:
        channels = ["All"] + sorted(customers["acquisition_channel"].unique().tolist())
        channel = st.selectbox("Acquisition channel", channels)
    with col3:
        segments = ["All"] + sorted(customers["segment"].unique().tolist())
        segment = st.selectbox("Segment", segments)

    cust = customers
    if channel != "All":
        cust = cust[cust["acquisition_channel"] == channel]
    if segment != "All":
        cust = cust[cust["segment"] == segment]
    subs_f = subs[subs["customer_id"].isin(cust["customer_id"])]

    if view == "Logo retention":
        matrix = cohorts.logo_retention_matrix(subs_f, cust)
        title = "Logo Retention Cohort"
    else:
        matrix = cohorts.revenue_retention_matrix(subs_f, cust)
        title = "Revenue Retention Cohort"

    if matrix.empty:
        st.warning("No data for the selected filters.")
        return

    st.plotly_chart(viz.cohort_heatmap(matrix, title), use_container_width=True)

    # Highlight the engineered cohorts when looking at all channels or self-serve
    promo_cohorts = ["2024-07", "2024-08", "2024-09"] if channel in ("All", "Self-Serve Promo") else None
    st.plotly_chart(viz.m12_retention_bar(matrix, highlight_cohorts=promo_cohorts),
                    use_container_width=True)

    if channel == "Self-Serve Promo":
        st.info(
            "**Insight:** The Q3 2024 Self-Serve Promo cohort (Jul/Aug/Sep 2024) "
            "shows materially worse retention than other channels. This pattern "
            "is invisible in company-wide headlines but emerges here. See the "
            "**Segment & Channel Deep-Dive** page for the quantified gap."
        )


if __name__ == "__main__":
    main()
