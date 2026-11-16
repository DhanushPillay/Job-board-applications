# Data dictionary

Source file: `job-board-applications.csv`
Supplied: one row per application, July to September 2026
Rows: 1,206 raw; 1,200 after removing 6 exact duplicates
Nature: synthetic; no names, contact details or other personal data

| Column | Type | Allowed values | Notes |
|---|---|---|---|
| `application_id` | text | unique identifier | Duplicate IDs after exact-row dedup stop the run. |
| `applied_on` | date | 2026-07-01 to 2026-09-30 | Application date. The snapshot ends 2026-09-30. |
| `role_category` | category | Software, Data, Design, Marketing, Finance, Operations | Six roles. Finance has only one hire, so role-level estimates there are weak. |
| `work_mode` | category | remote, hybrid, on_site | 9 labels were normalised from `Remote`, `Hybrid`, `On-site`. |
| `stipend_inr_month` | integer | 0 to 40,000, steps of 5,000 | 0 means unpaid. No outlier removal. |
| `source` | category | search, social, email, referral, college | 15 missing values are labelled `unknown` and excluded from source comparisons. None of the 15 was hired. |
| `steps_done` | integer | 0 to 4 | 4 means the applicant completed every step. |
| `shortlisted` | yes/no | yes, no | Funnel stage 1. |
| `interviewed` | yes/no | yes, no | Funnel stage 2. Must be a subset of shortlisted. |
| `hired` | yes/no | yes, no | Funnel stage 3. Must be a subset of interviewed. |
| `days_to_first_reply` | number or blank | 1 to 32 when present | Blank means no reply by the 2026-09-30 snapshot, not a missing value to impute. |

## Missingness

| Field | Blank rows | Treatment |
|---|---|---|
| `source` | 15 | Label `unknown`; exclude from Q1 comparisons. |
| `days_to_first_reply` | 234 | Treat as no reply by 30 September 2026. Do not impute. |

Every row with a blank reply date is non-shortlisted. No shortlisted, interviewed or hired row has a blank reply date.

## Cleaning log

1. Strip leading and trailing whitespace from every field.
2. Drop 6 exact duplicate rows (1,206 to 1,200).
3. Normalise 9 work-mode labels to `remote`, `hybrid`, `on_site`.
4. Label 15 missing `source` values `unknown`; keep them out of Q1 rankings.
5. Parse dates and numbers with explicit errors; fail the run if a value cannot be parsed.
6. Keep blank reply dates as `NaN` and create a `replied` flag.
7. Keep 466 unpaid applications; do not drop zero stipends.
8. Do not remove outliers or winsorise stipends.
9. Do not use `application_id` as an analysis feature; IDs are not printed in outputs.

## Analysis definitions

- **Hires per 100:** `100 * hired / applications`.
- **Paid:** `stipend_inr_month > 0`.
- **Unpaid:** `stipend_inr_month = 0`.
- **Completed all steps:** `steps_done = 4`.
- **Never replied:** `days_to_first_reply` is blank as of 2026-09-30.
- **Snapshot:** 2026-09-30. Applications near that date have less exposure time; Q3 includes a 21-day maturity check.

## Validation

`analysis.py` checks the schema, duplicates, categories, numeric ranges, date range, funnel order, and the blank-reply rule before writing outputs. `outputs/data_quality.json` records pass, warning, fail and not-assessed checks. `--no-expected-checks` skips only assertions tied to this exact supplied file; structural checks still run.
