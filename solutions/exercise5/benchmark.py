import argparse
import csv
import re
import subprocess
import sys
from pathlib import Path

import yaml


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


def compute_stats(values: list):
    n = len(values)
    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / n
    cv = (variance ** 0.5) / abs(mean) if mean != 0 else 0.0
    return mean, variance, cv


def defines_slug(definitions: dict) -> str:
    """Create a filesystem-safe name from a defines dict."""
    return "_".join(f"{k}={v}" for k, v in definitions.items()) or "default"


def get_build_path(program_name, prog_cfg, definitions: dict) -> Path:
    """Return the per-define-combo build subdirectory."""
    base = Path(prog_cfg.get("build_path")).expanduser().resolve()
    return base / program_name / defines_slug(definitions)


def build_program(prog_name, prog_cfg, definitions: dict):
    base_build_path = Path(prog_cfg.get("build_path")).expanduser().resolve()
    build_path = get_build_path(prog_name, prog_cfg, definitions)
    build_path.mkdir(parents=True, exist_ok=True)

    source_path = base_build_path.parent

    defines = " ".join(f"-D{k}={v}" for k, v in definitions.items())
    build_cmd = f"cmake -G Ninja {defines} {source_path}"
    print(f"Building {prog_name} [{defines_slug(definitions)}] with: {build_cmd}")
    try:
        subprocess.run(build_cmd, cwd=build_path, shell=True, check=True)
        subprocess.run(f"ninja {prog_name}", cwd=build_path, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to build {prog_name}: {e}")
        exit(-1)


def get_unconverged_combos(rows: list, cv_threshold: float = 0.05) -> set:
    """Returns set of (defines, args) combos that haven't converged yet."""
    if not rows:
        return None  # no data yet, run everything
    metric_keys = [k for k in rows[0] if k not in ("defines", "args", "rep")]
    unconverged = set()
    combos = {(r["defines"], r["args"]) for r in rows}
    for defines_str, args_str in combos:
        combo_rows = [r for r in rows if r["defines"] == defines_str and r["args"] == args_str]
        if len(combo_rows) < 3:
            unconverged.add((defines_str, args_str))
            continue
        
        vals = [r["wall_clock_s"] for r in combo_rows]
        _, _, cv = compute_stats(vals)
        if cv >= cv_threshold:
            unconverged.add((defines_str, args_str))
    return unconverged


def check_converged(results: dict[str, list], cv_threshold: float = 0.05) -> dict[str, bool]:
    """Returns per-program convergence status, checked per (defines, args) combo."""
    converged = {}
    for prog_name, rows in results.items():
        if not rows:
            converged[prog_name] = False
            continue
        unconverged = get_unconverged_combos(rows, cv_threshold)
        converged[prog_name] = len(unconverged) == 0
    return converged


def run_once(prog_name, prog_cfg, meas_path, meas_args, lcc3, massif, rep, results, skip_combos=None):
    """Run all define/arg combos for one program once, appending rows to results."""
    raw_defines = prog_cfg.get("defines", [{}])
    raw_args = prog_cfg.get("args", [[]])
    prefix = prog_cfg.get("prefix", [])
    define_list = [entry if isinstance(entry, dict) else {} for entry in raw_defines]
    arg_list = [[str(a) for a in entry] for entry in raw_args]

    for definitions in define_list:
        build_path = get_build_path(prog_name, prog_cfg, definitions)
        prog_path = build_path / prog_name
        defines_str = defines_slug(definitions)

        for args in arg_list:
            args_str = " ".join(args)

            if skip_combos is not None and (defines_str, args_str) not in skip_combos:
                continue  

            base_cmd = prefix + [str(prog_path)] + args
            cmd = []
            if (massif):
                cmd += ([meas_path] + meas_args + ["/usr/bin/valgrind", "--tool=massif", "--time-unit=ms"] + base_cmd) if meas_path else base_cmd
            else:
                cmd += ([meas_path] + meas_args + base_cmd) if meas_path else base_cmd
            if lcc3:
                cmd = ["srun"] + cmd
            

            print(f"  [{prog_name}|{defines_str}] rep={rep} cmd: {' '.join(cmd)}")
            try:
                result = subprocess.run(cmd, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, universal_newlines=True)
            except FileNotFoundError as exc:
                sys.exit(f"ERROR: {exc}")

            if result.returncode != 0:
                print(f"WARNING: {prog_name} rep {rep} failed (exit {result.returncode}), aborting")
                exit(1)

            if meas_path:
                metrics = parse_time_output(result.stderr)
                row = {"defines": defines_str, "args": args_str, "rep": rep, **metrics}
                results.setdefault(prog_name, []).append(row)


def write_results(results: dict[str, list], output_dir: Path):
    for prog_name, rows in results.items():
        if not rows:
            continue
        metric_keys = [k for k in rows[0] if k not in ("defines", "args", "rep")]
        fieldnames = ["defines", "args", "rep"] + metric_keys
        csv_path = output_dir / f"{prog_name}.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"Saved {csv_path}")

        print(f"\n{'defines':<20} {'args':<18}", end="")
        for key in metric_keys:
            print(f"  {key+'_mean':>15}  {key+'_cv':>10}", end="")
        print()

        combos = {(r["defines"], r["args"]) for r in rows}
        for defines_str, args_str in sorted(combos):
            combo_rows = [r for r in rows if r["defines"] == defines_str and r["args"] == args_str]
            print(f"  {defines_str:<20} {args_str:<18}", end="")
            for key in metric_keys:
                vals = [r[key] for r in combo_rows]
                mean, _, cv = compute_stats(vals)
                print(f"  {mean:>15.3f}  {cv:>10.4f}", end="")
            print()


def run_experiment(config: dict):
    lcc3 = config.get("lcc3", True)
    programs = config.get("programs", {})
    repetitions = config.get("repetitions", 5)
    converge = config.get("converge", False)
    meas_cfg = config.get("measurement_program", {})
    meas_path = meas_cfg.get("path", None)
    massif = config.get("massif", False)
    meas_args = meas_cfg.get("args", [])

    CV_THRESHOLD = 0.05
    MAX_REPS = 20

    output_dir = Path(config.get("output", {}).get("path", "./benchmark")).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    for prog_name, prog_cfg in programs.items():
        raw_defines = prog_cfg.get("defines", [{}])
        define_list = [entry if isinstance(entry, dict) else {} for entry in raw_defines]
        for definitions in define_list:
            build_program(prog_name, prog_cfg, definitions)

    results: dict[str, list] = {}

    for rep in range(repetitions):
        print(f"\n--- Rep {rep + 1}/{repetitions} ---")
        for prog_name, prog_cfg in programs.items():
            run_once(prog_name, prog_cfg, meas_path, meas_args, lcc3, massif, rep, results)

    if converge:
        print("\n--- Convergence phase ---")
        rep = repetitions
        while rep < MAX_REPS:
            converged = check_converged(results, CV_THRESHOLD)
            if all(converged.values()):
                print(f"All programs converged after {rep} reps total")
                break
            for prog_name, prog_cfg in programs.items():
                if converged.get(prog_name, False):
                    continue
                unconverged = get_unconverged_combos(results.get(prog_name, []), CV_THRESHOLD)
                run_once(prog_name, prog_cfg, meas_path, meas_args, lcc3, massif, rep, results, skip_combos=unconverged)
            rep += 1
        else:
            print(f"Hit max reps ({MAX_REPS}) without full convergence")
            for prog_name, converged_status in check_converged(results, CV_THRESHOLD).items():
                print(f"  {prog_name}: {'converged' if converged_status else 'NOT converged'}")

    write_results(results, output_dir)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="Path to YAML config")
    args = parser.parse_args()
    config_path = Path(args.config)
    if not config_path.exists():
        sys.exit(f"Error: config file '{config_path}' not found.")
    with open(config_path) as f:
        config = yaml.safe_load(f)
    run_experiment(config)


if __name__ == "__main__":
    main()
