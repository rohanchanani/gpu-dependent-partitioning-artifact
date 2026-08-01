#!/usr/bin/env python3
"""Generate weak-scaling figures from data/final/weak_scaling_raw.csv."""

from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "data" / "final" / "weak_scaling_raw.csv"
OUT_DIR = ROOT / "figures"

FONT_SIZE = 15
TITLE_SIZE = 17
TICK_SIZE = 13
LEGEND_SIZE = 13

APPS = {
    "Circuit": "circuit",
    "Pennant": "pennant",
    "MiniAero": "miniaero",
}


def configure_matplotlib():
    plt.rcParams.update({
        "font.size": FONT_SIZE,
        "axes.titlesize": TITLE_SIZE,
        "axes.labelsize": FONT_SIZE,
        "xtick.labelsize": TICK_SIZE,
        "ytick.labelsize": TICK_SIZE,
        "legend.fontsize": LEGEND_SIZE,
    })


def summarize(df, app_key):
    app_df = df[df["app"] == app_key].copy()
    return (
        app_df.groupby("p")
        .agg(
            gpu_median_ms=("gpu_us", lambda x: x.median() / 1000),
            cpu_median_ms=("cpu_us", lambda x: x.median() / 1000),
        )
        .reset_index()
    )


def plot_app(df, app_name, app_key):
    s = summarize(df, app_key)
    fig, ax = plt.subplots(figsize=(7.2, 4.8))

    ax.plot(s["p"], s["gpu_median_ms"], color="#dc2626", marker="s",
            linewidth=2.4, markersize=7, label="GPU")
    ax.plot(s["p"], s["cpu_median_ms"], color="#2563eb", marker="o",
            linewidth=2.4, markersize=7, label="CPU")

    ax.set_title(f"{app_name} Weak Scaling")
    ax.set_xlabel("# of GPUs [Pieces]")
    ax.set_ylabel("Runtime (ms)")
    ax.set_xticks(s["p"])
    ax.set_yscale("log")
    ax.grid(True, which="both", linestyle="--", alpha=0.35)
    ax.legend()
    fig.tight_layout()
    return fig


def main():
    configure_matplotlib()
    OUT_DIR.mkdir(exist_ok=True)
    df = pd.read_csv(CSV_PATH)

    for app_name, app_key in APPS.items():
        fig = plot_app(df, app_name, app_key)
        stem = app_key.lower()
        for suffix in ["png", "pdf"]:
            path = OUT_DIR / f"weak_scaling_{stem}.{suffix}"
            fig.savefig(path, dpi=300, bbox_inches="tight")
            print(f"wrote {path}")
        plt.close(fig)


if __name__ == "__main__":
    main()
