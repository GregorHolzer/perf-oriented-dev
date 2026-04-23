import subprocess
import csv
import numpy as np

EXEC_PATH = "./build"
OUTPUT_FILE = "out.csv"

REPS = 10

LCC3 = False

lcc3_sizes = sizes = sorted(set([
        *[2**i for i in range(9, 29)],
        24576, 28672, 31130, 32768, 34406, 36864, 40960,
        196608, 229376, 249037, 262144, 275251, 294912, 327680,
        9437184, 10485760, 11534336, 12288000, 12582912, 12877824, 13631488, 15099494
    ]))

def main():
    sizes = sorted(set([
        *[2**i for i in range(9,29)],
        24576, 28672, 31130, 32768, 34406, 36864, 40960,
        393216, 458752, 498073, 524288, 550502, 589824, 655360,
        14680064, 15728640, 16252928, 16777216, 17301504, 17825792, 18874368
    ]))

    if LCC3: sizes = lcc3_sizes
    
    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["size_kb", "latency_ns"])

        for size in sizes:
            durations = []
            for i in range(REPS):
                samples = 5
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