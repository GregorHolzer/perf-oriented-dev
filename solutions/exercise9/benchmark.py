from pathlib import Path
import subprocess
import re
import csv

containers = ["vector", "list", "list_shuffled"]

elements = [10, 1000 ,100000, 10000000]

element_size = [8, 512, 8000000]

instruction_mix = [0.0, 0.01, 0.1, 0.5]

BUILD_DIR = Path("./build")

CMAKE_DIR = Path("./")

RUNS = 3

LCC3 = False

def build():
  for size in element_size:
    build_dir = BUILD_DIR / f"size_{size}"
    build_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
      ["cmake", str(CMAKE_DIR.resolve()), "-G", "Ninja", f"-DENTRY_SIZE={size}"],
       cwd=build_dir,
       check=True,
      )
    subprocess.run("ninja", shell=True, cwd=build_dir)
    
def get_dir(element_size: int) -> Path:
  return BUILD_DIR / f"size_{element_size}"

def parse_output(output: str) -> dict:
    patterns = {
        "ins_del":      r"ins/del:\s*([\d]+)",
        "reads_writes": r"reads/writes:\s*([\d]+)",
        "elapsed":      r"elapsed:\s*([\d.]+)s",
    }
    results = {}
    for key, pat in patterns.items():
        match = re.search(pat, output)
        if match is None:
            return None 
        results[key] = int(match.group(1)) if key != "elapsed" else float(match.group(1))
    return results

def run_experiment(container: str, elements: int, size: int, fraction: float):
    cmd = f"./benchmark {container} {elements} {fraction}"
    if(LCC3):
        cmd = f"srun ./benchmark {container} {elements} {fraction}"
    result = subprocess.run(
        cmd,
        cwd=get_dir(size),
        capture_output=True,
        text=True,
        shell=True,
    )
    if result.returncode != 0:
       print(f"Program failed: {result.stdout} {result.stderr}")
       return
    output = parse_output(result.stdout)

    total_operations = output['ins_del'] + output['reads_writes']
    if total_operations > 0 and abs(output['ins_del'] / total_operations - fraction) > 1e-2:
        print(f"Warning: operation ratio does not match: expected: {fraction}, actual: {output['ins_del'] / total_operations}")

    output["elements"] = elements
    output["size"] = size
    output["fraction"] = fraction

    csv_path = CMAKE_DIR / f"{container}.csv"
    file_exists = csv_path.exists()

    with open(csv_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["elements", "size", "fraction", "ins_del", "reads_writes", "elapsed"])
        if not file_exists:
            writer.writeheader()
        writer.writerow(output)

def main():
    build()
    total = RUNS * len(element_size) * len(elements) * len(instruction_mix) * len(containers)
    current = 0
    for r in range(RUNS):
        for size in element_size:
            for element in elements:
                for fraction in instruction_mix:
                    for container in containers:
                        current += 1
                        print(f"[{current}/{total}] Run {r+1}/{RUNS} | container={container} elements={element} size={size} fraction={fraction}")
                        run_experiment(container, element, size, fraction)
        
if __name__ == "__main__":
  main()

