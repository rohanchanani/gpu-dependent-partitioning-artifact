#!/usr/bin/env python3
"""Generate image/preimage buffer-sweep figures from data/final/microbenchmarks.csv."""

from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "data" / "final" / "microbenchmarks.csv"
OUT_DIR = ROOT / "figures"

FONT_SIZE = 15
TITLE_SIZE = 17
TICK_SIZE = 13
LEGEND_SIZE = 13

BUFFER_TICKS = [1, 2, 3, 4, 5, 7, 10, 15, 20, 25, 30, 40, 50, 75, 100]
DIM_ORDER = ["1d", "2d", "3d"]
DIM_LABELS = {"1d": "1D -> 1D", "2d": "2D -> 2D", "3d": "3D -> 3D"}

STYLE = {
    ("CPU", "dense"): dict(color="#2563eb", marker="o", linestyle="-", label="CPU dense"),
    ("CPU", "sparse"): dict(color="#2563eb", marker="^", linestyle=(0, (4, 2)), label="CPU sparse"),
    ("GPU", "dense"): dict(color="#dc2626", marker="s", linestyle="-", label="GPU dense"),
    ("GPU", "sparse"): dict(color="#dc2626", marker="D", linestyle=(0, (4, 2)), label="GPU sparse"),
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


def make_figure(df, op):
    op_df = df[df["op"] == op].copy()
    fig, axes = plt.subplots(1, 3, figsize=(12.5, 4.2), sharey=True, constrained_layout=True)
    legend_handles = {}

    for ax, dim in zip(axes, DIM_ORDER):
        panel = op_df[op_df["dimension"] == dim].copy()

        for backend in ["CPU", "GPU"]:
            for density in ["dense", "sparse"]:
                g = panel[
                    (panel["backend"] == backend) &
                    (panel["density"] == density)
                ].sort_values("buffer_percent")
                if g.empty:
                    continue
                style = STYLE[(backend, density)]
                line, = ax.plot(
                    g["buffer_percent"],
                    g["median_ms"],
                    color=style["color"],
                    marker=style["marker"],
                    linestyle=style["linestyle"],
                    linewidth=2.3,
                    markersize=6.5,
                    label=style["label"],
                )
                legend_handles[style["label"]] = line

        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xticks(BUFFER_TICKS)
        ax.set_xticklabels([str(x) for x in BUFFER_TICKS], rotation=35, ha="right")
        ax.set_title(DIM_LABELS[dim])
        ax.grid(True, which="major", linewidth=0.7, alpha=0.35)
        ax.grid(True, which="minor", linewidth=0.35, alpha=0.15)
        ax.set_xlabel("Scratch buffer (% of requirement range)")

    axes[0].set_ylabel("Dependent partitioning time (ms)")
    fig.suptitle({
        "image": "Image: buffer-size sensitivity",
        "preimage": "Preimage: buffer-size sensitivity",
    }[op])

    labels = ["CPU dense", "CPU sparse", "GPU dense", "GPU sparse"]
    handles = [legend_handles[label] for label in labels if label in legend_handles]
    fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, -0.11), ncol=4, frameon=False)
    return fig


def main():
    configure_matplotlib()
    OUT_DIR.mkdir(exist_ok=True)

    df = pd.read_csv(CSV_PATH)
    df = df[df["op"].isin(["image", "preimage"])].copy()
    for col in ["buffer_percent", "median_ms"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    for op in ["image", "preimage"]:
        fig = make_figure(df, op)
        for suffix in ["png", "pdf"]:
            path = OUT_DIR / f"{op}_buffer_sweep.{suffix}"
            fig.savefig(path, dpi=300, bbox_inches="tight")
            print(f"wrote {path}")
        plt.close(fig)


if __name__ == "__main__":
    main()
