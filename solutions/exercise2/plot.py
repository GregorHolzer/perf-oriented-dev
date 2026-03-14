#!/usr/bin/env python3
import argparse
import csv
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

METRICS = [
    ("wall_clock_s", "Wall Clock (s)"),
    ("user_cpu_s",   "User CPU (s)"),
    ("sys_cpu_s",    "Sys CPU (s)"),
    ("max_rss_kb",   "Max RSS (KB)"),
]


def load_csv(path: Path) -> list[dict]:
    rows = []
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row.get("wall_clock_s") or row["wall_clock_s"].strip() == "":
                continue
            try:
                parsed = {
                    "defines": row.get("defines", "default"),
                    "args":    row.get("args", ""),
                }
                for metric, _ in METRICS:
                    parsed[metric] = float(row[metric]) if row.get(metric, "").strip() else 0.0
                rows.append(parsed)
            except ValueError:
                continue
    return rows


def compute_stats(values: list):
    n = len(values)
    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / n
    std = variance ** 0.5
    cv = std / abs(mean) if mean != 0 else 0.0
    return mean, std, cv


def collect_stats(directory: Path) -> dict[str, dict]:
    """Returns {prog_name: {combo_label: {metric: (mean, std, cv)}}}"""
    stats = {}
    for csv_path in sorted(directory.glob("*.csv")):
        prog_name = csv_path.stem
        rows = load_csv(csv_path)
        if not rows:
            continue

        combos = {(r["defines"], r["args"]) for r in rows}
        prog_stats = {}
        for defines_str, args_str in sorted(combos):
            combo_rows = [r for r in rows if r["defines"] == defines_str and r["args"] == args_str]
            label = f"{defines_str}\n{args_str}" if defines_str not in ("default", "") else args_str
            metric_stats = {}
            for metric, _ in METRICS:
                vals = [r[metric] for r in combo_rows]
                metric_stats[metric] = compute_stats(vals)
            prog_stats[label] = metric_stats

        stats[prog_name] = prog_stats
    return stats


def plot_metric(axes_row, all_progs, no_load_stats, load_stats, metric_key, metric_label):
    colors = {"no load": "#4C9BE8", "external load": "#E8704C"}

    for ax, prog in zip(axes_row, all_progs):
        no_load = no_load_stats.get(prog, {})
        load    = load_stats.get(prog, {})
        all_combos = sorted(set(no_load) | set(load))

        x = np.arange(len(all_combos))
        width = 0.35

        for combo_dict, offset, label, color in [
            (no_load, -width / 2, "no load",        colors["no load"]),
            (load,     width / 2, "external load",  colors["external load"]),
        ]:
            means = [combo_dict.get(c, {}).get(metric_key, (0, 0, 0))[0] for c in all_combos]
            stds  = [combo_dict.get(c, {}).get(metric_key, (0, 0, 0))[1] for c in all_combos]
            cvs   = [combo_dict.get(c, {}).get(metric_key, (0, 0, 0))[2] for c in all_combos]

            bars = ax.bar(x + offset, means, width, label=label, color=color,
                          yerr=stds, capsize=4, error_kw={"elinewidth": 1.2})

            for bar, cv, std in zip(bars, cvs, stds):
                h = bar.get_height()
                if h > 0:
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        h + std + ax.get_ylim()[1] * 0.01,
                        f"cv={cv:.2f}",
                        ha="center", va="bottom", fontsize=6.5, rotation=45
                    )

        ax.set_xticks(x)
        ax.set_xticklabels(all_combos, fontsize=8)
        ax.set_ylabel(metric_label, fontsize=8)
        ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())
        ax.grid(axis="y", linestyle="--", alpha=0.4)
        ax.legend(fontsize=7)


def plot(no_load_dir: Path, load_dir: Path, output_path: Path):
    no_load_stats = collect_stats(no_load_dir)
    load_stats    = collect_stats(load_dir)

    all_progs = sorted(set(no_load_stats) | set(load_stats))
    n_progs   = len(all_progs)

    output_path = Path(output_path)

    for metric_key, metric_label in METRICS:
        fig, axes = plt.subplots(
            1, n_progs,
            figsize=(4 * n_progs, 5),
            sharey=False,
            squeeze=False,
        )

        for ax, prog in zip(axes[0], all_progs):
            ax.set_title(prog, fontweight="bold", fontsize=11)

        plot_metric(axes[0], all_progs, no_load_stats, load_stats, metric_key, metric_label)

        fig.suptitle(f"No Load vs External Load — {metric_label}", fontsize=14, fontweight="bold", y=1.01)
        fig.tight_layout()

        out = output_path.parent / f"{output_path.stem}_{metric_key}{output_path.suffix}"
        fig.savefig(out, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"Saved plot to {out}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("no_load_dir", help="Directory with no-load CSVs")
    parser.add_argument("load_dir",    help="Directory with external-load CSVs")
    parser.add_argument("--output", default="comparison.png", help="Output plot path")
    args = parser.parse_args()

    plot(
        Path(args.no_load_dir).expanduser().resolve(),
        Path(args.load_dir).expanduser().resolve(),
        Path(args.output).expanduser().resolve(),
    )


if __name__ == "__main__":
    main()