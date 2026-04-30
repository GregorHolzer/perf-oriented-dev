import argparse
import csv
import re
import subprocess
import shutil
import sys
from pathlib import Path

REPS = 20

ARENA_LIB_PATH = "./libarena.so"

BENCH_MARK_PATH = "/scratch/cb761230/perf-oriented-dev/tools/build/malloctest"

OUTPUT = "./"

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

def write_result(alloc_name: str, row: dict):
    filepath = Path(OUTPUT) / f"{alloc_name}.csv"
    file_exists = filepath.exists()
    with open(filepath, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

def main():
    std_cmd = f"srun --exclusive /usr/bin/time -v {BENCH_MARK_PATH} 1 500 1000000 10 1000"
    custom_cmd = f"srun --exclusive --export=ALL,LD_PRELOAD={ARENA_LIB_PATH} /usr/bin/time -v {BENCH_MARK_PATH} 1 500 1000000 10 1000"

    for i in range(REPS):
        print(f"Run {i}/{REPS}:")
        print(f"Running Command: {std_cmd}")
        result = subprocess.run(std_cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
          print(f"Command failed: {result.stderr}, Aborting")
          exit(-1)
        metrics = parse_time_output(result.stderr)
        write_result("Default Allocator", metrics)
        result = subprocess.run(custom_cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
          print(f"Command failed: {result.stderr}, Aborting")
          exit(-1)
        metrics = parse_time_output(result.stderr)
        write_result("Custom Allocator", metrics)

if __name__ == "__main__":
    main()
    