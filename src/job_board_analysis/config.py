"""Paths and the fixed domain vocabulary of the dataset."""

from __future__ import annotations

from pathlib import Path

# config.py lives at src/job_board_analysis/config.py; the project root is two
# levels up, so data/ and outputs/ resolve the same way from a checkout.
ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "job-board-applications.csv"
DEFAULT_OUT = ROOT / "outputs"

ROLE_ORDER = ["Software", "Data", "Design", "Marketing", "Finance", "Operations"]
SOURCE_ORDER = ["referral", "email", "search", "college", "social"]
YES_NO = {"yes", "no"}
REQUIRED_COLUMNS = [
    "application_id",
    "applied_on",
    "role_category",
    "work_mode",
    "stipend_inr_month",
    "source",
    "steps_done",
    "shortlisted",
    "interviewed",
    "hired",
    "days_to_first_reply",
]
