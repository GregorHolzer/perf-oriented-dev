import argparse
import csv
import re
import subprocess
import shutil
import sys
from pathlib import Path

ID = "cb761230"

MIMALLOC = "/scratch/cb761230/perf-oriented-dev/third_party/mimalloc/build/libmimalloc.so.2.3"

RPMALLOC  = "/scratch/cb761230/perf-oriented-dev/third_party/rpmalloc/librpmalloc.so"

SOURCE_CODE = "/scratch/cb761230/perf-oriented-dev/solutions/exercise7/taskA/allscale_api"

WORK_DIR = f"/tmp/{ID}"

BUILD_DIR = f"{WORK_DIR}/build"

OUTPUT = "/scratch/cb761230/perf-oriented-dev/solutions/exercise7/taskA/"

REPS = 20

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

def setup():
    shutil.copytree(SOURCE_CODE, WORK_DIR, dirs_exist_ok=True)
    Path(BUILD_DIR).mkdir(exist_ok=True)
    result = subprocess.run(
        ["cmake", "-DCMAKE_BUILD_TYPE=Release", "-G", "Ninja", "../code"],
        cwd=BUILD_DIR,
    )
    if result.returncode != 0:
        print(result.stderr, result.stdout)
        exit(1)

def write_result(alloc_name: str, row: dict):
    filepath = Path(OUTPUT) / f"{alloc_name}.csv"
    file_exists = filepath.exists()
    with open(filepath, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

def run_once(alloc_name: str, rep: int, alloc_path: str, metrics: dict[str, list]):
    print(f"Running: {alloc_name}, Rep: {rep}, Cleaning...")
    result = subprocess.run(
        f"ninja clean",
        cwd=BUILD_DIR,
        shell=True
    )
    if result.returncode != 0:
        print(f"Error cleaning: {alloc_name}, {rep}, {alloc_path}")
        exit(1)
    if alloc_path:
        cmd = f"LD_PRELOAD={alloc_path} /usr/bin/time -v ninja"
    else:
        cmd = "/usr/bin/time -v ninja"
    print(f"Running: {alloc_name}, Rep: {rep}, Building...")
    result = subprocess.run(
        cmd,
        cwd=BUILD_DIR,
        shell=True,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"Error running: {cmd}, rep: {rep}")
        exit(1)
    output = parse_time_output(result.stderr)
    output["rep"] = rep
    metrics[alloc_name].append(output)
    write_result(alloc_name, output) 

def run_experiment():
    setup()
    metrics = {name: [] for name in ["malloc", "mimalloc", "rpmalloc"]}
    allocators = {
        "malloc": None,
        "mimalloc": MIMALLOC,
        "rpmalloc": RPMALLOC
    } 
    for i in range(REPS):
        for allocator in allocators.keys():
            run_once(allocator, i, allocators[allocator], metrics)

def main():
    run_experiment()

if __name__ == "__main__":
    main()

  
