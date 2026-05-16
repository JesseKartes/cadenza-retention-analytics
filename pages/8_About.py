"""About / Methodology — the portfolio narrative wrapper."""
from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="Cadenza — About", layout="wide")


def main():
    st.title("About this project")

    st.markdown(
        """
        **Cadenza Retention Analytics** is a portfolio project demonstrating SaaS
        revenue operations fluency. The data is synthetic. The dashboard, the metric
        calculations, and the insight it surfaces are real.

        ## The story
        Cadenza is a (fictional) B2B sales engagement platform. On the surface,
        the company's retention metrics look healthy — NRR around 108%, GRR around 91%.
        But when you decompose by acquisition channel, a **Self-Serve Promo** cohort
        from Q3 2024 churns at roughly **2× the rate** of customers from other channels.
        The Cohort Analysis and Segment & Channel pages of this dashboard surface that
        pattern.

        ## What I'd do next at a real company
        - **CSM intervention playbook** for the Self-Serve Promo cohort: contract-end
          outreach 60 days early, value-realization check-ins, expansion offers.
        - **Channel-quality scoring** partnered with marketing: weight new-customer
          acquisitions by 12-month retention probability, not just first-month MRR.
        - **Tighter promo gating**: require a minimum 90-day product engagement
          threshold before discount eligibility on future promotional campaigns.

        ## Phase 2 — Pipeline & Forecasting

        Phase 2 adds opportunity-level data on top of the Phase 1 subscription model.
        Each non-Self-Serve Phase 1 customer was won as a new-business opportunity
        that closed on their signup date; each annual renewal and each Phase 1
        upgrade event spawns its own opportunity record. Self-Serve Promo customers
        have no opportunity (self-serve is no-touch).

        Three motions are modeled distinctly:

        - **New Business** — five-stage cycle (Discovery → Qualification → POC → Negotiation → Closed)
        - **Renewal** — short two-stage cycle on each annual anniversary; lost renewals align
          to Phase 1 churn events within ±30 days
        - **Expansion** — one-stage cycle, closes on the date of the Phase 1 upgrade event

        The engineered Phase 2 insight: **Mid-Market deals stall in Proof of Concept ~2×
        longer than SMB or Enterprise**, with markedly worse POC → Negotiation conversion.
        Surfaces in the Stage Velocity Heatmap on the Pipeline page. The recommendation:
        the POC motion is built for SMB (fast, self-guided) and Enterprise (custom,
        white-glove); Mid-Market falls in the gap and needs its own playbook.

        ### Scope and deferrals

        The Pipeline page is scoped to **net-new acquisition only** — the funnel,
        stage velocity, and conversion analyses all assume the new-business
        five-stage cycle. Renewals and expansions exist in the data model and
        feed the Forecasting page's commit/best-case/pipeline buckets (because
        a real forecast call blends all three motions), but dedicated
        renewal-management and expansion-pipeline analytics — at-risk renewals,
        gross renewal rate trend, expansion attainment, cross-sell mix — are
        **deferred to a future phase (Phase 2.5+)**. In a real RevOps stack
        those workflows are typically owned by CSM/AM teams in a separate
        tool surface (e.g., Gainsight for renewals); they deserve their own
        page rather than being grafted onto a new-business funnel.

        - **Quota is new-business only.** Renewal and expansion bookings do not count
          toward AE attainment. Matches how most SaaS organizations separate AE comp
          from CSM/AM comp. Renewal and expansion analytics live on the Pipeline and
          Forecasting pages.
        """
    )

    st.markdown("---")
    st.markdown("### Phase 3: Quota Attainment & Rep Performance")
    st.markdown(
        """
The Quota page surfaces rep-level performance: quarterly attainment,
attainment distribution across the team, a longitudinal ramp curve, and
territory × segment balance. Twelve reps carry tiered quotas
(SMB \\$80K, Mid-Market \\$150K, Enterprise \\$500K per quarter) and are
staggered across hire cohorts — four veterans (hired pre-2023), four
mid-tenure, four still ramping at dataset end.
Tiers calibrated against the dataset's actual per-rep deal volume so attainment percentages land in a realistic 30-150% range across the team.

**Hidden insight #3 — ramp longer than assumed.** The team's actual ramp curve
hits full productivity around month 9, not the industry-standard month 6.
New hires below 70% attainment aren't underperforming — they're tracking
the team's normal ramp. Adjust hiring lead times and ramped-quota schedules
accordingly.

**Quota scope:** new-business only. Renewal and expansion ACV do not count
toward attainment. Matches typical SaaS comp structures where AEs are paid
on new-logo bookings.
"""
    )

    st.divider()

    st.subheader("Metric definitions")
    st.markdown(
        """
        **Phase 1 — Retention**

        | Metric | Formula | Notes |
        | --- | --- | --- |
        | **ARR** | MRR × 12 | Point-in-time run rate. |
        | **Logo Churn** | customers_churned_in_period ÷ customers_active_at_start | Counts customers. |
        | **Gross Revenue Churn** | (churn_MRR + contraction_MRR) ÷ MRR_at_start | Excludes expansion. |
        | **GRR** | 1 − Gross Revenue Churn, capped at 100% | Floor retention. |
        | **NRR** | (start_MRR − churn − contraction + expansion) ÷ start_MRR | Includes expansion; can exceed 100%. |

        **Phase 2 — Pipeline & Forecasting**

        | Metric | Formula | Notes |
        | --- | --- | --- |
        | **Total Pipeline** | sum(amount) for open opps with created_date ≤ as_of | Includes all opp types unless filtered. |
        | **Weighted Pipeline** | sum(amount × stage_probability) for open opps | Discovery 10%, Qualification 20%, POC 40%, Negotiation 65%. |
        | **Pipeline Coverage** | total_pipeline ÷ quarter_target | Reported as a multiple; 3.0× is the conventional healthy threshold. |
        | **Win Rate (TTM)** | closed_won ÷ (closed_won + closed_lost) over close_date window | Pipeline page reports new-business win rate. Real-world: renewals win ~90%, new business ~25–35%. |
        | **Avg Sales Cycle (days)** | mean(close_date − created_date) for closed-won in window | Closed-won only; loss cycles distort. |
        | **Avg Days in Stage** | mean(days_in_stage) over completed (exited) stage occupancies in window | Excludes in-progress stages. |
        | **Stage Conversion** | of deals that exited from_stage, fraction that ever reached to_stage | Excludes deals still in from_stage. |
        | **Forecast Buckets** | sum by category: Negotiation = Commit, POC/Renewal/Expansion Disc = Best Case, Discovery/Qual = Pipeline | Standard RevOps categorization. |
        | **Forecast Accuracy** | weighted_pipeline at snapshot ÷ actual closed-won in [snapshot, snapshot + 3mo) | 1.0 = perfect; >1.0 = over-forecast; <1.0 = under-forecast. |

        **Phase 3 — Quota Attainment & Rep Performance**

        | Metric | Formula | Notes |
        | --- | --- | --- |
        | **Quarterly Attainment %** | sum(closed_won amount for rep in quarter) ÷ quarterly_quota | New-business only. |
        | **Team Attainment %** | sum(all closed_won amount in quarter) ÷ sum(all reps' quarterly_quota) | Blended across all active reps. |
        | **Rep Win Rate** | closed_won_count ÷ (closed_won_count + closed_lost_count) | New-business deals closing in the quarter, per rep. |
        | **Avg Deal Size (per rep)** | mean(amount) across rep's closed-won deals in quarter | New-business only. |
        | **Avg Cycle Time (per rep)** | mean(close_date − created_date) in days across rep's closed-won deals in quarter | Closed-won only. |
        | **Tenure Months** | (reference_date − hire_date).days ÷ 30.44 | Continuous tenure in months. |
        | **Rolling-3mo Attainment** | closed_won_3mo ÷ quarterly_quota | Used in the ramp curve to smooth month-to-month volatility. |
        | **Ramp Tenure Bucket** | One of: 0–3, 3–6, 6–12, 12+ months | Groups reps by tenure band for ramp analysis. |

        TTM = trailing 12 months. All numerators and denominators use a cohort
        defined as "customers active at the start of the period."
        """
    )

    st.divider()

    st.subheader("Tech stack")
    st.markdown(
        """
        - Python 3.12, pandas, numpy
        - Streamlit (app) + Plotly (charts)
        - pytest (~44 tests across two phases, hand-built fixtures)
        - GitHub + Streamlit Community Cloud (deployment)

        **Architecture:** Pure-function data pipeline. `src/data_generator.py` produces
        deterministic CSVs (seed=42). `src/metrics.py` + `src/cohorts.py` compute
        retention; `src/pipeline.py` + `src/forecast.py` compute pipeline metrics.
        `src/viz.py` builds Plotly figures with no Streamlit imports. Pages in
        `Overview.py` and `pages/*.py` are presentation-only.
        """
    )

    st.subheader("Links")
    st.markdown(
        """
        - **Source code:** https://github.com/JesseKartes/cadenza-retention-analytics
        - **Live dashboard:** https://cadenza-retention-analytics.streamlit.app
        - **Author:** [Jesse Kartes](https://www.linkedin.com/in/jessekartes/) — RevOps / Sales Operations
        """
    )


if __name__ == "__main__":
    main()
