import argparse
import csv
import re
import subprocess
import sys
from pathlib import Path
import numpy as np

import optuna
import yaml

optuna.logging.set_verbosity(optuna.logging.WARNING)

BOUND = 256

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
    median = np.median(values)
    variance = sum((x - mean) ** 2 for x in values) / n
    cv = (variance ** 0.5) / abs(mean) if mean != 0 else 0.0
    return mean, variance, cv, median

def defines_slug(definitions: dict) -> str:
    return "_".join(f"{k}={v}" for k, v in definitions.items()) or "default"

def merge_defines(base: dict, tile: dict) -> dict:
    merged = dict(base)
    merged.update(tile)
    return merged


def get_build_path(program_name, prog_cfg, definitions: dict) -> Path:
    base = Path(prog_cfg.get("build_path")).expanduser().resolve()
    return base / program_name / defines_slug(definitions)


def build_program(prog_name, prog_cfg, definitions: dict):
    base_build_path = Path(prog_cfg.get("build_path")).expanduser().resolve()
    build_path = get_build_path(prog_name, prog_cfg, definitions)
    build_path.mkdir(parents=True, exist_ok=True)
    source_path = base_build_path.parent
    defines = " ".join(f"-D{k}={v}" for k, v in definitions.items())
    build_cmd = f"cmake -G Ninja {defines} {source_path}"
    #print(f"Building {prog_name} [{defines_slug(definitions)}]")
    try:
        subprocess.run(build_cmd, cwd=build_path, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        subprocess.run(f"ninja {prog_name}", cwd=build_path, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        print(f"Failed to build {prog_name}: {e}")
        exit(-1)


def tile_sizes(min_tile: int, bound: int) -> list[int]:
    sizes, v = [], min_tile
    while v <= bound:
        sizes.append(v)
        v *= 2
    return sizes

def run_tile(prog_name, prog_cfg, meas_path, meas_args, lcc3, massif,
             definitions: dict, args: list, rep: int) -> dict | None:
    """
    Build (if needed) and run one (definitions, args) combo for one rep.
    Returns a metrics dict, or None if meas_path is not set.
    """
    build_program(prog_name, prog_cfg, definitions)

    build_path = get_build_path(prog_name, prog_cfg, definitions)
    prog_path = build_path / prog_name
    prefix = prog_cfg.get("prefix", [])
    defines_str = defines_slug(definitions)
    args_str = " ".join(str(a) for a in args)

    base_cmd = prefix + [str(prog_path)] + [str(a) for a in args]
    if massif:
        cmd = ([meas_path] + meas_args +
               ["/usr/bin/valgrind", "--tool=massif", "--time-unit=ms"] +
               base_cmd) if meas_path else base_cmd
    else:
        cmd = ([meas_path] + meas_args + base_cmd) if meas_path else base_cmd
    if lcc3:
        cmd = ["srun"] + cmd

    #print(f"  [{prog_name}|{defines_str}] rep={rep} cmd: {' '.join(cmd)}")
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
        return {"defines": defines_str, "args": args_str, "rep": rep, **metrics}
    return None


def get_unconverged_combos(rows: list, cv_threshold: float = 0.05) -> set:
    """Returns set of (defines, args) combos that haven't converged yet."""
    if not rows:
        return None
    unconverged = set()
    combos = {(r["defines"], r["args"]) for r in rows}
    for defines_str, args_str in combos:
        combo_rows = [r for r in rows if r["defines"] == defines_str and r["args"] == args_str]
        if len(combo_rows) < 3:
            unconverged.add((defines_str, args_str))
            continue
        vals = [r["wall_clock_s"] for r in combo_rows]
        _, _, cv, _ = compute_stats(vals)
        if cv >= cv_threshold:
            unconverged.add((defines_str, args_str))
    return unconverged


def check_converged(results: dict[str, list], cv_threshold: float = 0.05) -> dict[str, bool]:
    converged = {}
    for prog_name, rows in results.items():
        if not rows:
            converged[prog_name] = False
            continue
        unconverged = get_unconverged_combos(rows, cv_threshold)
        converged[prog_name] = len(unconverged) == 0
    return converged


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

        print(f"\n{'defines':<40} {'args':<18}", end="")
        for key in metric_keys:
            print(f"  {key+'_median':>15}  {key+'_cv':>10}", end="")
        print()

        combos = {(r["defines"], r["args"]) for r in rows}
        for defines_str, args_str in sorted(combos):
            combo_rows = [r for r in rows
                          if r["defines"] == defines_str and r["args"] == args_str]
            print(f"  {defines_str:<40} {args_str:<18}", end="")
            for key in metric_keys:
                vals = [r[key] for r in combo_rows]
                mean, _, cv, median = compute_stats(vals)
                print(f"  {median:>15.3f}  {cv:>10.4f}", end="")
            print()


def run_optuna_search(
    prog_name, prog_cfg,
    meas_path, meas_args, lcc3, massif,
    sizes: list[int],
    n_trials: int,
    n_warmup_reps: int,
    results: dict[str, list],
):
    """
    Run an Optuna TPE study for one program.

    Each trial picks (M_T, N_T, K_T) from `sizes`, runs `n_warmup_reps`
    repetitions, and reports the mean wall_clock_s to Optuna.
    All raw rows are appended to results[prog_name] for CSV export.
    """
    raw_defines      = prog_cfg.get("defines", [{}])
    raw_args         = prog_cfg.get("args", [[]])
    base_define_list = [e if isinstance(e, dict) else {} for e in raw_defines]
    arg_list         = [[str(a) for a in e] for e in raw_args]

    def objective(trial: optuna.Trial) -> float:
        m_t = trial.suggest_categorical("M_T", sizes)
        n_t = trial.suggest_categorical("N_T", sizes)
        k_t = trial.suggest_categorical("K_T", sizes)
        tile = {"M_T": m_t, "N_T": n_t, "K_T": k_t}
        print(f"Sampled tile M:{m_t}, N:{n_t}, K:{k_t}")
        wall_times = []
        for base_defs in base_define_list:
            definitions = merge_defines(base_defs, tile)
            for args in arg_list:
                for i in range(n_warmup_reps):
                    print(f"\tRunning {i}/{n_warmup_reps}:", end=" ")
                    row = run_tile(prog_name, prog_cfg, meas_path, meas_args,
                                   lcc3, massif, definitions, args, rep=i)
                    if row:
                        results.setdefault(prog_name, []).append(row)
                        print(f"{row["wall_clock_s"]} seconds")
                        wall_times.append(row["wall_clock_s"])

        if not wall_times:
            raise optuna.exceptions.TrialPruned()
        print(f"Median of Runs: {np.median(wall_times)}")
        return np.median(wall_times)

    study = optuna.create_study(
        direction="minimize",
        sampler=optuna.samplers.TPESampler(seed=42),
        pruner=optuna.pruners.MedianPruner(),
    )
    study.optimize(objective, n_trials=n_trials, show_progress_bar=True)

    best = study.best_trial
    print(f"\n  [{prog_name}] Best tile after {n_trials} trials:")
    print(f"    M_T={best.params['M_T']}  N_T={best.params['N_T']}  "
          f"K_T={best.params['K_T']}  ->  {best.value:.3f}s")
    return study


def run_convergence(
    prog_name, prog_cfg,
    meas_path, meas_args, lcc3, massif,
    results: dict[str, list],
    cv_threshold: float = 0.05,
    max_reps: int = 20,
):
    """Extra reps on unconverged combos found by the Optuna search."""
    rows = results.get(prog_name, [])
    rep = max((r["rep"] for r in rows), default=-1) + 1

    while rep < max_reps:
        unconverged = get_unconverged_combos(rows, cv_threshold)
        if not unconverged:
            print(f"  [{prog_name}] Converged after {rep} total reps")
            break

        raw_args         = prog_cfg.get("args", [[]])
        arg_list         = [[str(a) for a in e] for e in raw_args]

        for combo_defines, combo_args in list(unconverged):
            # Reconstruct definitions dict from slug
            defs = dict(part.split("=") for part in combo_defines.split("_") if "=" in part)
            defs_typed = {k: int(v) if v.isdigit() else v for k, v in defs.items()}
            args = combo_args.split() if combo_args else []
            row = run_tile(prog_name, prog_cfg, meas_path, meas_args,
                           lcc3, massif, defs_typed, args, rep=rep)
            if row:
                rows.append(row)
        rep += 1
    else:
        print(f"  [{prog_name}] Hit max reps ({max_reps}) without full convergence")


# ── Experiment entry point ────────────────────────────────────────────────────

def run_experiment(config: dict):
    lcc3      = config.get("lcc3", True)
    programs  = config.get("programs", {})
    converge  = config.get("converge", False)
    meas_cfg  = config.get("measurement_program", {})
    meas_path = meas_cfg.get("path", None)
    massif    = config.get("massif", False)
    meas_args = meas_cfg.get("args", [])

    tile_bound   = config.get("tile_bound", BOUND)
    tile_min     = config.get("tile_min", 8)
    n_trials     = config.get("optuna_trials", 50)
    n_warmup     = config.get("optuna_warmup_reps", 2)
    cv_threshold = config.get("cv_threshold", 0.05)
    max_reps     = config.get("max_reps", 20)

    sizes = tile_sizes(tile_min, tile_bound)
    total_combos = len(sizes) ** 3
    print(f"Tile search space: {total_combos} combos "
          f"(M_T x N_T x K_T, powers of 2 in [{tile_min},{tile_bound}])")
    print(f"Optuna TPE: {n_trials} trials x {n_warmup} warmup reps each "
          f"(~{n_trials * n_warmup} runs vs {total_combos} exhaustive)")

    output_dir = Path(config.get("output", {}).get("path", "./benchmark")).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    results: dict[str, list] = {}

    for prog_name, prog_cfg in programs.items():
        print(f"\n=== {prog_name} ===")
        run_optuna_search(
            prog_name, prog_cfg,
            meas_path, meas_args, lcc3, massif,
            sizes=sizes,
            n_trials=n_trials,
            n_warmup_reps=n_warmup,
            results=results,
        )

        if converge:
            print(f"\n--- Convergence phase: {prog_name} ---")
            run_convergence(
                prog_name, prog_cfg,
                meas_path, meas_args, lcc3, massif,
                results=results,
                cv_threshold=cv_threshold,
                max_reps=max_reps,
            )

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
