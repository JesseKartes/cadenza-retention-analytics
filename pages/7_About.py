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
        """
    )

    st.divider()

    st.subheader("Metric definitions")
    st.markdown(
        """
        | Metric | Formula | Notes |
        | --- | --- | --- |
        | **ARR** | MRR × 12 | Point-in-time run rate. |
        | **Logo Churn** | customers_churned_in_period ÷ customers_active_at_start | Counts customers. |
        | **Gross Revenue Churn** | (churn_MRR + contraction_MRR) ÷ MRR_at_start | Excludes expansion. |
        | **GRR** | 1 − Gross Revenue Churn, capped at 100% | Floor retention. |
        | **NRR** | (start_MRR − churn − contraction + expansion) ÷ start_MRR | Includes expansion; can exceed 100%. |

        TTM = trailing 12 months. All numerators and denominators use a cohort
        defined as "customers active at the start of the period."
        """
    )

    st.divider()

    st.subheader("Tech stack")
    st.markdown(
        """
        - Python 3.11, pandas, numpy
        - Streamlit (app) + Plotly (charts)
        - pytest (test suite proving metric formulas against hand-built fixtures)
        - GitHub + Streamlit Community Cloud (deployment)
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
