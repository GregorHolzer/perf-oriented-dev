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
        metrics["wall_clock_s"] = float(m.group(1)) * 60 + float(m.group(2))
    m = re.search(r'Elapsed \(wall clock\) time.*?(\d+):(\d+\.\d+)', stderr)
    if m:
        metrics["wall_clock_s"] = float(m.group(1)) * 60 + float(m.group(2))

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

def compute_stats(values: list) -> tuple:
    n = len(values)
    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / n
    return mean, variance


def run_experiment(config: dict):
    lcc3 = config.get("lcc3", True)

    programs = config.get("programs", {})

    repetitions = config.get("repetitions", 1)

    meas_cfg = config.get("measurement_program", {})

    meas_path = meas_cfg.get("path", None)

    meas_args = meas_cfg.get("args", [])

    if meas_path is None:
        print("Running without measurement...")
    else:
        arg_str = "".join(meas_args)
        print(f"Running with {meas_path} {arg_str} <program>")

    output_dir = Path(config.get("output", {}).get("path", "./benchmark")).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    for prog_name, prog_cfg in programs.items():
        print(f"\n{'='*100}\nProgram: {prog_name}")

        prog_path   = prog_cfg.get("path")
        raw_args    = prog_cfg.get("args", [[]])

        arg_list = [[str(a) for a in entry] for entry in raw_args]

        all_rows = []

        for args in arg_list:
            args_str = " ".join(args)
            base_cmd = [prog_path] + args
            if lcc3:
                base_cmd = ["srun"] + [prog_path] + args
            
            cmd = ([meas_path] + meas_args + base_cmd) if meas_path else base_cmd
            print(f"  Command : {' '.join(cmd)}  --  Reps: {repetitions}")

            for rep in range(1, repetitions + 1):
                try:
                    result = subprocess.run(cmd, stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE, text=True)
                except FileNotFoundError as exc:
                    sys.exit(f"ERROR: {exc}")
                if result.returncode != 0:
                    print(f"WARNING: rep {rep} failed (exit {result.returncode}), abort")
                    exit(1)
                if meas_path:
                    metrics = parse_time_output(result.stderr)
                    row = {"args": args_str, "rep": rep, **metrics} 
                    all_rows.append(row)

        metric_keys = [k for k in all_rows[0] if k not in ("args", "rep")]
        fieldnames  = ["args", "rep"] + metric_keys

        csv_path = output_dir / f"{prog_name}.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_rows)

        print(f"\n  Saved to {csv_path}")

        print(f"\n  {'args':<18}", end="")
        for key in metric_keys:
            print(f"  {key+'_mean':>15}  {key+'_var':>15}", end="")
        print()

        for args in arg_list:
            args_str = " ".join(args)
            arg_rows = [r for r in all_rows if r["args"] == args_str]
            print(f"  {args_str:<18}", end="")
            for key in metric_keys:
                vals = [r[key] for r in arg_rows]
                mean, var = compute_stats(vals)
                print(f"  {mean:>15.3f}  {var:>15.3f}", end="")
            print()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="Path to YAML config (default: config.yaml)")
    args = parser.parse_args()
    config_path = Path(args.config)
    if not config_path.exists():
        sys.exit(f"Error: config file '{config_path}' not found.")

    with open(config_path) as f:
        config = yaml.safe_load(f)

    run_experiment(config)


if __name__ == "__main__":
    main()
