"""The three analysis questions."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from .config import ROLE_ORDER, SOURCE_ORDER
from .console import log
from .stats import add_wilson, newcombe_diff


def question_1(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Hires per 100 applications by source, overall and within role."""
    source = df.groupby("source", as_index=False).agg(
        applications=("application_id", "size"), hires=("hired_i", "sum")
    )
    source["hires_per_100"] = 100 * source.hires / source.applications
    source = add_wilson(source, "hires", "applications")

    role_rate = df.pivot_table(
        index="role_category", columns="source", values="hired_i", aggfunc="mean"
    )
    role_weights = df.role_category.value_counts(normalize=True)

    standardised = []
    for name in source.source:
        rates = role_rate[name].dropna()
        weights = role_weights.reindex(rates.index)
        standardised.append(100 * (rates * weights).sum() / weights.sum())
    source["role_standardised_per_100"] = standardised
    source["analysis_group"] = np.where(
        source.source.eq("unknown"), "excluded_missing_source", "ranked"
    )
    source = source.sort_values("hires_per_100", ascending=False).reset_index(drop=True)

    role_long = df.groupby(["role_category", "source"], as_index=False).agg(
        applications=("application_id", "size"), hires=("hired_i", "sum")
    )
    role_long = role_long[role_long.source.ne("unknown")]
    role_long["hires_per_100"] = 100 * role_long.hires / role_long.applications
    role_long = add_wilson(role_long, "hires", "applications")
    role_long["role_category"] = pd.Categorical(
        role_long.role_category, categories=ROLE_ORDER, ordered=True
    )
    role_long["source"] = pd.Categorical(role_long.source, categories=SOURCE_ORDER, ordered=True)
    role_long = role_long.sort_values(["role_category", "source"]).reset_index(drop=True)

    counts = source.set_index("source")
    referral_hires = int(counts.loc["referral", "hires"])
    referral_n = int(counts.loc["referral", "applications"])
    tests = []
    for name in SOURCE_ORDER:
        if name == "referral":
            continue
        other_hires = int(counts.loc[name, "hires"])
        other_n = int(counts.loc[name, "applications"])
        table = [
            [referral_hires, referral_n - referral_hires],
            [other_hires, other_n - other_hires],
        ]
        _, p_value = stats.fisher_exact(table)
        tests.append(
            {
                "comparison": f"referral vs {name}",
                "referral_hires": referral_hires,
                "referral_n": referral_n,
                "other_hires": other_hires,
                "other_n": other_n,
                "p_value": p_value,
            }
        )
    tests_df = pd.DataFrame(tests)
    tests_df["p_adjusted"] = stats.false_discovery_control(tests_df.p_value.to_numpy())

    log("Q1. Hires per 100 applications by source")
    for _, row in source.iterrows():
        log(
            f"  {row.source:<8} {row.applications:>4} apps  {row.hires:>3} hires  "
            f"{row.hires_per_100:5.1f} per 100  (95% CI {row.ci_low:4.1f}-{row.ci_high:4.1f})  "
            f"role-standardised {row.role_standardised_per_100:5.1f}"
        )
    adjusted_text = "; ".join(
        f"{row.comparison.replace('referral vs ', '')} p={row.p_value:.3g} "
        f"(BH {row.p_adjusted:.3g})"
        for _, row in tests_df.iterrows()
    )
    log(f"  Fisher exact vs referral: {adjusted_text}")
    log("  Role leaders:")
    for role in ROLE_ORDER:
        subset = role_long[role_long.role_category.eq(role)]
        best = subset.loc[subset.hires_per_100.idxmax()]
        log(f"    {role:<10} {best.source:<8} {best.hires_per_100:5.1f} per 100")
    log()

    return source, role_long, tests_df


def question_2(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Shortlist rate for applicants who complete all 4 steps vs those who do not."""
    by_step = df.groupby("steps_done", as_index=False).agg(
        applications=("application_id", "size"), shortlisted=("shortlisted_i", "sum")
    )
    by_step["shortlist_rate_pct"] = 100 * by_step.shortlisted / by_step.applications
    by_step = add_wilson(by_step, "shortlisted", "applications")

    groups = []
    for label, mask in (
        ("all 4 steps", df.completed_all_steps),
        ("0-3 steps", ~df.completed_all_steps),
    ):
        subset = df[mask]
        groups.append(
            {
                "group": label,
                "applications": len(subset),
                "shortlisted": int(subset.shortlisted_i.sum()),
                "shortlist_rate_pct": 100 * subset.shortlisted_i.mean(),
            }
        )
    comparison = add_wilson(pd.DataFrame(groups), "shortlisted", "applications")

    all4 = comparison.iloc[0]
    early = comparison.iloc[1]
    diff_pp = all4.shortlist_rate_pct - early.shortlist_rate_pct
    risk_ratio = all4.shortlist_rate_pct / early.shortlist_rate_pct
    ci_low, ci_high = newcombe_diff(
        int(all4.shortlisted),
        int(all4.applications),
        int(early.shortlisted),
        int(early.applications),
    )
    chi2, p_value, _, _ = stats.chi2_contingency(
        pd.crosstab(df.completed_all_steps, df.shortlisted_i)
    )
    tests = pd.DataFrame(
        [
            {
                "difference_pp": diff_pp,
                "difference_ci_low_pp": 100 * ci_low,
                "difference_ci_high_pp": 100 * ci_high,
                "risk_ratio": risk_ratio,
                "chi2": chi2,
                "p_value": p_value,
                "n_all4": int(all4.applications),
                "n_0_3": int(early.applications),
            }
        ]
    )

    rows = []
    role_p_values = []
    for role in ROLE_ORDER:
        subset = df[df.role_category.eq(role)]
        a = subset[subset.completed_all_steps]
        b = subset[~subset.completed_all_steps]
        table = [
            [int(a.shortlisted_i.sum()), int(len(a) - a.shortlisted_i.sum())],
            [int(b.shortlisted_i.sum()), int(len(b) - b.shortlisted_i.sum())],
        ]
        _, role_p = stats.fisher_exact(table)
        role_low, role_high = newcombe_diff(
            int(a.shortlisted_i.sum()),
            len(a),
            int(b.shortlisted_i.sum()),
            len(b),
        )
        role_p_values.append(role_p)
        rows.append(
            {
                "role_category": role,
                "applications": len(subset),
                "n_all4": len(a),
                "shortlist_pct_all4": 100 * a.shortlisted_i.mean(),
                "n_0_3": len(b),
                "shortlist_pct_0_3": 100 * b.shortlisted_i.mean(),
                "diff_pp": 100 * (a.shortlisted_i.mean() - b.shortlisted_i.mean()),
                "diff_ci_low_pp": 100 * role_low,
                "diff_ci_high_pp": 100 * role_high,
                "risk_ratio": a.shortlisted_i.mean() / b.shortlisted_i.mean(),
                "p_value": role_p,
            }
        )
    by_role = pd.DataFrame(rows)
    by_role["p_adjusted"] = stats.false_discovery_control(role_p_values)

    log("Q2. Shortlisting by application-step completion")
    for _, row in comparison.iterrows():
        log(
            f"  {row.group:<12} {row.applications:>4} apps  {row.shortlisted:>3} shortlisted  "
            f"{row.shortlist_rate_pct:5.1f}%  (95% CI {row.ci_low:4.1f}-{row.ci_high:4.1f})"
        )
    log(
        f"  Difference: +{diff_pp:.1f} pp (95% CI {100 * ci_low:.1f}-{100 * ci_high:.1f}); "
        f"risk ratio {risk_ratio:.2f}; chi-square p {p_value:.2g}"
    )
    log(
        "  By role gap: "
        + ", ".join(f"{r.role_category} +{r.diff_pp:.1f} pp" for r in by_role.itertuples())
        + f" (max BH p {by_role.p_adjusted.max():.2g})"
    )
    log()

    return by_step, comparison, tests, by_role


def reply_stats(group: pd.DataFrame) -> dict[str, object]:
    replied = group.days_to_first_reply.dropna()
    return {
        "applications": len(group),
        "replied": len(replied),
        "never_replied": int((~group.replied).sum()),
        "never_replied_pct": 100 * (1 - len(replied) / len(group)),
        "median_days": replied.median(),
        "mean_days": replied.mean(),
        "p75_days": replied.quantile(0.75),
        "p90_days": replied.quantile(0.90),
        "max_days": replied.max(),
    }


def question_3(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Reply speed and never-replied share for paid vs unpaid roles."""
    rows = [
        {"group": label, **reply_stats(subset)}
        for label, subset in (("paid", df[df.paid]), ("unpaid", df[~df.paid]))
    ]
    summary = add_wilson(pd.DataFrame(rows), "never_replied", "applications")

    paid_days = df[df.paid].days_to_first_reply.dropna()
    unpaid_days = df[~df.paid].days_to_first_reply.dropna()
    mann_whitney = stats.mannwhitneyu(paid_days, unpaid_days, alternative="two-sided")
    never_chi2, never_p, _, _ = stats.chi2_contingency(pd.crosstab(df.paid, df.replied))
    never_low, never_high = newcombe_diff(
        int(summary.loc[1, "never_replied"]),
        int(summary.loc[1, "applications"]),
        int(summary.loc[0, "never_replied"]),
        int(summary.loc[0, "applications"]),
    )
    tests = pd.DataFrame(
        [
            {
                "median_diff_days": summary.loc[1, "median_days"] - summary.loc[0, "median_days"],
                "mean_diff_days": summary.loc[1, "mean_days"] - summary.loc[0, "mean_days"],
                "never_reply_diff_pp": summary.loc[1, "never_replied_pct"]
                - summary.loc[0, "never_replied_pct"],
                "never_reply_diff_ci_low_pp": 100 * never_low,
                "never_reply_diff_ci_high_pp": 100 * never_high,
                "mannwhitney_u": mann_whitney.statistic,
                "mannwhitney_p": mann_whitney.pvalue,
                "never_reply_chi2": never_chi2,
                "never_reply_p": never_p,
            }
        ]
    )

    month = df.assign(month=df.applied_on.dt.to_period("M").astype(str))
    cutoff = df.applied_on.max() - pd.Timedelta(days=21)
    scopes = [(f"month {name}", subset) for name, subset in month.groupby("month")]
    scopes.append(("matured >=21 days", df[df.applied_on <= cutoff]))
    robustness = []
    for scope, subset in scopes:
        for label, group in (("paid", subset[subset.paid]), ("unpaid", subset[~subset.paid])):
            row = reply_stats(group)
            robustness.append(
                {
                    "scope": scope,
                    "group": label,
                    "applications": row["applications"],
                    "never_replied": row["never_replied"],
                    "never_replied_pct": row["never_replied_pct"],
                    "median_days": row["median_days"],
                    "mean_days": row["mean_days"],
                }
            )
    robustness_df = add_wilson(pd.DataFrame(robustness), "never_replied", "applications")

    log("Q3. Reply speed, paid vs unpaid roles")
    for _, row in summary.iterrows():
        log(
            f"  {row.group:<6} {row.applications:>4} apps  {row.replied:>4} replied  "
            f"never {row.never_replied:>3} ({row.never_replied_pct:4.1f}%, "
            f"95% CI {row.ci_low:4.1f}-{row.ci_high:4.1f}%)  "
            f"median {row.median_days:4.1f}d  mean {row.mean_days:4.1f}d  p90 {row.p90_days:4.1f}d"
        )
    log(
        f"  Median gap {tests.loc[0, 'median_diff_days']:.1f}d; never-reply gap "
        f"{tests.loc[0, 'never_reply_diff_pp']:.1f} pp "
        f"(95% CI {tests.loc[0, 'never_reply_diff_ci_low_pp']:.1f}-"
        f"{tests.loc[0, 'never_reply_diff_ci_high_pp']:.1f}); "
        f"Mann-Whitney p {mann_whitney.pvalue:.2g}"
    )
    log()

    return summary, tests, robustness_df
