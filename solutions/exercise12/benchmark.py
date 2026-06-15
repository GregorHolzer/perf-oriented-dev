import subprocess
import re
from enum import Enum
import sys
import csv
import os

class BuildType(Enum):
    BaseLine = "baseline"
    Gprof = "gprof"

SRC_DIRS = {
    BuildType.BaseLine: "./lua-baseline",
    BuildType.Gprof: "./lua-profiled"
}

COMPILE_FLAGS = {
    BuildType.BaseLine: [],
    BuildType.Gprof: ["MYCFLAGS=-pg -fno-inline", "MYLDFLAGS=-pg"],
}

LUA_SRC = "./fib.lua"

REPS = 1

def parse_benchmark(text: str) -> dict:
    results = {}
    pattern = r"(\d+) x (\w+)\((\d+)\)\s+time:\s+([\d.]+) s\s+--\s+(\d+)"
    for m in re.finditer(pattern, text):
        iterations, func, n, time, result = m.groups()
        results[func] = {
            "iterations": int(iterations),
            "n": int(n),
            "time_s": float(time),
            "result": int(result),
        }
    return results

def build(type: BuildType):
    src_dir = SRC_DIRS[type]
    subprocess.run(["make", "clean"], cwd=src_dir)
    subprocess.run(["make", "linux"] + COMPILE_FLAGS[type], cwd=src_dir, check=True)

def benchmark(type: BuildType):
    out_dir = f"{type.value}_out"
    os.makedirs(out_dir, exist_ok=True)
    csv_path = os.path.join(out_dir, "results.csv")
    lua_bin = os.path.join(SRC_DIRS[type], "src", "lua")

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["run", "func", "iterations", "n", "time_s", "result"])
        writer.writeheader()
        for i in range(REPS):
            print(f"--- Running Benchmark {i + 1}/{REPS} --- ")
            output = subprocess.run([lua_bin, LUA_SRC], capture_output=True, text=True)
            results = parse_benchmark(output.stdout)
            for func, data in results.items():
                writer.writerow({"run": i, "func": func, **data})


def main():
    try:
        type = BuildType(sys.argv[1])
    except ValueError:
        print(f"Invalid build type. Choose from: {[e.value for e in BuildType]}")
        sys.exit(1)
    build(type)
    benchmark(type)



if __name__ == "__main__":
    main()