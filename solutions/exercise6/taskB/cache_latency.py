import subprocess
import csv

EXEC_PATH = "./build"
OUTPUT_FILE = "out.csv"

def main():
    sizes = sorted(set([
        # Normal powers of 2
        *[2**i for i in range(21)],
        # L1 boundary (~32 KB)
        24, 28, 32, 36, 40, 48,
        # L2 boundary (~256 KB)
        192, 224, 256, 288, 320, 384,
        # L3 boundary (~12 MB)
        8192, 10240, 11264, 12288, 13312, 14336, 16384,
    ]))
    
    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["size_kb", "latency_ns"])

        for size in sizes:
            samples = max(1, 10_000 // size)
            result = subprocess.run(
                f"srun ./cache_benchmark {size} {samples}",
                shell=True, cwd=EXEC_PATH, capture_output=True, text=True
            )
            if result.stdout:
                line = result.stdout.strip()
                print(line)
                size_kb, latency_ns, _ = line.split(", ")
                writer.writerow([size_kb, latency_ns])

if __name__ == "__main__":
    main()