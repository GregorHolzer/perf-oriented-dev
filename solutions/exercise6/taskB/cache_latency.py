import subprocess
import csv

EXEC_PATH = "./build"
OUTPUT_FILE = "cache_latency.csv"

def main():
    sizes = [2**i for i in range(21)]
    
    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["size_kb", "latency_ns"])

        for size in sizes:
            samples = max(1, 10_000 // size)
            result = subprocess.run(
                f"./cache_benchmark {size} {samples}",
                shell=True, cwd=EXEC_PATH, capture_output=True, text=True
            )
            if result.stdout:
                line = result.stdout.strip()
                print(line)
                size_kb, latency_ns, _ = line.split(", ")
                writer.writerow([size_kb, latency_ns])

if __name__ == "__main__":
    main()