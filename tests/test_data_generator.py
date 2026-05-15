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
