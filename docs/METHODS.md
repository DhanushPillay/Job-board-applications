# Methods

## Scope

Three descriptive questions about 1,200 synthetic job-board applications from July to September 2026. The unit is one application. The analysis is observational: no randomisation, no causal claim.

## Cleaning

The supplied 1,206 rows contain 6 exact duplicates, giving 1,200 applications. Nine work-mode labels are normalised. Fifteen missing `source` values are labelled `unknown` and excluded from source comparisons; none was hired. The 234 blank `days_to_first_reply` values are treated as "no reply by 30 September 2026" and are not imputed. Zero stipends are kept as unpaid. No rows are removed for being unusual. The full log is in `data/data_dictionary.md`.

## Q1: hires per 100 by source

For source \(s\):

\[
\text{rate}_s = 100 \times \frac{\text{hires}_s}{\text{applications}_s}
\]

- Wilson score 95% interval for each source.
- Direct standardisation: apply the overall role distribution to each source's role-specific hire rates. This removes the part of the source difference explained by a different role mix.
- Fisher exact test for referral versus each other source, on the 2x2 table of hired and not hired.
- Benjamini-Hochberg adjustment across the four pairwise tests. This controls the false discovery rate, not the family-wise error rate.
- Within-role rates are reported with Wilson intervals and application counts. Cells are small, so the interval matters more than the point estimate.

## Q2: shortlisting by step completion

Compare `steps_done = 4` with `steps_done` 0 to 3.

- Shortlist rate and Wilson 95% interval for each group.
- Risk difference in percentage points, with a Newcombe hybrid score interval. This is preferable to a Wald interval when proportions are near 0 or 1.
- Risk ratio.
- Pearson chi-square with Yates correction for the 2x2 table.
- The same comparison within each role, using Fisher exact tests and Benjamini-Hochberg adjustment across the six roles.

The estimate is an association. Step completion may trigger review, or it may proxy for motivation or fit; the data cannot separate those mechanisms.

## Q3: reply speed, paid versus unpaid

- Paid: `stipend_inr_month > 0`. Unpaid: stipend 0.
- Median, mean, p75 and p90 days among applications that received a reply.
- Never-replied share over all applications in the group, with a Wilson 95% interval.
- Newcombe 95% interval for the difference in never-replied shares.
- Mann-Whitney U test for reply days; Pearson chi-square with Yates correction for never-replied.
- Robustness: repeat by application month and restrict to applications at least 21 days old at the snapshot. The maturity cut keeps applications submitted on or before 9 September 2026, so each has at least three weeks to receive a reply.

The never-replied share is right-censored: a blank means "not yet by 30 September", not "never". The maturity check reduces this concern but cannot remove it.

## Data quality

`analysis.py` checks completeness, uniqueness, validity, consistency, timeliness, distribution and accuracy before estimation. Results are in `outputs/data_quality.json`. A hard failure stops the run; warnings are reported, not silently repaired. Accuracy is not assessed because there is no independent source.

## Reproducibility

- Fixed input in `data/`; no network, randomness or timestamps in outputs.
- Dependencies are pinned in `pyproject.toml`.
- `python run_all.py` writes every file in `outputs/` for the supplied extract. `--no-expected-checks` relaxes the expected row counts and still writes the same outputs.
- `pytest` covers the helpers, cleaning contract, the three questions, output generation and rerun determinism.
- The CSVs, JSON and chart PNG have been byte-identical across reruns in this environment.

## Limitations

- The data is synthetic and supplied; there is no external source to reconcile against.
- Q1 role cells are small (8 to 146 applications, at most 7 hires). Finance has one hire total.
- Q2 is observational; the large gap is not a treatment effect.
- Q3 blanks are censored. The 21-day check is a sensitivity analysis, not a fix.
- No adjustment for role, month or other covariates beyond the Q1 role standardisation. The sample is too small for a stable multivariable model.
