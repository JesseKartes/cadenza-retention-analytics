# Phase 3 Retrospective and Phase 4 Entry Point

**Status:** Phase 3 shipped and merged to `main` 2026-05-16. Streamlit Cloud auto-deployed. Phase 4 not started, not yet scoped.

This document is the bridge between Phase 3 (Quota & Rep Performance, complete) and whatever comes next. It captures what was built, what changed mid-flight, and what a next-session implementer needs to know.

---

## What was actually shipped (vs. spec)

The Phase 3 spec (`docs/superpowers/specs/2026-05-16-cadenza-phase3-quota-rep-performance-design.md`) and plan (`docs/superpowers/plans/2026-05-16-cadenza-phase3-quota-rep-performance.md`) describe the intended build. The 19 implementation tasks shipped close to spec, but the calibration loop afterward made significant changes to the data-generation strategy. All of those changes are documented in a single post-implementation polish commit (`fix(phase-3): generator calibration polish`).

### Changes from spec, with reasoning

- **Specialty assignment changed from modal-backfit to cohort-aligned pre-assignment + segment-aware deal routing.** The spec said "Derived in a two-pass step: opportunities are generated first with uniform-random `owner_rep_id`, then each rep's modal closed-won segment is computed and written back." In practice, SMB is 70% of new-business deals via `SEGMENT_WEIGHTS`, so every rep's modal segment was SMB. All 12 reps backfit to SMB specialty with uniform $150K quotas — destroying the tiered-quota narrative the spec promised. Replaced with: skeleton assigns specialty by hire cohort (veterans → Enterprise, mid-tenure → Mid-Market, new hires → SMB), and `_generate_new_business_opps` selects `owner_rep_id` using pure specialty routing (matching-specialty reps only, with fallback to all eligible reps when no specialist has been hired yet). Tells a "career progression" team-building story and concentrates the ramp signal in the high-volume SMB cohort.
- **Quota tiers lowered to match dataset volume.** Spec said `SMB $150K / MM $500K / Enterprise $1.5M`. After cohort-aligned specialty routing landed, team attainment fell to 28% with 11/12 reps at-risk because the dataset's per-rep close volume couldn't sustain those tiers. Calibrated down to `SMB $80K / MM $150K / Enterprise $500K`. Team Q4 2025 attainment now lands at 84% with 7/12 at-quota — realistic SaaS distribution.
- **Pre-hire reps excluded from owner selection.** Bug found in the post-implementation review: `_choose_owner_by_tenure` initially included reps with negative tenure (deals closing before the rep's hire date) at 0.55 weight, producing 22% of deals attributed before the rep existed. The longitudinal ramp line chart showed 174% at month 0 because of this. Fixed by filtering `eligible` to reps hired ≤ close_date. Bug was structural — the same filter applies to renewal/expansion generators too (extended fix to `_choose_eligible_rep` for uniform-random renewal/expansion ownership).
- **Routing strength settled at pure (specialty-match-only).** Tried 5:1 weight (~70% concentration) and 19:1 (~90%) before landing on pure routing. At 5:1, occasional Enterprise spillover landed on SMB reps and produced 1245% attainment outliers (Rowan Okafor, $996K closed on $80K SMB quota). At 19:1 the outlier just moved to a different SMB rep (Taylor Bhatt at 1015%). Pure routing — non-matching reps get weight 0, with a fallback to all eligible reps when no specialist exists yet — eliminates cross-specialty $-outliers entirely. The "no cross-specialty wins" trade-off is defensible: it's synthetic data with deterministic routing.
- **`test_ramp_curve_visible_in_data` scoped to SMB cohort.** Spec-described test compared `<6mo` vs `12+mo` medians across all reps. After cohort-aligned specialty (where 12+mo bucket is dominated by Enterprise specialists with $1.5M quotas), the cross-cohort comparison inverted (Enterprise vets show low % attainment on big quotas; SMB new hires show high % on small quotas). Test now compares within SMB cohort only, where the ramp narrative actually lives. Gap is currently 38pp (well above the 20pp threshold) in the SMB cohort. The data-layer `ramp_curve` function still computes across all reps; only the test's guardrail uses the SMB-scoped view.
- **§1 attainment-distribution chart got percentage text labels on every bar.** Caught only during Playwright visual review. Reps at 0% attainment (Kai Anderson, Diego Park — both Enterprise specialists with no Q4 closes) were rendering as invisible bars (zero width). Added `text=[f"{p:.0%}" ...]` and `textposition="outside"` so 0% reps display "0%" right at the y-axis.
- **§2 ramp curve aggregation changed from mean to median + smoothing + tighter x-axis.** The team-wide line chart originally used `.mean()` across reps and showed 0-30 months. Enterprise lumpiness produced a wildly oscillating line with no clear ramp shape. Switched to `.median()` (robust to outliers), added a 3-month centered rolling smooth on top of the bucket medians, capped x-axis at 18 months. Result: clean visible ramp from ~55% at month 0 → ~115% by month 9.
- **§2 annotation positions staggered.** Original `annotation_position="top"` for both the month-6 and month-9 reference lines caused the labels "Industry-assumed ramp" and "Actual full productivity" to stack on top of each other (since the lines are only 3 months apart). Fixed by using `"top left"` for month 6 and `"top right"` for month 9, plus shortening the label text to "Assumed ramp (6mo)" / "Actual ramp (~9mo)".

### Bugs caught and fixed mid-build

- **Pre-hire reps owning deals** (described above). The biggest correctness bug surfaced in the post-implementation final code review, not in any of the 19 task reviews. Lesson: structural assumptions about eligibility need explicit tests, not just "the code looks right."
- **Ramp insight too weak after 19:1 routing tightening.** `test_ramp_curve_visible_in_data` started failing at 17.2pp gap (threshold 20pp) after tightening from 5:1 to 19:1. Tightening concentrated wins to Enterprise specialists (veterans, high tenure factor), thinning the SMB cohort's deal volume and weakening the ramp signal there. Pure routing fixed it by routing SMB deals exclusively to SMB specialists.
- **Bimodal attainment distribution after backfit.** All-SMB specialty + uniform $150K quota produced 4 reps at 100-675% and 7 at-risk in Q4 2025. Worse: the top performer (Blake Reyes) had only 8 months tenure, contradicting the §2 ramp narrative ("new reps underperform"). Surfaced in the final code review; resolved via the calibration loop above.
- **§1 chart 0% bars invisible** + **§2 annotation overlap**. Both were UX issues only caught via Playwright visual review of the live dashboard. Unit tests passed; data was correct; the *render* was wrong. Lesson: visual review is a required gate for any viz changes, not a "nice to have."

### Decisions worth remembering

- **Tiered quotas require actually-tiered reps.** Modal-backfit alone doesn't work when one segment dominates the dataset's deal volume. Either pre-assign specialty (option c) or expect uniform-quota outcomes.
- **Pure routing > weighted routing for synthetic-data dashboards.** Weighted routing leaves a small probability of cross-specialty spillover; for a 12-rep team with 33 Enterprise deals, even 1% spillover produces visible outliers on the attainment chart. Pure routing with a "no specialist yet hired" fallback is the only model that fully eliminates them.
- **Quotas must be calibrated against actual data volume, not industry aspirations.** Spec wrote $150K/$500K/$1.5M as "what real SaaS quotas look like." The dataset's per-rep close volume couldn't sustain those tiers. Always run the generator and check actual per-rep $ before locking quotas.
- **Playwright visual review caught two real issues subagent code reviews missed.** Annotation overlap and 0% bar invisibility are both rendering problems that don't fail unit tests. Mandatory step for any Phase 4 viz work: launch Streamlit locally and step through every page screen-by-screen.
- **The 5-iteration calibration loop got squashed.** Five sequential `fix(generator):` commits (pre-hire bug, modal-backfit replacement, quota tier reduction, 5:1 → 19:1 routing, pure routing) were consolidated into a single `fix(phase-3): generator calibration polish` commit via `git reset --soft` before the PR. Hiring-manager-readable git history.

---

## Conventions to carry into Phase 4

Phase 4 (if any) should follow the same patterns established in Phases 1-3.

**Architecture**
- Pure data pipeline: generator → flat CSVs → pure pandas modules → Streamlit + Plotly.
- Pure functions (no IO, no Streamlit imports, no global state) in `src/*.py`. No Streamlit imports outside `Overview.py` and `pages/`.
- Each Streamlit page has its own `@st.cache_data load_data()`. No shared session state.

**Testing**
- TDD with hand-built fixtures in `tests/conftest.py`. Fixture comments document hand-calculated expected metric values — the fixtures are the contract.
- Sanity/guardrail tests on the generator for any engineered insight, with thresholds in the assertion message so failure is informative.
- Maintain the Phase 1 byte-identical invariant: any Phase 4 generator additions use a different `RNG_SEED+N` and write to *new* CSVs.
- **Mandatory:** visual review via Playwright (or equivalent) after any viz changes. Unit tests don't catch annotation overlap, color collisions, missing text labels, or empty-data rendering.

**Naming and style**
- `from __future__ import annotations` at the top of every Python module.
- Conventional commits (`feat:`, `fix:`, `chore:`, `docs:`, `test:`, `polish:`, `ops:`).
- All numerator/denominator definitions in metric docstrings — interview-defensible.

**Visualization**
- Cadenza brand palette in `src/viz.py`. Don't introduce new colors.
- Percent metrics use `yaxis_tickformat=".0%"`. Dollar metrics use `f"${v:,.0f}"`.
- Bar charts with potential 0-value bars must use `text=` labels with `textposition="outside"` so empty bars are still visible.
- Vertical reference lines with annotations within 4-5 units of each other need staggered `annotation_position` ("top left" / "top right") to avoid label overlap.

**Deployment**
- Streamlit Cloud, Python 3.12 (pinned in deploy UI — NOT via `runtime.txt` or `.python-version`).
- Auto-redeploy on `git push origin main`. Data CSVs must be committed.

---

## Phase 4 entry point (not yet scoped)

Possible Phase 4 directions, ranked by hiring-manager value:

1. **Activity tracking** — calls, emails, meetings per rep × per opp. Would add `activities.csv` to the dataset and connect activity intensity to win-rate / cycle-time. Tells a "high-activity reps win more" story, complementing the ramp insight.
2. **Marketing funnel / MQL-SQL-Opp** — adds upstream of opportunity creation. Would surface lead-source quality patterns (e.g., "Inbound Marketing leads convert at 2× Outbound rate but have lower ACV"). Connects retention (Phase 1) to acquisition motion.
3. **Named-account drilldown** — clickable account view across all phases. Aggregates retention, opps, expansion, and rep activity by account. Less analytical insight; more "interactive demo" value.
4. **Executive summary page** — single-screen "what to brief the CRO with" view. Pulls top KPIs from all 4 prior pages and surfaces the three engineered insights in one place. Useful as a portfolio-piece capstone.

### Data model implications

- New CSV(s) would be appended to `data/generated/`. Use `RNG_SEED+4` (Phase 4) so prior CSVs stay byte-identical.
- Don't change the existing schemas. Add new tables alongside.

### When the user (Jesse) says "let's start Phase 4"

1. Read this document and Phase 2's retrospective for prior architectural context.
2. Invoke `superpowers:brainstorming` — Phase 4 is its own design cycle.
3. Use the Phase 3 spec/plan as templates.
4. Keep all conventions from Phases 1-3.
5. Phase 4 lives in the same repo. New module(s) in `src/`. New page in `pages/`. If a new page is added, About moves from `pages/8_About.py` to `pages/9_About.py`.
6. New CHANGELOG entry on ship. New retrospective doc on ship.

### What NOT to redo

- Don't touch the Phase 1 retention modules (`src/metrics.py`, `src/cohorts.py`), Phase 2 pipeline modules (`src/pipeline.py`, `src/forecast.py`), or Phase 3 quota module (`src/quota.py`) unless Phase 4 *requires* it (and document why).
- Don't change the Cadenza brand palette or existing Streamlit pages' UX.
- Don't change the Phase 1 customer/subscription/event CSVs — they're invariant-locked.
- Don't revert to modal-segment backfit or weighted routing — both produced visible outliers. Pure routing is the keeper.
- Don't change the Phase 3 quota tiers ($80K/$150K/$500K) — they're calibrated against actual per-rep deal volume.

---

## Memory pointers for the next-session Claude

If a fresh Claude session is helping Jesse with Phase 4, the following memory files exist:

- `user_career_transition.md` — Who Jesse is, why he's doing this, identity refs.
- `project_cadenza_retention_analytics.md` — Current project state, deploy URL, lessons.
- `feedback_collaboration_style.md` — How Jesse engages: asks "why," values consistency, expects teaching-style explanations.

Memory directory: `/Users/jesse/.claude/projects/-Users-jesse-Documents-Projects-revops-portfolio-claude/memory/`

After Phase 4 ships, update `project_cadenza_retention_analytics.md` with the Phase 4 ship date and create a Phase 4 retrospective at `docs/superpowers/phase4-retrospective.md`.
