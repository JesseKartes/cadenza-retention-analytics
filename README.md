# Cadenza Retention Analytics

A SaaS retention analytics application I built as a portfolio project while interviewing for Revenue Operations / Sales Operations roles in SaaS.

**Live dashboard:** _TODO link after Streamlit Cloud deploy_

**Author:** Jesse Kartes · [LinkedIn](https://www.linkedin.com/in/_TODO_)

---

## The story

Cadenza is a fictional B2B sales engagement platform. I generated 36 months of synthetic subscription data for 600+ customers across three segments, five acquisition channels, and three plan tiers. I then built a Streamlit application that surfaces the canonical SaaS retention metrics — ARR, NRR, GRR, Logo Churn — plus a cohort retention heatmap.

The dataset deliberately encodes a pattern that real RevOps teams encounter: customers acquired through a Q3 2024 self-serve promotional channel churn at roughly **2× the rate** of customers from other channels. The dashboard's job is to surface that pattern.

## What the dashboard shows

- **Overview** — headline KPIs (ARR ~$X, NRR ~108%, GRR ~91%), MRR waterfall, and trailing-12-month retention trend. At first glance, the company looks healthy.
- **Cohort Analysis** — the heatmap. Filter to "Self-Serve Promo" and the Q3 2024 cohort lights up red.
- **Segment & Channel Deep-Dive** — quantifies the gap. Self-Serve Promo logo churn comes in around 28% — nearly 2× the ~15% average across other channels — while its GRR (~92%) drags the bottom of the table.
- **About** — methodology, metric formulas, and what I'd recommend at a real company (CSM intervention plan, channel-quality scoring, tighter promo gating).

## How it's built

```
Python data generator  →  3 flat CSVs  →  pandas metric/cohort modules  →  Streamlit + Plotly dashboard
```

- `src/data_generator.py` — synthetic data simulator (lifecycle, expansion, contraction, churn, the encoded insight).
- `src/metrics.py` — ARR, Logo Churn, Gross Revenue Churn, GRR, NRR, MRR Waterfall. Pure pandas functions.
- `src/cohorts.py` — logo and revenue retention cohort matrices.
- `src/viz.py` — Plotly figure builders. Pure functions, no Streamlit imports.
- `Overview.py` + `pages/*.py` — four-page dashboard.
- `tests/` — pytest suite. Hand-built fixtures with hand-calculated expected metric values prove the formulas are correct. The data generator has sanity tests that lock in the engineered pattern.

## Running it locally

```bash
git clone https://github.com/_TODO_/cadenza-retention-analytics.git
cd cadenza-retention-analytics
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m src.data_generator   # regenerates the CSVs (optional; a snapshot is committed)
streamlit run Overview.py
```

## Running the tests

```bash
pytest -v
```

## Why I built this

I spent five years owning forecasting and renewal analytics for $250M of new sales and $5M MRR of recurring lease revenue at an industrial company. Translating that experience into SaaS-native language is the bridge this project builds. Every metric, formula, and visual choice in this dashboard is something a SaaS finance or RevOps team would recognize on day one.
