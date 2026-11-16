"""The reply-speed chart."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .config import DEFAULT_OUT


def make_chart(df: pd.DataFrame, out_dir: Path | str = DEFAULT_OUT) -> Path:
    """One chart: cumulative reply curve, paid vs unpaid."""
    days = np.arange(0, 33)
    colors = {"paid": "#0B6E69", "unpaid": "#C2410C"}

    fig = plt.figure(figsize=(9.4, 5.6), facecolor="white")
    ax = fig.add_axes([0.075, 0.17, 0.90, 0.66])

    for group, subset in (("paid", df[df.paid]), ("unpaid", df[~df.paid])):
        series = subset.days_to_first_reply.dropna()
        shares = np.array(
            [100 * (subset.days_to_first_reply <= day).sum() / len(subset) for day in days]
        )
        ax.step(
            days,
            shares,
            where="post",
            color=colors[group],
            linewidth=2.4,
            solid_capstyle="round",
            label=f"{group.title()} (median {series.median():.0f} days)",
        )
        ax.scatter([days[-1]], [shares[-1]], color=colors[group], s=34, zorder=5)
        ax.text(
            33.0,
            shares[-1],
            f"{group.title()}\n{shares[-1]:.0f}% replied",
            color=colors[group],
            fontsize=10.5,
            fontweight="bold",
            va="center",
            ha="left",
            linespacing=1.35,
        )

    ax.set_xlim(0, 40.5)
    ax.set_ylim(0, 100)
    ax.set_xticks(np.arange(0, 33, 4))
    ax.set_yticks(np.arange(0, 101, 20))
    ax.set_xlabel("Days since application", fontsize=10.5, labelpad=9, color="#334155")
    ax.set_ylabel(
        "Share of applications with a reply (%)", fontsize=10.5, labelpad=9, color="#334155"
    )
    ax.grid(axis="y", color="#E2E8F0", linewidth=0.9)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color("#CBD5E1")
    ax.tick_params(colors="#475569", labelsize=9.5, length=0)
    ax.legend(
        loc="lower right",
        frameon=False,
        fontsize=9.5,
        handlelength=2.4,
        labelcolor="#334155",
        bbox_to_anchor=(0.72, 0.02),
    )

    fig.text(
        0.075,
        0.935,
        "Paid roles reply faster, and go silent far less often",
        fontsize=16.5,
        fontweight="bold",
        color="#0F172A",
        ha="left",
    )
    fig.text(
        0.075,
        0.885,
        "Cumulative share of applications with a first reply, July-September 2026 "
        f"({int(df.paid.sum())} paid, {int((~df.paid).sum())} unpaid)",
        fontsize=10,
        color="#52606D",
        ha="left",
    )
    fig.text(
        0.075,
        0.045,
        "Paid = stipend above INR 0. Blank reply dates are treated as no reply by 30 September 2026.\n"
        "Source: supplied job-board dataset, after removing exact duplicate rows. "
        "Regenerate with python -m job_board_analysis.",
        fontsize=8,
        color="#64748B",
        ha="left",
        linespacing=1.5,
    )

    path = Path(out_dir) / "chart_reply_speed.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=300, facecolor="white")
    plt.close(fig)
    return path
