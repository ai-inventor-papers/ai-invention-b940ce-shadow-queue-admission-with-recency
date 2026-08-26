#!/usr/bin/env python3
"""Per-Key Decay vs Global TinyLFU Cache Admission.

Compares a faithful W-TinyLFU cache-admission baseline (global Count-Min sketch +
doorkeeper Bloom filter, periodic global reset) against a proposed per-key-decay
variant (each key's frequency-decay rate bucketed from its own shadow-queue
inter-arrival coefficient-of-variation) across synthetic Zipf(+drift) traces, on
steady-state hit ratio, drift-recovery time, and exact memory overhead.

Both policies share the identical SLRU eviction backbone (sim/slru.py) so any
difference is attributable to the admission test alone.
"""

from __future__ import annotations

import argparse
import gc
import json
import multiprocessing as mp
import resource
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
from loguru import logger

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sim.admission import BaselineAdmission, PerKeyDecayAdmission  # noqa: E402
from sim.metrics import compute_metrics  # noqa: E402
from sim.slru import SLRU  # noqa: E402
from sim.traces import Scenario, count_lines, load_real_trace, make_zipf_drift_trace  # noqa: E402

logger.remove()
logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss}|{level:<7}|{message}")
Path("logs").mkdir(exist_ok=True)
logger.add("logs/run.log", rotation="30 MB", level="DEBUG")

RAM_BUDGET_BYTES = 20 * 1024 ** 3  # 20 GB soft budget within the 57 GB container limit
resource.setrlimit(resource.RLIMIT_AS, (RAM_BUDGET_BYTES * 3, RAM_BUDGET_BYTES * 3))
resource.setrlimit(resource.RLIMIT_CPU, (3600 * 5, 3600 * 5))

WORKSPACE = Path(__file__).resolve().parent
DRIFT_TYPES = ["none", "periodic_reshuffle", "burst_cold_keys", "gradual_rank_shift", "combined"]
ALPHAS = [0.8, 1.0, 1.2]
W_SWEEP = [4, 8, 16, 32]
CACHE_RATIOS = [0.01, 0.05, 0.10]
N_KEYS = 10_000
N_REQUESTS = 200_000
RECOVERY_WINDOW = 2000


def run_scenario(trace: np.ndarray, method_cls, cache_capacity: int, **method_kwargs) -> dict:
    cache = SLRU(cache_capacity)
    admission = method_cls(cache_capacity, **method_kwargs)
    n = len(trace)
    hits = np.zeros(n, dtype=bool)
    on_access = admission.on_access
    for t in range(n):
        hits[t] = on_access(int(trace[t]), cache)
    result = {"hits": hits, "memory_bytes": admission.memory_bytes()}
    if hasattr(admission, "bucket_histogram"):
        result["bucket_histogram"] = admission.bucket_histogram()
    return result


def _run_one_config(args: dict) -> dict:
    """Top-level (picklable) worker: runs one (scenario, cache_ratio, method[, W]) config."""
    scenario_name = args["scenario_name"]
    scenario_trace = args["trace"]
    drift_events = args["drift_events"]
    cache_ratio = args["cache_ratio"]
    n_keys = args["n_keys"]
    method = args["method"]
    w_ratio = args.get("w_ratio")
    scenario_meta = args["scenario_meta"]

    capacity = max(4, int(n_keys * cache_ratio))
    t0 = time.perf_counter()
    if method == "baseline":
        res = run_scenario(scenario_trace, BaselineAdmission, capacity, w_over_c_ratio=w_ratio)
    else:
        res = run_scenario(scenario_trace, PerKeyDecayAdmission, capacity)
    elapsed = time.perf_counter() - t0

    metrics = compute_metrics(res["hits"], drift_events, window=min(RECOVERY_WINDOW, len(scenario_trace) // 4 or 1))
    out = {
        "scenario": scenario_name,
        "scenario_meta": scenario_meta,
        "cache_ratio": cache_ratio,
        "cache_capacity": capacity,
        "method": method,
        "w_ratio": w_ratio,
        "memory_bytes": res["memory_bytes"],
        "elapsed_s": elapsed,
        **metrics,
    }
    if "bucket_histogram" in res:
        out["bucket_histogram"] = res["bucket_histogram"]
    return out


def build_configs(scenarios: list[Scenario], cache_ratios: list[float], w_sweep: list[int]) -> list[dict]:
    configs = []
    for sc in scenarios:
        for cache_ratio in cache_ratios:
            for w_ratio in w_sweep:
                configs.append({
                    "scenario_name": sc.name, "trace": sc.trace, "drift_events": sc.drift_events,
                    "cache_ratio": cache_ratio, "n_keys": sc.n_keys, "method": "baseline",
                    "w_ratio": w_ratio, "scenario_meta": sc.meta,
                })
            configs.append({
                "scenario_name": sc.name, "trace": sc.trace, "drift_events": sc.drift_events,
                "cache_ratio": cache_ratio, "n_keys": sc.n_keys, "method": "perkey",
                "w_ratio": None, "scenario_meta": sc.meta,
            })
    return configs


def run_configs_parallel(configs: list[dict], num_workers: int) -> list[dict]:
    results = []
    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=num_workers, mp_context=mp.get_context("spawn")) as pool:
        futures = {pool.submit(_run_one_config, cfg): i for i, cfg in enumerate(configs)}
        done = 0
        for fut in as_completed(futures):
            try:
                results.append(fut.result())
            except Exception:
                logger.exception(f"Config {futures[fut]} failed")
                continue
            done += 1
            if done % 20 == 0 or done == len(configs):
                logger.info(f"  progress: {done}/{len(configs)} configs, {time.perf_counter() - t0:.1f}s elapsed")
    return results


def pick_best_baseline_w(results: list[dict]) -> None:
    """Annotates each baseline result group with whether it is the best-tuned W for
    that scenario+cache_ratio (highest steady-state hit ratio among the W sweep)."""
    groups: dict[tuple, list[dict]] = {}
    for r in results:
        if r["method"] != "baseline":
            continue
        key = (r["scenario"], r["cache_ratio"])
        groups.setdefault(key, []).append(r)
    for group in groups.values():
        best = max(group, key=lambda r: r["steady_state_hit_ratio"])
        for r in group:
            r["is_best_w_for_scenario"] = r is best


def _base_scenario_family(scenario_name: str) -> str:
    if "_seed" in scenario_name:
        return scenario_name.split("_seed")[0]
    return scenario_name


def aggregate_across_seeds(results: list[dict]) -> list[dict]:
    """Groups results by (scenario_family, cache_ratio, method, w_ratio) across seed
    replicates and computes mean/std/95%-CI-half-width for steady-state hit ratio and
    memory_bytes — turning point estimates into estimates with variance."""
    groups: dict[tuple, list[dict]] = {}
    for r in results:
        family = _base_scenario_family(r["scenario"])
        key = (family, r["cache_ratio"], r["method"], r["w_ratio"])
        groups.setdefault(key, []).append(r)

    aggregates = []
    for (family, cache_ratio, method, w_ratio), rows in groups.items():
        n = len(rows)
        hr = np.array([row["steady_state_hit_ratio"] for row in rows], dtype=np.float64)
        mem = np.array([row["memory_bytes"] for row in rows], dtype=np.float64)
        hr_mean, hr_std = float(hr.mean()), float(hr.std(ddof=1)) if n > 1 else 0.0
        ci95_halfwidth = float(1.96 * hr_std / np.sqrt(n)) if n > 1 else 0.0
        aggregates.append({
            "scenario_family": family, "cache_ratio": cache_ratio, "method": method, "w_ratio": w_ratio,
            "n_seeds": n,
            "hit_ratio_mean": hr_mean, "hit_ratio_std": hr_std, "hit_ratio_ci95_halfwidth": ci95_halfwidth,
            "memory_bytes_mean": float(mem.mean()), "memory_bytes_std": float(mem.std(ddof=1)) if n > 1 else 0.0,
        })
    return aggregates


def to_gen_sol_schema(results: list[dict], metadata: dict, aggregates: list[dict] | None = None) -> dict:
    """Maps results into exp_gen_sol_out.json schema: one 'dataset' per scenario, one
    'example' per (cache_ratio, method[, W]) config within it."""
    by_scenario: dict[str, list[dict]] = {}
    for r in results:
        by_scenario.setdefault(r["scenario"], []).append(r)

    datasets = []
    for scenario_name, rows in sorted(by_scenario.items()):
        examples = []
        for r in rows:
            input_desc = json.dumps({
                "scenario": r["scenario"], "scenario_meta": r["scenario_meta"],
                "cache_ratio": r["cache_ratio"], "cache_capacity": r["cache_capacity"],
                "method": r["method"], "w_ratio": r["w_ratio"],
            })
            output_desc = json.dumps({
                "steady_state_hit_ratio": r["steady_state_hit_ratio"],
                "memory_bytes": r["memory_bytes"],
                "n_recovery_events": len(r["recovery_events"]),
            })
            example = {
                "input": input_desc,
                "output": output_desc,
                "metadata_cache_ratio": r["cache_ratio"],
                "metadata_cache_capacity": r["cache_capacity"],
                "metadata_method": r["method"],
                "metadata_w_ratio": r["w_ratio"],
                "metadata_memory_bytes": r["memory_bytes"],
                "metadata_elapsed_s": r["elapsed_s"],
                "metadata_recovery_events": r["recovery_events"],
                "metadata_scenario_meta": r["scenario_meta"],
                "predict_steady_state_hit_ratio": str(r["steady_state_hit_ratio"]),
            }
            if "is_best_w_for_scenario" in r:
                example["metadata_is_best_w_for_scenario"] = r["is_best_w_for_scenario"]
            if "bucket_histogram" in r:
                example["metadata_bucket_histogram"] = r["bucket_histogram"]
            examples.append(example)
        datasets.append({"dataset": scenario_name, "examples": examples})

    if aggregates:
        agg_examples = []
        for a in aggregates:
            agg_examples.append({
                "input": json.dumps({
                    "scenario_family": a["scenario_family"], "cache_ratio": a["cache_ratio"],
                    "method": a["method"], "w_ratio": a["w_ratio"], "n_seeds": a["n_seeds"],
                }),
                "output": json.dumps({
                    "hit_ratio_mean": a["hit_ratio_mean"], "hit_ratio_ci95_halfwidth": a["hit_ratio_ci95_halfwidth"],
                }),
                "metadata_cache_ratio": a["cache_ratio"], "metadata_method": a["method"], "metadata_w_ratio": a["w_ratio"],
                "metadata_n_seeds": a["n_seeds"], "metadata_hit_ratio_std": a["hit_ratio_std"],
                "metadata_hit_ratio_ci95_halfwidth": a["hit_ratio_ci95_halfwidth"],
                "metadata_memory_bytes_mean": a["memory_bytes_mean"], "metadata_memory_bytes_std": a["memory_bytes_std"],
                "predict_hit_ratio_mean": str(a["hit_ratio_mean"]),
            })
        datasets.append({"dataset": "aggregate_across_seeds", "examples": agg_examples})

    return {"metadata": metadata, "datasets": datasets}


def _detect_cpus() -> int:
    import math
    import os
    try:
        parts = Path("/sys/fs/cgroup/cpu.max").read_text().split()
        if parts[0] != "max":
            return math.ceil(int(parts[0]) / int(parts[1]))
    except (FileNotFoundError, ValueError):
        pass
    try:
        q = int(Path("/sys/fs/cgroup/cpu/cpu.cfs_quota_us").read_text())
        p = int(Path("/sys/fs/cgroup/cpu/cpu.cfs_period_us").read_text())
        if q > 0:
            return math.ceil(q / p)
    except (FileNotFoundError, ValueError):
        pass
    try:
        return len(os.sched_getaffinity(0))
    except (AttributeError, OSError):
        pass
    return os.cpu_count() or 1


def aggregate_bucket_histogram(results: list[dict]) -> dict:
    """Sums per-key decay-bucket assignment counts across all perkey-method configs.
    Diagnoses whether the CoV-based classifier actually differentiates keys (per
    fallback_plan item 3) rather than collapsing onto a single bucket."""
    totals = {"stable": 0, "mixed": 0, "volatile": 0}
    n_configs = 0
    for r in results:
        hist = r.get("bucket_histogram")
        if hist:
            for k, v in hist.items():
                totals[k] += v
            n_configs += 1
    total_keys = sum(totals.values())
    fractions = {k: (v / total_keys if total_keys else 0.0) for k, v in totals.items()}
    return {"counts": totals, "fractions": fractions, "n_configs_counted": n_configs}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-keys", type=int, default=N_KEYS)
    parser.add_argument("--n-requests", type=int, default=N_REQUESTS)
    parser.add_argument("--cache-ratios", type=float, nargs="+", default=CACHE_RATIOS)
    parser.add_argument("--w-sweep", type=int, nargs="+", default=W_SWEEP)
    parser.add_argument("--drift-types", type=str, nargs="+", default=DRIFT_TYPES)
    parser.add_argument("--alphas", type=float, nargs="+", default=ALPHAS)
    parser.add_argument("--real-trace-path", type=str, default=None)
    parser.add_argument("--real-trace-windows", type=int, default=1,
                         help="Number of non-overlapping windows to draw from the real trace file (variance across windows).")
    parser.add_argument("--n-seeds", type=int, default=1,
                         help="Number of independently-seeded replicate traces per (alpha, drift_type) scenario, for variance across runs.")
    parser.add_argument("--output", type=str, default=str(WORKSPACE / "method_out.json"))
    parser.add_argument("--num-workers", type=int, default=None)
    args = parser.parse_args()

    num_workers = args.num_workers or max(1, _detect_cpus() - 1)
    logger.info(f"Using {num_workers} worker processes")

    logger.info(f"Building scenarios: n_keys={args.n_keys}, n_requests={args.n_requests}, "
                f"alphas={args.alphas}, drift_types={args.drift_types}, n_seeds={args.n_seeds}")
    scenarios = []
    seed = 1000
    for alpha in args.alphas:
        for drift_type in args.drift_types:
            for rep in range(args.n_seeds):
                sc = make_zipf_drift_trace(args.n_keys, args.n_requests, alpha, drift_type, seed)
                if args.n_seeds > 1:
                    sc.name = f"{sc.name}_seed{rep}"
                    sc.meta = {**sc.meta, "seed_rep": rep, "seed": seed}
                scenarios.append(sc)
                seed += 1

    real_trace_used = False
    if args.real_trace_path:
        total_lines = count_lines(args.real_trace_path)
        max_windows = max(1, total_lines // args.n_requests) if args.n_requests > 0 else 1
        n_windows = min(args.real_trace_windows, max_windows)
        for w in range(n_windows):
            suffix = f"_window{w}" if n_windows > 1 else ""
            real = load_real_trace(
                args.real_trace_path, max_requests=args.n_requests,
                skip_lines=w * args.n_requests, name_suffix=suffix,
            )
            if real is not None:
                scenarios.append(real)
                real_trace_used = True
                logger.info(f"Loaded real trace window {w}: {real.name}, n_keys={real.n_keys}, n_requests={len(real.trace)}")
            else:
                logger.warning(f"Could not load real trace window {w} at {args.real_trace_path}; skipping")
        if not real_trace_used:
            logger.warning(f"Could not load any real trace window at {args.real_trace_path}; continuing synthetic-only")

    logger.info(f"Built {len(scenarios)} scenarios")
    configs = build_configs(scenarios, args.cache_ratios, args.w_sweep)
    logger.info(f"Built {len(configs)} total configs "
                f"({len(scenarios)} scenarios x {len(args.cache_ratios)} cache_ratios x "
                f"({len(args.w_sweep)} baseline-W + 1 perkey))")

    t0 = time.perf_counter()
    results = run_configs_parallel(configs, num_workers)
    logger.info(f"Ran {len(results)}/{len(configs)} configs in {time.perf_counter() - t0:.1f}s")

    pick_best_baseline_w(results)
    aggregates = aggregate_across_seeds(results) if args.n_seeds > 1 else []

    metadata = {
        "method_name": "per_key_decay_vs_global_tinylfu",
        "description": (
            "W-TinyLFU baseline (global Count-Min + doorkeeper, periodic global reset) vs "
            "proposed per-key decay-rate-bucketed admission (CoV of shadow-queue inter-arrival "
            "gaps), on shared SLRU eviction, across synthetic Zipf(+drift) traces."
        ),
        "n_keys": args.n_keys, "n_requests": args.n_requests,
        "cache_ratios": args.cache_ratios, "w_sweep": args.w_sweep,
        "alphas": args.alphas, "drift_types": args.drift_types,
        "real_trace_used": real_trace_used, "n_seeds": args.n_seeds,
        "real_trace_windows_requested": args.real_trace_windows,
        "n_scenarios": len(scenarios), "n_configs": len(configs), "n_results": len(results),
        "total_runtime_s": time.perf_counter() - t0,
        "perkey_decay_bucket_histogram": aggregate_bucket_histogram(results),
    }
    out = to_gen_sol_schema(results, metadata, aggregates)

    Path(args.output).write_text(json.dumps(out, indent=2))
    logger.info(f"Wrote {args.output}")
    del results, configs, scenarios
    gc.collect()


if __name__ == "__main__":
    main()
