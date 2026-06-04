import subprocess
import csv
import re
import os
import posixpath

def parse_time_ms(stdout: str) -> float | None:
    m = re.search(r'Time:\s*([\d.]+)\s*ms', stdout)
    return float(m.group(1)) if m else None

def build(build_dir, cmake_flags):
    os.makedirs(build_dir, exist_ok=True)
    subprocess.run(["cmake", "../..", "-G", "Ninja"] + cmake_flags, cwd=build_dir, check=True)
    subprocess.run(["ninja"], cwd=build_dir, check=True)

def write_to_csv(filename, n, mode, time_ms):
    file_exists = os.path.exists(filename)
    with open(filename, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["n", "mode", "time_ms"])
        if not file_exists:
            writer.writeheader()
        writer.writerow({"n": n, "mode": mode, "time_ms": time_ms})

reps = 3
max_n_rec = 15
max_n = 22

print("Compiling...")
build("./build/std",     ["-DUSE_CACHE=OFF", "-DDYNAMIC=OFF"])
build("./build/cache",   ["-DUSE_CACHE=ON",  "-DDYNAMIC=OFF"])
build("./build/dynamic", ["-DUSE_CACHE=OFF", "-DDYNAMIC=ON"])

modes = [
    ("std",     "./build/std",     max_n_rec),
    ("cache",   "./build/cache",   max_n),
    ("dynamic", "./build/dynamic", max_n),
]

for rep in range(reps):
    for mode, build_dir, limit in modes:
        for n in range(1, limit + 1):
            exe = posixpath.join(build_dir, "delannoy")
            try:
                proc = subprocess.run(
                    ["srun", exe, str(n)],
                    capture_output=True, text=True
                )
                time_ms = parse_time_ms(proc.stdout)
                if time_ms is not None:
                    write_to_csv("results.csv", n, mode, time_ms)
                    print(f"[{mode}] n={n} rep={rep+1} -> {time_ms:.3f} ms")
                else:
                    print(f"[{mode}] n={n} rep={rep+1} -> parse failed: {proc.stdout!r}")
            except subprocess.TimeoutExpired:
                print(f"Timeout: n={n}, mode={mode}")