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

MAX_CONCURRENT_EVENTS = 3
PROGRAM_NAME = "ssca2"
PROGRAM_RUN_CMD = ["/scratch/cb761230/perf-oriented-dev/larger_samples/ssca2/build/ssca2", "17"]
OUTPUT_CSV = f"counters_{PROGRAM_NAME}.csv"

def parse_perf_output(stderr_text):
    """Parse perf stat stderr output into {event: value} dict."""
    results = {}
    for line in stderr_text.splitlines():
        line = line.strip()
        not_counted = re.match(r'<not counted>\s+(\S+)', line)
        if not_counted:
            results[not_counted.group(1)] = None
            continue
        match = re.match(r'^([\d,]+)\s+(\S+)', line)
        if match:
            value = int(match.group(1).replace(',', ''))
            event = match.group(2)
            results[event] = value
    return results

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
