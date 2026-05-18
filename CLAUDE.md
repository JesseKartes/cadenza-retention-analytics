# Cadenza Retention Analytics

SaaS retention analytics portfolio project. **Phase 1** (retention metrics + cohort analysis), **Phase 2** (Pipeline & Forecasting), and **Phase 3** (Quota & Rep Performance) are shipped and live. A **Tableau Public companion** (2026-05-17) mirrors the analysis in a four-dashboard workbook for tooling versatility.

**Live Streamlit dashboard:** https://cadenza-retention-analytics.streamlit.app
**Tableau Public companion:** https://public.tableau.com/app/profile/jesse.kartes/viz/Cadenza/CadenzaRetention

The dataset deliberately encodes a hidden insight: the Q3 2024 Self-Serve Promo cohort churns at ~2× the rate of other channels. The dashboard's job is to surface that pattern.

## Quick commands

```bash
source .venv/bin/activate
pytest -v                                   # 81 tests; must stay green
streamlit run Overview.py                   # local dashboard at :8501
python -m src.data_generator                # regenerate generated CSVs (deterministic, seed=42)
python -m scripts.build_tableau_extracts    # regenerate Tableau-friendly extracts in data/tableau/
bash scripts/build_plan_html.sh             # regenerate the browser-friendly Tableau build guide
```

## Architecture

```
src/data_generator.py → data/generated/*.csv (customers, subscriptions, events, opportunities, opportunity_stage_history, pipeline_snapshots, reps)
                          │
                          ├──→ src/{metrics,cohorts,pipeline,forecast,quota}.py → src/viz.py → Overview.py + pages/ (Streamlit)
                          │
                          └──→ scripts/build_tableau_extracts.py → data/tableau/*.csv → tableau/cadenza.twb (Tableau Public)
```

- `src/*.py` modules are **pure functions** — no IO, no Streamlit imports, no global state.
- The entry script is `Overview.py` (not `streamlit_app.py` — renamed so the sidebar reads "Overview").
- Generated CSVs are committed to the repo because Streamlit Cloud doesn't regenerate them.
- `src/viz.py` returns `plotly.graph_objects.Figure` objects; Streamlit pages just wrap them in `st.plotly_chart`.
- The Tableau extracts pipeline is **read-only** — it calls existing `src/*.py` functions and writes long-format CSVs. Never modify `src/*.py` to suit Tableau; metric definitions are owned by Phase 1-3 and Tableau adapts.

## Conventions

- **TDD with hand-built fixtures** in `tests/conftest.py`. Fixture comments document hand-calculated expected metric values — the fixtures are the contract.
- **Conventional commits** (`feat:`, `fix:`, `docs:`, `test:`, `polish:`, `ops:`, `chore:`).
- **Cadenza brand palette** is defined as constants in `src/viz.py`. Don't introduce new colors.
- **Metric formulas** are surfaced in docstrings AND in the About page's metric table. Keep both in sync.

## Gotchas

- **Streamlit Cloud Python version** is set in the deploy UI (Settings → Python version), **not** via `runtime.txt` or `.python-version`. Locked deps require Python 3.12.
- **Cohort matrices** distinguish "cohort hasn't reached this age yet" (NaN, blank in heatmap) from "everyone churned" (0.0, red). The `_mask_future_months` helper in `src/cohorts.py` is what enforces this; don't bypass it by filling NaN with 0.
- **Dataset window is Jan 2023 – Dec 2025.** YoY deltas need ≥24 months of prior data, so they only appear for reporting months from Jan 2025 onward. The Overview page surfaces this explicitly when it applies.
- **Don't reintroduce dropped code.** `streamlit_app.py` (renamed), the Gross Revenue Churn KPI tile (redundant with GRR), and the `s > 0` filter in `m12_retention_bar` (made unnecessary by the NaN fix) were all removed for reasons. Check `CHANGELOG.md` before reviving anything.

## Starting Phase 4

Phase 3 (Quota & Rep Performance) is complete. Read `docs/superpowers/phase3-retrospective.md` first (it's the most recent and lists what NOT to touch, plus suggested Phase 4 directions). Phase 2's retrospective adds deeper architectural context if needed. Then invoke `superpowers:brainstorming` to design the next phase.

Phase 4 will live in the same repo. Same fixtures pattern, same brand palette, same commit conventions. About page lives at `pages/8_About.py`; any new page should be inserted before it and About renumbered accordingly. **Mandatory new step:** after any viz changes, do a Playwright visual review — unit tests don't catch annotation overlap, missing text labels on empty bars, or color collisions, all of which Phase 3 hit.

## Reference docs

- Phase 1: spec `docs/superpowers/specs/2026-05-13-cadenza-retention-analytics-design.md`, plan `docs/superpowers/plans/2026-05-13-cadenza-retention-analytics.md`, retrospective `docs/superpowers/phase1-retrospective.md`
- Phase 2: spec `docs/superpowers/specs/2026-05-15-cadenza-phase2-pipeline-forecasting-design.md`, plan `docs/superpowers/plans/2026-05-15-cadenza-phase2-pipeline-forecasting.md`, retrospective `docs/superpowers/phase2-retrospective.md`
- Phase 3: spec `docs/superpowers/specs/2026-05-16-cadenza-phase3-quota-rep-performance-design.md`, plan `docs/superpowers/plans/2026-05-16-cadenza-phase3-quota-rep-performance.md`, retrospective `docs/superpowers/phase3-retrospective.md`
- Release notes: `CHANGELOG.md`
