import argparse
import csv
import hashlib
import re
import subprocess
import sys
from pathlib import Path
from receive_option import get_diffs

import yaml

def parse_time_output(stderr: str) -> dict:
    metrics = {}
    for pattern, key, cast in [
        (r'(\d+):(\d+\.\d+)elapsed',                   "wall_clock_s", None),
        (r'Elapsed \(wall clock\) time.*?(\d+):(\d+\.\d+)', "wall_clock_s", None),
    ]:
        m = re.search(pattern, stderr)
        if m:
            metrics[key] = float(m.group(1)) * 60 + float(m.group(2))

    for pattern, key in [
        (r'([\d.]+)user',                   "user_cpu_s"),
        (r'User time.*?:\s*([\d.]+)',        "user_cpu_s"),
        (r'([\d.]+)system',                  "sys_cpu_s"),
        (r'System time.*?:\s*([\d.]+)',      "sys_cpu_s"),
    ]:
        m = re.search(pattern, stderr)
        if m:
            metrics[key] = float(m.group(1))

    m = re.search(r'Maximum resident set size \(kbytes\):\s*(\d+)', stderr)
    if m:
        metrics["max_rss_kb"] = int(m.group(1))
    return metrics


def compute_stats(values: list) -> tuple:
    n = len(values)
    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / n
    cv = (variance ** 0.5) / abs(mean) if mean != 0 else 0.0
    return mean, variance, cv

def defines_slug(definitions: dict) -> str:
    """Filesystem-safe, Ninja-safe identifier for a definitions dict."""
    def sanitize(s: str) -> str:
        return (str(s).lstrip("-")
                .replace("-", "_").replace("=", "_")
                .replace("[", "").replace("]", "").replace("|", "_"))

    slug = "_".join(f"{sanitize(k)}__{sanitize(v)}" for k, v in definitions.items()) or "default"
    if len(slug) > 80:
        slug = slug[:40] + "__" + hashlib.md5(slug.encode()).hexdigest()[:8]
    return slug


def get_build_path(prog_name: str, prog_cfg: dict, definitions: dict) -> Path:
    base = Path(prog_cfg["build_path"]).expanduser().resolve()
    return base / prog_name / defines_slug(definitions)


def format_gcc_flag(flag: str, val) -> str:
    """Convert a (flag, value) diff entry into a GCC flag string."""
    if val in (None, "[enabled]"):
        return flag                 
    elif val == "[disabled]":
        return ""
    else:
        return f"{flag}{val}"        


def build_program(prog_name: str, prog_cfg: dict, definitions: dict):
    build_path = get_build_path(prog_name, prog_cfg, definitions)
    build_path.mkdir(parents=True, exist_ok=True)
    source_path = Path(prog_cfg["build_path"]).expanduser().resolve().parent

    cmake_vars = {k: v for k, v in definitions.items() if not k.startswith("-")}
    gcc_flags  = {k: v for k, v in definitions.items() if k.startswith("-")}

    base_cflags = cmake_vars.pop("CMAKE_C_FLAGS", "")
    extra_flags = " ".join(filter(None, (format_gcc_flag(f, v) for f, v in gcc_flags.items())))
    all_cflags  = " ".join(filter(None, [base_cflags, extra_flags]))

    cmake_defines = " ".join(f"-D{k}={v}" for k, v in cmake_vars.items())
    if all_cflags:
        cmake_defines += f" -DCMAKE_C_FLAGS='{all_cflags}'"

    build_cmd = f"cmake -G Ninja {cmake_defines} {source_path}"
    print(f"  [build] {prog_name} [{defines_slug(definitions)}]: {build_cmd}")
    try:
        subprocess.run(build_cmd, cwd=build_path, shell=True, check=True)
        subprocess.run(f"ninja {prog_name}", cwd=build_path, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        sys.exit(f"Build failed for {prog_name}: {e}")

def run_once(prog_name: str, prog_cfg: dict, meas_path, meas_args: list,
             lcc3: bool, massif: bool, rep: int, results: dict,
             definitions_override: dict = None, skip_combos: set = None):
    """Run all (definitions, args) combos once, appending rows to results."""
    raw_args = prog_cfg.get("args", [[]])
    prefix   = prog_cfg.get("prefix", [])

    if definitions_override is not None:
        define_list = [definitions_override]
    else:
        define_list = [e if isinstance(e, dict) else {} for e in prog_cfg.get("defines", [{}])]

    arg_list = [[str(a) for a in entry] for entry in raw_args]

    for definitions in define_list:
        build_path  = get_build_path(prog_name, prog_cfg, definitions)
        prog_path   = build_path / prog_name
        defines_str = defines_slug(definitions)

        for args in arg_list:
            args_str = " ".join(args)

            if skip_combos is not None and (defines_str, args_str) not in skip_combos:
                continue

            base_cmd = prefix + [str(prog_path)] + args
            if massif:
                cmd = ([meas_path] + meas_args +
                       ["/usr/bin/valgrind", "--tool=massif", "--time-unit=ms"] +
                       base_cmd) if meas_path else base_cmd
            else:
                cmd = ([meas_path] + meas_args + base_cmd) if meas_path else base_cmd

            if lcc3:
                cmd = ["srun"] + cmd

            print(f"  [{prog_name}|{defines_str}] rep={rep} cmd: {' '.join(cmd)}")
            try:
                proc = subprocess.run(cmd, stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE, universal_newlines=True)
            except FileNotFoundError as e:
                sys.exit(f"ERROR: {e}")

            if proc.returncode != 0:
                sys.exit(f"ERROR: {prog_name} rep {rep} failed (exit {proc.returncode})")

            if meas_path:
                metrics = parse_time_output(proc.stderr)
                results.setdefault(prog_name, []).append(
                    {"defines": defines_str, "args": args_str, "rep": rep, **metrics}
                )


def get_unconverged_combos(rows: list, cv_threshold: float = 0.05) -> set | None:
    if not rows:
        return None
    combos = {(r["defines"], r["args"]) for r in rows}
    unconverged = set()
    for defines_str, args_str in combos:
        combo_rows = [r for r in rows if r["defines"] == defines_str and r["args"] == args_str]
        if len(combo_rows) < 3:
            unconverged.add((defines_str, args_str))
            continue
        _, _, cv = compute_stats([r["wall_clock_s"] for r in combo_rows])
        if cv >= cv_threshold:
            unconverged.add((defines_str, args_str))
    return unconverged


def check_converged(results: dict, cv_threshold: float = 0.05) -> dict:
    return {
        prog: len(get_unconverged_combos(rows, cv_threshold) or []) == 0
        for prog, rows in results.items()
    }


def write_results(results: dict, output_dir: Path):
    for prog_name, rows in results.items():
        if not rows:
            continue
        metric_keys = [k for k in rows[0] if k not in ("defines", "args", "rep")]
        fieldnames  = ["defines", "args", "rep"] + metric_keys
        csv_path    = output_dir / f"{prog_name}.csv"

        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"\nSaved {csv_path}")

        print(f"{'defines':<40} {'args':<18}", end="")
        for key in metric_keys:
            print(f"  {key+'_mean':>15}  {key+'_cv':>8}", end="")
        print()

        for defines_str, args_str in sorted({(r["defines"], r["args"]) for r in rows}):
            combo = [r for r in rows if r["defines"] == defines_str and r["args"] == args_str]
            print(f"  {defines_str:<38} {args_str:<18}", end="")
            for key in metric_keys:
                mean, _, cv = compute_stats([r[key] for r in combo])
                print(f"  {mean:>15.3f}  {cv:>8.4f}", end="")
            print()

def iter_flag_defines(programs: dict, diffs: list):
    """Yield (prog_name, prog_cfg, flag_define) for every program x diff combo."""
    for prog_name, prog_cfg in programs.items():
        raw_defines = prog_cfg.get("defines", [{}])
        define_list = [e if isinstance(e, dict) else {} for e in raw_defines]
        for base_define in define_list:
            for flag, _, v3 in diffs:
                yield prog_name, prog_cfg, {**base_define, flag: v3}


def run_experiment(config: dict):
    diffs      = get_diffs()
    programs   = config.get("programs", {})
    lcc3       = config.get("lcc3", True)
    repetitions = config.get("repetitions", 5)
    converge   = config.get("converge", False)
    meas_cfg   = config.get("measurement_program", {})
    meas_path  = meas_cfg.get("path", None)
    meas_args  = meas_cfg.get("args", [])
    massif     = config.get("massif", False)
    CV_THRESHOLD = 0.05
    MAX_REPS   = 20

    output_dir = Path(config.get("output", {}).get("path", "./benchmark")).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n=== Build phase ===")
    for prog_name, prog_cfg, flag_define in iter_flag_defines(programs, diffs):
        build_program(prog_name, prog_cfg, flag_define)

    results: dict[str, list] = {}
    print("\n=== Measurement phase ===")
    for rep in range(repetitions):
        print(f"\n--- Rep {rep + 1}/{repetitions} ---")
        for prog_name, prog_cfg, flag_define in iter_flag_defines(programs, diffs):
            run_once(prog_name, prog_cfg, meas_path, meas_args,
                     lcc3, massif, rep, results,
                     definitions_override=flag_define)

    if converge:
        print("\n=== Convergence phase ===")
        rep = repetitions
        while rep < MAX_REPS:
            converged = check_converged(results, CV_THRESHOLD)
            if all(converged.values()):
                print(f"All programs converged after {rep} reps")
                break
            for prog_name, prog_cfg, flag_define in iter_flag_defines(programs, diffs):
                if converged.get(prog_name, False):
                    continue
                unconverged = get_unconverged_combos(results.get(prog_name, []), CV_THRESHOLD)
                run_once(prog_name, prog_cfg, meas_path, meas_args,
                         lcc3, massif, rep, results,
                         definitions_override=flag_define,
                         skip_combos=unconverged)
            rep += 1
        else:
            print(f"Hit max reps ({MAX_REPS}) without full convergence")
            for prog_name, status in check_converged(results, CV_THRESHOLD).items():
                print(f"  {prog_name}: {'converged' if status else 'NOT converged'}")

    write_results(results, output_dir)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="Path to YAML config file")
    args = parser.parse_args()
    config_path = Path(args.config)
    if not config_path.exists():
        sys.exit(f"Error: config file '{config_path}' not found.")
    with open(config_path) as f:
        config = yaml.safe_load(f)
    run_experiment(config)


if __name__ == "__main__":
    main()