#!/usr/bin/env python3
"""W-TinyLFU-style global-reset cache admission vs per-key-decay (full ring-buffer
and compressed EWMA) variants, evaluated on real + synthetic cache-access traces
with injected popularity drift. See gen_plan_experiment_1_idx1 for the full spec.
"""

from __future__ import annotations

import gc
import json
import math
import multiprocessing as mp
import resource
import sys
import time
from collections import OrderedDict, deque
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd
from loguru import logger

WORKDIR = Path(__file__).resolve().parent
DATASET_WS = Path(
    "/ai-inventor/aii_data/runs/run_0SmnUmg5PYNb/3_invention_loop/iter_1/gen_art/gen_art_dataset_1"
)
TEMP_DATASETS = DATASET_WS / "temp" / "datasets"
FULL_DATA_JSON = DATASET_WS / "full_data_out.json"
MANIFEST_JSON = TEMP_DATASETS / "manifest.json"

LOGS_DIR = WORKDIR / "logs"
RESULTS_DIR = WORKDIR / "results"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

logger.remove()
logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss}|{level:<7}|{message}")
logger.add(LOGS_DIR / "run.log", rotation="30 MB", level="DEBUG")

# ~28GB container RAM limit (see aii-use-hardware skill output); leave headroom.
resource.setrlimit(resource.RLIMIT_AS, (16 * 1024**3, 16 * 1024**3))
resource.setrlimit(resource.RLIMIT_CPU, (3 * 3600, 3 * 3600))

# ----------------------------------------------------------------------------
# Trace registry: the exact 10 traces used in full_data_out.json. We load the
# UNCAPPED per-trace CSVs from the dataset's temp/datasets/ workspace (not the
# 20,000-row-capped JSON) so drift recovery has full resolution, per the
# artifact plan's explicit preference. Falls back to the capped JSON if a CSV
# is missing.
# ----------------------------------------------------------------------------
TRACE_IDS = [
    "real_twitter_cache_trace_cluster026",
    "real_derived_wikipedia_pageviews_by_second",
    "synthetic_zipf_alpha0.8_control",
    "synthetic_zipf_alpha1.0_control",
    "synthetic_zipf_alpha1.2_control",
    "synthetic_zipf_alpha0.8_cold_key_burst_mag-high_freq-rare",
    "synthetic_zipf_alpha1.0_rank_reshuffle_mag-low_freq-rare",
    "synthetic_zipf_alpha1.0_cold_key_burst_mag-high_freq-rare",
    "synthetic_zipf_alpha1.2_rank_reshuffle_mag-high_freq-frequent",
    "synthetic_zipf_alpha1.2_cold_key_burst_mag-low_freq-frequent",
]

CACHE_RATIOS = [0.01, 0.05, 0.10]
SEEDS = [0, 1, 2, 3, 4]
SYSTEMS = [
    "global_reset_baseline_W8",
    "global_reset_baseline_best_tuned",
    "per_key_decay_full",
    "per_key_decay_compressed",
]
WC_CANDIDATES = [4, 8, 16, 32]
PROB_FRAC = 0.2
SHADOW_MULT = 4  # shadow-queue bound = capacity * SHADOW_MULT resident keys
DRIFT_WINDOW = 500
DRIFT_HORIZON = 3000
DRIFT_STRIDE = 100
LOG_STRIDE = 50

# Exact struct sizes (computed, not asserted) -- see memory accounting section.
_FULL_DTYPE = np.dtype([("last_arrival", "f8"), ("ring", "f4", (6,)), ("freq", "f8"), ("n_gaps", "i1")])
_COMPRESSED_DTYPE = np.dtype([("last_arrival", "f4"), ("ewma_mean", "f4"), ("ewma_var", "f4"), ("freq", "f2")])
PER_KEY_DECAY_FULL_BYTES = int(_FULL_DTYPE.itemsize)
PER_KEY_DECAY_COMPRESSED_BYTES = int(_COMPRESSED_DTYPE.itemsize)


def cms_bytes(w: int, d: int = 4) -> int:
    """4-bit saturating counters packed 2-per-byte + 1-bit doorkeeper + 8B global counter."""
    return math.ceil(d * w / 2) + math.ceil(w / 8) + 8


# ----------------------------------------------------------------------------
# Data loading
# ----------------------------------------------------------------------------
def load_manifest() -> dict:
    return json.loads(MANIFEST_JSON.read_text())


def load_trace(trace_id: str, manifest: dict, row_cap: int | None = None) -> dict:
    """Loads (key_id[int32], arrival_time[float64]) for a trace plus its metadata.

    Prefers the uncapped CSV in temp/datasets/; falls back to the 20,000-row
    capped full_data_out.json if the CSV is unavailable.
    """
    meta = manifest[trace_id]
    csv_path = TEMP_DATASETS / meta["file"]
    if csv_path.exists():
        df = pd.read_csv(csv_path, usecols=["key", "arrival_time"], dtype={"key": str})
        source = "uncapped_csv"
    else:
        logger.warning(f"{trace_id}: uncapped CSV missing, falling back to capped full_data_out.json")
        data = json.loads(FULL_DATA_JSON.read_text())
        ds = next(d for d in data["datasets"] if d["dataset"] == trace_id)
        rows = []
        for ex in ds["examples"]:
            rec = json.loads(ex["input"])
            rows.append((rec["key"], rec.get("arrival_time", rec.get("row_index", 0.0))))
        df = pd.DataFrame(rows, columns=["key", "arrival_time"])
        source = "capped_json_fallback"
    if row_cap is not None:
        df = df.iloc[:row_cap]
    codes, uniques = pd.factorize(df["key"].to_numpy(), sort=False)
    key_ids = codes.astype(np.int32)
    arrival_time = df["arrival_time"].to_numpy(dtype=np.float64)
    drift_event_list = meta.get("drift_event_list", [])
    if drift_event_list:
        types = {e["event_type"] for e in drift_event_list}
        drift_regime = "combined" if len(types) > 1 else next(iter(types))
    else:
        drift_regime = "none"
    trace_type = (
        "real_twitter" if trace_id.startswith("real_twitter") else
        "real_wikipedia" if trace_id.startswith("real_derived_wikipedia") else
        "synthetic_zipf"
    )
    return {
        "trace_id": trace_id,
        "key_ids": key_ids,
        "arrival_time": arrival_time,
        "num_unique_keys": int(len(uniques)),
        "num_requests": int(len(key_ids)),
        "alpha": meta.get("alpha"),
        "is_synthetic": bool(meta.get("is_synthetic", False)),
        "drift_scenario_id": meta.get("drift_scenario_id", "none"),
        "drift_regime": drift_regime,
        "drift_event_list": drift_event_list,
        "trace_type": trace_type,
        "data_source": source,
    }


# ----------------------------------------------------------------------------
# Core simulator components
# ----------------------------------------------------------------------------
class SLRU:
    """Segmented LRU: probationary (20% cap) + protected (80% cap).

    IDENTICAL eviction-policy object reused unmodified across all systems --
    only the frequency estimator supplied to on_miss()/promotion differs.
    """

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.prob_cap = max(1, int(round(capacity * PROB_FRAC)))
        self.prot_cap = max(1, capacity - self.prob_cap)
        self.protected: OrderedDict = OrderedDict()
        self.probationary: OrderedDict = OrderedDict()

    def _insert_probationary(self, k: int, freq_fn) -> bool:
        """Returns True if k was admitted (into probationary)."""
        if len(self.probationary) < self.prob_cap:
            self.probationary[k] = True
            return True
        victim = next(iter(self.probationary))
        victim_freq = freq_fn(victim)
        cand_freq = freq_fn(k)
        if cand_freq > victim_freq:
            del self.probationary[victim]
            self.probationary[k] = True
            return True
        return False

    def access(self, k: int, freq_fn) -> bool:
        """Returns True on hit; on miss, runs the admission test and returns False."""
        if k in self.protected:
            self.protected.move_to_end(k)
            return True
        if k in self.probationary:
            del self.probationary[k]
            if len(self.protected) >= self.prot_cap:
                demoted, _ = self.protected.popitem(last=False)
                self._insert_probationary(demoted, freq_fn)
            self.protected[k] = True
            return True
        self._insert_probationary(k, freq_fn)
        return False


class GlobalResetEstimator:
    """Count-Min Sketch (d=4) + 1-bit doorkeeper, exact TinyLFU global periodic halving."""

    def __init__(self, capacity: int, wc: int = 8, seed: int = 0):
        self.w = max(16, capacity * wc)
        self.d = 4
        self.counters = np.zeros((self.d, self.w), dtype=np.uint8)
        self.door = np.zeros(self.w, dtype=bool)
        self.W = max(1, 10 * capacity)
        self.count = 0
        rng = np.random.RandomState(seed)
        self.a = rng.randint(1, 2**31 - 1, size=self.d).astype(np.int64) | 1
        self.b = rng.randint(0, 2**31 - 1, size=self.d).astype(np.int64)
        self.door_a = int(rng.randint(1, 2**31 - 1)) | 1
        self.door_b = int(rng.randint(0, 2**31 - 1))
        self.bytes_used = cms_bytes(self.w, self.d)

    def _slots(self, key: int):
        return [int(((key * int(self.a[i]) + int(self.b[i])) & 0x7FFFFFFFFFFF) % self.w) for i in range(self.d)]

    def _door_slot(self, key: int) -> int:
        return int(((key * self.door_a + self.door_b) & 0x7FFFFFFFFFFF) % self.w)

    def on_request(self, key: int, now: float) -> None:
        ds = self._door_slot(key)
        if not self.door[ds]:
            self.door[ds] = True
        else:
            for i in range(self.d):
                s = ((key * int(self.a[i]) + int(self.b[i])) & 0x7FFFFFFFFFFF) % self.w
                if self.counters[i, s] < 15:
                    self.counters[i, s] += 1
            self.count += 1
            if self.count >= self.W:
                self.counters >>= 1
                self.door[:] = False
                self.count = 0

    def get_freq(self, key: int) -> float:
        ds = self._door_slot(key)
        base = 1.0 if self.door[ds] else 0.0
        mn = 15
        for i in range(self.d):
            s = ((key * int(self.a[i]) + int(self.b[i])) & 0x7FFFFFFFFFFF) % self.w
            v = int(self.counters[i, s])
            if v < mn:
                mn = v
        return float(mn) + base if (base or mn > 0) else 0.0


class PerKeyDecayFullEstimator:
    """45-byte-class per-key decay: 6-slot inter-arrival gap ring buffer + 3 CoV buckets."""

    def __init__(self, capacity: int, shadow_mult: int = SHADOW_MULT):
        self.shadow_cap = max(capacity * shadow_mult, capacity + 16)
        self.state: OrderedDict = OrderedDict()  # key -> [last_arrival, deque(gaps), freq]

    def on_request(self, key: int, now: float) -> None:
        if key in self.state:
            self.state.move_to_end(key)
            st = self.state[key]
            gap = now - st[0]
            st[0] = now
            gaps: deque = st[1]
            gaps.append(gap)
            if len(gaps) >= 3:
                arr = np.fromiter(gaps, dtype=np.float64)
                mean = float(arr.mean())
                std = float(arr.std())
                cov = std / mean if mean > 1e-12 else 0.0
                if cov < 0.5:
                    rate = 0.99
                elif cov > 1.5:
                    rate = 0.7
                else:
                    rate = 0.9
            else:
                rate = 0.9
            st[2] = st[2] * rate + 1.0
        else:
            if len(self.state) >= self.shadow_cap:
                self.state.popitem(last=False)
            self.state[key] = [now, deque(maxlen=6), 1.0]

    def get_freq(self, key: int) -> float:
        st = self.state.get(key)
        return st[2] if st is not None else 0.0

    def bytes_used(self) -> int:
        return len(self.state) * PER_KEY_DECAY_FULL_BYTES

    def n_resident(self) -> int:
        return len(self.state)


class PerKeyDecayCompressedEstimator:
    """O(1)-state per-key decay: streaming EWMA mean/var, continuous CoV->decay-rate map."""

    ALPHA = 0.2
    EPS = 1e-9

    def __init__(self, capacity: int, shadow_mult: int = SHADOW_MULT):
        self.shadow_cap = max(capacity * shadow_mult, capacity + 16)
        self.state: OrderedDict = OrderedDict()  # key -> [last_arrival, mean, var, freq]
        self.cov_samples: list[float] = []  # for degenerate-behavior diagnostics

    @staticmethod
    def _decay_rate(cov: float) -> float:
        return float(np.clip(0.99 - 0.25 * min(cov, 1.5), 0.55, 0.99))

    def on_request(self, key: int, now: float) -> None:
        if key in self.state:
            self.state.move_to_end(key)
            st = self.state[key]
            gap = now - st[0]
            st[0] = now
            mean = st[1]
            var = st[2]
            new_mean = mean + self.ALPHA * (gap - mean)
            new_var = (1 - self.ALPHA) * (var + self.ALPHA * (gap - mean) ** 2)
            st[1] = new_mean
            st[2] = new_var
            cov = math.sqrt(max(new_var, 0.0)) / max(new_mean, self.EPS)
            if len(self.cov_samples) < 20000:
                self.cov_samples.append(cov)
            rate = self._decay_rate(cov)
            st[3] = st[3] * rate + 1.0
        else:
            if len(self.state) >= self.shadow_cap:
                self.state.popitem(last=False)
            self.state[key] = [now, 0.0, 0.0, 1.0]

    def get_freq(self, key: int) -> float:
        st = self.state.get(key)
        return st[3] if st is not None else 0.0

    def bytes_used(self) -> int:
        return len(self.state) * PER_KEY_DECAY_COMPRESSED_BYTES

    def n_resident(self) -> int:
        return len(self.state)


# ----------------------------------------------------------------------------
# One config simulation
# ----------------------------------------------------------------------------
def simulate(key_ids: np.ndarray, arrival_time: np.ndarray, capacity: int, system: str, seed: int, wc: int = 8):
    n = len(key_ids)
    hits = np.zeros(n, dtype=bool)
    slru = SLRU(capacity)

    if system in ("global_reset_baseline_W8", "global_reset_baseline_best_tuned"):
        est = GlobalResetEstimator(capacity, wc=wc, seed=seed)
        mem_bytes = est.bytes_used
        n_resident = est.w
    elif system == "per_key_decay_full":
        est = PerKeyDecayFullEstimator(capacity)
        mem_bytes = None
        n_resident = None
    elif system == "per_key_decay_compressed":
        est = PerKeyDecayCompressedEstimator(capacity)
        mem_bytes = None
        n_resident = None
    else:
        raise ValueError(f"unknown system {system}")

    freq_fn = est.get_freq
    for i in range(n):
        k = int(key_ids[i])
        t = float(arrival_time[i])
        est.on_request(k, t)
        hits[i] = slru.access(k, freq_fn)

    if mem_bytes is None:
        mem_bytes = est.bytes_used()
        n_resident = est.n_resident()

    cov_samples = getattr(est, "cov_samples", None)
    return hits, mem_bytes, n_resident, cov_samples


# ----------------------------------------------------------------------------
# Drift recovery analysis
# ----------------------------------------------------------------------------
def analyze_drift(hits: np.ndarray, drift_event_list: list[dict]) -> list[dict]:
    n = len(hits)
    prefix = np.concatenate(([0.0], np.cumsum(hits.astype(np.float64))))

    def windowed(idx: int, window: int = DRIFT_WINDOW) -> float:
        idx = min(idx, n)
        lo = max(0, idx - window)
        denom = idx - lo
        return float((prefix[idx] - prefix[lo]) / denom) if denom > 0 else float("nan")

    results = []
    for event in drift_event_list:
        start_idx = int(event["start_index"])
        end_idx = int(event["end_index"])
        if start_idx >= n:
            continue
        pre_drift_optimal = windowed(start_idx, DRIFT_WINDOW)
        horizon_end = min(end_idx + DRIFT_HORIZON, n)
        series_idx = list(range(end_idx, horizon_end + 1, DRIFT_STRIDE))
        series = [windowed(idx, DRIFT_WINDOW) for idx in series_idx] if series_idx else []
        post_drift_optimal = float(np.nanmean(series[-5:])) if len(series) >= 1 else pre_drift_optimal

        censored = False
        if post_drift_optimal >= pre_drift_optimal:
            threshold = 0.9 * post_drift_optimal
            cond = lambda v: v >= threshold  # noqa: E731
        else:
            threshold = 1.1 * post_drift_optimal
            cond = lambda v: v <= threshold  # noqa: E731

        recovery_time = None
        for idx in range(end_idx, horizon_end + 1, DRIFT_STRIDE):
            if cond(windowed(idx, DRIFT_WINDOW)):
                recovery_time = idx - end_idx
                break
        if recovery_time is None:
            recovery_time = horizon_end - end_idx
            censored = (horizon_end < end_idx + DRIFT_HORIZON) or True
            if horizon_end >= end_idx + DRIFT_HORIZON:
                censored = True

        results.append({
            "event_id": event.get("event_id"),
            "event_type": event.get("event_type"),
            "start_index": start_idx,
            "end_index": end_idx,
            "pre_drift_optimal_hit_ratio": pre_drift_optimal,
            "post_drift_optimal_hit_ratio": post_drift_optimal,
            "recovery_time": recovery_time,
            "recovery_censored": bool(censored),
        })
    return results


def windowed_series(hits: np.ndarray, stride: int = LOG_STRIDE, window: int = DRIFT_WINDOW) -> list[float]:
    n = len(hits)
    prefix = np.concatenate(([0.0], np.cumsum(hits.astype(np.float64))))
    out = []
    for idx in range(stride, n + 1, stride):
        lo = max(0, idx - window)
        denom = idx - lo
        out.append(float((prefix[idx] - prefix[lo]) / denom) if denom > 0 else 0.0)
    return out


# ----------------------------------------------------------------------------
# Best-tuned baseline W/C selection (tuned once per (trace, cache_ratio), not per seed)
# ----------------------------------------------------------------------------
def tune_best_wc(key_ids: np.ndarray, arrival_time: np.ndarray, capacity: int, tune_seed: int = 0) -> int:
    """Picks W/C in WC_CANDIDATES minimizing hit-ratio loss on the stationary
    (first-20%) portion of the stream, per the hypothesis's own success criterion."""
    n = len(key_ids)
    tune_n = max(1000, int(0.2 * n))
    kk = key_ids[:tune_n]
    tt = arrival_time[:tune_n]
    best_wc, best_hr = WC_CANDIDATES[0], -1.0
    for wc in WC_CANDIDATES:
        hits, _, _, _ = simulate(kk, tt, capacity, "global_reset_baseline_W8", tune_seed, wc=wc)
        hr = float(hits.mean()) if len(hits) else 0.0
        if hr > best_hr:
            best_hr = hr
            best_wc = wc
    return best_wc


# ----------------------------------------------------------------------------
# Worker: run all systems for one (trace, cache_ratio, seed)
# ----------------------------------------------------------------------------
def run_one_trace_ratio_seed(args) -> list[dict]:
    trace_id, key_ids, arrival_time, num_unique_keys, drift_event_list, trace_meta, cache_ratio, seed, best_wc_cache = args
    capacity = max(1, int(round(cache_ratio * num_unique_keys)))
    out = []
    for system in SYSTEMS:
        wc = 8
        if system == "global_reset_baseline_best_tuned":
            wc = best_wc_cache[(trace_id, cache_ratio)]
        t0 = time.time()
        hits, mem_bytes, n_resident, cov_samples = simulate(key_ids, arrival_time, capacity, system, seed, wc=wc)
        elapsed = time.time() - t0
        drift_results = analyze_drift(hits, drift_event_list)
        series = windowed_series(hits)
        overall_hit_ratio = float(hits.mean()) if len(hits) else 0.0
        tail_n = max(1, int(0.1 * len(hits)))
        steady_state_hit_ratio = float(hits[-tail_n:].mean()) if len(hits) else 0.0
        cov_summary = None
        if cov_samples:
            arr = np.array(cov_samples)
            cov_summary = {
                "mean": float(arr.mean()),
                "std": float(arr.std()),
                "p10": float(np.percentile(arr, 10)),
                "p50": float(np.percentile(arr, 50)),
                "p90": float(np.percentile(arr, 90)),
                "n_samples": int(len(arr)),
            }
        out.append({
            "trace_id": trace_id,
            "trace_type": trace_meta["trace_type"],
            "drift_regime": trace_meta["drift_regime"],
            "alpha": trace_meta["alpha"],
            "is_synthetic": trace_meta["is_synthetic"],
            "data_source": trace_meta["data_source"],
            "cache_ratio": cache_ratio,
            "cache_capacity": capacity,
            "seed": seed,
            "system": system,
            "wc_used": wc if "baseline" in system else None,
            "num_requests": int(len(key_ids)),
            "num_unique_keys": int(num_unique_keys),
            "overall_hit_ratio": overall_hit_ratio,
            "steady_state_hit_ratio": steady_state_hit_ratio,
            "memory_bytes": int(mem_bytes),
            "memory_n_resident_keys_or_slots": int(n_resident),
            "windowed_hit_ratio_series_stride50": series,
            "drift_events": drift_results,
            "cov_distribution": cov_summary,
            "sim_elapsed_seconds": elapsed,
        })
    return out


# ----------------------------------------------------------------------------
# Aggregation helpers
# ----------------------------------------------------------------------------
def bootstrap_ci(values: list[float], n_resamples: int = 1000, seed: int = 0):
    if not values:
        return None
    arr = np.array(values, dtype=np.float64)
    rng = np.random.RandomState(seed)
    if len(arr) == 1:
        return {"mean": float(arr[0]), "ci_lo": float(arr[0]), "ci_hi": float(arr[0]), "n": 1}
    means = np.empty(n_resamples)
    for b in range(n_resamples):
        idx = rng.randint(0, len(arr), size=len(arr))
        means[b] = arr[idx].mean()
    return {
        "mean": float(arr.mean()),
        "ci_lo": float(np.percentile(means, 2.5)),
        "ci_hi": float(np.percentile(means, 97.5)),
        "n": int(len(arr)),
    }


def aggregate(config_results: list[dict]) -> dict:
    by_key = {}
    for r in config_results:
        by_key.setdefault(r["trace_id"], {}).setdefault(r["cache_ratio"], {}).setdefault(r["seed"], {})[r["system"]] = r

    hit_delta_groups: dict[tuple, list[float]] = {}
    equivalence_flags: list[bool] = []
    memory_ratios: dict[str, list[float]] = {"per_key_decay_full": [], "per_key_decay_compressed": []}
    recovery_groups: dict[tuple, list[float]] = {}

    for trace_id, by_ratio in by_key.items():
        for cache_ratio, by_seed in by_ratio.items():
            for seed, by_system in by_seed.items():
                if "global_reset_baseline_best_tuned" not in by_system:
                    continue
                baseline = by_system["global_reset_baseline_best_tuned"]
                for system in ("per_key_decay_full", "per_key_decay_compressed", "global_reset_baseline_W8"):
                    if system not in by_system:
                        continue
                    r = by_system[system]
                    delta = r["steady_state_hit_ratio"] - baseline["steady_state_hit_ratio"]
                    key = (r["trace_type"], r["drift_regime"], system)
                    hit_delta_groups.setdefault(key, []).append(delta)
                    if system.startswith("per_key_decay"):
                        equivalence_flags.append(abs(delta) <= 0.01)
                        memory_ratios[system].append(r["memory_bytes"] / max(baseline["memory_bytes"], 1))
                    for ev in r["drift_events"]:
                        rk = (r["drift_regime"], system)
                        recovery_groups.setdefault(rk, []).append(float(ev["recovery_time"]))

    hit_delta_ci = {
        f"{k[0]}|{k[1]}|{k[2]}": bootstrap_ci(v) for k, v in hit_delta_groups.items()
    }
    recovery_ci = {
        f"{k[0]}|{k[1]}": bootstrap_ci(v) for k, v in recovery_groups.items()
    }
    memory_ratio_summary = {
        sys_name: (float(np.mean(vals)) if vals else None) for sys_name, vals in memory_ratios.items()
    }
    equivalence_fraction = float(np.mean(equivalence_flags)) if equivalence_flags else None

    return {
        "steady_state_hit_ratio_delta_vs_best_tuned_baseline_by_group": hit_delta_ci,
        "recovery_time_by_drift_regime_and_system": recovery_ci,
        "memory_ratio_to_baseline_mean": memory_ratio_summary,
        "fraction_configs_within_1pp_equivalence_margin": equivalence_fraction,
        "n_config_results": len(config_results),
    }


# ----------------------------------------------------------------------------
# Main driver: gradual scaling per aii-long-running-tasks
# ----------------------------------------------------------------------------
def build_grid(trace_ids: list[str], cache_ratios: list[float], seeds: list[int]):
    grid = []
    for tid in trace_ids:
        for cr in cache_ratios:
            for sd in seeds:
                grid.append((tid, cr, sd))
    return grid


def main():
    logger.info("Loading manifest and traces")
    manifest = load_manifest()

    stage = sys.argv[1] if len(sys.argv) > 1 else "full"
    row_cap = None
    if stage == "mini":
        trace_ids, cache_ratios, seeds, row_cap = TRACE_IDS[:1], [0.05], [0], 2000
    elif stage == "smoke":
        trace_ids, cache_ratios, seeds, row_cap = TRACE_IDS, [0.05], [0], None
    else:
        trace_ids, cache_ratios, seeds = TRACE_IDS, CACHE_RATIOS, SEEDS

    logger.info(f"Stage={stage}: {len(trace_ids)} traces x {len(cache_ratios)} ratios x {len(seeds)} seeds x {len(SYSTEMS)} systems")

    traces = {}
    for tid in trace_ids:
        t0 = time.time()
        tr = load_trace(tid, manifest, row_cap=row_cap)
        logger.info(f"Loaded {tid}: {tr['num_requests']} requests, {tr['num_unique_keys']} unique keys, source={tr['data_source']} ({time.time()-t0:.1f}s)")
        traces[tid] = tr

    logger.info("Tuning best W/C per (trace, cache_ratio) on stationary 20% prefix")
    best_wc_cache = {}
    for tid in trace_ids:
        tr = traces[tid]
        for cr in cache_ratios:
            capacity = max(1, int(round(cr * tr["num_unique_keys"])))
            wc = tune_best_wc(tr["key_ids"], tr["arrival_time"], capacity)
            best_wc_cache[(tid, cr)] = wc
            logger.debug(f"{tid} cr={cr}: best_wc={wc}")

    grid = build_grid(trace_ids, cache_ratios, seeds)
    logger.info(f"Grid size: {len(grid)} (trace,ratio,seed) tuples -> {len(grid)*len(SYSTEMS)} total system runs")

    checkpoint_path = RESULTS_DIR / f"config_results_{stage}.jsonl"
    checkpoint_path.write_text("")  # fresh checkpoint per run

    n_cpus = 6  # cgroup-detected in aii-use-hardware step; leave 0 margin since sim is short-lived per task
    max_workers = max(1, n_cpus - 1)
    tasks = []
    for (tid, cr, sd) in grid:
        tr = traces[tid]
        tasks.append((
            tid, tr["key_ids"], tr["arrival_time"], tr["num_unique_keys"], tr["drift_event_list"],
            {"trace_type": tr["trace_type"], "drift_regime": tr["drift_regime"], "alpha": tr["alpha"],
             "is_synthetic": tr["is_synthetic"], "data_source": tr["data_source"]},
            cr, sd, best_wc_cache,
        ))

    n_written = 0
    t_start = time.time()
    with ProcessPoolExecutor(max_workers=max_workers, mp_context=mp.get_context("spawn")) as pool:
        futures = {pool.submit(run_one_trace_ratio_seed, task): task for task in tasks}
        with open(checkpoint_path, "a") as fh:
            for fut in as_completed(futures):
                task = futures[fut]
                try:
                    results = fut.result()
                except Exception:
                    logger.exception(f"Config failed: trace={task[0]} ratio={task[6]} seed={task[7]}")
                    continue
                for r in results:
                    fh.write(json.dumps(r) + "\n")
                    n_written += 1
                fh.flush()
                if n_written % (len(SYSTEMS) * 5) == 0:
                    elapsed = time.time() - t_start
                    logger.info(f"Checkpointed {n_written} results ({elapsed:.1f}s elapsed)")

    logger.info(f"Simulation complete: {n_written} results written to {checkpoint_path} in {time.time()-t_start:.1f}s")

    expected = len(grid) * len(SYSTEMS)
    if n_written != expected:
        logger.warning(f"Result count mismatch: expected {expected}, got {n_written} -- some configs may have failed")

    config_results = [json.loads(line) for line in checkpoint_path.read_text().splitlines() if line.strip()]
    logger.info(f"Read back {len(config_results)} checkpointed results")

    aggregates = aggregate(config_results)

    memory_accounting = {
        "baseline_sketch_bytes_formula": "ceil(d*w/2) + ceil(w/8) + 8, d=4, w=capacity*W/C",
        "per_key_decay_full_bytes_per_resident_key": PER_KEY_DECAY_FULL_BYTES,
        "per_key_decay_full_struct": {"last_arrival_f8": 8, "ring_f4x6": 24, "freq_f8": 8, "n_gaps_i1": 1, "itemsize_with_padding": PER_KEY_DECAY_FULL_BYTES},
        "per_key_decay_compressed_bytes_per_resident_key": PER_KEY_DECAY_COMPRESSED_BYTES,
        "per_key_decay_compressed_struct": {"last_arrival_f4": 4, "ewma_mean_f4": 4, "ewma_var_f4": 4, "freq_f2": 2, "itemsize_with_padding": PER_KEY_DECAY_COMPRESSED_BYTES},
        "compressed_vs_full_byte_ratio": PER_KEY_DECAY_COMPRESSED_BYTES / PER_KEY_DECAY_FULL_BYTES,
        "shadow_queue_basis": f"per-key-decay memory is accounted per SHADOW-QUEUE-RESIDENT key only (LRU-bounded to capacity*{SHADOW_MULT}), not full key space",
        "memory_ratio_to_baseline_mean": aggregates["memory_ratio_to_baseline_mean"],
    }

    methodology_notes = {
        "row_cap_used": row_cap,
        "traces_used": trace_ids,
        "cache_ratios_used": cache_ratios,
        "seeds_used": seeds,
        "systems_used": SYSTEMS,
        "expected_grid_size": expected,
        "actual_grid_size": len(config_results),
        "missing_configs": expected - len(config_results),
        "best_wc_per_trace_ratio": {f"{k[0]}|{k[1]}": v for k, v in best_wc_cache.items()},
        "data_sources_used": {tid: traces[tid]["data_source"] for tid in trace_ids},
        "recovery_time_censoring_note": "recovery_time is censored (recovery_censored=true) if the trailing-window hit ratio never reaches the recovery threshold within the DRIFT_HORIZON=3000-step post-event window, OR if the trace ends before the horizon is reached (uncapped CSVs used where available, so trace-boundary censoring should be rare but is still flagged)",
    }

    output = {
        "metadata": {
            "method_name": "cache_admission_global_reset_vs_per_key_decay",
            "description": "W-TinyLFU-style Count-Min-Sketch global-reset admission (W/C=8 fixed and best-tuned) vs two per-key exponential-decay frequency estimators (full 6-slot gap-ring-buffer, and a compressed O(1) EWMA variant) for cache admission under skewed and drifting key popularity, evaluated on 2 real and 8 synthetic Zipf traces.",
            "parameters": {
                "cache_ratios": cache_ratios,
                "seeds": seeds,
                "wc_candidates": WC_CANDIDATES,
                "prob_frac": PROB_FRAC,
                "shadow_mult": SHADOW_MULT,
                "drift_window": DRIFT_WINDOW,
                "drift_horizon": DRIFT_HORIZON,
            },
            "methodology_notes": methodology_notes,
        },
        "datasets": [
            {
                "dataset": "config_results",
                "examples": [
                    {
                        "input": json.dumps({
                            "trace_id": r["trace_id"], "cache_ratio": r["cache_ratio"],
                            "seed": r["seed"], "system": r["system"], "cache_capacity": r["cache_capacity"],
                        }),
                        "output": json.dumps(r),
                        "metadata_trace_id": r["trace_id"],
                        "metadata_trace_type": r["trace_type"],
                        "metadata_drift_regime": r["drift_regime"],
                        "metadata_system": r["system"],
                        "metadata_cache_ratio": r["cache_ratio"],
                        "metadata_seed": r["seed"],
                        f"predict_{r['system']}": json.dumps({
                            "overall_hit_ratio": r["overall_hit_ratio"],
                            "steady_state_hit_ratio": r["steady_state_hit_ratio"],
                            "memory_bytes": r["memory_bytes"],
                        }),
                    }
                    for r in config_results
                ],
            },
            {
                "dataset": "aggregates",
                "examples": [{
                    "input": "aggregate_summary_request",
                    "output": json.dumps(aggregates),
                    "predict_cache_admission_aggregates": json.dumps(aggregates),
                }],
            },
            {
                "dataset": "memory_accounting",
                "examples": [{
                    "input": "memory_accounting_request",
                    "output": json.dumps(memory_accounting),
                    "predict_cache_admission_memory_accounting": json.dumps(memory_accounting),
                }],
            },
        ],
    }

    out_path = WORKDIR / f"method_out.json" if stage == "full" else WORKDIR / f"method_out_{stage}.json"
    out_path.write_text(json.dumps(output, indent=2))
    logger.info(f"Wrote {out_path} ({out_path.stat().st_size/1e6:.2f} MB)")


if __name__ == "__main__":
    main()
