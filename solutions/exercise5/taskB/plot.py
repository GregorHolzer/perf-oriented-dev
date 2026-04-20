"""
Plot for taskB: compare -O2 baseline, each individual O3 flag added on top of O2, and -O3.
Reads taskB CSVs and taskA CSVs (for O2/O3 baselines).
"""

import csv
import sys
from pathlib import Path
from collections import defaultdict
import statistics

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

TASKB_DIR = Path(".")         
TASKA_DIR = Path("../taskA")  
OUTPUT_DIR = Path(".")

PROGRAMS = ["ssca2", "mmul", "nbody", "npb_bt_w", "qap", "delannoy"]

METRIC = "wall_clock_s"

FLAG_LABELS = {
    "CMAKE_C_FLAGS__O2_fgcse_after_reload__enabled":          "fgcse-after-reload",
    "CMAKE_C_FLAGS__O2_fipa_cp_clone__enabled":               "fipa-cp-clone",
    "CMAKE_C_FLAGS__O2_floop_interchange__enabled":           "floop-interchange",
    "CMAKE_C_FLAGS__O2_floop_unroll_and_jam__enabled":        "floop-unroll-and-jam",
    "CMAKE_C_FLAGS__O2_fpeel_loops__enabled":                 "fpeel-loops",
    "CMAKE_C_FLAGS__O2_fpredictive_commoning__enabled":       "fpredictive-commoning",
    "CMAKE_C_FLAGS__O2_fsplit_loops__enabled":                "fsplit-loops",
    "CMAKE_C_FLAGS__O2_fsplit_paths__enabled":                "fsplit-paths",
    "CMAKE_C_FLAGS__O2_ftree_loop_distribution__enabled":     "ftree-loop-distribution",
    "CMAKE_C_FLAGS__O2_ftree_partial_pre__enabled":           "ftree-partial-pre",
    "CMAKE_C_FLAGS__O2_funroll_completely_grow_size__enabled":"funroll-completely-grow-size",
    "CMAKE_C_FLAGS__O2_funswitch_loops__enabled":             "funswitch-loops",
    "CMAKE_C_FLAGS__O2_fvect_cost_model___dynamic":           "fvect-cost-model=dynamic",
    "CMAKE_C_FLAGS__O2_fversion_loops_for_strides__enabled":  "fversion-loops-for-strides",
}


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path) as f:
        return list(csv.DictReader(f))


def group_mean(rows: list[dict], defines: str, metric: str) -> float | None:
    vals = [float(r[metric]) for r in rows
            if r["defines"] == defines and metric in r and r[metric]]
    return statistics.mean(vals) if vals else None


def group_stdev(rows: list[dict], defines: str, metric: str) -> float:
    vals = [float(r[metric]) for r in rows
            if r["defines"] == defines and metric in r and r[metric]]
    return statistics.stdev(vals) if len(vals) > 1 else 0.0


def match_flag_label(defines_str: str) -> str | None:
    """Match a defines slug to a FLAG_LABELS key by substring — handles extra defines like S=1000."""
    for key, label in FLAG_LABELS.items():
        flag_part = key.replace("CMAKE_C_FLAGS__O2_", "")
        if flag_part in defines_str:
            return label
    return None


def get_baseline(taska_rows: list[dict], flag_name: str) -> float | None:
    """Get mean wall_clock_s for a given CMAKE_C_FLAGS value from taskA CSV."""
    vals = [float(r[METRIC]) for r in taska_rows
            if r.get("defines", "") == flag_name and METRIC in r and r[METRIC]]
    return statistics.mean(vals) if vals else None


def plot_program(prog: str) -> dict[str, float]:
    """Plot per-program bar chart. Returns {flag_label: pct_improvement_vs_o2}."""
    taskb_rows = read_csv(TASKB_DIR / f"{prog}.csv")
    taska_rows = read_csv(TASKA_DIR / f"{prog}.csv")

    if not taskb_rows:
        print(f"  [skip] {prog}: no taskB data")
        return {}

    o2_baseline = None
    o3_baseline = None
    for defines_str in set(r["defines"] for r in taska_rows):
        ds = defines_str.upper()
        if "O2" in ds and "O3" not in ds and o2_baseline is None:
            o2_baseline = get_baseline(taska_rows, defines_str)
        if "O3" in ds and o3_baseline is None:
            o3_baseline = get_baseline(taska_rows, defines_str)

    all_defines = sorted(set(r["defines"] for r in taskb_rows))

    labels, means, stdevs = [], [], []
    for d in all_defines:
        label = match_flag_label(d)
        if label:
            labels.append(label)
            means.append(group_mean(taskb_rows, d, METRIC))
            stdevs.append(group_stdev(taskb_rows, d, METRIC))

    valid = [(l, m, s) for l, m, s in zip(labels, means, stdevs) if m is not None]
    if not valid:
        print(f"  [skip] {prog}: no valid flag data")
        return {}
    valid.sort(key=lambda x: x[1], reverse=True)
    labels, means, stdevs = zip(*valid)

    fig, ax = plt.subplots(figsize=(14, 5))

    x = np.arange(len(labels))
    bars = ax.bar(x, means, yerr=stdevs, capsize=4,
                  color="#4C72B0", alpha=0.85, label="O2 + flag", zorder=3)

    if o2_baseline:
        ax.axhline(o2_baseline, color="#DD4444", linewidth=1.8,
                   linestyle="--", label=f"-O2 baseline ({o2_baseline:.3f}s)", zorder=4)
    if o3_baseline:
        ax.axhline(o3_baseline, color="#22AA55", linewidth=1.8,
                   linestyle="-.", label=f"-O3 baseline ({o3_baseline:.3f}s)", zorder=4)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=35, ha="right", fontsize=8.5)
    ax.set_ylabel(f"{METRIC} (s)")
    ax.set_title(f"{prog}: -O2 + individual O3 flags vs baselines", fontsize=12, fontweight="bold")
    ax.legend(fontsize=9)
    ax.yaxis.grid(True, linestyle="--", alpha=0.5, zorder=0)
    ax.set_axisbelow(True)

    for bar, mean in zip(bars, means):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(stdevs) * 0.05,
                f"{mean:.3f}", ha="center", va="bottom", fontsize=7, color="#222222")

    plt.tight_layout()
    out = OUTPUT_DIR / f"{prog}.png"
    plt.savefig(out, dpi=150)
    plt.close()
    print(f"  Saved {out}")

    if not o2_baseline:
        return {}
    return {
        label: (o2_baseline - mean) / o2_baseline * 100
        for label, mean in zip(labels, means)
    }



def print_top_flags(all_improvements: dict[str, dict[str, float]], top_n: int = 3):
    """
    all_improvements: {prog: {flag_label: pct_improvement}}
    Ranks flags by mean percentage improvement across all programs.
    Positive = faster than O2, negative = slower.
    """
    all_flags = set()
    for prog_data in all_improvements.values():
        all_flags.update(prog_data.keys())

    flag_scores: dict[str, list[float]] = defaultdict(list)
    for prog_data in all_improvements.values():
        for flag, pct in prog_data.items():
            flag_scores[flag].append(pct)

    ranked = sorted(flag_scores.items(),
                    key=lambda x: statistics.mean(x[1]),
                    reverse=True)

    print("\n" + "=" * 60)
    print(f"  TOP {top_n} FLAGS BY MEAN % IMPROVEMENT OVER -O2")
    print("=" * 60)
    for i, (flag, scores) in enumerate(ranked[:top_n], 1):
        mean_pct = statistics.mean(scores)
        n_progs  = len(scores)
        direction = "faster" if mean_pct > 0 else "slower"
        print(f"  #{i}  {flag}")
        print(f"       Mean improvement: {mean_pct:+.3f}% ({direction}) across {n_progs} program(s)")
        for prog, prog_data in all_improvements.items():
            if flag in prog_data:
                pct = prog_data[flag]
                print(f"         {prog:<15} {pct:+.3f}%")
        print()

    print("=" * 60)
    print(f"  BOTTOM {top_n} FLAGS (most harmful / least effective)")
    print("=" * 60)
    for i, (flag, scores) in enumerate(ranked[-top_n:][::-1], 1):
        mean_pct = statistics.mean(scores)
        n_progs  = len(scores)
        direction = "faster" if mean_pct > 0 else "slower"
        print(f"  #{i}  {flag}")
        print(f"       Mean improvement: {mean_pct:+.3f}% ({direction}) across {n_progs} program(s)")
        for prog, prog_data in all_improvements.items():
            if flag in prog_data:
                pct = prog_data[flag]
                print(f"         {prog:<15} {pct:+.3f}%")
        print()


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        TASKB_DIR = Path(sys.argv[1])
    if len(sys.argv) >= 3:
        TASKA_DIR = Path(sys.argv[2])
    if len(sys.argv) >= 4:
        OUTPUT_DIR = Path(sys.argv[3])

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"TaskB CSVs : {TASKB_DIR}")
    print(f"TaskA CSVs : {TASKA_DIR}")
    print(f"Output dir : {OUTPUT_DIR}\n")

    all_improvements: dict[str, dict[str, float]] = {}

    for prog in PROGRAMS:
        print(f"Plotting {prog}...")
        improvements = plot_program(prog)
        if improvements:
            all_improvements[prog] = improvements

    print_top_flags(all_improvements, top_n=3)