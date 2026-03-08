#!/usr/bin/env python3
import argparse
import csv
from collections import defaultdict
from pathlib import Path


def compute_stats(values: list) -> tuple:
    n = len(values)
    if n == 0:
        return 0.0, 0.0
    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / (n - 1) if n > 1 else 0.0
    return mean, variance


def csv_to_md(csv_path: str):
    groups = defaultdict(list)
    metric_keys = []

    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            args = row["args"] if row.get("args") else "(no args)"
            metric_keys = ["wall_clock_s", "user_cpu_s", "sys_cpu_s", "max_rss_kb"]
            entry = {}
            for k in metric_keys:
                entry[k] = float(row[k])
            entry["cpu_time_s"] = entry["user_cpu_s"] + entry["sys_cpu_s"]
            groups[args].append(entry)
            
    display_keys = ["wall_clock_s", "cpu_time_s", "max_rss_kb"]

    col_headers = []
    for k in display_keys:
        col_headers.append(f"{k}_mean")
        col_headers.append(f"{k}_var")

    print("| args | " + " | ".join(col_headers) + " |")
    print("| --- | " + " | ".join("---" for _ in col_headers) + " |")

    for args, rows in groups.items():
        cells = [args]
        for k in display_keys:
            vals = [r[k] for r in rows if k in r]
            mean, var = compute_stats(vals)
            cells.append(f"{mean:.6f}")
            cells.append(f"{var:.6f}")
        print("| " + " | ".join(cells) + " |")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", help="Path to CSV file")
    args = parser.parse_args()

    path = Path(args.csv)
    if not path.exists():
        raise SystemExit(f"Error: file '{path}' not found.")

    csv_to_md(path)


if __name__ == "__main__":
    main()
