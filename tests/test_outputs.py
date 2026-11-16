from __future__ import annotations

import json
import struct
from pathlib import Path

import pandas as pd

import analysis
import run_all

EXPECTED_OUTPUTS = {
    "q1_source_rates.csv",
    "q1_role_rates.csv",
    "q1_tests.csv",
    "q2_by_steps.csv",
    "q2_comparison.csv",
    "q2_tests.csv",
    "q2_by_role.csv",
    "q3_paid_vs_unpaid.csv",
    "q3_tests.csv",
    "q3_robustness.csv",
    "results.md",
    "summary.txt",
    "data_quality.json",
    "chart_reply_speed.png",
}


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    return struct.unpack(">II", data[16:24])


def test_full_pipeline(tmp_path, data_path):
    out = tmp_path / "outputs"
    analysis.main(data_path, out)
    assert {path.name for path in out.iterdir()} == EXPECTED_OUTPUTS

    dq = json.loads((out / "data_quality.json").read_text(encoding="utf-8"))
    assert dq["summary"] == {"pass": 11, "warn": 2, "fail": 0, "not_assessed": 1}
    assert dq["rows_raw"] == 1206
    assert dq["rows_clean"] == 1200

    results = (out / "results.md").read_text(encoding="utf-8")
    assert "## Data quality" in results
    assert "Newcombe 95% CI" in results
    assert "Benjamini-Hochberg" in results
    assert "data_quality.json" in results

    assert png_size(out / "chart_reply_speed.png") == (2820, 1680)


def test_outputs_are_deterministic(tmp_path, data_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    analysis.main(data_path, first)
    analysis.main(data_path, second)

    for name in sorted(EXPECTED_OUTPUTS):
        assert (first / name).read_bytes() == (second / name).read_bytes(), name


def test_cli_reports_missing_input(tmp_path, capsys):
    code = analysis.cli(
        [
            "--data",
            str(tmp_path / "does-not-exist.csv"),
            "--out",
            str(tmp_path / "out"),
        ]
    )
    assert code == 2
    assert "ERROR:" in capsys.readouterr().err


def test_cli_no_expected_checks(tmp_path, data_path):
    subset = tmp_path / "subset.csv"
    raw = pd.read_csv(data_path, dtype=str).drop_duplicates().iloc[1:]
    raw.to_csv(subset, index=False)
    out = tmp_path / "out"
    code = analysis.cli(
        [
            "--data",
            str(subset),
            "--out",
            str(out),
            "--no-expected-checks",
        ]
    )
    assert code == 0
    assert (out / "results.md").exists()
    assert "1,199 applications analysed" in (out / "results.md").read_text(encoding="utf-8")


def test_run_all_writes_subset_outputs(tmp_path, data_path):
    subset = tmp_path / "subset.csv"
    raw = pd.read_csv(data_path, dtype=str).drop_duplicates().iloc[1:]
    raw.to_csv(subset, index=False)
    out = tmp_path / "run-all-out"
    code = run_all.cli(
        [
            "--data",
            str(subset),
            "--out",
            str(out),
            "--no-expected-checks",
        ]
    )
    assert code == 0
    assert {path.name for path in out.iterdir()} == EXPECTED_OUTPUTS
    assert "1,199 applications analysed" in (out / "results.md").read_text(encoding="utf-8")
