"""Tests that the synthetic data generator produces the patterns the
dashboard is built to surface. These are sanity tests, not unit tests:
they verify the macro behavior of the simulation.
"""
from __future__ import annotations

import pandas as pd
import pytest

from src.data_generator import (
    GeneratorConfig,
    generate_customers,
    generate_subscriptions_and_events,
)


@pytest.fixture(scope="module")
def generated():
    cfg = GeneratorConfig()
    customers = generate_customers(cfg)
    subs, events = generate_subscriptions_and_events(customers, cfg)
    return customers, subs, events


def test_customer_count_is_reasonable(generated):
    customers, _, _ = generated
    assert 600 <= len(customers) <= 900


def test_all_three_segments_present(generated):
    customers, _, _ = generated
    assert set(customers["segment"].unique()) == {"SMB", "Mid-Market", "Enterprise"}


def test_all_five_channels_present(generated):
    customers, _, _ = generated
    assert set(customers["acquisition_channel"].unique()) == {
        "Outbound Sales", "Inbound Marketing", "Partner Referral",
        "Self-Serve Promo", "Event/Conference",
    }


def test_q3_2024_promo_cohort_overrepresents_self_serve(generated):
    """The engineered bump should make Self-Serve Promo visibly dominate Q3 2024."""
    customers, _, _ = generated
    q3_2024 = customers[customers["signup_cohort"].isin(["2024-07", "2024-08", "2024-09"])]
    channel_mix = q3_2024["acquisition_channel"].value_counts(normalize=True)
    assert channel_mix.get("Self-Serve Promo", 0) > 0.40, (
        f"Self-Serve Promo should be >40% of Q3 2024 cohort, got {channel_mix.to_dict()}"
    )


def test_self_serve_promo_q3_cohort_churns_worse(generated):
    """The core engineered insight: Q3 2024 Self-Serve Promo cohort has
    materially worse 12-month retention than the rest of the book."""
    customers, subs, _ = generated

    target_cohorts = ["2024-07", "2024-08", "2024-09"]
    promo_q3 = customers[
        (customers["signup_cohort"].isin(target_cohorts))
        & (customers["acquisition_channel"] == "Self-Serve Promo")
    ]
    other_cohorts = customers[
        (customers["signup_cohort"].isin(target_cohorts))
        & (customers["acquisition_channel"] != "Self-Serve Promo")
    ]

    def retained_at_m12(cohort_customers: pd.DataFrame) -> float:
        if len(cohort_customers) == 0:
            return 1.0
        retained = 0
        for _, c in cohort_customers.iterrows():
            signup = pd.Timestamp(c["signup_date"]).to_period("M")
            target = (signup + 12).to_timestamp().strftime("%Y-%m-%d")
            still_active = (
                (subs["customer_id"] == c["customer_id"])
                & (subs["month"] == target)
            ).any()
            if still_active:
                retained += 1
        return retained / len(cohort_customers)

    promo_retention = retained_at_m12(promo_q3)
    other_retention = retained_at_m12(other_cohorts)

    assert other_retention - promo_retention > 0.15, (
        f"Promo cohort M12 retention ({promo_retention:.2%}) should be at "
        f"least 15 points worse than other Q3 2024 channels ({other_retention:.2%})."
    )


def test_total_mrr_grows_over_time(generated):
    _, subs, _ = generated
    first_month_mrr = subs[subs["month"] == "2023-01-01"]["mrr"].sum()
    last_month_mrr = subs[subs["month"] == "2025-12-01"]["mrr"].sum()
    assert last_month_mrr > first_month_mrr * 3, (
        f"Expected meaningful growth over 36 months; got {first_month_mrr:.0f} -> {last_month_mrr:.0f}"
    )


def test_event_types_cover_full_lifecycle(generated):
    _, _, events = generated
    types = set(events["event_type"].unique())
    assert {"signup", "churn"} <= types
    # upgrades/downgrades should exist but not strictly required every run
    assert "upgrade" in types


import hashlib
from pathlib import Path

import pandas as pd
import pytest


DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "generated"


@pytest.fixture(scope="module")
def generated_phase2():
    """Load the committed Phase 2 CSVs."""
    opps = pd.read_csv(DATA_DIR / "opportunities.csv")
    history = pd.read_csv(DATA_DIR / "opportunity_stage_history.csv")
    return opps, history


def test_midmarket_poc_stall_is_at_least_2x_smb(generated_phase2):
    """Engineered insight protection: Mid-Market dwells in POC at least 2x as
    long as SMB does. If a future tweak weakens this, the test fails loudly.
    """
    opps, history = generated_phase2

    nb_opps = opps[opps["opportunity_type"] == "new_business"]
    poc = history[history["stage"] == "Proof of Concept"]
    poc_completed = poc[poc["exited_date"].notna()].copy()
    joined = poc_completed.merge(
        nb_opps[["opportunity_id", "segment"]], on="opportunity_id", how="inner"
    )

    by_seg = joined.groupby("segment")["days_in_stage"].mean()
    assert "Mid-Market" in by_seg.index and "SMB" in by_seg.index
    ratio = by_seg["Mid-Market"] / by_seg["SMB"]
    assert ratio >= 2.0, (
        f"Mid-Market POC stall insight has weakened: Mid-Market avg POC dwell = "
        f"{by_seg['Mid-Market']:.1f} days, SMB = {by_seg['SMB']:.1f} days, "
        f"ratio = {ratio:.2f} (must be ≥ 2.0). Re-tune NB_STAGE_DWELL_DAYS."
    )


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_phase1_csvs_unchanged_after_phase2_generator():
    """Running the full generator (including Phase 2) must produce the same
    customers.csv / subscriptions.csv / events.csv as Phase 1 committed.

    Compares hashes of currently-committed Phase 1 CSVs to freshly-regenerated
    output. If they differ, Phase 2 generator code has accidentally consumed
    Phase 1's RNG stream or otherwise perturbed determinism.
    """
    import tempfile
    from src.data_generator import write_to_disk

    expected = {
        "customers.csv": _file_hash(DATA_DIR / "customers.csv"),
        "subscriptions.csv": _file_hash(DATA_DIR / "subscriptions.csv"),
        "events.csv": _file_hash(DATA_DIR / "events.csv"),
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        write_to_disk(Path(tmpdir))
        for name, expected_hash in expected.items():
            actual_hash = _file_hash(Path(tmpdir) / name)
            assert actual_hash == expected_hash, (
                f"{name} differs after regeneration. Phase 2 generator is "
                f"perturbing Phase 1 RNG or outputs."
            )


def test_generate_reps_skeleton_shape():
    """generate_reps_skeleton returns 12 reps, 3 per territory, 4 per hire cohort."""
    import numpy as np
    from src.data_generator import generate_reps_skeleton, RNG_SEED

    rng = np.random.default_rng(RNG_SEED + 3)
    reps = generate_reps_skeleton(rng)

    assert len(reps) == 12
    assert list(reps.columns) == ["rep_id", "name", "hire_date", "territory"]
    # 3 reps per territory
    assert (reps.groupby("territory").size() == 3).all()
    # 4 in each hire cohort
    hire = pd.to_datetime(reps["hire_date"])
    veteran = ((hire >= "2021-01-01") & (hire <= "2022-12-31")).sum()
    mid     = ((hire >= "2023-01-01") & (hire <= "2024-06-30")).sum()
    new     = ((hire >= "2024-07-01") & (hire <= "2025-06-30")).sum()
    assert veteran == 4
    assert mid == 4
    assert new == 4
    # rep_id format
    assert reps["rep_id"].tolist() == [f"REP-{i:02d}" for i in range(1, 13)]
    # All names unique
    assert reps["name"].nunique() == 12


def test_generate_reps_skeleton_deterministic():
    """Same seed → same DataFrame, byte for byte."""
    import numpy as np
    from src.data_generator import generate_reps_skeleton, RNG_SEED

    rng1 = np.random.default_rng(RNG_SEED + 3)
    rng2 = np.random.default_rng(RNG_SEED + 3)
    a = generate_reps_skeleton(rng1)
    b = generate_reps_skeleton(rng2)
    pd.testing.assert_frame_equal(a, b)


def test_backfit_specialty_picks_modal_segment():
    """A rep with 5 SMB wins and 2 MM wins is tagged SMB."""
    from src.data_generator import backfit_reps_specialty_and_quota

    reps_skel = pd.DataFrame([
        {"rep_id": "REP-01", "name": "Test One", "hire_date": "2021-01-15", "territory": "North"},
        {"rep_id": "REP-02", "name": "Test Two", "hire_date": "2021-01-15", "territory": "South"},
    ])
    opps = pd.DataFrame([
        # REP-01: 5 SMB wins, 2 MM wins → SMB
        *[{"opportunity_id": f"OPP-{i}", "owner_rep_id": "REP-01",
           "opportunity_type": "new_business", "status": "closed_won",
           "segment": "SMB", "amount": 10_000.0, "close_date": "2024-01-01",
           "created_date": "2023-12-01", "customer_id": None,
           "account_name": "x", "acquisition_channel": "Outbound Sales",
           "current_stage": "Closed Won"} for i in range(5)],
        *[{"opportunity_id": f"OPP-{i+5}", "owner_rep_id": "REP-01",
           "opportunity_type": "new_business", "status": "closed_won",
           "segment": "Mid-Market", "amount": 50_000.0, "close_date": "2024-01-01",
           "created_date": "2023-12-01", "customer_id": None,
           "account_name": "x", "acquisition_channel": "Outbound Sales",
           "current_stage": "Closed Won"} for i in range(2)],
        # REP-02: 3 Enterprise wins → Enterprise
        *[{"opportunity_id": f"OPP-{i+7}", "owner_rep_id": "REP-02",
           "opportunity_type": "new_business", "status": "closed_won",
           "segment": "Enterprise", "amount": 800_000.0, "close_date": "2024-01-01",
           "created_date": "2023-12-01", "customer_id": None,
           "account_name": "x", "acquisition_channel": "Outbound Sales",
           "current_stage": "Closed Won"} for i in range(3)],
    ])

    result = backfit_reps_specialty_and_quota(reps_skel, opps)
    result = result.set_index("rep_id")

    assert result.loc["REP-01", "segment_specialty"] == "SMB"
    assert result.loc["REP-01", "quarterly_quota"] == 150_000.0
    assert result.loc["REP-02", "segment_specialty"] == "Enterprise"
    assert result.loc["REP-02", "quarterly_quota"] == 1_500_000.0


def test_backfit_quota_tiers_by_specialty():
    """Quarterly quota tier: SMB $150K, Mid-Market $500K, Enterprise $1.5M."""
    from src.data_generator import QUOTA_BY_SPECIALTY

    assert QUOTA_BY_SPECIALTY == {
        "SMB": 150_000.0,
        "Mid-Market": 500_000.0,
        "Enterprise": 1_500_000.0,
    }


# ---------------------------------------------------------------------------
# Phase 3 generator guardrail tests
# ---------------------------------------------------------------------------

def test_phase1_csvs_unchanged_after_phase3(tmp_path):
    """Phase 1 CSVs (customers / subscriptions / events) must be byte-identical
    after the Phase 3 generator runs. Phase 1 invariant lock.
    """
    import hashlib
    from src.data_generator import write_to_disk

    write_to_disk(tmp_path)

    repo_dir = Path(__file__).resolve().parents[1] / "data" / "generated"
    for fname in ["customers.csv", "subscriptions.csv", "events.csv"]:
        committed = (repo_dir / fname).read_bytes()
        regenerated = (tmp_path / fname).read_bytes()
        assert hashlib.sha256(committed).hexdigest() == hashlib.sha256(regenerated).hexdigest(), (
            f"{fname} differs after Phase 3 regenerate — Phase 1 invariant broken"
        )


def test_team_win_rate_stays_in_band(tmp_path):
    """TTM new-business win rate must remain in [0.21, 0.25] — Phase 2 calibration.

    With tenure-weighted owner assignment, total wins/losses are preserved exactly,
    so this is a regression guard rather than a fresh calibration.
    """
    from src.data_generator import write_to_disk

    write_to_disk(tmp_path)
    opps = pd.read_csv(tmp_path / "opportunities.csv")
    nb = opps[opps["opportunity_type"] == "new_business"].copy()
    nb["close_date"] = pd.to_datetime(nb["close_date"])
    # TTM relative to 2025-12-01 (the dashboard's "now")
    end = pd.Timestamp("2025-12-01")
    start = end - pd.DateOffset(months=12)
    ttm = nb[(nb["close_date"] >= start) & (nb["close_date"] <= end)
             & (nb["status"].isin(["closed_won", "closed_lost"]))]
    won = (ttm["status"] == "closed_won").sum()
    lost = (ttm["status"] == "closed_lost").sum()
    wr = won / (won + lost)
    assert 0.21 <= wr <= 0.25, f"team TTM win rate {wr:.3f} outside band [0.21, 0.25]"


def test_midmarket_poc_stall_still_2x(tmp_path):
    """Phase 2 insight: Mid-Market POC dwell ≥ 2× SMB POC dwell. Regression guard."""
    from src.data_generator import write_to_disk

    write_to_disk(tmp_path)
    history = pd.read_csv(tmp_path / "opportunity_stage_history.csv")
    opps = pd.read_csv(tmp_path / "opportunities.csv")
    merged = history.merge(opps[["opportunity_id", "segment", "opportunity_type"]],
                            on="opportunity_id")
    poc = merged[(merged["stage"] == "Proof of Concept")
                  & (merged["opportunity_type"] == "new_business")
                  & merged["days_in_stage"].notna()]
    smb_mean = poc[poc["segment"] == "SMB"]["days_in_stage"].mean()
    mm_mean = poc[poc["segment"] == "Mid-Market"]["days_in_stage"].mean()
    ratio = mm_mean / smb_mean
    assert ratio >= 2.0, f"POC stall ratio {ratio:.2f} < 2.0× (was 2.75× in Phase 2)"


def test_ramp_curve_visible_in_data(tmp_path):
    """Phase 3 insight: reps with <6 months tenure have median attainment ≥ 20pp
    lower than reps with 12+ months tenure. This protects the engineered
    ramp insight against future generator tweaks.
    """
    from src.data_generator import write_to_disk
    from src.quota import ramp_curve

    write_to_disk(tmp_path)
    reps = pd.read_csv(tmp_path / "reps.csv")
    opps = pd.read_csv(tmp_path / "opportunities.csv")
    opps = opps[(opps["opportunity_type"] == "new_business")
                 & (opps["status"] == "closed_won")]

    curve = ramp_curve(opps, reps)
    early = curve.loc[curve["tenure_months"] < 6.0, "attainment_pct"].median()
    tenured = curve.loc[curve["tenure_months"] >= 12.0, "attainment_pct"].median()
    gap_pp = (tenured - early) * 100
    assert gap_pp >= 20.0, (
        f"ramp gap is only {gap_pp:.1f}pp — engineered insight #3 is too weak; "
        f"early-tenure median={early:.3f}, tenured median={tenured:.3f}"
    )


def test_reps_csv_specialty_matches_historical_mix(tmp_path):
    """Each rep's segment_specialty equals their modal closed-won segment.
    Validates the two-pass backfit."""
    from src.data_generator import write_to_disk

    write_to_disk(tmp_path)
    reps = pd.read_csv(tmp_path / "reps.csv")
    opps = pd.read_csv(tmp_path / "opportunities.csv")
    nb_won = opps[(opps["opportunity_type"] == "new_business")
                   & (opps["status"] == "closed_won")]

    for _, rep in reps.iterrows():
        rep_won = nb_won[nb_won["owner_rep_id"] == rep["rep_id"]]
        if len(rep_won) == 0:
            assert rep["segment_specialty"] == "SMB", \
                f"rep with no wins should default to SMB; got {rep['segment_specialty']}"
            continue
        modal = (
            rep_won.groupby("segment").size()
            .sort_values(ascending=False).index[0]
        )
        # Handle alphabetical tie-break
        counts = rep_won.groupby("segment").size().sort_values(ascending=False)
        top_count = counts.iloc[0]
        tied_segments = sorted(counts[counts == top_count].index.tolist())
        expected = tied_segments[0]
        assert rep["segment_specialty"] == expected, (
            f"{rep['rep_id']} specialty={rep['segment_specialty']} but modal segment={expected}"
        )


def test_reps_csv_shape(tmp_path):
    """reps.csv has 12 rows, 3 per territory, 4 per hire cohort, all 6 columns."""
    from src.data_generator import write_to_disk

    write_to_disk(tmp_path)
    reps = pd.read_csv(tmp_path / "reps.csv")

    assert len(reps) == 12
    assert list(reps.columns) == [
        "rep_id", "name", "hire_date", "segment_specialty",
        "territory", "quarterly_quota",
    ]
    assert (reps.groupby("territory").size() == 3).all()
    hire = pd.to_datetime(reps["hire_date"])
    assert ((hire >= "2021-01-01") & (hire <= "2022-12-31")).sum() == 4
    assert ((hire >= "2023-01-01") & (hire <= "2024-06-30")).sum() == 4
    assert ((hire >= "2024-07-01") & (hire <= "2025-06-30")).sum() == 4
