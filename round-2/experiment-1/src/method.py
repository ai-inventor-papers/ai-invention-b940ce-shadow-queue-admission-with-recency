#!/usr/bin/env python3
"""Ablation: what actually broke per-key cache decay.

Attributes the prior iteration's per-key-decay drift-recovery deficit to
three candidate causes by running a 5-arm ablation over the SAME simulator:

  baseline      -- plain W-TinyLFU (Count-Min sketch + doorkeeper + periodic
                    global halving), no decay classifier at all.
  full          -- the original per-key-decay variant: CV-based online
                    volatility classifier + hashed (collision-prone) per-slot
                    decay-state storage.
  oracle_only   -- CV classifier replaced by a look-ahead "oracle" label,
                    storage still hashed.  Isolates the classifier's
                    contribution.
  unhashed_only -- CV classifier kept, storage switched to an exact
                    per-key dict (no collisions).  Isolates storage's
                    contribution.
  both_oracle   -- oracle label + exact per-key storage.  Upper-bound
                    ceiling: does the architecture win AT ALL once both
                    confounds are removed?

Consumes gen_art_dataset_1's full_data_out (10 traces: 9 synthetic Zipf
traces with injected drift + 1 real RetailRocket clickstream trace) --
the exact real-trace wiring the prior iteration silently failed to
exercise (0 rows consumed there; every row is consumed here).

Also reproduces the prior iteration's memory dual-accounting confound (two
conventions for pricing the shadow-queue's inter-arrival history buffer)
inside ONE codebase, and sweeps hashed-table size against collision rate.
"""

from __future__ import annotations

import gc
import hashlib
import json
import resource
import sys
import time
from collections import OrderedDict, deque
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from loguru import logger

np.seterr(over="ignore")

WORKDIR = Path(__file__).resolve().parent
LOG_DIR = WORKDIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

logger.remove()
logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss}|{level:<7}|{message}")
logger.add(LOG_DIR / "run.log", rotation="30 MB", level="DEBUG")

RAM_BUDGET_BYTES = 6 * 1024**3
resource.setrlimit(resource.RLIMIT_AS, (RAM_BUDGET_BYTES * 3, RAM_BUDGET_BYTES * 3))
resource.setrlimit(resource.RLIMIT_CPU, (3600 * 5, 3600 * 5))

NUM_WORKERS = 5
OUT_PATH = WORKDIR / "method_out.json"
DATA_DIR = WORKDIR / "full_data_out"

DEPTH = 4
CM_MAX = 15  # 4-bit saturating counter max
LOG_EVERY = 25

# --------------------------------------------------------------------------- #
# Hashing
# --------------------------------------------------------------------------- #

_SEEDS = np.array([0x9E3779B1, 0x85EBCA77, 0xC2B2AE3D, 0x27D4EB2F], dtype=np.uint64)


def hash_scalar(key: int, seed_idx: int, width: int) -> int:
    h = hashlib.blake2b(
        key.to_bytes(8, "little", signed=False) if key >= 0 else (-key - 1).to_bytes(8, "little"),
        digest_size=8,
        person=_SEEDS[seed_idx].tobytes()[:8],
    )
    return int.from_bytes(h.digest(), "little") % width


# --------------------------------------------------------------------------- #
# Baseline W-TinyLFU components (reused verbatim in behavior from the prior
# iteration's method.py -- art_.../iter_1 gen_art_experiment_1)
# --------------------------------------------------------------------------- #


class CountMinSketch:
    def __init__(self, width: int):
        self.width = width
        self.counters = np.zeros((DEPTH, width), dtype=np.uint8)

    def increment(self, key: int) -> None:
        for d in range(DEPTH):
            idx = hash_scalar(key, d, self.width)
            if self.counters[d, idx] < CM_MAX:
                self.counters[d, idx] += 1

    def estimate(self, key: int) -> int:
        return int(min(self.counters[d, hash_scalar(key, d, self.width)] for d in range(DEPTH)))

    def halve_all(self) -> None:
        self.counters >>= 1

    def memory_bytes(self) -> int:
        return self.counters.nbytes


class DoorkeeperBloom:
    def __init__(self, width_bits: int):
        self.width_bits = width_bits
        self.bits = np.zeros(width_bits, dtype=bool)

    def _idx(self, key: int, d: int) -> int:
        return hash_scalar(key, d, self.width_bits)

    def maybe_add(self, key: int) -> bool:
        present = all(self.bits[self._idx(key, d)] for d in range(2))
        for d in range(2):
            self.bits[self._idx(key, d)] = True
        return present

    def reset(self) -> None:
        self.bits[:] = False

    def memory_bytes(self) -> int:
        return self.bits.nbytes


N_BUCKETS = 3
HALF_LIVES = np.array([50_000.0, 5_000.0, 500.0], dtype=np.float64)
CV_THRESH = (0.5, 1.2)


def classify_cv_to_bucket(cv: float) -> int:
    if cv < CV_THRESH[0]:
        return 0
    if cv < CV_THRESH[1]:
        return 1
    return 2


DEFAULT_CV = 1.0


class ShadowQueue:
    """Bounded recent-miss history feeding CV to the online classifier."""

    def __init__(self, capacity: int, history_len: int = 8):
        self.capacity = capacity
        self.history_len = history_len
        self.timestamps: dict[int, deque] = {}
        self.order: deque = deque()

    def record_miss(self, key: int, t: int) -> float:
        if key not in self.timestamps:
            if len(self.timestamps) >= self.capacity:
                oldest = self.order.popleft()
                self.timestamps.pop(oldest, None)
            self.timestamps[key] = deque(maxlen=self.history_len)
            self.order.append(key)
        dq = self.timestamps[key]
        dq.append(t)
        if len(dq) < 3:
            return DEFAULT_CV
        arr = np.fromiter(dq, dtype=np.float64)
        gaps = np.diff(arr)
        gaps = gaps[gaps > 0]
        if gaps.size < 2:
            return DEFAULT_CV
        mean = gaps.mean()
        if mean <= 0:
            return DEFAULT_CV
        return float(gaps.std() / mean)

    def memory_bytes(self) -> int:
        return self.capacity * (8 + self.history_len * 8)


class SLRU:
    """Segmented LRU: 20% probationary / 80% protected."""

    def __init__(self, capacity: int, probation_frac: float = 0.2):
        self.capacity = capacity
        self.probation_cap = max(1, int(round(capacity * probation_frac)))
        self.protected_cap = capacity - self.probation_cap
        self.probation: OrderedDict[int, None] = OrderedDict()
        self.protected: OrderedDict[int, None] = OrderedDict()

    def contains(self, key: int) -> bool:
        return key in self.probation or key in self.protected

    def size(self) -> int:
        return len(self.probation) + len(self.protected)

    def is_full(self) -> bool:
        return self.size() >= self.capacity

    def promote_to_protected(self, key: int) -> None:
        if key in self.probation:
            del self.probation[key]
            self.protected[key] = None
            self.protected.move_to_end(key)
            if len(self.protected) > self.protected_cap:
                demoted, _ = self.protected.popitem(last=False)
                self.probation[demoted] = None
                self.probation.move_to_end(demoted)
        elif key in self.protected:
            self.protected.move_to_end(key)

    def admit_to_probation(self, key: int) -> None:
        self.probation[key] = None
        self.probation.move_to_end(key)

    def peek_victim(self) -> int | None:
        if self.probation:
            return next(iter(self.probation))
        if self.protected:
            return next(iter(self.protected))
        return None

    def evict(self, key: int) -> None:
        self.probation.pop(key, None)
        self.protected.pop(key, None)


# --------------------------------------------------------------------------- #
# Decay estimator: NOW parameterized by label_mode x storage_mode, the two
# confounds this ablation isolates.
# --------------------------------------------------------------------------- #


class DecayEstimator:
    def __init__(self, width: int, storage_mode: str, oracle_labels: dict[int, int] | None):
        self.width = width
        self.storage_mode = storage_mode  # 'hashed' | 'unhashed'
        self.oracle_labels = oracle_labels or {}
        self.touches = 0
        self.bucket_overwrites = 0
        self.bucket_assignment_counts = np.zeros(N_BUCKETS, dtype=np.int64)
        if storage_mode == "hashed":
            self.counters = np.zeros((DEPTH, width), dtype=np.float32)
            self.last_update_time = np.zeros((DEPTH, width), dtype=np.float32)
            self.decay_bucket_slot = np.zeros((DEPTH, width), dtype=np.uint8)
            self.slot_owner_key = -np.ones((DEPTH, width), dtype=np.int64)
        else:  # unhashed: exact per-key dicts, no collisions by construction
            self.counter: dict[int, float] = {}
            self.last_t: dict[int, float] = {}
            self.bucket: dict[int, int] = {}

    def _bucket_for(self, key: int, cv: float, label_mode: str) -> int:
        if label_mode == "oracle":
            return self.oracle_labels.get(key, 1)
        return classify_cv_to_bucket(cv)

    def touch(self, key: int, t: int, cv: float, label_mode: str) -> None:
        bucket = self._bucket_for(key, cv, label_mode)
        self.bucket_assignment_counts[bucket] += 1
        half_life = HALF_LIVES[bucket]
        self.touches += 1
        if self.storage_mode == "hashed":
            for d in range(DEPTH):
                idx = hash_scalar(key, d, self.width)
                owner = self.slot_owner_key[d, idx]
                if owner != -1 and owner != key:
                    self.bucket_overwrites += 1
                self.slot_owner_key[d, idx] = key
                dt = t - self.last_update_time[d, idx]
                if dt > 0:
                    self.counters[d, idx] *= 0.5 ** (dt / half_life)
                self.counters[d, idx] += 1.0
                self.last_update_time[d, idx] = t
                self.decay_bucket_slot[d, idx] = bucket
        else:
            prev_c = self.counter.get(key, 0.0)
            prev_t = self.last_t.get(key, t)
            dt = t - prev_t
            if dt > 0:
                prev_c *= 0.5 ** (dt / half_life)
            self.counter[key] = prev_c + 1.0
            self.last_t[key] = t
            self.bucket[key] = bucket

    def estimate(self, key: int, t: int) -> float:
        if self.storage_mode == "hashed":
            best = None
            for d in range(DEPTH):
                idx = hash_scalar(key, d, self.width)
                bucket = int(self.decay_bucket_slot[d, idx])
                half_life = HALF_LIVES[bucket]
                dt = t - self.last_update_time[d, idx]
                val = float(self.counters[d, idx]) * (0.5 ** (max(dt, 0) / half_life))
                best = val if best is None else min(best, val)
            return best if best is not None else 0.0
        else:
            if key not in self.counter:
                return 0.0
            bucket = self.bucket[key]
            half_life = HALF_LIVES[bucket]
            dt = t - self.last_t[key]
            return self.counter[key] * (0.5 ** (max(dt, 0) / half_life))

    def memory_bytes(self) -> int:
        if self.storage_mode == "hashed":
            return int(self.counters.nbytes + self.last_update_time.nbytes + self.decay_bucket_slot.nbytes)
        # per-key allocation: 8B key + 4B float32 counter + 4B float32 time + 1B bucket
        return len(self.counter) * (8 + 4 + 4 + 1)

    def collision_rate(self) -> float:
        return self.bucket_overwrites / self.touches if (self.touches and self.storage_mode == "hashed") else 0.0


ARMS = ["baseline", "full", "oracle_only", "unhashed_only", "both_oracle"]
ARM_LABEL_STORAGE = {
    "full": ("cv", "hashed"),
    "oracle_only": ("oracle", "hashed"),
    "unhashed_only": ("cv", "unhashed"),
    "both_oracle": ("oracle", "unhashed"),
}


def matched_widths(cache_capacity: int, shadow_capacity: int) -> tuple[int, int]:
    baseline_width = 65536
    baseline_per_width_bytes = DEPTH * 1 + 8
    baseline_bytes = baseline_per_width_bytes * baseline_width
    shadow_bytes = ShadowQueue(shadow_capacity).memory_bytes()
    decay_per_width_bytes = DEPTH * (4 + 4 + 1) + 8
    remaining = baseline_bytes - shadow_bytes
    decay_width = max(256, int(remaining / decay_per_width_bytes))
    return baseline_width, decay_width


def oracle_labels_from_cv_fulltrace(keys: np.ndarray) -> dict[int, int]:
    """Look-ahead 'oracle': full-trace inter-arrival CV per key, computed
    with knowledge of the WHOLE trace (unavailable to an online classifier).
    Documented as an upper-bound proxy, not a true ground-truth oracle."""
    df = pd.DataFrame({"k": keys, "t": np.arange(len(keys))})
    labels: dict[int, int] = {}
    for k, g in df.groupby("k")["t"]:
        arr = g.to_numpy(dtype=np.float64)
        if arr.size < 3:
            labels[int(k)] = 1
            continue
        gaps = np.diff(arr)
        gaps = gaps[gaps > 0]
        if gaps.size < 2:
            labels[int(k)] = 1
            continue
        mean = gaps.mean()
        cv = gaps.std() / mean if mean > 0 else 1.0
        labels[int(k)] = classify_cv_to_bucket(cv)
    return labels


def oracle_labels_from_tercile(keys: np.ndarray) -> dict[int, int]:
    """Coarser fallback oracle (fallback_plan item 3): bucket by empirical
    total-trace access-count tercile when a CV-based oracle degenerates
    (e.g. too few repeat visits per item)."""
    counts = pd.Series(keys).value_counts()
    q1, q2 = counts.quantile([1 / 3, 2 / 3])
    labels: dict[int, int] = {}
    for k, c in counts.items():
        if c <= q1:
            labels[int(k)] = 2  # rare -> treat as volatile/bursty
        elif c <= q2:
            labels[int(k)] = 1
        else:
            labels[int(k)] = 0  # frequent -> stable
    return labels


# --------------------------------------------------------------------------- #
# Core simulator
# --------------------------------------------------------------------------- #


def simulate(
    keys: np.ndarray,
    cache_capacity: int,
    arm: str,
    width: int,
    shadow_capacity: int,
    reset_W: int | None,
    oracle_labels: dict[int, int] | None,
) -> dict:
    n = len(keys)
    slru = SLRU(cache_capacity)
    shadow = ShadowQueue(capacity=shadow_capacity)
    doorkeeper = DoorkeeperBloom(width_bits=width * 8)

    if arm == "baseline":
        estimator: Any = CountMinSketch(width)
        label_mode = storage_mode = None
    else:
        label_mode, storage_mode = ARM_LABEL_STORAGE[arm]
        estimator = DecayEstimator(width, storage_mode, oracle_labels)

    hits = 0
    hit_series: list[list[float]] = []
    window_hits = deque(maxlen=2000)
    sample_counter = 0

    for t in range(n):
        key = int(keys[t])
        if slru.contains(key):
            hits += 1
            window_hits.append(1)
            slru.promote_to_protected(key)
        else:
            window_hits.append(0)
            if not slru.is_full():
                slru.admit_to_probation(key)
                if arm == "baseline":
                    doorkeeper.maybe_add(key)
                    estimator.increment(key)
                else:
                    cv = shadow.record_miss(key, t)
                    estimator.touch(key, t, cv, label_mode)
            else:
                victim = slru.peek_victim()
                if arm == "baseline":
                    seen_before = doorkeeper.maybe_add(key)
                    estimator.increment(key)
                    cand_est = estimator.estimate(key) if seen_before else 0
                    victim_est = estimator.estimate(victim)
                else:
                    cv = shadow.record_miss(key, t)
                    estimator.touch(key, t, cv, label_mode)
                    cand_est = estimator.estimate(key, t)
                    victim_est = estimator.estimate(victim, t)
                if cand_est > victim_est:
                    slru.evict(victim)
                    slru.admit_to_probation(key)

        if arm == "baseline" and reset_W:
            sample_counter += 1
            if sample_counter >= reset_W:
                estimator.halve_all()
                doorkeeper.reset()
                sample_counter = 0

        if t % LOG_EVERY == 0 and len(window_hits) > 0:
            hit_series.append([t, sum(window_hits) / len(window_hits)])

    mem = estimator.memory_bytes() + doorkeeper.memory_bytes()
    if arm != "baseline":
        mem += shadow.memory_bytes()

    result = {
        "steady_state_hit_ratio": hits / n,
        "hit_ratio_time_series": hit_series,
        "memory_bytes": int(mem),
    }
    if arm != "baseline":
        total_bucket = int(estimator.bucket_assignment_counts.sum())
        result["decay_bucket_assignment_stats"] = {
            "stable": float(estimator.bucket_assignment_counts[0] / total_bucket) if total_bucket else 0.0,
            "medium": float(estimator.bucket_assignment_counts[1] / total_bucket) if total_bucket else 0.0,
            "bursty": float(estimator.bucket_assignment_counts[2] / total_bucket) if total_bucket else 0.0,
        }
        result["decay_slot_collision_rate"] = estimator.collision_rate()
    return result


def compute_recovery_time(
    keys: np.ndarray,
    cache_capacity: int,
    arm: str,
    width: int,
    shadow_capacity: int,
    reset_W: int | None,
    oracle_labels: dict[int, int] | None,
    drift_time: int,
    threshold: float = 0.9,
) -> float | None:
    """First t>drift_time where the rolling hit ratio recrosses `threshold`
    of the post-drift-only converged optimum (estimated by re-simulating
    the post-drift segment in isolation)."""
    post_segment = keys[drift_time:]
    if len(post_segment) < 4000:
        return None
    post_result = simulate(post_segment, cache_capacity, arm, width, shadow_capacity, reset_W, oracle_labels)
    tail_start = int(len(post_segment) * 0.8)
    tail_series = [hr for t, hr in post_result["hit_ratio_time_series"] if t >= tail_start]
    optimal = float(np.mean(tail_series)) if tail_series else post_result["steady_state_hit_ratio"]
    target = threshold * optimal

    full_result = simulate(keys, cache_capacity, arm, width, shadow_capacity, reset_W, oracle_labels)
    for t, hr in full_result["hit_ratio_time_series"]:
        if t > drift_time and hr >= target:
            return float(t - drift_time)
    return None


# --------------------------------------------------------------------------- #
# Data loading
# --------------------------------------------------------------------------- #


def load_full_data_out() -> dict[str, np.ndarray]:
    """Load both full_data_out parts, group rows by dataset name, parse the
    input JSON strings, and return {dataset_name: keys_array}. Inspects the
    real schema directly (list under top-level 'datasets', each item
    {'dataset': name, 'examples': [{'input': '{"t":..,"k":..}', ...}, ...]})
    -- this is the exact field layout the prior iteration's wiring bug
    silently missed for real_retailrocket_events."""
    by_dataset: dict[str, list[tuple[int, int]]] = {}
    for part in ["full_data_out_1.json", "full_data_out_2.json"]:
        path = DATA_DIR / part
        logger.info(f"Loading {path} ...")
        with open(path) as f:
            blob = json.load(f)
        for ds in blob["datasets"]:
            name = ds["dataset"]
            rows = by_dataset.setdefault(name, [])
            for ex in ds["examples"]:
                rec = json.loads(ex["input"])
                rows.append((rec["t"], rec["k"]))
        del blob
        gc.collect()

    out: dict[str, np.ndarray] = {}
    for name, rows in by_dataset.items():
        rows.sort(key=lambda r: r[0])
        out[name] = np.array([k for _, k in rows], dtype=np.int64)
    return out


def load_drift_events(dataset_name: str) -> list[int]:
    """Scan full_data_out for metadata_drift_event rows belonging to
    `dataset_name` and return their request_index values, sorted."""
    events: set[int] = set()
    for part in ["full_data_out_1.json", "full_data_out_2.json"]:
        with open(DATA_DIR / part) as f:
            blob = json.load(f)
        for ds in blob["datasets"]:
            if ds["dataset"] != dataset_name:
                continue
            for ex in ds["examples"]:
                de = ex.get("metadata_drift_event")
                if de:
                    for ev in de:
                        events.add(int(ev["request_index"]))
        del blob
        gc.collect()
    return sorted(events)


# --------------------------------------------------------------------------- #
# Worker
# --------------------------------------------------------------------------- #


def _run_one_config(cfg: dict) -> dict:
    try:
        keys = cfg["keys"]
        n = len(keys)
        n_keys = int(keys.max()) + 1
        cache_ratio = cfg["cache_ratio"]
        arm = cfg["arm"]
        cache_capacity = max(8, int(round(n_keys * cache_ratio)))
        shadow_capacity = max(16, cache_capacity)
        baseline_width, decay_width = matched_widths(cache_capacity, shadow_capacity)
        table_size_mult = cfg.get("table_size_mult", 1.0)
        width = baseline_width if arm == "baseline" else int(decay_width * table_size_mult)
        reset_W = int(cache_capacity * 8) if arm == "baseline" else None

        oracle_labels = cfg.get("oracle_labels")

        t0 = time.perf_counter()
        sim_result = simulate(keys, cache_capacity, arm, width, shadow_capacity, reset_W, oracle_labels)
        elapsed = time.perf_counter() - t0

        drift_events = cfg.get("drift_events") or []
        recoveries = []
        for ev in drift_events:
            r = compute_recovery_time(keys, cache_capacity, arm, width, shadow_capacity, reset_W, oracle_labels, ev)
            if r is not None:
                recoveries.append(r)

        out = {
            "dataset_name": cfg["dataset_name"],
            "arm": arm,
            "cache_ratio": cache_ratio,
            "cache_capacity": cache_capacity,
            "table_size_mult": table_size_mult,
            "n_requests": n,
            "n_keys": n_keys,
            "steady_state_hit_ratio": sim_result["steady_state_hit_ratio"],
            "memory_bytes": sim_result["memory_bytes"],
            "n_drift_events_observed": len(drift_events),
            "mean_recovery_time_requests": float(np.mean(recoveries)) if recoveries else None,
            "recovery_times_per_event": recoveries,
            "elapsed_sec": elapsed,
            "hit_ratio_time_series": sim_result["hit_ratio_time_series"][::8],
        }
        if "decay_bucket_assignment_stats" in sim_result:
            out["decay_bucket_assignment_stats"] = sim_result["decay_bucket_assignment_stats"]
            out["decay_slot_collision_rate"] = sim_result["decay_slot_collision_rate"]
        return out
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc), "config_keys": list(cfg.keys())}


def block_bootstrap_ci(values: list[float], n_boot: int = 2000, seed: int = 0, block: int = 1) -> dict:
    """Bootstrap CI over a small set of point values (here: per-scenario or
    per-event repeats). With no per-run stochasticity in this deterministic
    simulator, seeds cannot vary the trace; CIs here resample across the
    available repeats (drift events / cache ratios) rather than across
    seeds, which is the honest thing to do for a deterministic sim."""
    vals = [v for v in values if v is not None and np.isfinite(v)]
    if not vals:
        return {"mean": None, "ci_low": None, "ci_high": None, "n": 0}
    arr = np.array(vals)
    if len(arr) == 1:
        return {"mean": float(arr[0]), "ci_low": float(arr[0]), "ci_high": float(arr[0]), "n": 1}
    rng = np.random.default_rng(seed)
    boots = [rng.choice(arr, size=len(arr), replace=True).mean() for _ in range(n_boot)]
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {"mean": float(arr.mean()), "ci_low": float(lo), "ci_high": float(hi), "n": len(arr)}


# --------------------------------------------------------------------------- #
# Unit tests
# --------------------------------------------------------------------------- #


def run_unit_tests() -> None:
    logger.info("Stage 1: unit/correctness tests")

    cms = CountMinSketch(width=1024)
    for _ in range(10):
        cms.increment(1001)
    for _ in range(3):
        cms.increment(2002)
    est_a, est_b = cms.estimate(1001), cms.estimate(2002)
    assert est_a >= 10 and est_b >= 3
    cms.halve_all()
    assert cms.estimate(1001) <= est_a
    logger.info(f"CMS OK: A {est_a}->{cms.estimate(1001)} B={est_b}")

    slru = SLRU(capacity=4, probation_frac=0.5)
    script = [1, 2, 3, 1, 2, 4, 1, 2, 5, 1]
    results = []
    for key in script:
        hit = slru.contains(key)
        results.append(hit)
        if hit:
            slru.promote_to_protected(key)
        else:
            if slru.is_full():
                slru.evict(slru.peek_victim())
            slru.admit_to_probation(key)
    assert results[0] is False and results[3] is True
    logger.info(f"SLRU OK: {results}")

    sq = ShadowQueue(capacity=100)
    for t in [0, 100, 200, 300, 400]:
        cv_reg = sq.record_miss(42, t)
    for t in [0, 5, 400, 410, 800]:
        cv_burst = sq.record_miss(43, t)
    assert cv_reg < cv_burst
    logger.info(f"ShadowQueue OK: regular={cv_reg:.3f} bursty={cv_burst:.3f}")

    # oracle_only must ignore CV entirely: force a wrong CV but oracle label wins
    dec_h = DecayEstimator(width=1024, storage_mode="hashed", oracle_labels={7: 2})
    dec_h.touch(7, t=0, cv=0.01, label_mode="oracle")  # cv says stable(0), oracle says bursty(2)
    assert dec_h.decay_bucket_slot[0, hash_scalar(7, 0, 1024)] == 2, "oracle label not applied"
    logger.info("oracle label_mode OK")

    # unhashed storage must never collide: two keys sharing a hashed slot
    # would collide under storage_mode='hashed' but not under 'unhashed'
    dec_u = DecayEstimator(width=4, storage_mode="unhashed", oracle_labels=None)
    for k in range(200):
        dec_u.touch(k, t=k, cv=0.1, label_mode="cv")
    assert dec_u.collision_rate() == 0.0, "unhashed storage must report zero collisions by construction"
    dec_h2 = DecayEstimator(width=4, storage_mode="hashed", oracle_labels=None)
    for k in range(200):
        dec_h2.touch(k, t=k, cv=0.1, label_mode="cv")
    assert dec_h2.collision_rate() > 0.0, "hashed storage at tiny width must show collisions"
    logger.info(f"storage_mode OK: unhashed_collision={dec_u.collision_rate():.4f} hashed_collision={dec_h2.collision_rate():.4f}")

    logger.info("Stage 1 PASSED")


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

SYNTH_DRIFT_SCENARIOS = ["rank_shuffle", "cold_burst", "combined", "slow_drift"]
CACHE_RATIOS = [0.01, 0.05]
REAL_NAME = "real_retailrocket_events"


def main() -> None:
    t_start = time.perf_counter()

    def elapsed() -> float:
        return time.perf_counter() - t_start

    run_unit_tests()

    logger.info("Stage 2: loading full_data_out (both parts)")
    by_dataset = load_full_data_out()
    for alpha_scenario in [f"synthetic_alpha1.0_{s}" for s in SYNTH_DRIFT_SCENARIOS] + [REAL_NAME]:
        assert alpha_scenario in by_dataset and len(by_dataset[alpha_scenario]) > 0, (
            f"{alpha_scenario} empty at load time -- data wiring bug"
        )
    for name, arr in by_dataset.items():
        logger.info(f"  {name}: {len(arr)} rows, {int(arr.max()) + 1} distinct-key-space (max_key+1)")
    assert len(by_dataset[REAL_NAME]) > 100_000, "real_retailrocket_events row count far below expected ~229,676"

    logger.info("Stage 3: precomputing drift-event indices + oracle labels")
    scenario_events = {s: load_drift_events(f"synthetic_alpha1.0_{s}") for s in SYNTH_DRIFT_SCENARIOS}
    for s, evs in scenario_events.items():
        logger.info(f"  synthetic_alpha1.0_{s}: {len(evs)} drift events at {evs}")

    scenario_oracle = {
        s: oracle_labels_from_cv_fulltrace(by_dataset[f"synthetic_alpha1.0_{s}"]) for s in SYNTH_DRIFT_SCENARIOS
    }
    real_oracle = oracle_labels_from_tercile(by_dataset[REAL_NAME])
    logger.info(f"real oracle (tercile fallback, per fallback_plan item 3): {len(real_oracle)} keys labeled")

    # --- Pilot: time a 5-run batch (1 scenario, 1 ratio) to sanity-check + extrapolate ---
    logger.info("Stage 4: pilot batch (5 arms x 1 scenario x 1 ratio)")
    pilot_scenario = "rank_shuffle"
    pilot_keys = by_dataset[f"synthetic_alpha1.0_{pilot_scenario}"]
    pilot_t0 = time.perf_counter()
    pilot_results = []
    for arm in ARMS:
        cfg = {
            "dataset_name": f"synthetic_alpha1.0_{pilot_scenario}",
            "arm": arm,
            "cache_ratio": 0.05,
            "keys": pilot_keys,
            "drift_events": scenario_events[pilot_scenario],
            "oracle_labels": scenario_oracle[pilot_scenario],
        }
        r = _run_one_config(cfg)
        assert "error" not in r, f"pilot arm={arm} failed: {r.get('error')}"
        pilot_results.append(r)
        logger.info(f"  arm={arm}: hit={r['steady_state_hit_ratio']:.4f} coll={r.get('decay_slot_collision_rate')}")
    pilot_wall = time.perf_counter() - pilot_t0
    # Sanity: unhashed_only/both_oracle must show ZERO collisions; full/oracle_only nonzero.
    by_arm = {r["arm"]: r for r in pilot_results}
    assert by_arm["unhashed_only"]["decay_slot_collision_rate"] == 0.0
    assert by_arm["both_oracle"]["decay_slot_collision_rate"] == 0.0
    assert by_arm["full"]["decay_slot_collision_rate"] > 0.0
    logger.info(f"Pilot batch OK, wall={pilot_wall:.1f}s for 5 runs")

    n_synth_configs = len(ARMS) * len(SYNTH_DRIFT_SCENARIOS) * len(CACHE_RATIOS)
    n_real_configs = len(ARMS) * len(CACHE_RATIOS)
    est_total_s = (pilot_wall / 5) * (n_synth_configs + n_real_configs) / NUM_WORKERS
    logger.info(f"Estimated remaining grid: {n_synth_configs}+{n_real_configs} configs, ~{est_total_s:.0f}s parallel")

    # --- Build full grid ---
    logger.info("Stage 5: building full grid")
    grid: list[dict] = []
    for scenario in SYNTH_DRIFT_SCENARIOS:
        ds_name = f"synthetic_alpha1.0_{scenario}"
        keys = by_dataset[ds_name]
        events = scenario_events[scenario]
        oracle = scenario_oracle[scenario]
        for ratio in CACHE_RATIOS:
            for arm in ARMS:
                grid.append(
                    {
                        "dataset_name": ds_name,
                        "arm": arm,
                        "cache_ratio": ratio,
                        "keys": keys,
                        "drift_events": events,
                        "oracle_labels": oracle,
                    }
                )
    for ratio in CACHE_RATIOS:
        for arm in ARMS:
            grid.append(
                {
                    "dataset_name": REAL_NAME,
                    "arm": arm,
                    "cache_ratio": ratio,
                    "keys": by_dataset[REAL_NAME],
                    "drift_events": [],
                    "oracle_labels": real_oracle,
                }
            )
    logger.info(f"Grid size: {len(grid)} configs (incl. pilot already run separately, not re-run)")

    logger.info("Stage 6: running grid (ProcessPoolExecutor)")
    results: list[dict] = list(pilot_results)  # keep pilot results, don't redo them
    remaining = [
        cfg for cfg in grid if not (cfg["dataset_name"] == f"synthetic_alpha1.0_{pilot_scenario}" and cfg["cache_ratio"] == 0.05)
    ]
    with ProcessPoolExecutor(max_workers=NUM_WORKERS) as ex:
        futs = {ex.submit(_run_one_config, cfg): cfg for cfg in remaining}
        done_ct = 0
        for fut in as_completed(futs):
            r = fut.result()
            if "error" in r:
                logger.error(f"config failed: {r}")
            else:
                results.append(r)
            done_ct += 1
            if done_ct % 10 == 0:
                logger.info(f"  {done_ct}/{len(remaining)} done, elapsed={elapsed():.0f}s")
    logger.info(f"Grid done: {len(results)} results, elapsed={elapsed():.0f}s")

    # --- Hashed table-size vs collision-rate sweep ---
    logger.info("Stage 7: hashed table-size vs collision-rate sweep")
    rep_scenario = "combined"
    rep_keys = by_dataset[f"synthetic_alpha1.0_{rep_scenario}"]
    rep_oracle = scenario_oracle[rep_scenario]
    table_sweep = []
    for mult in [0.5, 1.0, 2.0, 4.0]:
        cfg = {
            "dataset_name": f"synthetic_alpha1.0_{rep_scenario}",
            "arm": "full",
            "cache_ratio": 0.05,
            "keys": rep_keys,
            "drift_events": [],
            "oracle_labels": rep_oracle,
            "table_size_mult": mult,
        }
        r = _run_one_config(cfg)
        table_sweep.append(
            {
                "table_size_mult": mult,
                "collision_rate": r["decay_slot_collision_rate"],
                "steady_state_hit_ratio": r["steady_state_hit_ratio"],
                "memory_bytes": r["memory_bytes"],
            }
        )
        logger.info(f"  mult={mult}: collision={r['decay_slot_collision_rate']:.4f} hit={r['steady_state_hit_ratio']:.4f}")

    # --- Memory dual-accounting reconciliation ---
    logger.info("Stage 8: memory dual-accounting reconciliation")
    mem_cfg_keys = rep_keys
    mem_cfg_ratio = 0.05
    n_keys_mem = int(mem_cfg_keys.max()) + 1
    cache_capacity_mem = max(8, int(round(n_keys_mem * mem_cfg_ratio)))
    shadow_capacity_mem = max(16, cache_capacity_mem)
    baseline_width_mem, decay_width_mem = matched_widths(cache_capacity_mem, shadow_capacity_mem)

    base_sim = simulate(mem_cfg_keys, cache_capacity_mem, "baseline", baseline_width_mem, shadow_capacity_mem, cache_capacity_mem * 8, None)
    full_sim = simulate(mem_cfg_keys, cache_capacity_mem, "full", decay_width_mem, shadow_capacity_mem, None, rep_oracle)
    shadow_bytes_mem = ShadowQueue(shadow_capacity_mem).memory_bytes()

    decay_core_bytes = full_sim["memory_bytes"] - shadow_bytes_mem  # estimator+doorkeeper only
    mem_conventions = {}
    for convention in ["shared_with_sketch", "per_key"]:
        mem_bytes = decay_core_bytes if convention == "shared_with_sketch" else decay_core_bytes + shadow_bytes_mem
        mem_conventions[convention] = {
            "mem_bytes": int(mem_bytes),
            "baseline_sketch_bytes": int(base_sim["memory_bytes"]),
            "overhead_ratio_vs_plain_tinylfu": mem_bytes / base_sim["memory_bytes"],
        }
    logger.info(f"Memory conventions: {mem_conventions}")
    logger.info(
        "Prior iteration reported 0.003%% (matched-width design target) and 16.9x (from a separate simulator's "
        "accounting) for these two conventions; reconciled figures above -- reported as-measured, not forced to match."
    )

    # --- Attribution analysis ---
    logger.info("Stage 9: attribution analysis")
    by_key = {}
    for r in results:
        by_key.setdefault((r["dataset_name"], r["cache_ratio"]), {})[r["arm"]] = r

    attribution_table = {}
    for scenario in SYNTH_DRIFT_SCENARIOS:
        ds_name = f"synthetic_alpha1.0_{scenario}"
        attribution_table[scenario] = {}
        for ratio in CACHE_RATIOS:
            cell = by_key.get((ds_name, ratio), {})
            if not cell or "baseline" not in cell or "full" not in cell:
                continue

            def delta(metric: str, a: str, b: str) -> dict:
                va, vb = cell.get(a, {}).get(metric), cell.get(b, {}).get(metric)
                if va is None or vb is None:
                    return {"delta": None}
                return {"delta": va - vb, "a": va, "b": vb}

            attribution_table[scenario][str(ratio)] = {
                "full_vs_baseline_hit": delta("steady_state_hit_ratio", "full", "baseline"),
                "full_vs_baseline_recovery": delta("mean_recovery_time_requests", "full", "baseline"),
                "oracle_only_vs_full_recovery": delta("mean_recovery_time_requests", "oracle_only", "full"),
                "unhashed_only_vs_full_recovery": delta("mean_recovery_time_requests", "unhashed_only", "full"),
                "both_oracle_vs_full_recovery": delta("mean_recovery_time_requests", "both_oracle", "full"),
                "both_oracle_vs_baseline_recovery": delta("mean_recovery_time_requests", "both_oracle", "baseline"),
                "both_oracle_vs_baseline_hit": delta("steady_state_hit_ratio", "both_oracle", "baseline"),
            }

    # Headline verdict: does both_oracle beat baseline on recovery time in >=3/4 scenarios?
    # "beat" = strictly lower (faster) mean_recovery_time_requests, lower is better.
    wins = 0
    scenarios_evaluated = 0
    per_scenario_verdict = {}
    for scenario in SYNTH_DRIFT_SCENARIOS:
        cells = attribution_table.get(scenario, {})
        scenario_win = None
        for ratio_key, d in cells.items():
            dd = d["both_oracle_vs_baseline_recovery"]["delta"]
            if dd is not None:
                scenario_win = dd < 0
                break
        if scenario_win is not None:
            scenarios_evaluated += 1
            wins += int(scenario_win)
        per_scenario_verdict[scenario] = scenario_win
    headline_verdict = {
        "both_oracle_beats_baseline_recovery_n_scenarios": wins,
        "scenarios_evaluated": scenarios_evaluated,
        "threshold_required": 3,
        "verdict": "ARCHITECTURE_HAS_MERIT_ONCE_DECONFOUNDED" if wins >= 3 else "ARCHITECTURE_DOES_NOT_WIN_EVEN_DECONFOUNDED",
        "per_scenario": per_scenario_verdict,
    }
    logger.info(f"Headline verdict: {headline_verdict}")

    real_results = [r for r in results if r["dataset_name"] == REAL_NAME]
    real_summary = {}
    for arm in ARMS:
        arm_rows = [r for r in real_results if r["arm"] == arm]
        real_summary[arm] = {
            "hit_ratios_by_ratio": {str(r["cache_ratio"]): r["steady_state_hit_ratio"] for r in arm_rows},
            "n_real_requests_consumed": arm_rows[0]["n_requests"] if arm_rows else 0,
        }

    hit_ratio_ci = {}
    recovery_ci = {}
    for scenario in SYNTH_DRIFT_SCENARIOS:
        ds_name = f"synthetic_alpha1.0_{scenario}"
        for arm in ARMS:
            vals_hit = [
                r["steady_state_hit_ratio"] for r in results if r["dataset_name"] == ds_name and r["arm"] == arm
            ]
            vals_rec = [
                r["mean_recovery_time_requests"]
                for r in results
                if r["dataset_name"] == ds_name and r["arm"] == arm and r["mean_recovery_time_requests"] is not None
            ]
            hit_ratio_ci[f"{scenario}::{arm}"] = block_bootstrap_ci(vals_hit)
            recovery_ci[f"{scenario}::{arm}"] = block_bootstrap_ci(vals_rec)

    logger.info(f"Total wall clock: {elapsed():.0f}s")

    out = {
        "metadata": {
            "description": (
                "5-arm ablation (baseline, full, oracle_only, unhashed_only, both_oracle) attributing the prior "
                "iteration's per-key-decay drift-recovery deficit to the CV volatility classifier vs. hashed "
                "per-key storage collisions vs. the architecture itself, on synthetic drift traces (alpha=1.0, "
                "all 4 documented drift scenarios) plus the real RetailRocket trace consumed here for the first "
                "time (prior iteration had 0 real-trace rows wired in)."
            ),
            "grid_reduction_notes": (
                "Reduced from the plan's 375-config grid to a 60-config grid (5 arms x 4 scenarios x 2 cache_ratios "
                "for synthetic, plus 5 arms x 2 cache_ratios for real): alpha restricted to 1.0 (canonical, required), "
                "cache_ratios cut from 3 to 2 per fallback_plan item (c). Multi-seed repeats were dropped because "
                "this simulator is fully deterministic given the input trace (no RNG in the hot loop) -- the traces "
                "themselves are fixed by the upstream dataset, so re-running under a different 'seed' label would "
                "reproduce byte-identical results and waste compute; bootstrap CIs instead resample the available "
                "cache_ratio/scenario repeats, which is the honest substitute given a deterministic sim."
            ),
            "oracle_definition": (
                "Synthetic-trace oracle = full-trace look-ahead inter-arrival CV per key (upper-bound proxy, NOT a "
                "true ground-truth volatility label -- the dataset carries no injected per-key burst/stable tags, "
                "only drift-EVENT metadata). Real-trace oracle = access-count tercile (fallback_plan item 3), since "
                "a full-trace CV oracle degenerates for many low-repeat RetailRocket items."
            ),
            "baseline_reset_W": "cache_capacity * 8 (a reasonable fixed W-TinyLFU window size; NOT re-tuned via sweep "
            "in this reduced grid, since this direction's focus is confound attribution, not baseline sizing).",
            "headline_verdict": headline_verdict,
            "memory_dual_accounting": mem_conventions,
            "hashed_table_size_vs_collision_sweep": table_sweep,
            "attribution_table": attribution_table,
            "hit_ratio_bootstrap_ci": hit_ratio_ci,
            "recovery_time_bootstrap_ci": recovery_ci,
            "real_trace_summary": real_summary,
            "n_configs_run": len(results),
            "wall_clock_sec": elapsed(),
        },
        "datasets": [
            {
                "dataset": "ablation_results",
                "examples": [
                    {
                        "input": json.dumps(
                            {
                                "dataset_name": r["dataset_name"],
                                "arm": r["arm"],
                                "cache_ratio": r["cache_ratio"],
                                "table_size_mult": r["table_size_mult"],
                            }
                        ),
                        "output": json.dumps(
                            {
                                "steady_state_hit_ratio": r["steady_state_hit_ratio"],
                                "mean_recovery_time_requests": r["mean_recovery_time_requests"],
                                "memory_bytes": r["memory_bytes"],
                            }
                        ),
                        "metadata_full_record": r,
                        f"predict_{r['arm']}": json.dumps(
                            {
                                "steady_state_hit_ratio": r["steady_state_hit_ratio"],
                                "mean_recovery_time_requests": r["mean_recovery_time_requests"],
                                "memory_bytes": r["memory_bytes"],
                                "decay_slot_collision_rate": r.get("decay_slot_collision_rate"),
                            }
                        ),
                    }
                    for r in results
                ],
            }
        ],
    }

    def _json_default(o):
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating,)):
            return float(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        raise TypeError(f"not serializable: {type(o)}")

    with open(OUT_PATH, "w") as f:
        json.dump(out, f, default=_json_default)
    logger.info(f"Wrote {OUT_PATH} ({OUT_PATH.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
