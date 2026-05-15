"""Cadenza Pipeline — new-business pipeline coverage, stage velocity,
conversion, and aging.

Scope is intentionally net-new acquisition only. Renewal and expansion
pipelines are tracked separately (deferred — see About page).

The hero viz is the Stage Velocity Heatmap, which surfaces the engineered
'Mid-Market POC stall' insight without further drilling.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src import pipeline as pl
from src import viz

st.set_page_config(page_title="Cadenza — Pipeline", layout="wide")

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "generated"


@st.cache_data
def load_data():
    opps = pd.read_csv(DATA_DIR / "opportunities.csv")
    history = pd.read_csv(DATA_DIR / "opportunity_stage_history.csv")
    return opps, history


def sidebar_filters(opps: pd.DataFrame) -> dict:
    st.sidebar.markdown("## Cadenza")
    st.sidebar.caption("Sales engagement platform · fictional · portfolio project")
    st.sidebar.divider()
    st.sidebar.markdown("### Filters")

    as_of = st.sidebar.date_input("As-of date", value=pd.Timestamp("2025-12-01"))
    segments = ["All"] + sorted(opps["segment"].unique().tolist())
    segment = st.sidebar.selectbox("Segment", segments)
    channels = ["All"] + sorted(opps["acquisition_channel"].unique().tolist())
    channel = st.sidebar.selectbox("Acquisition channel", channels)
    return {"as_of": as_of.strftime("%Y-%m-%d"), "segment": segment, "channel": channel}


def apply_filters(opps: pd.DataFrame, f: dict) -> pd.DataFrame:
    v = opps
    if f["segment"] != "All":
        v = v[v["segment"] == f["segment"]]
    if f["channel"] != "All":
        v = v[v["acquisition_channel"] == f["channel"]]
    return v


def main():
    st.title("New Business Pipeline")
    st.caption("Net-new acquisition deals only. Renewal and expansion pipelines "
               "use different stage flows and are deferred to a future phase — "
               "see the About page. The Stage Velocity Heatmap surfaces a "
               "Mid-Market POC stall.")

    opps_all, history_all = load_data()
    # Lock to new business — renewal/expansion analytics are out of scope here.
    opps_all = opps_all[opps_all["opportunity_type"] == "new_business"]

    f = sidebar_filters(opps_all)
    opps = apply_filters(opps_all, f)

    # Editable target
    target = st.sidebar.number_input("Quarterly pipeline target ($)",
                                      min_value=0, value=5_000_000, step=100_000)

    # KPIs
    cur_total = pl.total_pipeline(opps, f["as_of"])
    cur_weighted = pl.weighted_pipeline(opps, f["as_of"])
    cur_coverage = pl.pipeline_coverage(opps, target, f["as_of"])
    ttm_start = (pd.Timestamp(f["as_of"]) - pd.DateOffset(months=12)).strftime("%Y-%m-01")
    cur_win = pl.win_rate(opps, ttm_start, f["as_of"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Pipeline", f"${cur_total:,.0f}")
    c2.metric("Weighted Pipeline", f"${cur_weighted:,.0f}")
    c3.metric("Coverage Ratio", f"{cur_coverage:.2f}×",
              delta="healthy" if cur_coverage >= 3.0 else "below 3×",
              delta_color="normal" if cur_coverage >= 3.0 else "inverse")
    c4.metric("Win Rate (TTM)", f"{cur_win:.1%}")

    st.divider()

    # Pipeline by Stage (horizontal bar)
    st.plotly_chart(viz.pipeline_by_stage_figure(opps, f["as_of"]), use_container_width=True)

    # Stage Velocity Heatmap — hero viz
    st.subheader("Stage Velocity by Segment")
    st.caption("Average days each segment spends in each stage. "
               "Watch the Proof of Concept column.")
    history = history_all[history_all["opportunity_id"].isin(opps["opportunity_id"])]
    st.plotly_chart(
        viz.stage_velocity_heatmap(history, opps, ttm_start, f["as_of"]),
        use_container_width=True,
    )

    # Stage Conversion Table
    st.subheader("Stage-to-Stage Conversion")
    transitions = [
        ("Discovery", "Qualification"),
        ("Qualification", "Proof of Concept"),
        ("Proof of Concept", "Negotiation"),
        ("Negotiation", "Closed Won"),
    ]
    seg_rows = []
    for seg in ["SMB", "Mid-Market", "Enterprise"]:
        seg_opp_ids = opps[opps["segment"] == seg]["opportunity_id"]
        seg_hist = history_all[history_all["opportunity_id"].isin(seg_opp_ids)]
        row = {"segment": seg}
        for fr, to in transitions:
            if to == "Closed Won":
                won_ids = set(opps[
                    (opps["segment"] == seg) & (opps["status"] == "closed_won")
                ]["opportunity_id"])
                neg_entered_ids = set(seg_hist[seg_hist["stage"] == "Negotiation"]["opportunity_id"])
                rate = len(won_ids & neg_entered_ids) / len(neg_entered_ids) if neg_entered_ids else 0.0
            else:
                rate = pl.stage_conversion(seg_hist, fr, to, ttm_start, f["as_of"])
            row[f"{fr[:4]}→{to[:4]}"] = rate
        seg_rows.append(row)
    conv_df = pd.DataFrame(seg_rows).set_index("segment")
    st.dataframe(
        conv_df.style.format("{:.0%}").highlight_min(axis=0, color="#FECACA"),
        use_container_width=True,
    )

    # Aging Deals
    st.subheader("Aging Deals — open > 60 days in current stage")
    aging = pl.aging_deals(opps, history_all, f["as_of"], threshold_days=60)
    if len(aging) == 0:
        st.info("No aging deals. (Threshold = 60 days in current stage.)")
    else:
        display_cols = ["opportunity_id", "account_name", "segment", "current_stage",
                        "days_in_current_stage", "amount", "owner_rep_id"]
        st.dataframe(
            aging[display_cols].head(50),
            use_container_width=True,
            hide_index=True,
            column_config={"amount": st.column_config.NumberColumn(format="$%.0f")},
        )


if __name__ == "__main__":
    main()
