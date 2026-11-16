"""CSV tables, results.md and the run log."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .config import DEFAULT_OUT, ROLE_ORDER, SOURCE_ORDER
from .console import LOG


def markdown_table(df: pd.DataFrame) -> str:
    columns = list(df.columns)
    lines = [
        "| " + " | ".join(columns) + " |",
        "|" + "|".join(["---"] * len(columns)) + "|",
    ]
    for _, row in df.iterrows():
        values = []
        for value in row:
            if isinstance(value, (float, np.floating)):
                if float(value).is_integer():
                    values.append(str(int(value)))
                else:
                    values.append(f"{value:.1f}")
            else:
                values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def write_outputs(
    df: pd.DataFrame,
    stats_found: dict[str, int],
    q1_source: pd.DataFrame,
    q1_role: pd.DataFrame,
    q1_tests: pd.DataFrame,
    q2_by_step: pd.DataFrame,
    q2_comparison: pd.DataFrame,
    q2_tests: pd.DataFrame,
    q2_by_role: pd.DataFrame,
    q3_summary: pd.DataFrame,
    q3_tests: pd.DataFrame,
    q3_robustness: pd.DataFrame,
    chart_path: Path,
    dq_report: dict[str, object],
    out_dir: Path | str = DEFAULT_OUT,
) -> None:
    out_dir = Path(out_dir)

    def display(frame: pd.DataFrame, columns: list[str], headers: list[str]) -> pd.DataFrame:
        return frame[columns].rename(columns=dict(zip(columns, headers, strict=True)))

    def save(
        frame: pd.DataFrame,
        name: str,
        *,
        round_to: dict[str, int] | None = None,
        sig3: tuple[str, ...] = (),
        as_text: tuple[str, ...] = (),
    ) -> None:
        out = frame.copy()
        for column, decimals in (round_to or {}).items():
            out[column] = out[column].round(decimals)
        for column in sig3:
            out[column] = out[column].map(lambda value: f"{value:.3g}")
        for column in as_text:
            out[column] = out[column].astype(str)
        out.to_csv(out_dir / name, index=False)

    save(
        q1_source,
        "q1_source_rates.csv",
        round_to={
            "hires_per_100": 2,
            "ci_low": 2,
            "ci_high": 2,
            "role_standardised_per_100": 2,
        },
    )
    save(
        q1_role,
        "q1_role_rates.csv",
        round_to={"hires_per_100": 2, "ci_low": 2, "ci_high": 2},
        as_text=("role_category", "source"),
    )
    save(q1_tests, "q1_tests.csv", sig3=("p_value", "p_adjusted"))
    save(
        q2_by_step,
        "q2_by_steps.csv",
        round_to={"shortlist_rate_pct": 2, "ci_low": 2, "ci_high": 2},
    )
    save(
        q2_comparison,
        "q2_comparison.csv",
        round_to={"shortlist_rate_pct": 2, "ci_low": 2, "ci_high": 2},
    )
    save(
        q2_tests,
        "q2_tests.csv",
        round_to={
            "difference_pp": 2,
            "difference_ci_low_pp": 2,
            "difference_ci_high_pp": 2,
            "risk_ratio": 3,
            "chi2": 2,
        },
        sig3=("p_value",),
    )
    save(
        q2_by_role,
        "q2_by_role.csv",
        round_to={
            "shortlist_pct_all4": 2,
            "shortlist_pct_0_3": 2,
            "diff_pp": 2,
            "diff_ci_low_pp": 2,
            "diff_ci_high_pp": 2,
            "risk_ratio": 2,
        },
        sig3=("p_value", "p_adjusted"),
    )
    save(
        q3_summary,
        "q3_paid_vs_unpaid.csv",
        round_to={
            "never_replied_pct": 2,
            "ci_low": 2,
            "ci_high": 2,
            "median_days": 2,
            "mean_days": 2,
            "p75_days": 2,
            "p90_days": 2,
        },
    )
    save(
        q3_tests,
        "q3_tests.csv",
        round_to={
            "median_diff_days": 2,
            "mean_diff_days": 2,
            "never_reply_diff_pp": 2,
            "never_reply_diff_ci_low_pp": 2,
            "never_reply_diff_ci_high_pp": 2,
        },
        sig3=("mannwhitney_p", "never_reply_p"),
    )
    save(
        q3_robustness,
        "q3_robustness.csv",
        round_to={
            "never_replied_pct": 2,
            "ci_low": 2,
            "ci_high": 2,
            "median_days": 2,
            "mean_days": 2,
        },
    )

    # Human-readable results companion.
    source_display = display(
        q1_source[q1_source.analysis_group.eq("ranked")],
        [
            "source",
            "applications",
            "hires",
            "hires_per_100",
            "ci_low",
            "ci_high",
            "role_standardised_per_100",
        ],
        [
            "Source",
            "Applications",
            "Hires",
            "Hires per 100",
            "CI low",
            "CI high",
            "Role-standardised per 100",
        ],
    )

    role_wide = q1_role.pivot(
        index="role_category", columns="source", values="hires_per_100"
    ).reindex(ROLE_ORDER)[SOURCE_ORDER]
    role_n = q1_role.pivot(index="role_category", columns="source", values="applications").reindex(
        ROLE_ORDER
    )[SOURCE_ORDER]
    role_display = role_wide.astype(object)
    for role in role_display.index:
        for source in role_display.columns:
            rate = role_wide.loc[role, source]
            n = role_n.loc[role, source]
            role_display.loc[role, source] = (
                "-" if pd.isna(rate) or pd.isna(n) else f"{rate:.1f} ({int(n)})"
            )
    role_display = role_display.reset_index()
    role_display.columns = ["Role"] + [source.title() for source in role_display.columns[1:]]

    by_step_display = display(
        q2_by_step,
        ["steps_done", "applications", "shortlisted", "shortlist_rate_pct", "ci_low", "ci_high"],
        [
            "Steps done",
            "Applications",
            "Shortlisted",
            "Shortlist rate (%)",
            "CI low",
            "CI high",
        ],
    )
    comparison_display = display(
        q2_comparison,
        ["group", "applications", "shortlisted", "shortlist_rate_pct", "ci_low", "ci_high"],
        [
            "Group",
            "Applications",
            "Shortlisted",
            "Shortlist rate (%)",
            "CI low",
            "CI high",
        ],
    )
    role_gap_display = display(
        q2_by_role,
        ["role_category", "n_all4", "shortlist_pct_all4", "n_0_3", "shortlist_pct_0_3", "diff_pp"],
        [
            "Role",
            "n (4 steps)",
            "Shortlist % (4 steps)",
            "n (0-3 steps)",
            "Shortlist % (0-3 steps)",
            "Gap (pp)",
        ],
    )

    q3_display = display(
        q3_summary,
        [
            "group",
            "applications",
            "replied",
            "never_replied",
            "never_replied_pct",
            "median_days",
            "mean_days",
            "p75_days",
            "p90_days",
        ],
        [
            "Group",
            "Applications",
            "Replied",
            "Never replied",
            "Never replied (%)",
            "Median days",
            "Mean days",
            "P75 days",
            "P90 days",
        ],
    )
    robustness_display = display(
        q3_robustness,
        ["scope", "group", "applications", "never_replied_pct", "median_days", "mean_days"],
        [
            "Scope",
            "Group",
            "Applications",
            "Never replied (%)",
            "Median days",
            "Mean days",
        ],
    )

    dq_table = display(
        pd.DataFrame(dq_report["checks"]),
        ["dimension", "check", "status", "observed"],
        ["Dimension", "Check", "Status", "Observed"],
    )
    dq_summary = dq_report["summary"]
    dq_warnings = [check for check in dq_report["checks"] if check["status"] in {"warn", "fail"}]
    warning_text = "; ".join(f"{check['check']}: {check['observed']}" for check in dq_warnings)
    (out_dir / "data_quality.json").write_text(
        json.dumps(dq_report, indent=2) + "\n", encoding="utf-8"
    )
    cutoff = df.applied_on.max() - pd.Timedelta(days=21)
    cutoff_text = f"{cutoff.day} {cutoff:%B %Y}"

    results = f"""# Results: job board applications, July-September 2026

Data: {stats_found["raw_rows"]:,} supplied rows, {stats_found["duplicate_rows"]} exact duplicates removed, **{len(df):,} applications analysed**. {int(df.shortlisted_i.sum()):,} shortlisted, {int(df.interviewed_i.sum()):,} interviewed and {int(df.hired_i.sum()):,} hired. Paid means a monthly stipend above INR 0 ({stats_found["paid"]:,} applications); unpaid means INR 0 ({stats_found["unpaid"]:,}).

## Data quality

**{dq_summary["pass"]} pass, {dq_summary["warn"]} warning, {dq_summary["fail"]} fail, {dq_summary["not_assessed"]} not assessed.** Warnings: {warning_text}.

{markdown_table(dq_table)}

Machine-readable version: `data_quality.json`. The accuracy check is not assessed because the supplied extract has no independent source of truth.

## Q1. Hires per 100 applications by source

{markdown_table(source_display)}

{markdown_table(role_display)}

Cells show hires per 100 applications with the number of applications in brackets. Source-by-role cells are small; read them with the confidence intervals in `q1_role_rates.csv`.

## Q2. Shortlisting by application-step completion

{markdown_table(comparison_display)}

{markdown_table(by_step_display)}

{markdown_table(role_gap_display)}

Per-role confidence intervals and exact p-values are in `q2_by_role.csv`.

## Q3. Reply speed, paid versus unpaid

{markdown_table(q3_display)}

{markdown_table(robustness_display)}

Blank reply dates are treated as no reply by 30 September 2026. The 21-day maturity cut keeps applications submitted on or before {cutoff_text}.

## Chart

![Cumulative reply curve, paid versus unpaid](chart_reply_speed.png)

## Method notes

- **Q1:** hires / applications x 100. Wilson 95% confidence intervals. Direct standardisation applies the overall role distribution to each source's role-specific hire rates. Fisher exact tests compare referral with each other source, with Benjamini-Hochberg adjustment across the four tests. The 15 applications with missing source (0 hires) are excluded from all source comparisons.
- **Q2:** shortlist rate for applications with `steps_done = 4` versus `steps_done` 0-3. Wilson intervals, a Newcombe 95% CI for the risk difference, risk ratio, Pearson chi-square, and the same comparison within each role with Fisher exact tests and Benjamini-Hochberg adjustment.
- **Q3:** paid = `stipend_inr_month > 0`. Median and mean days are calculated among applications that received a reply. Blank reply dates are treated as "no reply by 30 September 2026", not imputed. Never-reply shares use Wilson intervals; the gap uses a Newcombe interval. Mann-Whitney U for reply days; chi-square for never-replied. The maturity check and monthly split test whether the September snapshot drives the result.
- **Data quality:** `data_quality.json` records checks across completeness, uniqueness, validity, consistency, timeliness, distribution and accuracy. Warnings are shown rather than silently fixed.
"""
    (out_dir / "results.md").write_text(results, encoding="utf-8")

    summary = "\n".join(LOG) + f"\n\nChart: {chart_path.name}\n"
    (out_dir / "summary.txt").write_text(summary, encoding="utf-8")
