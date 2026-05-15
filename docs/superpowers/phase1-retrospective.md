# Phase 1 Retrospective and Phase 2 Entry Point

**Status:** Phase 1 shipped and deployed 2026-05-15. Phase 2 not started.

This document is the bridge between Phase 1 (Retention Analytics, complete) and Phase 2 (Pipeline & Forecasting, planned). It captures what was actually built, what was changed mid-flight, and what a next-session implementer needs to know before continuing.

---

## What was actually shipped (vs. spec)

The original design spec (`docs/superpowers/specs/2026-05-13-cadenza-retention-analytics-design.md`) and implementation plan (`docs/superpowers/plans/2026-05-13-cadenza-retention-analytics.md`) describe the intended Phase 1. Most of the spec shipped as designed; a few things changed during build or post-ship polish.

### Changes from spec, with reasoning

- **Entry-point file renamed `streamlit_app.py` → `Overview.py`.** The Streamlit Cloud convention names the main script in the sidebar from its filename; `streamlit_app.py` produced a "streamlit app" sidebar entry, which looked unprofessional. `Overview.py` reads correctly. Streamlit Cloud requires the main file path to be set to `Overview.py` in its deploy settings.
- **Gross Revenue Churn KPI tile removed from the Overview page.** It is mathematically `1 − GRR` and reading both side-by-side adds noise without information. GRR alone is sufficient.
- **YoY deltas added to all 4 KPI tiles** (ARR, NRR, GRR, Logo Churn). Logo Churn uses `delta_color="inverse"` so an increase shows red. When the prior trailing-12-month window falls outside the dataset, a caption explains why the deltas hide — better UX than silent disappearance.
- **Cohort matrices distinguish "future" from "zero".** The original implementation filled missing cells with `0`, making cohorts that hadn't yet reached month 12 appear as 0% (red) on the heatmap. The shipped code masks those cells as `NaN` so they appear blank — distinguishing "no data yet" from "everyone churned." This bug was caught by Jesse during dashboard review.
- **Self-Serve Promo monthly churn probability** tuned from 0.025 → 0.030 in the generator to ensure the M12 retention gap test reliably passes by >15 percentage points after the Task 3 fix (which deferred lifecycle rolls to the month after signup).

### Bug caught and fixed mid-build

- **Events dated before signup.** Original `generate_subscriptions_and_events` rolled churn/expansion in the same month a customer signed up. Lifecycle events used the 15th of the month (`_mid_month`), so a customer signing up on day 16+ could have a churn event dated before their signup. Fix: track newly-activated customer IDs per month and skip them in the lifecycle loop. (Commit `1451884`.)

### Decisions worth remembering

- **Synthetic data committed to the repo.** Streamlit Cloud doesn't run the data generator at deploy time; it reads the committed CSVs directly. The generator is reproducible (`RNG_SEED=42`) so anyone cloning the repo gets identical data. Re-running the generator before commit is a no-op.
- **`src/viz.py` deliberately has no Streamlit imports.** Charts are pure Plotly `go.Figure` builders so they can be unit-tested or reused outside Streamlit.
- **Page 3 uses styled DataFrames instead of bar charts.** The original plan called for grouped bar charts; the styled `st.dataframe` approach with `highlight_min/max` displays more information in less vertical space. The unused `grouped_metric_bar` function still exists in `src/viz.py` from the original plan — Phase 2 can either reuse it or delete it.

---

## Conventions to carry into Phase 2

Phase 2 should follow the same patterns established here so the codebase stays coherent.

**Architecture**
- Pure data pipeline: generator → flat CSVs → pure pandas modules → Streamlit + Plotly.
- Pure functions (no IO, no global state) in `src/metrics.py`, `src/cohorts.py`, `src/viz.py`.
- Streamlit pages are presentation only — they call into `src/*` modules.
- Each Streamlit page has its own `@st.cache_data load_data()`. No shared session state across pages.

**Testing**
- TDD with hand-built fixtures in `tests/conftest.py` that have hand-calculated expected values written in test-body comments. The fixtures are the contract.
- Sanity tests on the generator to lock in any engineered insight, with thresholds in the assertion message so failure mode is informative.

**Naming and style**
- `from __future__ import annotations` at the top of every Python module.
- Conventional commits (`feat:`, `fix:`, `chore:`, `docs:`, `test:`, `style:`, `polish:`, `ops:`).
- All numerator/denominator definitions in metric docstrings — interview-defensible.

**Visualization**
- Cadenza brand palette: `CADENZA_PRIMARY #1F3A8A`, `CADENZA_ACCENT #06B6D4`, `CADENZA_GOOD #10B981`, `CADENZA_BAD #EF4444`, `CADENZA_NEUTRAL #94A3B8`. Defined in `src/viz.py`.
- Cohort/retention metrics shown as percentages with `yaxis_tickformat=".0%"`.

**Deployment**
- Streamlit Cloud, Python 3.12 (pinned in deploy UI settings — NOT via `runtime.txt`).
- Auto-redeploy on `git push origin main`.
- The `data/generated/*.csv` files must be committed; Cloud doesn't regenerate them.

---

## Phase 2 entry point

Phase 2 is **Pipeline & Forecasting Analytics**. Not started. Will be its own design → plan → implement cycle.

### Suggested Phase 2 scope (refine during brainstorming)

- **Pipeline coverage:** weighted pipeline / target by stage, time period.
- **Stage conversion / velocity:** win rates by stage, average days-in-stage, deal aging.
- **Forecast vs. actual:** committed / best-case / pipeline buckets, accuracy over time.
- **Hidden insight (engineered):** suggested patterns — Mid-Market deals stalling in proof-of-concept stage 2x longer than other segments, OR forecast accuracy degrading for deals sourced via a specific marketing campaign.

### Data model implications

Phase 2 needs a `pipeline` or `opportunities` table that the current schema doesn't have:
- Suggested grain: one row per opportunity, with stage history (likely a separate `opportunity_events` table).
- Could share `customers` with Phase 1 if landed deals become subscriptions, or be entirely separate.
- The generator should be extended (new functions, same module) rather than rewritten.

### When the user (Jesse) says "let's start Phase 2"

1. Read this document for context.
2. Invoke the `superpowers:brainstorming` skill — Phase 2 is its own design cycle.
3. Use the Phase 1 spec/plan as templates for the Phase 2 versions.
4. Keep the same conventions (TDD with hand-built fixtures, conventional commits, pure functions, Cadenza brand palette).
5. Phase 2 lives in the same repo. New files (`src/pipeline.py`, `src/forecast.py`, etc.). New page in `pages/` (probably `5_Pipeline.py` and `6_Forecasting.py` or similar).
6. New CHANGELOG entry on ship.

### What NOT to redo

- Don't touch `src/metrics.py`, `src/cohorts.py`, or the data generator's customer/subscription logic unless Phase 2 *requires* changes (and document why if so).
- Don't change the Cadenza brand palette or the existing Streamlit pages' UX.
- Don't rebuild the test infrastructure — extend `tests/conftest.py` with new fixtures.

---

## Memory pointers for the next-session Claude

If a fresh Claude session is helping Jesse with Phase 2, the following memory files exist and should be loaded automatically:

- `user_career_transition.md` — Who Jesse is, why he's doing this, identity refs.
- `project_cadenza_retention_analytics.md` — Current project state, deploy URL, deploy lesson.
- `feedback_collaboration_style.md` — How Jesse engages: asks "why," values consistency, expects teaching-style explanations.

Memory directory: `/Users/jesse/.claude/projects/-Users-jesse-Documents-Projects-revops-portfolio-claude/memory/`
