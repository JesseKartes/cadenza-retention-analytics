# Phase 2 Retrospective and Phase 3 Entry Point

**Status:** Phase 2 shipped 2026-05-15. Phase 3 (Quota & Rep Performance) not started.

This document is the bridge between Phase 2 (Pipeline & Forecasting, complete) and Phase 3 (Quota & Rep Performance, planned). It captures what was built, what changed mid-flight, and what a next-session implementer needs to know.

---

## What was actually shipped (vs. spec)

The Phase 2 spec (`docs/superpowers/specs/2026-05-15-cadenza-phase2-pipeline-forecasting-design.md`) and plan (`docs/superpowers/plans/2026-05-15-cadenza-phase2-pipeline-forecasting.md`) describe the intended build. Most of it shipped as designed; a few things changed during build or polish.

### Changes from spec, with reasoning

- **Pipeline page scoped to new-business only.** The spec originally allowed an `opportunity_type` filter so users could view renewals or expansions through the same five-stage funnel UI. After build, the renewal/expansion views were mostly empty or nonsensical because renewal/expansion stage cycles are different (2-stage and 1-stage respectively). Rather than render half-useful pages, the page now locks `opportunity_type == "new_business"` at the top of `main()` and renames itself "New Business Pipeline." Renewal and expansion analytics are explicitly deferred — see About page's Scope & Deferrals section.
- **"Pipeline by Stage" replaced from funnel to horizontal bar chart.** Original plan called for a Plotly `Funnel` trace. The funnel rendered "percent of initial" labels like 880% / 678%, which were nonsensical for a point-in-time pipeline snapshot (funnels imply attrition, but pipeline at-rest has more $ in late stages because late-stage deals are bigger). Horizontal bar with stages top-to-bottom is the honest representation. See `pipeline_by_stage_figure` in `src/viz.py`.
- **Forecast bucket chart polished post-build.** Removed `$` from x-axis title (covered by legend), moved legend to `y=-0.55` (below tick labels), bumped default quarter target from $2M → $20M (so the dashed target line sits inside the bar instead of falling off the left edge).
- **New-business closed-lost population rebalanced from 80 → 1,500.** Originally `n_lost = 80` in `_generate_new_business_opps`. This — combined with 665 won deals seeded 1:1 with Phase 1 customers — produced a 83.4% TTM Win Rate, which contradicts the About-page claim that real-world new-business win rate is 25-35%. Bumping to 1,500 lands Win Rate around 22-23%. The Mid-Market POC stall guardrail still passes (2.75× ratio, well above 2.0× threshold) because lost deals walk the same dwell distributions.
- **About page renamed** `pages/4_About.py` → `pages/7_About.py` so it appears after Pipeline (5) and Forecasting (6) in the sidebar.

### Bugs caught and fixed mid-build

- **`$` rendered as LaTeX math.** Streamlit's MathJax interpreted `$ X new · $ Y renewal` as a math block. Fixed by escaping with `\$` in the source. Eventually deleted entirely when scope was simplified.
- **Empty `apply_filters` on opportunity_type.** After scoping to new_business, the filter helper still referenced an `opp_type` key that was no longer in the filters dict. Cleaned up.
- **Streamlit cache stale after CSV regen.** `@st.cache_data` happily served stale data after `python -m src.data_generator`. Killed and restarted the server. Worth documenting in Gotchas for Phase 3.

### Decisions worth remembering

- **Three opportunity types modeled distinctly:** `new_business` (5-stage), `renewal` (2-stage, links to Phase 1 annual anniversaries and churn events within ±30 days), `expansion` (1-stage, closes on the date of the Phase 1 upgrade event). Self-Serve Promo customers have no opportunity record (self-serve is no-touch).
- **Pipeline snapshots are quarterly,** reconstructed by walking stage history backwards from each snapshot date. 8 quarters × ~200 opps/snapshot ≈ 1,591 snapshot rows. The snapshot table is the basis for Forecasting's accuracy trend.
- **Phase 1 byte-identical invariant:** All Phase 2 generator code uses `RNG_SEED+2`, so `customers.csv`, `subscriptions.csv`, and `events.csv` are byte-identical between phases. Locked in by `test_phase1_csvs_unchanged_after_phase2_generator`.
- **Mid-Market POC stall guardrail:** `test_midmarket_poc_stall_is_at_least_2x_smb` enforces that the engineered insight survives future generator tuning. Threshold is 2.0×; current is 2.75×.

---

## Conventions to carry into Phase 3

Phase 3 should follow the same patterns established here and in Phase 1.

**Architecture**
- Pure data pipeline: generator → flat CSVs → pure pandas modules → Streamlit + Plotly.
- Pure functions (no IO, no global state) in `src/*.py`. No Streamlit imports outside `Overview.py` and `pages/`.
- Each Streamlit page has its own `@st.cache_data load_data()`. No shared session state.

**Testing**
- TDD with hand-built fixtures in `tests/conftest.py`. Fixture comments document hand-calculated expected metric values — the fixtures are the contract.
- Sanity/guardrail tests on the generator for any engineered insight, with thresholds in the assertion message so failure is informative.
- Maintain the Phase 1 byte-identical invariant: any Phase 3 generator additions use a different `RNG_SEED+N` and write to *new* CSVs.

**Naming and style**
- `from __future__ import annotations` at the top of every Python module.
- Conventional commits (`feat:`, `fix:`, `chore:`, `docs:`, `test:`, `polish:`, `ops:`).
- All numerator/denominator definitions in metric docstrings — interview-defensible.

**Visualization**
- Cadenza brand palette in `src/viz.py`. Don't introduce new colors.
- Percent metrics use `yaxis_tickformat=".0%"`. Dollar metrics use `f"${v:,.0f}"`.

**Deployment**
- Streamlit Cloud, Python 3.12 (pinned in deploy UI — NOT via `runtime.txt` or `.python-version`).
- Auto-redeploy on `git push origin main`. Data CSVs must be committed.

---

## Phase 3 entry point

Phase 3 is **Quota Attainment & Rep Performance**. Not started. Will be its own design → plan → implement cycle.

### Suggested Phase 3 scope (refine during brainstorming)

- **Rep scorecards:** quota attainment %, pipeline coverage per rep, win rate, average deal size, sales cycle.
- **Attainment distribution:** how many reps cleared quota, how many are at risk, who is carrying the team.
- **Ramp analysis:** first-90-day, first-180-day attainment curves for new reps vs. tenured reps.
- **Territory balance:** opp count and dollar volume by territory/segment — surface where coverage is thin.
- **Hidden insight (engineered):** suggested patterns to consider during brainstorming — e.g., a single overperforming rep masking a weak average, or a territory mismatch where deal volume is concentrated in 2 of 5 territories, or a ramp pattern where new reps take 9 months to hit quota vs. an assumed 6.

### Data model implications

- `REP_IDS` already exist in `src/data_generator.py` (`REP-001` through `REP-012`) and are populated on every opportunity's `owner_rep_id`. Phase 3 needs a separate `reps` table: rep_id, name, segment_specialty, hire_date, monthly_quota, territory.
- Quota attainment = sum(closed_won amount where owner_rep_id = R in period) / monthly_quota_for_R_in_period.
- Ramp: anchor against `hire_date`; bucket reps by tenure (0-3 months, 3-6, 6-12, 12+).
- Don't change the existing opportunity schema — add the `reps` table alongside.

### When the user (Jesse) says "let's start Phase 3"

1. Read this document and the Phase 1 retrospective.
2. Invoke `superpowers:brainstorming` — Phase 3 is its own design cycle.
3. Use the Phase 2 spec/plan as templates.
4. Keep all conventions from Phase 1 and Phase 2.
5. Phase 3 lives in the same repo. New module (`src/quota.py`). New page (`pages/7_Quota.py` — and renumber About to `8_About.py`).
6. New CHANGELOG entry on ship. New retrospective doc on ship.

### What NOT to redo

- Don't touch the Phase 1 retention modules (`src/metrics.py`, `src/cohorts.py`) or Phase 2 pipeline modules (`src/pipeline.py`, `src/forecast.py`) unless Phase 3 *requires* it (and document why).
- Don't change the Cadenza brand palette or existing Streamlit pages' UX.
- Don't change the Phase 1 customer/subscription/event CSVs — they're invariant-locked.
- Don't change the new-business closed-lost count or the Mid-Market POC dwell parameters — the win rate (~23%) and POC stall ratio (2.75×) are both calibrated.

---

## Memory pointers for the next-session Claude

If a fresh Claude session is helping Jesse with Phase 3, the following memory files exist and should be loaded automatically:

- `user_career_transition.md` — Who Jesse is, why he's doing this, identity refs.
- `project_cadenza_retention_analytics.md` — Current project state, deploy URL, deploy lessons.
- `feedback_collaboration_style.md` — How Jesse engages: asks "why," values consistency, expects teaching-style explanations.

Memory directory: `/Users/jesse/.claude/projects/-Users-jesse-Documents-Projects-revops-portfolio-claude/memory/`

After Phase 3 ships, update `project_cadenza_retention_analytics.md` with the Phase 3 ship date and create a Phase 3 retrospective at `docs/superpowers/phase3-retrospective.md`.
