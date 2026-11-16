from __future__ import annotations

import pytest

import job_board_analysis as analysis


def test_q1_source_ranking(cleaned):
    df, _ = cleaned
    source, role_rates, tests = analysis.question_1(df)
    ranked = source[source.analysis_group.eq("ranked")].set_index("source")
    assert ranked.index.tolist() == [
        "referral",
        "email",
        "search",
        "college",
        "social",
    ]
    assert ranked.loc["referral", "hires_per_100"] == pytest.approx(10.74, abs=0.01)
    assert ranked.loc["referral", "ci_low"] == pytest.approx(6.39, abs=0.01)
    assert ranked.loc["referral", "ci_high"] == pytest.approx(17.52, abs=0.01)
    assert ranked.hires_per_100.idxmax() == "referral"
    assert ranked.role_standardised_per_100.idxmax() == "referral"
    assert "unknown" not in ranked.index

    adjusted = tests.set_index("comparison")["p_adjusted"]
    assert adjusted["referral vs social"] == pytest.approx(0.00579, abs=1e-5)
    assert adjusted["referral vs college"] == pytest.approx(0.0289, abs=1e-3)
    assert adjusted["referral vs search"] == pytest.approx(0.0861, abs=1e-3)
    assert adjusted["referral vs email"] == pytest.approx(0.534, abs=1e-3)

    leaders = {}
    for role in analysis.ROLE_ORDER:
        subset = role_rates[role_rates.role_category.eq(role)]
        leaders[role] = subset.loc[subset.hires_per_100.idxmax(), "source"]
    assert leaders == {
        "Software": "email",
        "Data": "search",
        "Design": "referral",
        "Marketing": "referral",
        "Finance": "search",
        "Operations": "college",
    }


def test_q2_shortlist_gap(cleaned):
    df, _ = cleaned
    by_step, comparison, tests, by_role = analysis.question_2(df)
    assert by_step.applications.tolist() == [129, 178, 248, 242, 403]
    assert comparison.loc[0, "shortlist_rate_pct"] == pytest.approx(48.39, abs=0.01)
    assert comparison.loc[1, "shortlist_rate_pct"] == pytest.approx(9.28, abs=0.01)
    row = tests.iloc[0]
    assert row.difference_pp == pytest.approx(39.10, abs=0.01)
    assert row.difference_ci_low_pp == pytest.approx(33.78, abs=0.01)
    assert row.difference_ci_high_pp == pytest.approx(44.30, abs=0.01)
    assert row.risk_ratio == pytest.approx(5.211, abs=0.001)
    assert row.p_value < 1e-20
    assert (by_role.diff_pp > 30).all()
    assert by_role.p_adjusted.max() < 0.001


def test_q3_reply_gap(cleaned):
    df, _ = cleaned
    summary, tests, robustness = analysis.question_3(df)
    assert summary.loc[0, "group"] == "paid"
    assert summary.loc[1, "group"] == "unpaid"
    assert summary.loc[0, "median_days"] == 3
    assert summary.loc[1, "median_days"] == 7
    assert summary.loc[0, "never_replied_pct"] == pytest.approx(13.08, abs=0.01)
    assert summary.loc[1, "never_replied_pct"] == pytest.approx(29.61, abs=0.01)
    assert summary.loc[0, "ci_low"] == pytest.approx(10.83, abs=0.01)
    assert summary.loc[1, "ci_high"] == pytest.approx(33.91, abs=0.01)
    row = tests.iloc[0]
    assert row.never_reply_diff_pp == pytest.approx(16.53, abs=0.01)
    assert row.never_reply_diff_ci_low_pp == pytest.approx(11.78, abs=0.01)
    assert row.never_reply_diff_ci_high_pp == pytest.approx(21.39, abs=0.01)
    assert row.mannwhitney_p < 1e-60
    assert row.never_reply_p < 1e-10
    assert len(robustness) == 8
    mature = robustness[robustness.scope.eq("matured >=21 days")]
    paid = mature[mature.group.eq("paid")].iloc[0]
    unpaid = mature[mature.group.eq("unpaid")].iloc[0]
    assert unpaid.never_replied_pct - paid.never_replied_pct > 15
