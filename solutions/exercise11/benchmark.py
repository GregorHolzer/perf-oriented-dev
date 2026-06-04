import subprocess
import csv
import re
import os
import posixpath

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

def build(build_dir, use_cache):
    os.makedirs(build_dir, exist_ok=True)
    cache_flag = "-DUSE_CACHE=ON" if use_cache else "-DUSE_CACHE=OFF"
    subprocess.run(["cmake", "../..", "-G", "Ninja", cache_flag], cwd=build_dir, check=True)
    subprocess.run(["ninja"], cwd=build_dir, check=True)

def write_to_csv(filename, n, used_cache, metrics):
    file_exists = os.path.exists(filename)
    with open(filename, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["n", "cache", "wall_clock_s", "max_rss_kb"])
        if not file_exists:
            writer.writeheader()
        writer.writerow({"n": n, "cache": used_cache, "wall_clock_s": metrics["wall_clock_s"], "max_rss_kb": metrics["max_rss_kb"]})

max_n = 15

used_imputs = []

reps = 3

total = reps * max_n

print("Compiling...")

cache_dir = "./build/cache"

no_cache_dir = "./build/no_cache"

build(cache_dir, True)

build(no_cache_dir, False)

for rep in range(reps):
    for n in range(1, max_n + 1):
        print(f"--- Running {rep * max_n + n}/{total} ---")
        for used_cache, build_dir in [(False, no_cache_dir), (True, cache_dir)]:
            exe = posixpath.join(build_dir, "delannoy")
            try:
                proc = subprocess.run(
                    ["srun", "/usr/bin/time", "-v", exe, str(n)],
                    capture_output=True, text=True, timeout=60
                )
                metrics = parse_time_output(proc.stderr)
                write_to_csv("results.csv", n, used_cache, metrics)
            except subprocess.TimeoutExpired:
                print(f"Timeout: n={n}, cache={used_cache}")

