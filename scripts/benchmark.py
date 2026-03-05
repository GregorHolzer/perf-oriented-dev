#!/usr/bin/env python3
import argparse
import csv
import re
import subprocess
import sys
import time
from pathlib import Path

import yaml


def parse_time_output(stderr: str) -> dict:
    metrics = {}

    m = re.search(r'(\d+):(\d+\.\d+)elapsed', stderr)
    if m:
        metrics["elapsed_s"] = float(m.group(1)) * 60 + float(m.group(2))
    m = re.search(r'Elapsed \(wall clock\) time.*?(\d+):(\d+\.\d+)', stderr)
    if m:
        metrics["elapsed_s"] = float(m.group(1)) * 60 + float(m.group(2))

    m = re.search(r'([\d.]+)user', stderr)
    if m:
        metrics["user_cpu_s"] = float(m.group(1))
    m = re.search(r'User time.*?:\s*([\d.]+)', stderr)
    if m:
        metrics["user_cpu_s"] = float(m.group(1))

    m = re.search(r'([\d.]+)system', stderr)
    if m:
        metrics["sys_cpu_s"] = float(m.group(1))
    m = re.search(r'System time.*?:\s*([\d.]+)', stderr)
    if m:
        metrics["sys_cpu_s"] = float(m.group(1))

    m = re.search(r'Maximum resident set size \(kbytes\):\s*(\d+)', stderr)
    if m:
        metrics["max_rss_kb"] = int(m.group(1))

    return metrics


def wall_clock_fallback(start: float, end: float) -> dict:
    return {"wall_time_s": round(end - start, 6)}


def compute_stats(values: list) -> tuple:
    n = len(values)
    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / n
    return mean, variance


def run_experiment(config: dict):
    programs = config.get("programs", {})
    meas_cfg = config.get("measurement_program", {})
    output_dir = Path(config.get("output", {}).get("path", "./benchmark"))
    output_dir.mkdir(parents=True, exist_ok=True)

    meas_path = meas_cfg.get("path", "") or meas_cfg.get("name", "")
    meas_args = [str(a) for a in meas_cfg.get("args", [])]

    for prog_name, prog_cfg in programs.items():
        print(f"\n{'='*60}\nProgram: {prog_name}")

        prog_path   = prog_cfg.get("path") or prog_name
        raw_args    = prog_cfg.get("args", [])
        repetitions = int(prog_cfg.get("repetitions", 1))

        # Normalise: each entry in arg_list is a list of strings for one invocation.
        # Supports both:
        #   args: [[13, 14], [15, 16]]   <- list of arg lists
        #   args: [13]                   <- single flat list (treated as one invocation)
        if raw_args and not isinstance(raw_args[0], list):
            arg_list = [[str(a) for a in raw_args]]
        else:
            arg_list = [[str(a) for a in entry] for entry in raw_args]

        all_rows = []

        for args in arg_list:
            args_str = " ".join(args)
            print(f"\n  Args: {args_str}")
            base_cmd = [prog_path] + args
            cmd = ([meas_path] + meas_args + base_cmd) if meas_path else base_cmd
            print(f"  Command : {' '.join(cmd)}  |  Reps: {repetitions}")

            for rep in range(1, repetitions + 1):
                print(f"    Rep {rep}/{repetitions} ... ", end="", flush=True)
                t_start = time.perf_counter()
                try:
                    result = subprocess.run(cmd, stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE, text=True)
                except FileNotFoundError as exc:
                    sys.exit(f"ERROR: {exc}")
                t_end = time.perf_counter()

                if meas_path:
                    metrics = parse_time_output(result.stderr)
                    if not metrics:
                        metrics = wall_clock_fallback(t_start, t_end)
                else:
                    metrics = wall_clock_fallback(t_start, t_end)

                row = {"args": args_str, "rep": rep, **metrics}
                all_rows.append(row)
                print(metrics)

        metric_keys = [k for k in all_rows[0] if k not in ("args", "rep")]
        fieldnames  = ["args", "rep"] + metric_keys

        csv_path = output_dir / f"{prog_name}.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_rows)

        print(f"\n  Saved → {csv_path}")

        print(f"\n  {'args':<20} {'metric':<20} {'mean':>14}  {'variance':>14}")
        for args in arg_list:
            args_str = " ".join(args)
            arg_rows = [r for r in all_rows if r["args"] == args_str]
            for key in metric_keys:
                vals = [r[key] for r in arg_rows]
                mean, var = compute_stats(vals)
                print(f"  {args_str:<20} {key:<20} {mean:>14.6f}  {var:>14.6f}")


def main():
    parser = argparse.ArgumentParser(description="Run benchmarks from a YAML config.")
    parser.add_argument("config", nargs="?", default="config.yaml",
                        help="Path to YAML config (default: config.yaml)")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        sys.exit(f"Error: config file '{config_path}' not found.")

    with open(config_path) as f:
        config = yaml.safe_load(f)

    run_experiment(config)


if __name__ == "__main__":
    main()
