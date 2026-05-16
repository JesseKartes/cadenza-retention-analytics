"""Tests for src/quota.py — Cadenza Phase 3 quota / rep performance metrics."""
from __future__ import annotations

import pandas as pd
import pytest


def test_module_importable():
    """Smoke check: the empty module imports cleanly."""
    from src import quota  # noqa: F401
