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

# Distinct colors for up to ~10 directories; extend if needed
PALETTE = [
    "#4C9BE8", "#E8704C", "#5DBB63", "#B06DDB",
    "#E8C44C", "#4CBFBF", "#E84C7D", "#A0A0A0",
    "#8B5CF6", "#F59E0B",
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
            combo_rows = [
                r for r in rows
                if r["defines"] == defines_str and r["args"] == args_str
            ]
            label = (
                f"{defines_str}\n{args_str}"
                if defines_str not in ("default", "")
                else args_str
            )
            metric_stats = {}
            for metric, _ in METRICS:
                vals = [r[metric] for r in combo_rows]
                metric_stats[metric] = compute_stats(vals)
            prog_stats[label] = metric_stats
        stats[prog_name] = prog_stats
    return stats


def plot_metric(axes_row, all_progs, dir_stats_list, metric_key, metric_label):
    """
    dir_stats_list: list of (label, stats_dict) pairs, one per input directory.
    """
    n_dirs = len(dir_stats_list)
    width = 0.8 / n_dirs  # bars share the unit interval evenly

    for ax, prog in zip(axes_row, all_progs):
        all_combos = sorted(
            set().union(*[set(stats.get(prog, {})) for _, stats in dir_stats_list])
        )
        x = np.arange(len(all_combos))

        for i, (dir_label, dir_stats) in enumerate(dir_stats_list):
            prog_combos = dir_stats.get(prog, {})
            color = PALETTE[i % len(PALETTE)]
            offset = (i - (n_dirs - 1) / 2) * width

            means = [prog_combos.get(c, {}).get(metric_key, (0, 0, 0))[0] for c in all_combos]
            stds  = [prog_combos.get(c, {}).get(metric_key, (0, 0, 0))[1] for c in all_combos]


            bars = ax.bar(
                x + offset, means, width,
                label=dir_label, color=color,
                yerr=stds, capsize=4,
                error_kw={"elinewidth": 1.2},
            )



        ax.set_xticks(x)
        ax.set_xticklabels(all_combos, fontsize=8)
        ax.set_ylabel(metric_label, fontsize=8)
        ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())
        ax.grid(axis="y", linestyle="--", alpha=0.4)
        ax.legend(fontsize=7)


def plot(dirs: list[tuple[str, Path]], output_path: Path):
    """
    dirs: list of (label, path) pairs.
    """
    dir_stats_list = [(label, collect_stats(path)) for label, path in dirs]

    all_progs = sorted(
        set().union(*[set(stats) for _, stats in dir_stats_list])
    )
    n_progs = len(all_progs)

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

        plot_metric(axes[0], all_progs, dir_stats_list, metric_key, metric_label)
        fig.tight_layout()

        out = output_path.parent / f"{output_path.stem}_{metric_key}{output_path.suffix}"
        fig.savefig(out, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"Saved plot to {out}")


def main():
    parser = argparse.ArgumentParser(
        description="Compare benchmark CSVs across N directories.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Two dirs (original behaviour)
  %(prog)s no_load/ load/

  # Three dirs with custom labels
  %(prog)s no_load/:baseline load/:heavy_load optimised/:optimised

  # Labels are optional; directory name is used when omitted
  %(prog)s no_load/ load/ optimised/ --output results.png
""",
    )
    parser.add_argument(
        "dirs",
        nargs="+",
        metavar="DIR_OR_LABEL:DIR",
        help=(
            "One or more directories containing benchmark CSVs. "
            "Optionally prefix with a label: 'my_label:path/to/dir'. "
            "If no label is given, the directory name is used."
        ),
    )
    parser.add_argument(
        "--output", default="comparison.png",
        help="Base output path for plots (default: comparison.png)",
    )
    args = parser.parse_args()

    dirs: list[tuple[str, Path]] = []
    for entry in args.dirs:
        if ":" in entry:
            label, _, raw_path = entry.partition(":")
        else:
            raw_path = entry
            label = Path(entry).name  # use directory name as label
        path = Path(raw_path).expanduser().resolve()
        if not path.is_dir():
            parser.error(f"Not a directory: {path}")
        dirs.append((label, path))

    if len(dirs) < 2:
        parser.error("At least two directories are required.")

    plot(dirs, Path(args.output).expanduser().resolve())


if __name__ == "__main__":
    main()