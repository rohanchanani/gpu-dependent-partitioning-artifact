#!/usr/bin/env python3
"""Generate dynamic repartitioning figure from data/final/repartitioning.csv."""

from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "data" / "final" / "repartitioning.csv"
OUT_DIR = ROOT / "figures"

FONT_SIZE = 15
TITLE_SIZE = 17
TICK_SIZE = 13
LEGEND_SIZE = 13


def configure_matplotlib():
    plt.rcParams.update({
        "font.size": FONT_SIZE,
        "axes.titlesize": TITLE_SIZE,
        "axes.labelsize": FONT_SIZE,
        "xtick.labelsize": TICK_SIZE,
        "ytick.labelsize": TICK_SIZE,
        "legend.fontsize": LEGEND_SIZE,
    })


def main():
    configure_matplotlib()
    OUT_DIR.mkdir(exist_ok=True)

    df = pd.read_csv(CSV_PATH)
    baseline = df[df["repartition_interval"] == 0].iloc[0]
    peak = max(baseline["gpu"], baseline["cpu"])
    plot_df = df[df["repartition_interval"] > 0].copy().sort_values("repartition_interval")

    fig, ax = plt.subplots(figsize=(8.5, 5.4))
    ax.plot(plot_df["repartition_interval"], plot_df["gpu"], color="#dc2626",
            marker="s", linewidth=2.4, markersize=7, label="GPU")
    ax.plot(plot_df["repartition_interval"], plot_df["cpu"], color="#2563eb",
            marker="o", linewidth=2.4, markersize=7, label="CPU")
    ax.axhline(peak, color="black", linestyle="--", linewidth=1.2,
               label=f"Baseline throughput, no repartitioning = {peak:.1f}")

    ax.set_xlabel("Repartition interval (iterations)")
    ax.set_ylabel("Throughput (iterations/sec)")
    ax.set_title("Throughput vs. Repartition Interval")
    ax.set_xscale("linear")
    ax.grid(True, which="both", linestyle="--", linewidth=0.5, alpha=0.45)
    ax.legend()
    fig.tight_layout()

    for suffix in ["png", "pdf"]:
        path = OUT_DIR / f"repartitioning.{suffix}"
        fig.savefig(path, dpi=300, bbox_inches="tight")
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
