"""About / Methodology — the portfolio narrative wrapper."""
from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="Cadenza — About", layout="wide")


def main():
    st.title("About this project")

    st.markdown(
        """
        **Cadenza** is a (fictional) B2B sales engagement platform. This dashboard
        is a portfolio project demonstrating SaaS revenue operations fluency
        across retention, pipeline, and rep performance. The data is synthetic
        and deterministically generated; the dashboard, the metric calculations,
        and the insights they surface are real.

        ## What this dashboard covers

        Three motions of the SaaS revenue funnel:

        - **Retention** — ARR, NRR, GRR, logo churn, and cohort decay.
          *Overview*, *Cohort Analysis*, *Segment & Channel* pages.
        - **Pipeline & Forecasting** — open pipeline, weighted coverage,
          stage velocity, win rates, and forecast accuracy.
          *Pipeline*, *Forecasting* pages.
        - **Quota & Rep Performance** — quarterly attainment, attainment
          distribution, ramp curves, and territory × segment balance.
          *Quota* page.

        ## Three insights this dashboard surfaces

        ### Insight 1 — Self-Serve Promo churns ~2× faster

        On the surface, Cadenza's retention looks healthy — NRR around 108%,
        GRR around 91%. Decomposed by acquisition channel, a **Self-Serve Promo**
        cohort from Q3 2024 churns at roughly **2× the rate** of other channels.
        Surfaces on the *Cohort Analysis* and *Segment & Channel* pages.

        **What I'd do next at a real company**
        - **Tech-touch CSM motion** for the Self-Serve Promo cohort: contract-end
          outreach 60 days early, value-realization check-ins, expansion offers.
        - **Channel-quality scoring** partnered with marketing: weight new-customer
          acquisitions by M6 retention rate, not just first-month MRR.
        - **Tighter promo gating**: require a minimum 90-day product engagement
          threshold before discount eligibility on future promotional campaigns.

        ### Insight 2 — Mid-Market deals stall in POC ~2× longer

        Mid-Market new-business deals dwell in **Proof of Concept** roughly 2×
        longer than SMB or Enterprise deals, with markedly worse POC → Negotiation
        conversion. The POC motion is built for SMB (fast, self-guided) and
        Enterprise (custom, white-glove); Mid-Market falls in the gap. Surfaces
        on the *Pipeline* page's Stage Velocity Heatmap.

        **What I'd do next at a real company**
        - **Mid-Market-specific POC playbook**: dedicated SE coverage, time-boxed
          to 30 days, with defined success criteria agreed and emailed back to the
          buyer up front.
        - **Segment routing**: define Mid-Market by clear thresholds (revenue band,
          headcount, or tech stack signals) and route those deals to a dedicated
          SE pod — not handled as overgrown SMB or junior Enterprise.
        - **POC exit gates**: if a deal hasn't transitioned to Negotiation within
          45 days, trigger a forced review — escalate, re-scope, or disqualify.

        ### Insight 3 — Ramp is ~9 months, not 6

        The team's longitudinal ramp curve hits full productivity around **month 9**,
        not the industry-standard month 6. New hires below 70% attainment in their
        first two quarters aren't underperforming — they're tracking the team's
        normal ramp. Surfaces on the *Quota* page's ramp curve.

        **What I'd do next at a real company**
        - **Hiring lead times**: start backfill recruiting ~3 months earlier; assume a
          new rep contributes meaningful capacity at month 9, not month 6.
        - **Ramped quota schedule**: 25% / 50% / 100% over a 9-month curve instead of
          front-loading full quota at month 6.
        - **Performance reviews**: separate "tracking to ramp" from "underperforming."
          Reps below 70% in months 0-6 are on-curve, not a coaching problem.

        ## Scope and deferrals

        **Pipeline analysis is new-business only.** Funnel, stage velocity, and
        conversion metrics on the *Pipeline* page assume the five-stage new-business
        cycle. Renewals and expansions exist in the data model and contribute to the
        *Forecasting* page's commit / best-case / pipeline buckets (because a real
        forecast call blends all three motions), but dedicated renewal-management
        and expansion-pipeline analytics — at-risk renewals, gross renewal rate trend,
        expansion attainment, cross-sell mix — are deferred. In a real RevOps stack
        those workflows are typically owned by CSM/AM teams in a separate tool
        surface (e.g., Gainsight for renewals); they deserve their own dashboard
        rather than being grafted onto a new-business funnel.

        **Quota attainment is new-business only.** Renewal and expansion ACV do not
        count toward AE quota. Matches the typical SaaS comp structure where AEs are
        paid on new-logo bookings and CSM/AM teams are paid on renewal & expansion.
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

    st.subheader("Tech stack & architecture")
    st.markdown(
        """
        - Python 3.12, pandas, numpy
        - Streamlit (app) + Plotly (charts)
        - pytest (69 tests, hand-built fixtures with hand-calculated expected values)
        - GitHub + Streamlit Community Cloud (deployment)

        **Architecture:** Pure-function data pipeline. `src/data_generator.py` produces
        deterministic CSVs (seed=42). `src/metrics.py` and `src/cohorts.py` compute
        retention; `src/pipeline.py` and `src/forecast.py` compute pipeline metrics;
        `src/quota.py` computes quota and rep performance. `src/viz.py` builds Plotly
        figures with no Streamlit imports — so charts can be unit-tested or reused
        outside Streamlit. Pages in `Overview.py` and `pages/*.py` are
        presentation-only.
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
