"""Plotly figure builders for the Cadenza dashboard.

All functions take plain pandas DataFrames / Python scalars and return
plotly.graph_objects.Figure objects. They are independent of Streamlit
so they can be unit-tested or reused.
"""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


# Cadenza brand palette
CADENZA_PRIMARY = "#1F3A8A"      # deep indigo
CADENZA_ACCENT = "#06B6D4"        # cyan
CADENZA_GOOD = "#10B981"          # green
CADENZA_BAD = "#EF4444"           # red
CADENZA_NEUTRAL = "#94A3B8"       # slate


def waterfall_figure(walk: dict[str, float]) -> go.Figure:
    """SaaS MRR Waterfall: Starting -> New -> Expansion -> Contraction -> Churn -> Ending."""
    fig = go.Figure(
        go.Waterfall(
            measure=["absolute", "relative", "relative", "relative", "relative", "total"],
            x=["Starting MRR", "+ New", "+ Expansion", "- Contraction", "- Churn", "Ending MRR"],
            y=[walk["starting"], walk["new"], walk["expansion"], walk["contraction"], walk["churn"], walk["ending"]],
            connector={"line": {"color": CADENZA_NEUTRAL}},
            increasing={"marker": {"color": CADENZA_GOOD}},
            decreasing={"marker": {"color": CADENZA_BAD}},
            totals={"marker": {"color": CADENZA_PRIMARY}},
        )
    )
    fig.update_layout(
        title="MRR Waterfall",
        showlegend=False,
        yaxis_title="MRR ($)",
        height=420,
    )
    return fig


def trend_figure(df: pd.DataFrame, x_col: str, y_cols: list[str],
                 title: str, reference: float | None = None) -> go.Figure:
    """Line chart with optional horizontal reference (e.g., 100% for NRR/GRR)."""
    fig = go.Figure()
    palette = [CADENZA_PRIMARY, CADENZA_ACCENT, CADENZA_NEUTRAL]
    for i, col in enumerate(y_cols):
        fig.add_trace(go.Scatter(
            x=df[x_col], y=df[col], mode="lines+markers",
            name=col, line={"color": palette[i % len(palette)]}
        ))
    if reference is not None:
        fig.add_hline(y=reference, line_dash="dash", line_color=CADENZA_NEUTRAL,
                      annotation_text=f"{reference:.0%}", annotation_position="right")
    fig.update_layout(title=title, height=380, yaxis_tickformat=".0%")
    return fig


def cohort_heatmap(matrix: pd.DataFrame, title: str) -> go.Figure:
    """Cohort retention heatmap with diverging color scale around 100%."""
    z = matrix.values
    fig = go.Figure(
        go.Heatmap(
            z=z,
            x=[f"M{c}" for c in matrix.columns],
            y=matrix.index.astype(str),
            colorscale=[
                [0.0, CADENZA_BAD],
                [0.5, "#FCD34D"],
                [0.8, CADENZA_GOOD],
                [1.0, CADENZA_PRIMARY],
            ],
            zmin=0, zmax=1.2,
            colorbar={"title": "Retention", "tickformat": ".0%"},
            hovertemplate="Cohort %{y}<br>%{x}<br>Retention: %{z:.1%}<extra></extra>",
        )
    )
    fig.update_layout(
        title=title,
        height=560,
        xaxis_title="Months since signup",
        yaxis_title="Signup cohort",
        yaxis_autorange="reversed",
    )
    return fig


def m12_retention_bar(matrix: pd.DataFrame, highlight_cohorts: list[str] | None = None) -> go.Figure:
    """Bar chart of each cohort's M12 retention, sorted ascending."""
    if 12 not in matrix.columns:
        return go.Figure().update_layout(title="M12 retention (not enough history)")
    s = matrix[12].dropna().sort_values()
    colors = [CADENZA_BAD if (highlight_cohorts and c in highlight_cohorts) else CADENZA_PRIMARY for c in s.index]
    fig = go.Figure(go.Bar(x=s.index.astype(str), y=s.values, marker_color=colors))
    fig.add_hline(y=s.mean(), line_dash="dash", line_color=CADENZA_NEUTRAL,
                  annotation_text=f"Average across cohorts: {s.mean():.0%}",
                  annotation_position="right")
    fig.update_layout(
        title="M12 Retention by Signup Cohort",
        yaxis_tickformat=".0%",
        height=400,
    )
    return fig


def grouped_metric_bar(df: pd.DataFrame, group_col: str, value_col: str, title: str,
                       is_percent: bool = True) -> go.Figure:
    """Bar chart of a metric grouped by segment/channel."""
    fig = px.bar(df, x=group_col, y=value_col, title=title,
                 color_discrete_sequence=[CADENZA_PRIMARY])
    if is_percent:
        fig.update_layout(yaxis_tickformat=".0%")
    fig.update_layout(height=380)
    return fig


def stage_funnel_figure(opps: pd.DataFrame, as_of_date: str) -> go.Figure:
    """Funnel of total pipeline $ by stage, new_business deals only.

    Stages in NB order; bars colored from cyan (early) to indigo (late).
    """
    nb_open = opps[
        (opps["opportunity_type"] == "new_business")
        & (opps["status"] == "open")
        & (opps["created_date"] <= as_of_date)
    ]
    stages = ["Discovery", "Qualification", "Proof of Concept", "Negotiation"]
    by_stage = nb_open.groupby("current_stage")["amount"].sum().reindex(stages, fill_value=0)

    fig = go.Figure(go.Funnel(
        y=stages,
        x=by_stage.values,
        textinfo="value+percent initial",
        marker={"color": [CADENZA_ACCENT, "#0EA5E9", CADENZA_PRIMARY, "#0F172A"]},
    ))
    fig.update_layout(
        title="Pipeline by Stage (New Business)",
        height=420,
        xaxis_title="Pipeline ($)",
    )
    return fig


def stage_velocity_heatmap(history: pd.DataFrame, opps: pd.DataFrame,
                            start_date: str, end_date: str) -> go.Figure:
    """Heatmap of average days-in-stage, rows=segment, cols=new_business stage.

    Cell color: green (fast) to red (slow) via the Cadenza palette. This is
    where the Mid-Market POC stall pops visually.
    """
    nb_opps = opps[opps["opportunity_type"] == "new_business"]
    poc = history[history["exited_date"].notna()].copy()
    poc["entered_date"] = pd.to_datetime(poc["entered_date"])
    poc = poc[
        (poc["entered_date"] >= pd.Timestamp(start_date))
        & (poc["entered_date"] < pd.Timestamp(end_date))
    ]
    joined = poc.merge(nb_opps[["opportunity_id", "segment"]], on="opportunity_id", how="inner")

    stages = ["Discovery", "Qualification", "Proof of Concept", "Negotiation"]
    segments = ["SMB", "Mid-Market", "Enterprise"]
    matrix = (
        joined.groupby(["segment", "stage"])["days_in_stage"].mean()
        .unstack(level="stage")
        .reindex(index=segments, columns=stages)
    )

    fig = go.Figure(go.Heatmap(
        z=matrix.values,
        x=stages,
        y=segments,
        colorscale=[[0.0, CADENZA_GOOD], [0.5, "#FCD34D"], [1.0, CADENZA_BAD]],
        text=matrix.round(1).values,
        texttemplate="%{text} days",
        colorbar={"title": "Avg days"},
        hovertemplate="%{y} · %{x}<br>Avg %{z:.1f} days<extra></extra>",
    ))
    fig.update_layout(
        title="Stage Velocity — Average Days in Stage, by Segment",
        height=360,
        xaxis_title="Stage",
        yaxis_title="Segment",
    )
    return fig


def forecast_buckets_figure(buckets: dict[str, float], target: float | None = None) -> go.Figure:
    """Horizontal stacked bar: Commit / Best Case / Pipeline for a single snapshot."""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=["Forecast"], x=[buckets["commit"]], name="Commit",
        orientation="h", marker_color=CADENZA_PRIMARY,
        text=f"${buckets['commit']:,.0f}", textposition="inside",
    ))
    fig.add_trace(go.Bar(
        y=["Forecast"], x=[buckets["best_case"]], name="Best Case",
        orientation="h", marker_color=CADENZA_ACCENT,
        text=f"${buckets['best_case']:,.0f}", textposition="inside",
    ))
    fig.add_trace(go.Bar(
        y=["Forecast"], x=[buckets["pipeline"]], name="Pipeline",
        orientation="h", marker_color=CADENZA_NEUTRAL,
        text=f"${buckets['pipeline']:,.0f}", textposition="inside",
    ))
    if target is not None:
        fig.add_vline(x=target, line_dash="dash", line_color=CADENZA_BAD,
                      annotation_text=f"Target: ${target:,.0f}", annotation_position="top")
    fig.update_layout(
        barmode="stack",
        title="Forecast Buckets",
        height=200,
        xaxis_title="$",
        showlegend=True,
    )
    return fig


def forecast_bias_bar(bias: pd.DataFrame) -> go.Figure:
    """Grouped bar: per-segment weighted_forecast vs. actual_closed_won."""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=bias["segment"], y=bias["weighted_forecast"], name="Weighted Forecast",
        marker_color=CADENZA_PRIMARY,
    ))
    fig.add_trace(go.Bar(
        x=bias["segment"], y=bias["actual_closed_won"], name="Actual Closed-Won",
        marker_color=CADENZA_ACCENT,
    ))
    fig.update_layout(
        barmode="group",
        title="Forecast vs. Actual — by Segment",
        height=380,
        yaxis_title="$",
    )
    return fig
