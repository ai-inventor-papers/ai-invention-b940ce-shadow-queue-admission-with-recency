#!/usr/bin/env python3
"""Sharper baseline test + real Twitter trace replay.

Two additions on top of iter1's W-TinyLFU cache-admission simulator
(imported unchanged from iter1_method.py, a verbatim copy of iter1's method.py):

  Part A - Short global-reset multiplier sweep. Iter1 tuned the baseline's
  global-reset sample-size multiplier over {4, 8, 16, 32} and always picked
  the largest (32) at the win-corner cell (ratio=0.01, alpha=1.2). This part
  asks the sharper question: can an even SHORTER reset period (1x/2x/4x cache
  capacity) close the recovery-time gap with the proposed per-key-decay
  estimator, without any per-key machinery at all? If yes, the proposed
  mechanism's added complexity is not earning its keep at this cell.

  Part B - Real Twitter production trace replay (twitter/cache-trace,
  cluster026, 80,000 requests) end-to-end through both estimators, unchanged,
  reporting genuine steady-state hit ratio and memory footprint on real
  traffic (iter1 could not do this at all: it explicitly skipped the real-trace
  arm because only a bespoke multi-GB binary format was available then; the
  dataset dependency for this iteration ships it pre-decoded as JSON rows).
  A lightweight unsupervised JS-divergence changepoint detector over the
  per-key request stream then derives coarse, honestly-labeled candidate
  drift points on the (unlabeled) real trace, first validated against KNOWN
  drift events on a synthetic trace so an untrustworthy detector is caught
  before being trusted on real data.
"""

from __future__ import annotations

import gc
import json
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np
from loguru import logger

WORKSPACE = Path(__file__).resolve().parent
LOG_DIR = WORKSPACE / "logs"
LOG_DIR.mkdir(exist_ok=True)

logger.remove()
logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss}|{level:<7}|{message}")
logger.add(LOG_DIR / "run.log", rotation="30 MB", level="DEBUG")

sys.path.insert(0, str(WORKSPACE))
import iter1_method as base  # noqa: E402  (reuse iter1's estimator/simulator classes unchanged)

# ==========================================================================
# Configuration
# ==========================================================================

RATIO = 0.01
ALPHA = 1.2
KEY_SPACE = base.KEY_SPACE  # 150_000, identical to iter1 so cells are comparable
CACHE_CAPACITY = max(10, int(RATIO * KEY_SPACE))  # 1500, matches iter1's win-corner cell exactly
SHORT_MULTIPLIERS = [1, 2, 4]  # in addition to iter1's already-swept {4, 8, 16, 32}; 4 overlaps as a sanity cross-check
DRIFT_SCENARIOS = base.DRIFT_SCENARIOS  # all 4 from iter1, unchanged
SEEDS = base.SEEDS  # [1, 2, 3], matches iter1's seed set for the win-corner cell
N_REQUESTS_MAIN = base.N_REQUESTS_MAIN  # 600_000
RECOVERY_LOOKAHEAD_MAIN = base.RECOVERY_LOOKAHEAD_MAIN  # 60_000
BURST_PROB = base.BURST_PROB

# iter1's exact proposed-estimator (per-key decay) mean-recovery-time results at this
# cell, read directly from full_method_out.json (NOT rerun) for the head-to-head
# comparison against the newly-swept short-reset baseline arms.
IT1_EXPERIMENT_DIR = (
    WORKSPACE.parent.parent.parent / "iter_1" / "gen_art" / "gen_art_experiment_1"
)
IT1_FULL_OUT = IT1_EXPERIMENT_DIR / "full_method_out.json"

REAL_TRACE_PATH = WORKSPACE / "real_twitter_cache_trace"
IT1_BEST_MULTIPLIER_AT_CELL = 32  # iter1's Phase A tuning result for (ratio=0.01, alpha=1.2)
SHADOW_QUEUE_MULT = base.SHADOW_QUEUE_MULT

CP_WINDOW = 2000
CP_STRIDE = 500
CP_TOP_K = 50
CP_PERCENTILE = 95.0
CP_RECOVERY_LOOKAHEAD = 5000


# ==========================================================================
# Part A helpers
# ==========================================================================


def load_iter1_proposed_results(ratio: float, alpha: float) -> dict[str, dict]:
    """Reads iter1's already-computed proposed-estimator (per-key decay) results
    for every drift scenario at the given (ratio, alpha) cell, keyed by scenario
    name. Does NOT rerun anything -- iter1's full_method_out.json is authoritative.
    """
    if not IT1_FULL_OUT.exists():
        raise FileNotFoundError(
            f"iter1 full_method_out.json not found at {IT1_FULL_OUT}; cannot pull the "
            "proposed-estimator baseline for the head-to-head comparison. This is a hard "
            "dependency on iter1's artifact per the plan (do NOT silently invent a value)."
        )
    data = json.loads(IT1_FULL_OUT.read_text())
    grid = [ds for ds in data["datasets"] if ds["dataset"] == "phaseB_drift_scenario_grid"][0]["examples"]
    by_scenario: dict[str, list[dict]] = {}
    for ex in grid:
        cfg = json.loads(ex["input"])
        if abs(cfg["ratio"] - ratio) < 1e-9 and abs(cfg["alpha"] - alpha) < 1e-9:
            out = json.loads(ex["output"])
            by_scenario.setdefault(cfg["drift_scenario"], []).append(
                {"seed": cfg["seed"], "proposed_mean_recovery_time": out["proposed"]["mean_recovery_time"]}
            )
    if not by_scenario:
        raise ValueError(f"No iter1 grid rows found for ratio={ratio}, alpha={alpha}")
    result = {}
    for scenario, rows in by_scenario.items():
        vals = [r["proposed_mean_recovery_time"] for r in rows if r["proposed_mean_recovery_time"] is not None]
        result[scenario] = {
            "per_seed": rows,
            "mean_across_seeds": float(np.mean(vals)) if vals else None,
        }
    logger.info(f"Loaded iter1 proposed-estimator recovery times for {len(result)} scenarios at ratio={ratio}, alpha={alpha}")
    return result


def run_short_reset_cell(scenario: dict, multiplier: int, seed: int) -> dict:
    tr = base.make_zipf_drift_trace(
        N_REQUESTS_MAIN,
        KEY_SPACE,
        ALPHA,
        n_drift_events=scenario["n_drift_events"],
        drift_magnitude=scenario["drift_magnitude"],
        burst_prob=BURST_PROB,
        seed=seed,
    )
    est = base.GlobalResetFrequencyEstimator(CACHE_CAPACITY, multiplier, seed=seed * 7 + 1)
    res = base.run_trace(tr.keys, CACHE_CAPACITY, est)
    recovery = base.compute_recovery_times(res["rolling_hit_ratio"], tr.drift_indices, lookahead=RECOVERY_LOOKAHEAD_MAIN)
    tail_start = int(0.85 * N_REQUESTS_MAIN)
    steady = float(np.mean(res["rolling_hit_ratio"][tail_start:]))
    vals = [r["recovery_time"] for r in recovery]
    mean_recovery = float(np.mean(vals)) if vals else None
    n_censored = sum(1 for r in recovery if r["censored"])
    return {
        "multiplier": multiplier,
        "sample_size_W": multiplier * CACHE_CAPACITY,
        "seed": seed,
        "final_hit_ratio": res["final_hit_ratio"],
        "steady_state_hit_ratio": steady,
        "memory_bytes": res["memory_bytes"],
        "mean_recovery_time": mean_recovery,
        "n_drift_events": len(tr.drift_indices),
        "n_censored_recovery_events": n_censored,
        "recovery_events": recovery,
    }


def run_part_a() -> dict:
    logger.info(
        f"Part A: short-multiplier sweep at ratio={RATIO}, alpha={ALPHA} "
        f"(cache_capacity={CACHE_CAPACITY}), multipliers={SHORT_MULTIPLIERS}, "
        f"scenarios={len(DRIFT_SCENARIOS)}, seeds={SEEDS}"
    )
    iter1_proposed = load_iter1_proposed_results(RATIO, ALPHA)

    per_run = []
    by_scenario_mult: dict[tuple[str, int], list[dict]] = {}
    for scenario in DRIFT_SCENARIOS:
        for mult in SHORT_MULTIPLIERS:
            for seed in SEEDS:
                t0 = time.time()
                run = run_short_reset_cell(scenario, mult, seed)
                run["scenario"] = scenario["name"]
                per_run.append(run)
                by_scenario_mult.setdefault((scenario["name"], mult), []).append(run)
                logger.info(
                    f"Part A: scenario={scenario['name']} mult={mult} seed={seed} "
                    f"steady_hr={run['steady_state_hit_ratio']:.4f} "
                    f"mean_recovery={run['mean_recovery_time']} "
                    f"censored={run['n_censored_recovery_events']}/{run['n_drift_events']} "
                    f"({time.time()-t0:.1f}s)"
                )

    # Aggregate per (scenario, multiplier) across seeds
    aggregated = []
    for (scenario_name, mult), runs in by_scenario_mult.items():
        rec_vals = [r["mean_recovery_time"] for r in runs if r["mean_recovery_time"] is not None]
        hr_vals = [r["steady_state_hit_ratio"] for r in runs]
        collapse_flags = [r["n_censored_recovery_events"] == r["n_drift_events"] and r["n_drift_events"] > 0 for r in runs]
        aggregated.append(
            {
                "scenario": scenario_name,
                "multiplier": mult,
                "sample_size_W": mult * CACHE_CAPACITY,
                "n_seeds": len(runs),
                "mean_recovery_time": float(np.mean(rec_vals)) if rec_vals else None,
                "mean_steady_state_hit_ratio": float(np.mean(hr_vals)),
                "fully_censored_seeds": int(sum(collapse_flags)),
                "degenerate_admission_suspected": bool(
                    np.mean(hr_vals) < 0.5 or sum(collapse_flags) == len(runs)
                ),
            }
        )

    # Head-to-head: for each scenario, find the best (lowest mean recovery) short-reset
    # multiplier and compare against iter1's already-computed proposed-estimator result.
    head_to_head = []
    for scenario in DRIFT_SCENARIOS:
        name = scenario["name"]
        candidates = [a for a in aggregated if a["scenario"] == name and a["mean_recovery_time"] is not None]
        if not candidates:
            logger.warning(f"Part A: scenario={name} has no valid (non-fully-censored) short-reset arm; skipping head-to-head")
            continue
        best = min(candidates, key=lambda a: a["mean_recovery_time"])
        proposed_mean = iter1_proposed[name]["mean_across_seeds"]
        if proposed_mean is None or best["mean_recovery_time"] is None:
            gap_pct = None
        else:
            gap_pct = 100.0 * (best["mean_recovery_time"] - proposed_mean) / best["mean_recovery_time"]
        head_to_head.append(
            {
                "scenario": name,
                "best_short_reset_multiplier": best["multiplier"],
                "best_short_reset_mean_recovery_time": best["mean_recovery_time"],
                "best_short_reset_steady_state_hit_ratio": best["mean_steady_state_hit_ratio"],
                "proposed_estimator_mean_recovery_time_iter1": proposed_mean,
                "proposed_still_faster_pct": gap_pct,
                "interpretation": (
                    "proposed per-key-decay estimator STILL recovers faster than the best "
                    "short-reset global baseline -- short reset does not substitute for the mechanism"
                    if (gap_pct is not None and gap_pct > 0)
                    else "short-reset global baseline matches or beats the proposed estimator at this "
                    "cell -- this DISCONFIRMS the necessity of per-key decay for this scenario"
                    if gap_pct is not None
                    else "comparison unavailable (missing data on one side)"
                ),
            }
        )
        logger.info(
            f"Part A head-to-head [{name}]: best_short_reset(mult={best['multiplier']})="
            f"{best['mean_recovery_time']}, proposed(iter1)={proposed_mean}, "
            f"proposed_still_faster_pct={gap_pct}"
        )

    n_wins_for_proposed = sum(1 for h in head_to_head if h["proposed_still_faster_pct"] is not None and h["proposed_still_faster_pct"] > 0)
    return {
        "config": {
            "ratio": RATIO,
            "alpha": ALPHA,
            "cache_capacity": CACHE_CAPACITY,
            "key_space": KEY_SPACE,
            "n_requests_main": N_REQUESTS_MAIN,
            "short_multipliers_swept": SHORT_MULTIPLIERS,
            "iter1_multipliers_swept": base.SAMPLE_MULTIPLIERS,
            "iter1_chosen_multiplier_at_cell": IT1_BEST_MULTIPLIER_AT_CELL,
            "seeds": SEEDS,
            "drift_scenarios": DRIFT_SCENARIOS,
        },
        "per_run": per_run,
        "aggregated_by_scenario_multiplier": aggregated,
        "head_to_head_vs_iter1_proposed": head_to_head,
        "summary": {
            "n_scenarios_with_head_to_head": len(head_to_head),
            "n_scenarios_proposed_still_wins": n_wins_for_proposed,
            "fraction_scenarios_proposed_still_wins": (
                n_wins_for_proposed / len(head_to_head) if head_to_head else None
            ),
            "any_degenerate_admission_observed": any(a["degenerate_admission_suspected"] for a in aggregated),
        },
    }


# ==========================================================================
# Part B: real Twitter trace replay
# ==========================================================================


def load_real_trace_keys(path: Path) -> tuple[np.ndarray, list[str], list[str]]:
    """Loads the 80,000-request real Twitter trace, maps string keys to dense
    int ids (required by the Count-Min sketch / SLRU implementation, which is
    keyed on ints), and returns (int_key_array, ordered_string_keys, request_types).
    """
    logger.info(f"Loading real Twitter trace from {path}")
    data = json.loads(path.read_text())
    examples = data["datasets"][0]["examples"]
    logger.info(f"Loaded {len(examples)} raw rows from real_twitter_cache_trace")

    key_to_id: dict[str, int] = {}
    int_keys = np.empty(len(examples), dtype=np.int64)
    string_keys: list[str] = []
    request_types: list[str] = []
    for i, ex in enumerate(examples):
        row = json.loads(ex["input"])
        k = row["key"]
        string_keys.append(k)
        request_types.append(row.get("request_type", "unknown"))
        idx = key_to_id.get(k)
        if idx is None:
            idx = len(key_to_id)
            key_to_id[k] = idx
        int_keys[i] = idx

    rt_counts = Counter(request_types)
    logger.info(
        f"Real trace: {len(examples)} requests, {len(key_to_id)} distinct keys, "
        f"request_type breakdown={dict(rt_counts)}"
    )
    return int_keys, string_keys, request_types


def tune_real_trace_multiplier(int_keys: np.ndarray, cache_capacity: int) -> tuple[int, dict]:
    """Single-pass tuning: replays the FULL trace once per candidate multiplier
    (only 80k requests each, cheap) and picks the multiplier with the best final
    hit ratio -- same selection rule as iter1's _tune_baseline_multiplier, applied
    directly to the real trace rather than to a synthetic proxy."""
    sweep = {}
    best_mult, best_hr = base.SAMPLE_MULTIPLIERS[0], -1.0
    for mult in base.SAMPLE_MULTIPLIERS:
        est = base.GlobalResetFrequencyEstimator(cache_capacity, mult, seed=42)
        res = base.run_trace(int_keys, cache_capacity, est)
        sweep[mult] = res["final_hit_ratio"]
        if res["final_hit_ratio"] > best_hr:
            best_hr, best_mult = res["final_hit_ratio"], mult
    logger.info(f"Real-trace multiplier tuning sweep: {sweep} -> chosen={best_mult}")
    return best_mult, sweep


def run_real_trace_replay(int_keys: np.ndarray, cache_capacity: int) -> dict:
    best_mult, tuning_sweep = tune_real_trace_multiplier(int_keys, cache_capacity)

    results = {}
    for name, estimator in [
        ("baseline_w_tinylfu", base.GlobalResetFrequencyEstimator(cache_capacity, best_mult, seed=101)),
        (
            "per_key_decay",
            base.PerKeyDecayFrequencyEstimator(
                cache_capacity, shadow_queue_capacity=SHADOW_QUEUE_MULT * cache_capacity, seed=102
            ),
        ),
    ]:
        t0 = time.time()
        res = base.run_trace(int_keys, cache_capacity, estimator)
        n = len(int_keys)
        distinct_keys_touched = len(getattr(estimator, "shadow_meta", None)._od) if hasattr(estimator, "shadow_meta") else None
        results[name] = {
            "final_hit_ratio": res["final_hit_ratio"],
            "steady_state_hit_ratio": float(np.mean(res["rolling_hit_ratio"][int(0.5 * n):])),
            "memory_bytes": res["memory_bytes"],
            "memory_bytes_per_cache_slot": res["memory_bytes"] / cache_capacity,
            "rolling_hit_ratio": res["rolling_hit_ratio"],  # kept in-process for changepoint recovery calc; summarized before JSON export
            "tier_assignment_fractions": base.estimator_tier_diagnostics(estimator),
            "runtime_seconds": time.time() - t0,
        }
        logger.info(
            f"Real trace [{name}]: final_hr={res['final_hit_ratio']:.4f}, "
            f"memory_bytes={res['memory_bytes']}, runtime={time.time()-t0:.1f}s"
        )
    results["_meta"] = {"chosen_baseline_multiplier": best_mult, "tuning_sweep": tuning_sweep, "n_requests": len(int_keys)}
    return results


# ---- unsupervised JS-divergence changepoint detector ----


def _key_freq_distribution(keys_window, top_k: int) -> dict[int, float]:
    counts = Counter(keys_window)
    total = sum(counts.values())
    top = counts.most_common(top_k)
    dist = {k: c / total for k, c in top}
    return dist


def _js_divergence(p: dict, q: dict) -> float:
    keys = set(p) | set(q)
    if not keys:
        return 0.0
    p_arr = np.array([p.get(k, 0.0) for k in keys])
    q_arr = np.array([q.get(k, 0.0) for k in keys])
    p_arr = p_arr / max(p_arr.sum(), 1e-12)
    q_arr = q_arr / max(q_arr.sum(), 1e-12)
    m = 0.5 * (p_arr + q_arr)

    def _kl(a, b):
        mask = a > 0
        return float(np.sum(a[mask] * np.log2(a[mask] / np.maximum(b[mask], 1e-12))))

    return 0.5 * _kl(p_arr, m) + 0.5 * _kl(q_arr, m)


def detect_changepoints(
    keys: np.ndarray, window: int = CP_WINDOW, stride: int = CP_STRIDE, top_k: int = CP_TOP_K, percentile: float = CP_PERCENTILE
) -> tuple[list[int], list[float], float]:
    n = len(keys)
    starts = list(range(0, n - window, stride))
    if len(starts) < 2:
        return [], [], 0.0
    dists = [_key_freq_distribution(keys[s : s + window], top_k) for s in starts]
    js_scores = [_js_divergence(dists[i], dists[i + 1]) for i in range(len(dists) - 1)]
    if not js_scores:
        return [], [], 0.0
    threshold = float(np.percentile(js_scores, percentile))
    changepoints = [starts[i + 1] for i, s in enumerate(js_scores) if s > threshold]
    return changepoints, js_scores, threshold


def validate_changepoint_detector_on_synthetic() -> dict:
    """Sanity check per testing_plan step 3: run the SAME detector on a synthetic
    trace with KNOWN injected drift events, and report recall/precision against
    ground truth (with a generous tolerance window) before trusting it on the
    unlabeled real Twitter trace."""
    tr = base.make_zipf_drift_trace(
        N_REQUESTS_MAIN, KEY_SPACE, ALPHA, n_drift_events=8, drift_magnitude=0.2, burst_prob=0.5, seed=777
    )
    cps, js_scores, threshold = detect_changepoints(tr.keys)
    true_events = tr.drift_indices
    tolerance = CP_WINDOW + CP_STRIDE
    matched_true = 0
    for te in true_events:
        if any(abs(te - cp) <= tolerance for cp in cps):
            matched_true += 1
    recall = matched_true / len(true_events) if true_events else None
    matched_detected = 0
    for cp in cps:
        if any(abs(te - cp) <= tolerance for te in true_events):
            matched_detected += 1
    precision = matched_detected / len(cps) if cps else None
    result = {
        "n_true_drift_events": len(true_events),
        "n_detected_changepoints": len(cps),
        "tolerance_requests": tolerance,
        "recall": recall,
        "precision": precision,
        "threshold": threshold,
        "verdict": (
            "DETECTOR_VALIDATED_ON_SYNTHETIC"
            if (recall is not None and recall > 0.3)
            else "DETECTOR_LOW_RECALL_TREAT_REAL_TRACE_CHANGEPOINTS_AS_WEAK_SIGNAL"
        ),
    }
    logger.info(f"Changepoint detector synthetic validation: {result}")
    return result


def run_part_b() -> dict:
    if not REAL_TRACE_PATH.exists():
        raise FileNotFoundError(f"Real Twitter trace not found at {REAL_TRACE_PATH}")

    int_keys, string_keys, request_types = load_real_trace_keys(REAL_TRACE_PATH)
    n_distinct = int(int_keys.max()) + 1
    real_cache_capacity = max(10, int(round(RATIO * n_distinct)))
    logger.info(f"Real trace: {n_distinct} distinct keys -> matched cache_capacity={real_cache_capacity} (ratio={RATIO})")

    replay = run_real_trace_replay(int_keys, real_cache_capacity)

    validation = validate_changepoint_detector_on_synthetic()

    logger.info("Running changepoint detection over the real trace's per-key request stream")
    cps, js_scores, threshold = detect_changepoints(int_keys)
    percentile_used = CP_PERCENTILE
    relaxation_log = []
    if len(cps) == 0:
        for p in (90.0, 85.0):
            cps, js_scores, threshold = detect_changepoints(int_keys, percentile=p)
            relaxation_log.append({"percentile_tried": p, "n_changepoints": len(cps)})
            percentile_used = p
            if cps:
                break
    logger.info(f"Detected {len(cps)} candidate changepoints at percentile={percentile_used} (threshold={threshold:.5f})")

    changepoint_recovery = {}
    for name in ["baseline_w_tinylfu", "per_key_decay"]:
        rolling = replay[name]["rolling_hit_ratio"]
        per_cp = []
        for cp in cps:
            pre_lo, pre_hi = max(0, cp - base.ROLLING_WINDOW), cp
            if pre_hi <= pre_lo:
                continue
            plateau = float(np.mean(rolling[pre_lo:pre_hi]))
            search_lo = cp + base.ROLLING_WINDOW
            post_hi = min(len(rolling), cp + CP_RECOVERY_LOOKAHEAD)
            if post_hi <= search_lo:
                continue
            window = rolling[search_lo:post_hi]
            trough = float(np.min(window))
            target = trough + base.RECOVERY_TARGET_FRAC * (plateau - trough)
            recovered = np.where(window >= target)[0]
            per_cp.append(
                {
                    "changepoint_index": int(cp),
                    "recovery_time": int(recovered[0]) + base.ROLLING_WINDOW if len(recovered) else CP_RECOVERY_LOOKAHEAD,
                    "censored": bool(len(recovered) == 0),
                }
            )
        changepoint_recovery[name] = per_cp

    # Strip the large in-process rolling arrays before JSON export
    for name in ["baseline_w_tinylfu", "per_key_decay"]:
        replay[name].pop("rolling_hit_ratio", None)

    return {
        "config": {
            "real_trace_path": "real_twitter_cache_trace",
            "trace_id": "twitter_cluster026",
            "n_requests": len(int_keys),
            "n_distinct_keys": n_distinct,
            "ratio": RATIO,
            "matched_cache_capacity": real_cache_capacity,
            "request_type_breakdown": dict(Counter(request_types)),
        },
        "replay_results": replay,
        "changepoint_detector": {
            "method": "rolling-window Jensen-Shannon divergence over top-K key-identity frequency distributions",
            "window": CP_WINDOW,
            "stride": CP_STRIDE,
            "top_k": CP_TOP_K,
            "percentile_threshold_used": percentile_used,
            "percentile_relaxation_log": relaxation_log,
            "synthetic_validation": validation,
            "n_changepoints_detected": len(cps),
            "changepoints": cps,
            "changepoint_threshold": threshold,
            "js_scores_summary": {
                "mean": float(np.mean(js_scores)) if js_scores else None,
                "max": float(np.max(js_scores)) if js_scores else None,
                "n_windows": len(js_scores),
            },
            "recovery_time_at_changepoints": changepoint_recovery,
            "caveat": (
                "UNSUPERVISED, coarse, unlabeled -- these are candidate drift points from a "
                "JS-divergence heuristic, NOT ground-truth drift events. Recovery-time numbers "
                "around them are suggestive, not confirmatory. Validated separately (see "
                "synthetic_validation) against KNOWN drift events on a synthetic trace of the "
                "same key-space/alpha before being applied here."
            ),
        },
    }


# ==========================================================================
# Main
# ==========================================================================


def main() -> None:
    t0 = time.time()
    logger.info("=" * 70)
    logger.info("Sharper baseline test + real Twitter trace replay")
    logger.info("=" * 70)

    logger.info("--- Part A: short-multiplier global-reset sweep at win-corner cell ---")
    part_a = run_part_a()
    gc.collect()

    logger.info("--- Part B: real Twitter production trace replay ---")
    part_b = run_part_b()
    gc.collect()

    logger.info("Assembling method_out.json")

    part_a_examples = []
    for r in part_a["per_run"]:
        part_a_examples.append(
            {
                "input": json.dumps(
                    {
                        "ratio": RATIO,
                        "alpha": ALPHA,
                        "scenario": r["scenario"],
                        "multiplier": r["multiplier"],
                        "seed": r["seed"],
                        "cache_capacity": CACHE_CAPACITY,
                    }
                ),
                "output": json.dumps(
                    {k: v for k, v in r.items() if k not in ("recovery_events", "scenario", "multiplier", "seed")}
                ),
                "metadata_recovery_events": r["recovery_events"],
                "predict_steady_state_hit_ratio": str(r["steady_state_hit_ratio"]),
                "predict_mean_recovery_time": str(r["mean_recovery_time"]),
            }
        )

    part_b_examples = [
        {
            "input": json.dumps({"phase": "real_trace_replay", "trace_id": "twitter_cluster026"}),
            "output": json.dumps(part_b),
            "predict_baseline_final_hit_ratio": str(part_b["replay_results"]["baseline_w_tinylfu"]["final_hit_ratio"]),
            "predict_per_key_decay_final_hit_ratio": str(part_b["replay_results"]["per_key_decay"]["final_hit_ratio"]),
        }
    ]

    summary_examples = [
        {
            "input": json.dumps({"phase": "aggregate_summary"}),
            "output": json.dumps(
                {
                    "part_a_head_to_head": part_a["head_to_head_vs_iter1_proposed"],
                    "part_a_aggregated": part_a["aggregated_by_scenario_multiplier"],
                    "part_a_summary": part_a["summary"],
                    "part_b_config": part_b["config"],
                    "part_b_replay_summary": {
                        name: {k: v for k, v in res.items() if k != "tier_assignment_fractions"}
                        for name, res in part_b["replay_results"].items()
                        if name != "_meta"
                    },
                    "part_b_changepoint_summary": {
                        k: v for k, v in part_b["changepoint_detector"].items() if k != "recovery_time_at_changepoints"
                    },
                }
            ),
        }
    ]

    output = {
        "metadata": {
            "method_name": "sharper_baseline_test_plus_real_twitter_trace_replay",
            "description": (
                "Extends iter1's W-TinyLFU cache-admission simulator: (A) sweeps very short "
                "global-reset multipliers (1x/2x/4x cache capacity) at the win-corner cell "
                "(ratio=0.01, alpha=1.2) across all 4 drift scenarios, the sharpest possible "
                "disconfirmation test of the per-key-decay mechanism's necessity; (B) replays "
                "both estimators end-to-end over the real Twitter production trace "
                "(twitter/cache-trace cluster026, 80,000 requests) with an unsupervised "
                "JS-divergence changepoint detector, validated on synthetic ground truth first."
            ),
            "part_a_config": part_a["config"],
            "part_b_config": part_b["config"],
            "deviations_from_plan": [
                "Real trace was available pre-decoded as JSON via this iteration's dataset "
                "dependency (unlike iter1, which could not source a lightweight decoder for "
                "twitter/cache-trace's binary format and skipped the real-trace arm entirely); "
                "no fallback needed for Part B's data access.",
                "String keys in the real trace are mapped to dense sequential int ids on first "
                "occurrence (the shared sketch/SLRU implementation is keyed on ints); this "
                "preserves per-key identity and access order exactly, only the key encoding "
                "changes.",
                "Real-trace baseline multiplier is tuned directly on the real trace itself via a "
                "single-pass sweep over iter1's {4,8,16,32} candidates (cheap at 80k requests x4), "
                "rather than reusing iter1's synthetic-trace-derived multiplier, since real "
                "traffic statistics may differ from the synthetic generator.",
                "Real trace has no wall-clock inter-arrival gaps needed for per-key CoV (the "
                "PerKeyDecayFrequencyEstimator uses request-sequence-position gaps internally, "
                "which iter1's implementation already does regardless of trace source, so no "
                "fallback to a seq-position proxy was required).",
            ],
            "total_runtime_seconds": time.time() - t0,
        },
        "datasets": [
            {"dataset": "partA_short_reset_sweep", "examples": part_a_examples},
            {"dataset": "partB_real_trace_replay", "examples": part_b_examples},
            {"dataset": "aggregate_summary", "examples": summary_examples},
        ],
    }

    out_path = WORKSPACE / "method_out.json"
    out_path.write_text(json.dumps(output, indent=2, default=str))
    logger.info(f"Wrote {out_path} ({out_path.stat().st_size/1e6:.2f} MB)")
    logger.info(f"Total runtime: {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
