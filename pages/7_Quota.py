"""Cadenza Quota — quarterly attainment, attainment distribution, ramp curve,
territory balance, and rep scorecard.

Scope is new-business attainment only. Renewals and expansions don't count
toward quota — matches typical SaaS comp structures where AEs are paid on
new-logo bookings while CSMs/AMs handle the post-sale book. See About.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src import quota
from src import viz

st.set_page_config(page_title="Cadenza — Quota", layout="wide")

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "generated"


@st.cache_data
def load_data():
    return quota.load_quota_data(
        DATA_DIR / "reps.csv",
        DATA_DIR / "opportunities.csv",
    )


def _available_quarters(opps: pd.DataFrame) -> list[pd.Period]:
    cd = pd.to_datetime(opps["close_date"])
    quarters = sorted(set(cd.dt.to_period("Q")))
    return quarters


def filter_row(reps: pd.DataFrame, opps: pd.DataFrame) -> dict:
    quarters = _available_quarters(opps)
    default_idx = len(quarters) - 1  # most recent quarter

    c1, c2, c3 = st.columns([2, 2, 2])
    with c1:
        quarter = st.selectbox(
            "Quarter",
            options=quarters,
            index=default_idx,
            format_func=lambda q: f"{q.year}-Q{q.quarter}",
        )
    with c2:
        segment = st.selectbox(
            "Segment", ["All", "SMB", "Mid-Market", "Enterprise"]
        )
    with c3:
        territory = st.selectbox(
            "Territory", ["All", "North", "South", "East", "West"]
        )
    return {"quarter": quarter, "segment": segment, "territory": territory}


def apply_section_filters(opps: pd.DataFrame, reps: pd.DataFrame,
                            f: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Apply segment and territory filters. Quarter is applied per-section
    inside each metric call. Does NOT filter the ramp curve — §2 is longitudinal."""
    filtered_reps = reps.copy()
    filtered_opps = opps.copy()
    if f["territory"] != "All":
        filtered_reps = filtered_reps[filtered_reps["territory"] == f["territory"]]
        filtered_opps = filtered_opps[
            filtered_opps["owner_rep_id"].isin(filtered_reps["rep_id"])
        ]
    if f["segment"] != "All":
        filtered_opps = filtered_opps[filtered_opps["segment"] == f["segment"]]
    return filtered_reps, filtered_opps


def render_kpis(opps: pd.DataFrame, reps: pd.DataFrame, quarter: pd.Period):
    kpis = quota.team_kpis(opps, reps, quarter)

    # Optional: Δ vs prior quarter
    prior_q = quarter - 1
    if prior_q.year >= 2023:  # only if within dataset window
        prior = quota.team_kpis(opps, reps, prior_q)
        delta_team = (kpis["team_attainment_pct"] - prior["team_attainment_pct"]) * 100
        delta_median = (kpis["median_attainment"] - prior["median_attainment"]) * 100
        show_delta = True
    else:
        delta_team = None
        delta_median = None
        show_delta = False

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "Team Attainment",
        f"{kpis['team_attainment_pct']:.0%}",
        f"{delta_team:+.1f} pp" if show_delta else None,
    )
    c2.metric(
        "Reps At/Above Quota",
        f"{kpis['reps_at_or_above']} / {len(reps)}",
    )
    c3.metric(
        "Median Attainment",
        f"{kpis['median_attainment']:.0%}",
        f"{delta_median:+.1f} pp" if show_delta else None,
    )
    c4.metric(
        "At-Risk Count (<70%)",
        kpis["at_risk_count"],
    )
    if not show_delta:
        st.caption("Prior-quarter Δ hidden — selected quarter sits at the dataset edge.")


def render_section_attainment_distribution(opps: pd.DataFrame, reps: pd.DataFrame,
                                              quarter: pd.Period):
    st.subheader("Attainment Distribution")
    dist = quota.attainment_distribution(opps, reps, quarter)
    fig = viz.attainment_distribution_figure(dist, f"{quarter.year}-Q{quarter.quarter}")
    st.plotly_chart(fig, use_container_width=True)


def render_section_ramp_curve(opps_unfiltered: pd.DataFrame,
                                reps_unfiltered: pd.DataFrame):
    st.subheader("Ramp Curve")
    st.caption("Computed across all reps and all months in the dataset — NOT "
               "filtered by the quarter selector. The team reaches full "
               "productivity around month 9, three months later than the "
               "industry-standard 6-month ramp assumption.")
    curve = quota.ramp_curve(opps_unfiltered, reps_unfiltered)
    buckets = quota.ramp_bucket_attainment(opps_unfiltered, reps_unfiltered)
    col_left, col_right = st.columns([3, 2])
    with col_left:
        st.plotly_chart(viz.ramp_curve_figure(curve), use_container_width=True)
    with col_right:
        st.plotly_chart(viz.ramp_bucket_attainment_figure(buckets),
                          use_container_width=True)


def render_section_territory_balance(opps: pd.DataFrame, reps: pd.DataFrame,
                                       quarter: pd.Period):
    st.subheader("Territory & Segment Balance")
    balance = quota.territory_balance(opps, reps, quarter)
    fig = viz.territory_balance_figure(balance, f"{quarter.year}-Q{quarter.quarter}")
    st.plotly_chart(fig, use_container_width=True)


def render_section_scorecard(opps: pd.DataFrame, reps: pd.DataFrame,
                               quarter: pd.Period):
    st.subheader("Rep Scorecard")
    scorecard = quota.rep_scorecard(opps, reps, quarter)
    styled = viz.rep_scorecard_styler(scorecard)
    st.dataframe(styled, use_container_width=True, hide_index=True)


def main():
    st.title("Quota Attainment & Rep Performance")
    st.caption("Per-rep new-business attainment, attainment distribution, ramp "
               "curve, and territory balance. Quota credit is new-business only.")

    reps, opps = load_data()

    with st.container():
        f = filter_row(reps, opps)

    filtered_reps, filtered_opps = apply_section_filters(opps, reps, f)

    st.divider()
    render_kpis(filtered_opps, filtered_reps, f["quarter"])

    st.divider()
    render_section_attainment_distribution(filtered_opps, filtered_reps, f["quarter"])

    st.divider()
    # Ramp curve is longitudinal — uses UNfiltered data
    render_section_ramp_curve(opps, reps)

    st.divider()
    render_section_territory_balance(filtered_opps, filtered_reps, f["quarter"])

    st.divider()
    render_section_scorecard(filtered_opps, filtered_reps, f["quarter"])


main()
