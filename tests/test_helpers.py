from __future__ import annotations

import pandas as pd
import pytest

import analysis


def test_wilson_interval_for_referral():
    low, high = analysis.wilson_ci(13, 121)
    assert low == pytest.approx(6.39, abs=0.05)
    assert high == pytest.approx(17.52, abs=0.05)


def test_newcombe_interval_for_q2():
    low, high = analysis.newcombe_diff(195, 403, 74, 797)
    assert low == pytest.approx(0.3378, abs=0.0001)
    assert high == pytest.approx(0.4430, abs=0.0001)


def test_schema_rejects_missing_column():
    frame = pd.DataFrame({"application_id": ["a"]})
    with pytest.raises(analysis.DataContractError, match="missing required column"):
        analysis.validate_input_schema(frame)


def test_schema_rejects_blank_ids():
    frame = pd.DataFrame(
        {
            "application_id": [""],
            "applied_on": ["2026-07-01"],
            "role_category": ["Software"],
            "work_mode": ["remote"],
            "stipend_inr_month": ["10000"],
            "source": ["search"],
            "steps_done": ["4"],
            "shortlisted": ["yes"],
            "interviewed": ["yes"],
            "hired": ["yes"],
            "days_to_first_reply": ["2"],
        }
    )
    with pytest.raises(analysis.DataContractError, match="application_id is blank"):
        analysis.validate_input_schema(frame)
