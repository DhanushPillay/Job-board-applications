from __future__ import annotations

import pandas as pd
import pytest

import job_board_analysis as analysis


def test_cleaning_counts(cleaned):
    df, stats_found = cleaned
    assert stats_found == {
        "raw_rows": 1206,
        "duplicate_rows": 6,
        "work_mode_fixed": 9,
        "missing_source": 15,
        "rows": 1200,
        "missing_reply": 234,
        "unpaid": 466,
        "paid": 734,
    }
    assert len(df) == 1200
    assert df.application_id.is_unique
    assert int(df.shortlisted_i.sum()) == 269
    assert int(df.interviewed_i.sum()) == 175
    assert int(df.hired_i.sum()) == 64
    assert int(df.completed_all_steps.sum()) == 403


def test_domains_and_funnel(cleaned):
    df, _ = cleaned
    assert set(df.role_category) == set(analysis.ROLE_ORDER)
    assert set(df.work_mode) == {"remote", "hybrid", "on_site"}
    assert set(df.source) == set(analysis.SOURCE_ORDER) | {"unknown"}
    for column in ("shortlisted", "interviewed", "hired"):
        assert set(df[column]) == {"yes", "no"}
    assert df.steps_done.between(0, 4).all()
    assert df.stipend_inr_month.ge(0).all()
    assert (df.hired_i <= df.interviewed_i).all()
    assert (df.interviewed_i <= df.shortlisted_i).all()
    assert (df.loc[~df.replied, "shortlisted_i"] == 0).all()


def test_group_counts(cleaned):
    df, _ = cleaned
    assert int(df.paid.sum()) == 734
    assert int((~df.paid).sum()) == 466
    assert int((~df.replied).sum()) == 234
    assert int(df[df.completed_all_steps].shortlisted_i.sum()) == 195
    assert int(df[~df.completed_all_steps].shortlisted_i.sum()) == 74


def test_expected_checks_can_be_skipped(tmp_path, data_path):
    raw = pd.read_csv(data_path, dtype=str).drop_duplicates().head(200)
    subset = tmp_path / "subset.csv"
    raw.to_csv(subset, index=False)
    df, stats_found = analysis.clean_data(subset, check_expected=False)
    assert len(df) == 200
    assert stats_found["rows"] == 200


def test_missing_column_is_rejected(tmp_path, data_path):
    raw = pd.read_csv(data_path, dtype=str).drop(columns=["source"])
    bad = tmp_path / "bad.csv"
    raw.to_csv(bad, index=False)
    with pytest.raises(analysis.DataContractError, match="source"):
        analysis.clean_data(bad)


def test_unparseable_number_is_rejected(tmp_path, data_path):
    raw = pd.read_csv(data_path, dtype=str)
    raw.loc[0, "steps_done"] = "four"
    bad = tmp_path / "bad.csv"
    raw.to_csv(bad, index=False)
    with pytest.raises(analysis.DataContractError, match="could not parse"):
        analysis.clean_data(bad, check_expected=False)


def test_fractional_steps_are_rejected(tmp_path, data_path):
    raw = pd.read_csv(data_path, dtype=str)
    raw.loc[0, "steps_done"] = "3.5"
    bad = tmp_path / "bad.csv"
    raw.to_csv(bad, index=False)
    with pytest.raises(analysis.DataContractError, match="whole numbers"):
        analysis.clean_data(bad, check_expected=False)
