"""Cadenza Retention Analytics — Streamlit entry point + Overview page.

Other pages live in pages/. Streamlit auto-discovers them and renders them
in the sidebar nav.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src import cohorts, metrics, viz

st.set_page_config(
    page_title="Cadenza Retention Analytics",
    page_icon=":bar_chart:",
    layout="wide",
)

DATA_DIR = Path(__file__).resolve().parent / "data" / "generated"


@st.cache_data
def load_data():
    customers = pd.read_csv(DATA_DIR / "customers.csv")
    subs = pd.read_csv(DATA_DIR / "subscriptions.csv")
    events = pd.read_csv(DATA_DIR / "events.csv")
    return customers, subs, events


def sidebar_filters(customers: pd.DataFrame, subs: pd.DataFrame) -> dict:
    st.sidebar.markdown("## Cadenza")
    st.sidebar.caption("Sales engagement platform · fictional · portfolio project")
    st.sidebar.divider()
    st.sidebar.markdown("### Filters")

    months = sorted(subs["month"].unique())
    end_default = months[-1]
    end_month = st.sidebar.selectbox("Reporting month", months, index=len(months) - 1)

    segments = ["All"] + sorted(customers["segment"].unique().tolist())
    segment = st.sidebar.selectbox("Segment", segments)

    channels = ["All"] + sorted(customers["acquisition_channel"].unique().tolist())
    channel = st.sidebar.selectbox("Acquisition channel", channels)

    return {"end_month": end_month, "segment": segment, "channel": channel}


def apply_filters(customers: pd.DataFrame, subs: pd.DataFrame, f: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    cust = customers
    if f["segment"] != "All":
        cust = cust[cust["segment"] == f["segment"]]
    if f["channel"] != "All":
        cust = cust[cust["acquisition_channel"] == f["channel"]]
    subs_f = subs[subs["customer_id"].isin(cust["customer_id"])]
    return cust, subs_f


def render_overview(customers: pd.DataFrame, subs: pd.DataFrame, events: pd.DataFrame, f: dict):
    st.title("Overview")
    st.caption("Cadenza — the canonical SaaS retention dashboard. All data is synthetic.")

    end_month = f["end_month"]
    start_month_ttm = (pd.Timestamp(end_month) - pd.DateOffset(months=12)).strftime("%Y-%m-01")
    prev_month_ttm = (pd.Timestamp(start_month_ttm) - pd.DateOffset(months=12)).strftime("%Y-%m-01")

    cur_arr = metrics.arr(subs, end_month)
    cur_nrr = metrics.nrr(subs, start_month_ttm, end_month)
    cur_grr = metrics.grr(subs, start_month_ttm, end_month)
    cur_logo_churn = metrics.logo_churn(subs, start_month_ttm, end_month)
    cur_rev_churn = metrics.gross_revenue_churn(subs, start_month_ttm, end_month)

    prev_arr = metrics.arr(subs, start_month_ttm) if start_month_ttm in subs["month"].values else None
    prev_nrr = metrics.nrr(subs, prev_month_ttm, start_month_ttm) if prev_month_ttm in subs["month"].values else None

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("ARR", f"${cur_arr:,.0f}",
              delta=f"${cur_arr - prev_arr:,.0f}" if prev_arr else None)
    c2.metric("NRR (TTM)", f"{cur_nrr:.1%}",
              delta=f"{cur_nrr - prev_nrr:+.1%}" if prev_nrr else None)
    c3.metric("GRR (TTM)", f"{cur_grr:.1%}")
    c4.metric("Logo Churn (TTM)", f"{cur_logo_churn:.1%}")
    c5.metric("Gross Revenue Churn (TTM)", f"{cur_rev_churn:.1%}")

    st.divider()

    # MRR Waterfall — last 3 months
    waterfall_start = (pd.Timestamp(end_month) - pd.DateOffset(months=3)).strftime("%Y-%m-01")
    walk = metrics.mrr_waterfall(subs, events[events["customer_id"].isin(customers["customer_id"])],
                                  waterfall_start, end_month)
    st.subheader(f"MRR Waterfall — {waterfall_start} to {end_month}")
    st.plotly_chart(viz.waterfall_figure(walk), use_container_width=True)

    # NRR / GRR monthly trend (rolling 12-month)
    months = sorted(subs["month"].unique())
    trend_rows = []
    for m in months:
        start = (pd.Timestamp(m) - pd.DateOffset(months=12)).strftime("%Y-%m-01")
        if start not in months:
            continue
        trend_rows.append({
            "month": m,
            "NRR": metrics.nrr(subs, start, m),
            "GRR": metrics.grr(subs, start, m),
        })
    trend = pd.DataFrame(trend_rows)
    if not trend.empty:
        st.subheader("NRR and GRR — trailing 12-month, by reporting month")
        st.plotly_chart(viz.trend_figure(trend, "month", ["NRR", "GRR"],
                                          "Retention Trend", reference=1.0),
                        use_container_width=True)


def main():
    customers, subs, events = load_data()
    f = sidebar_filters(customers, subs)
    cust_f, subs_f = apply_filters(customers, subs, f)
    render_overview(cust_f, subs_f, events, f)


if __name__ == "__main__":
    main()
