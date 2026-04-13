import subprocess
import csv
import re
import sys

events = [
    "L1-dcache-load-misses",
    "L1-dcache-loads",
    "L1-dcache-prefetch-misses",
    "L1-dcache-prefetches",
    "L1-dcache-store-misses",
    "L1-dcache-stores",
    "L1-icache-load-misses",
    "L1-icache-loads",
    "LLC-load-misses",
    "LLC-loads",
    "LLC-prefetch-misses",
    "LLC-prefetches",
    "LLC-store-misses",
    "LLC-stores",
    "branch-load-misses",
    "branch-loads",
    "dTLB-load-misses",
    "dTLB-loads",
    "dTLB-store-misses",
    "dTLB-stores",
    "iTLB-load-misses",
    "iTLB-loads",
    "node-load-misses",
    "node-loads",
    "node-prefetch-misses",
    "node-prefetches",
    "node-store-misses",
    "node-stores",
]

MAX_CONCURRENT_EVENTS = 4
PROGRAM_NAME = "npb_bt"
PROGRAM_RUN_CMD = ["/scratch/cb761230/perf-oriented-dev/larger_samples/npb_bt/build/npb_bt_w"]
OUTPUT_CSV = f"counters_{PROGRAM_NAME}.csv"

def parse_perf_output(stderr_text):
    results = {}
    for line in stderr_text.splitlines():
        line = line.strip()
        not_counted = re.match(r'<not counted>\s+(\S+)', line)
        if not_counted:
            results[not_counted.group(1).split(':')[0]] = None
            continue
        match = re.match(r'^([\d,]+)\s+(\S+)', line)
        if match:
            value = int(match.group(1).replace(',', ''))
            event = match.group(2).split(':')[0]  # strip :u or :k suffix
            results[event] = value
    return results

def compute_ratios(all_results):
    def ratio(a, b):
        va = all_results.get(a)
        vb = all_results.get(b)
        if va is None or vb is None or vb == 0:
            return None
        return va / vb

    return {
        "L1-dcache-load-miss-rate":     ratio("L1-dcache-load-misses",     "L1-dcache-loads"),
        "L1-dcache-store-miss-rate":    ratio("L1-dcache-store-misses",    "L1-dcache-stores"),
        "L1-dcache-prefetch-miss-rate": ratio("L1-dcache-prefetch-misses", "L1-dcache-prefetches"),
        "L1-icache-load-miss-rate":     ratio("L1-icache-load-misses",     "L1-icache-loads"),
        "LLC-load-miss-rate":           ratio("LLC-load-misses",            "LLC-loads"),
        "LLC-store-miss-rate":          ratio("LLC-store-misses",           "LLC-stores"),
        "LLC-prefetch-miss-rate":       ratio("LLC-prefetch-misses",        "LLC-prefetches"),
        "dTLB-load-miss-rate":          ratio("dTLB-load-misses",           "dTLB-loads"),
        "dTLB-store-miss-rate":         ratio("dTLB-store-misses",          "dTLB-stores"),
        "iTLB-load-miss-rate":          ratio("iTLB-load-misses",           "iTLB-loads"),
        "node-load-miss-rate":          ratio("node-load-misses",           "node-loads"),
        "node-store-miss-rate":         ratio("node-store-misses",          "node-stores"),
        "node-prefetch-miss-rate":      ratio("node-prefetch-misses",       "node-prefetches"),
        "branch-miss-rate":             ratio("branch-load-misses",         "branch-loads"),
    }

all_results = {}

list_idx = 0
while list_idx < len(events):
    sel_events = events[list_idx:list_idx + MAX_CONCURRENT_EVENTS]
    e_arg = ",".join(sel_events)
    cmd = ["srun", "perf", "stat", "-e", e_arg] + PROGRAM_RUN_CMD

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if result.returncode != 0:
        print(f"Error: program exited with code {result.returncode}")
        print(result.stdout)
        print(result.stderr)
        sys.exit(-1)

    parsed = parse_perf_output(result.stderr)
    all_results.update(parsed)

    list_idx += MAX_CONCURRENT_EVENTS

ratios = compute_ratios(all_results)

ratios_csv = f"ratios_{PROGRAM_NAME}.csv"

with open(ratios_csv, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["metric", "value"])
    for metric, value in ratios.items():
        writer.writerow([metric, f"{value:.6f}" if value is not None else "n/a"])

print(f"\n{'Metric':<35} {'Rate':>10}")
print("-" * 47)
for metric, value in ratios.items():
    val_str = f"{value*100:.2f}%" if value is not None else "n/a"
    print(f"{metric:<35} {val_str:>10}")

with open(OUTPUT_CSV, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["event", "value"])
    for event, value in all_results.items():
        writer.writerow([event, value if value is not None else "not_counted"])

print(f"\nResults written to {OUTPUT_CSV}")

print(f"\n{'Event':<35} {'Value':>20}")
print("-" * 57)
for event, value in all_results.items():
    val_str = f"{value:,}" if value is not None else "not counted"
    print(f"{event:<35} {val_str:>20}")