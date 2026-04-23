import subprocess
import csv
import numpy as np

EXEC_PATH = "./build"
OUTPUT_FILE = "out.csv"

REPS = 10

LCC3 = True

lcc3_sizes = sizes = sorted(set([
        *[2**i for i in range(21)],
        24, 28, 32, 36, 40, 48,
        192, 224, 256, 288, 320, 384,
        8192, 10240, 11264, 12288, 13312, 14336, 16384,
    ]))

def main():
    sizes = sorted(set([
        *[2**i for i in range(21)],
        24, 28, 36, 40, 48,       
        384, 448, 640, 768,      
        12288, 14336, 18432, 20480 
    ]))

    if LCC3: sizes = lcc3_sizes
    
    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["size_kb", "latency_ns"])

        for size in sizes:
            durations = []
            for i in range(REPS):
                samples = max(1, 10_000 // size)
                cmd = f"./cache_benchmark {size} {samples}"
                if LCC3: cmd = f"srun ./cache_benchmark {size} {samples}"
                result = subprocess.run(
                    cmd,
                    shell=True, cwd=EXEC_PATH, capture_output=True, text=True
                )
                if result.stdout:
                    line = result.stdout.strip()
                    print(line)
                    _, latency_ns, _ = line.split(", ")
                    durations.append(float(latency_ns))
            writer.writerow([size, np.median(durations)])

if __name__ == "__main__":
    main()