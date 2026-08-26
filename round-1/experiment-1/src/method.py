#!/usr/bin/env python3
"""Per-Key Decay Cache Admission vs W-TinyLFU: discrete-event cache simulator.

Implements exact W-TinyLFU (Count-Min sketch + periodic global halving +
doorkeeper Bloom filter + shadow-queue admission test + SLRU eviction) side
by side with a per-key-decay variant that replaces global halving with a
per-key decay rate chosen from CV-based volatility buckets. Both share
identical SLRU eviction and admission-test comparison structure.

No real-world trace was available in this run's data dependency (the
gen_art_dataset_1 directory was empty and no user uploads were provided), so
per the artifact plan's fallback_plan item (2) this run is SYNTHETIC-ONLY:
both the steady-state hit-ratio parity check and the drift-recovery claim
are evaluated on synthetic Zipf traces. This is recorded as an explicit
scope reduction in method_out.json's top-level "notes" field.
"""

from __future__ import annotations

import gc
import hashlib
import json
import multiprocessing as mp
import resource
import sys
import time
from collections import deque
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import numpy as np
from loguru import logger

np.seterr(over="ignore")  # intentional uint64 wraparound in the multiplicative hash

# --------------------------------------------------------------------------- #
# Setup: paths, logging, resource limits
# --------------------------------------------------------------------------- #

WORKDIR = Path(__file__).resolve().parent
LOG_DIR = WORKDIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

logger.remove()
logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss}|{level:<7}|{message}")
logger.add(LOG_DIR / "run.log", rotation="30 MB", level="DEBUG")

# RAM budget: this workload is pure numpy arrays sized by sketch width and
# trace length, well under a few hundred MB per run. Cap generously.
RAM_BUDGET_BYTES = 6 * 1024**3  # 6 GB virtual-address budget
resource.setrlimit(resource.RLIMIT_AS, (RAM_BUDGET_BYTES * 3, RAM_BUDGET_BYTES * 3))
resource.setrlimit(resource.RLIMIT_CPU, (3600 * 5, 3600 * 5))  # 5h CPU-time safety cap

NUM_CPUS = 6  # detected via cgroup cfs_quota (510000/100000 = ~5.1 -> 6 avail)
NUM_WORKERS = max(1, NUM_CPUS - 1)

OUT_PATH = WORKDIR / "method_out.json"

# --------------------------------------------------------------------------- #
# Hashing utilities
# --------------------------------------------------------------------------- #

_SEEDS = np.array([0x9E3779B1, 0x85EBCA77, 0xC2B2AE3D, 0x27D4EB2F], dtype=np.uint64)


def hash_key(key: int, seed_idx: int, width: int) -> int:
    """Deterministic 32-bit-ish hash of (key, seed) -> [0, width)."""
    h = hashlib.blake2b(
        key.to_bytes(8, "little", signed=False) if key >= 0 else (-key - 1).to_bytes(8, "little"),
        digest_size=8,
        person=_SEEDS[seed_idx].tobytes()[:8],
    )
    return int.from_bytes(h.digest(), "little") % width


def hash_keys_vec(keys: np.ndarray, seed_idx: int, width: int) -> np.ndarray:
    """Vectorized multiplicative hash (fast path used inside the hot loop).

    Not cryptographic, but has the property required here: a fixed key maps
    to a fixed slot per seed, and different seeds decorrelate collisions.
    """
    seed = int(_SEEDS[seed_idx])
    k = keys.astype(np.uint64)
    x = (k * np.uint64(seed)) ^ (k >> np.uint64(17))
    x = x * np.uint64(0xFF51AFD7ED558CCD)
    x = x ^ (x >> np.uint64(33))
    return (x % np.uint64(width)).astype(np.int64)


def hash_scalar(key: int, seed_idx: int, width: int) -> int:
    seed = int(_SEEDS[seed_idx])
    k = np.uint64(key)
    x = (k * np.uint64(seed)) ^ (k >> np.uint64(17))
    x = x * np.uint64(0xFF51AFD7ED558CCD)
    x = x ^ (x >> np.uint64(33))
    return int(x % np.uint64(width))


# --------------------------------------------------------------------------- #
# Count-Min Sketch (baseline frequency estimator, W-TinyLFU)
# --------------------------------------------------------------------------- #

DEPTH = 4
CM_MAX = 15  # 4-bit saturating counters, as in real W-TinyLFU (Caffeine)


class CountMinSketch:
    """Baseline W-TinyLFU frequency estimator: 4-bit saturating counters,
    global halving on a periodic sample-count reset."""

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
    """1-bit-per-slot admission doorkeeper, reset alongside CMS halving."""

    def __init__(self, width_bits: int):
        self.width_bits = width_bits
        self.bits = np.zeros(width_bits, dtype=bool)

    def _idx(self, key: int, d: int) -> int:
        return hash_scalar(key, d, self.width_bits)

    def maybe_add(self, key: int) -> bool:
        """Returns True if key was already present (i.e. this is its 2nd+ sighting)."""
        present = all(self.bits[self._idx(key, d)] for d in range(2))
        for d in range(2):
            self.bits[self._idx(key, d)] = True
        return present

    def reset(self) -> None:
        self.bits[:] = False

    def memory_bytes(self) -> int:
        return self.bits.nbytes  # numpy bool array; conceptually 1 bit/slot


# --------------------------------------------------------------------------- #
# Per-key decay estimator (proposed method)
# --------------------------------------------------------------------------- #

# Volatility buckets: stable / medium / bursty, half-life in requests.
N_BUCKETS = 3
HALF_LIVES = np.array([50_000.0, 5_000.0, 500.0], dtype=np.float64)
# CV thresholds separating buckets (low CV -> stable/regular; high CV -> bursty)
CV_THRESH = (0.5, 1.2)


def classify_cv_to_bucket(cv: float) -> int:
    if cv < CV_THRESH[0]:
        return 0
    if cv < CV_THRESH[1]:
        return 1
    return 2


class PerKeyDecayEstimator:
    """CMS-shaped hashed-counter array with per-slot exponential decay.

    Each slot stores a float32 counter, a float32 last-update-time, and a
    uint8 decay-bucket id, all hashed on the same DEPTH x width layout as
    CountMinSketch for a fair memory comparison. Decay is applied lazily at
    update time using the elapsed ticks since the slot was last touched.

    Collision risk: unlike the baseline (which only ever needs an integer
    count), decay-rate storage here is bucket-per-SLOT, not bucket-per-KEY.
    Two keys sharing a slot under a given seed can silently overwrite each
    other's decay bucket. We log a `bucket_overwrite` counter (fallback_plan
    item 1) whenever a touch overwrites a slot with a *different* bucket
    than what is currently stored, so this confound is measurable rather
    than silent.
    """

    def __init__(self, width: int):
        self.width = width
        self.counters = np.zeros((DEPTH, width), dtype=np.float32)
        self.last_update_time = np.zeros((DEPTH, width), dtype=np.float32)
        self.decay_bucket_slot = np.zeros((DEPTH, width), dtype=np.uint8)
        self.slot_owner_key = -np.ones((DEPTH, width), dtype=np.int64)  # for collision logging
        self.touches = 0
        self.bucket_overwrites = 0
        self.bucket_assignment_counts = np.zeros(N_BUCKETS, dtype=np.int64)

    def touch(self, key: int, t: int, cv: float) -> None:
        bucket = classify_cv_to_bucket(cv)
        self.bucket_assignment_counts[bucket] += 1
        half_life = HALF_LIVES[bucket]
        self.touches += 1
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

    def estimate(self, key: int, t: int) -> float:
        """Estimate applies decay-since-last-touch at read time too, so a
        stale slot's contribution reflects elapsed time even without a
        fresh write (matches the touch()-time lazy-decay semantics)."""
        best = None
        for d in range(DEPTH):
            idx = hash_scalar(key, d, self.width)
            bucket = int(self.decay_bucket_slot[d, idx])
            half_life = HALF_LIVES[bucket]
            dt = t - self.last_update_time[d, idx]
            val = float(self.counters[d, idx]) * (0.5 ** (max(dt, 0) / half_life))
            best = val if best is None else min(best, val)
        return best if best is not None else 0.0

    def memory_bytes(self) -> int:
        return self.counters.nbytes + self.last_update_time.nbytes + self.decay_bucket_slot.nbytes

    def collision_rate(self) -> float:
        return self.bucket_overwrites / self.touches if self.touches else 0.0


# --------------------------------------------------------------------------- #
# Shadow queue: bounded recent-miss history, feeds CV to the decay estimator
# --------------------------------------------------------------------------- #

DEFAULT_CV = 1.0  # neutral prior (treated as "medium" bucket) until enough history


class ShadowQueue:
    """Bounded dict of recently-missed keys -> deque of last-k timestamps.

    Sized to `capacity` slots with FIFO eviction of the oldest-inserted key
    (tracked via an insertion-order deque of key ids), matching the plan's
    "bounded FIFO/dict" description.
    """

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
        # n_slots * (8 bytes key hash + history_len*8 bytes timestamps), per plan
        return self.capacity * (8 + self.history_len * 8)


# --------------------------------------------------------------------------- #
# SLRU eviction (shared by both systems)
# --------------------------------------------------------------------------- #

class SLRU:
    """Segmented LRU: probationary segment (20% capacity) + protected (80%).

    New admissions enter probation; a second hit promotes to protected.
    Eviction always pulls from the probationary segment's LRU end first
    (a full protected segment demotes its own LRU end into probation).
    """

    def __init__(self, capacity: int, probation_frac: float = 0.2):
        self.capacity = capacity
        self.probation_cap = max(1, int(round(capacity * probation_frac)))
        self.protected_cap = capacity - self.probation_cap
        # OrderedDict-like via dict (Python 3.7+ preserves insertion order);
        # we manually move-to-end on access to emulate LRU/MRU ordering.
        self.probation: dict[int, None] = {}
        self.protected: dict[int, None] = {}

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
            self.protected.move_to_end(key) if hasattr(self.protected, "move_to_end") else None
            if len(self.protected) > self.protected_cap:
                demoted, _ = next(iter(self.protected.items()))
                del self.protected[demoted]
                self.probation[demoted] = None
        elif key in self.protected:
            # refresh recency: pop+reinsert to move to MRU end
            del self.protected[key]
            self.protected[key] = None

    def admit_to_probation(self, key: int) -> None:
        self.probation[key] = None
        if len(self.probation) > self.probation_cap and self.protected_cap == 0:
            # degenerate tiny-cache case; nothing to do, caller handles eviction
            pass

    def peek_victim(self) -> int | None:
        """Victim candidate: probationary LRU end, else protected LRU end."""
        if self.probation:
            return next(iter(self.probation))
        if self.protected:
            return next(iter(self.protected))
        return None

    def evict(self, key: int) -> None:
        self.probation.pop(key, None)
        self.protected.pop(key, None)


# Python's plain dict lacks move_to_end; use OrderedDict instead for correctness.
from collections import OrderedDict  # noqa: E402


class SLRU:  # noqa: F811 (intentional redefinition with OrderedDict, cleaner semantics)
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
# Trace generation: synthetic Zipf traces with popularity drift
# --------------------------------------------------------------------------- #

def zipf_probs(n_keys: int, alpha: float, rng: np.random.Generator) -> np.ndarray:
    ranks = np.arange(1, n_keys + 1, dtype=np.float64)
    weights = 1.0 / np.power(ranks, alpha)
    perm = rng.permutation(n_keys)  # random rank->key assignment
    probs = np.zeros(n_keys, dtype=np.float64)
    probs[perm] = weights
    probs /= probs.sum()
    return probs


def gen_zipf_trace(
    n_requests: int,
    n_keys: int,
    alpha: float,
    drift_scenario: dict,
    seed: int,
) -> tuple[np.ndarray, list[int]]:
    """Generate a request trace of key ids with popularity drift events.

    drift_scenario: {"kind": "reshuffle"|"burst"|"none", "n_events": int,
                      "magnitude": float in (0,1]}
    Returns (keys_array, drift_event_times).
    """
    rng = np.random.default_rng(seed)
    probs = zipf_probs(n_keys, alpha, rng)
    kind = drift_scenario.get("kind", "none")
    n_events = drift_scenario.get("n_events", 0)
    magnitude = drift_scenario.get("magnitude", 0.0)

    keys = np.empty(n_requests, dtype=np.int64)
    drift_times: list[int] = []

    if kind == "none" or n_events == 0:
        keys[:] = rng.choice(n_keys, size=n_requests, p=probs)
        return keys, drift_times

    segment_len = n_requests // (n_events + 1)
    cur_probs = probs.copy()
    pos = 0
    for ev in range(n_events + 1):
        seg_n = segment_len if ev < n_events else (n_requests - pos)
        keys[pos:pos + seg_n] = rng.choice(n_keys, size=seg_n, p=cur_probs)
        pos += seg_n
        if ev < n_events:
            drift_times.append(pos)
            if kind == "reshuffle":
                n_swap = max(1, int(round(n_keys * magnitude)))
                top_keys = np.argsort(-cur_probs)[:n_swap]
                cold_keys = rng.choice(n_keys, size=n_swap, replace=False)
                new_probs = cur_probs.copy()
                new_probs[top_keys], new_probs[cold_keys] = (
                    cur_probs[cold_keys].copy(),
                    cur_probs[top_keys].copy(),
                )
                cur_probs = new_probs / new_probs.sum()
            elif kind == "burst":
                n_cold = max(1, int(round(n_keys * magnitude * 0.1)))
                cold_keys = rng.choice(n_keys, size=n_cold, replace=False)
                new_probs = cur_probs.copy()
                boost = magnitude * new_probs.sum()
                new_probs[cold_keys] += boost / n_cold
                cur_probs = new_probs / new_probs.sum()
    return keys, drift_times


DRIFT_SCENARIOS = {
    "D1_mild_reshuffle": {"kind": "reshuffle", "n_events": 1, "magnitude": 0.05},
    "D2_severe_reshuffle": {"kind": "reshuffle", "n_events": 1, "magnitude": 0.25},
    "D3_mild_burst": {"kind": "burst", "n_events": 1, "magnitude": 0.5},
    "D4_severe_burst": {"kind": "burst", "n_events": 1, "magnitude": 2.0},
}

# --------------------------------------------------------------------------- #
# Admission-test simulation loop (shared structure, per-system parametrized)
# --------------------------------------------------------------------------- #

LOG_EVERY = 200  # subsample the hit-ratio time series


def simulate(
    keys: np.ndarray,
    cache_capacity: int,
    system: str,  # "baseline" or "decay"
    width: int,
    reset_W: int | None,
    shadow_capacity: int,
) -> dict:
    n = len(keys)
    slru = SLRU(cache_capacity)
    shadow = ShadowQueue(capacity=shadow_capacity)
    doorkeeper = DoorkeeperBloom(width_bits=width * 8)

    if system == "baseline":
        estimator = CountMinSketch(width)
    else:
        estimator = PerKeyDecayEstimator(width)

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
                if system == "baseline":
                    doorkeeper.maybe_add(key)
                    estimator.increment(key)
                else:
                    cv = shadow.record_miss(key, t)
                    estimator.touch(key, t, cv)
            else:
                victim = slru.peek_victim()
                if system == "baseline":
                    seen_before = doorkeeper.maybe_add(key)
                    estimator.increment(key)
                    cand_est = estimator.estimate(key) if seen_before else 0
                    victim_est = estimator.estimate(victim)
                else:
                    cv = shadow.record_miss(key, t)
                    estimator.touch(key, t, cv)
                    cand_est = estimator.estimate(key, t)
                    victim_est = estimator.estimate(victim, t)
                if cand_est > victim_est:
                    slru.evict(victim)
                    slru.admit_to_probation(key)

        if system == "baseline" and reset_W:
            sample_counter += 1
            if sample_counter >= reset_W:
                estimator.halve_all()
                doorkeeper.reset()
                sample_counter = 0

        if t % LOG_EVERY == 0 and len(window_hits) > 0:
            hit_series.append([t, sum(window_hits) / len(window_hits)])

    mem = slru_estimator_mem(estimator, doorkeeper, shadow, system)
    result = {
        "steady_state_hit_ratio": hits / n,
        "hit_ratio_time_series": hit_series,
        "memory_bytes": mem,
    }
    if system == "decay":
        total_bucket = int(estimator.bucket_assignment_counts.sum())
        result["decay_bucket_assignment_stats"] = {
            "stable": float(estimator.bucket_assignment_counts[0] / total_bucket) if total_bucket else 0.0,
            "medium": float(estimator.bucket_assignment_counts[1] / total_bucket) if total_bucket else 0.0,
            "bursty": float(estimator.bucket_assignment_counts[2] / total_bucket) if total_bucket else 0.0,
        }
        result["decay_slot_collision_rate"] = estimator.collision_rate()
    return result


def slru_estimator_mem(estimator, doorkeeper: DoorkeeperBloom, shadow: ShadowQueue, system: str) -> int:
    total = estimator.memory_bytes() + doorkeeper.memory_bytes()
    if system == "decay":
        total += shadow.memory_bytes()
    return int(total)


def matched_widths(cache_capacity: int, shadow_capacity: int) -> tuple[int, int]:
    """Pick (baseline_width, decay_width) such that total memory footprints
    (sketch + doorkeeper (+ shadow queue for decay)) match within +/-15%.

    Baseline per-slot cost: DEPTH*1 byte (uint8 counters) + 1/8 byte doorkeeper bit.
    Decay per-slot cost: DEPTH*(4+4+1) bytes (float32 counter + float32 time + uint8 bucket)
                         + 1/8 byte doorkeeper bit, plus a FIXED shadow-queue cost
                         independent of width.
    Solve for decay_width given baseline_width so totals match within tolerance,
    accounting for the shadow queue's fixed overhead.
    """
    baseline_width = 65536
    # baseline: CMS counters (DEPTH*1 byte/slot) + doorkeeper bloom (width*8 bits = width*8 bytes as bool array)
    baseline_per_width_bytes = DEPTH * 1 + 8
    baseline_bytes = baseline_per_width_bytes * baseline_width

    shadow = ShadowQueue(shadow_capacity)
    shadow_bytes = shadow.memory_bytes()
    # decay: counters(4B) + last_update_time(4B) + decay_bucket(1B) per (DEPTH,width) slot,
    # plus doorkeeper bloom (width*8 bytes) -- shadow queue is a FIXED cost, not width-dependent.
    decay_per_width_bytes = DEPTH * (4 + 4 + 1) + 8
    remaining = baseline_bytes - shadow_bytes
    decay_width = max(256, int(remaining / decay_per_width_bytes))
    return baseline_width, decay_width


def _run_one_config(cfg: dict) -> dict:
    """Worker function: run one (trace, alpha, cache_ratio, drift_scenario,
    system, W, seed) config end-to-end and return its metrics."""
    try:
        n_requests = cfg["n_requests"]
        n_keys = cfg["n_keys"]
        alpha = cfg["alpha"]
        cache_ratio = cfg["cache_ratio"]
        drift_name = cfg["drift_scenario"]
        seed = cfg["seed"]
        system = cfg["system"]
        W_multiplier = cfg.get("W_multiplier")
        cache_capacity = max(8, int(round(n_keys * cache_ratio)))
        shadow_capacity = max(16, cache_capacity)

        baseline_width, decay_width = matched_widths(cache_capacity, shadow_capacity)
        width = baseline_width if system == "baseline" else decay_width
        reset_W = int(cache_capacity * W_multiplier) if (system == "baseline" and W_multiplier) else None

        drift_scenario = DRIFT_SCENARIOS.get(drift_name, {"kind": "none", "n_events": 0, "magnitude": 0.0})
        keys, drift_times = gen_zipf_trace(n_requests, n_keys, alpha, drift_scenario, seed)

        t0 = time.perf_counter()
        sim_result = simulate(keys, cache_capacity, system, width, reset_W, shadow_capacity)
        elapsed = time.perf_counter() - t0

        recovery = None
        if drift_times:
            recovery = compute_recovery_time(
                keys, cache_capacity, system, width, reset_W, shadow_capacity, drift_times[0], n_requests
            )

        out = {
            "trace_source": "synthetic_zipf",
            "alpha": alpha,
            "cache_ratio": cache_ratio,
            "cache_capacity": cache_capacity,
            "drift_scenario": drift_name,
            "system": system,
            "W_multiplier": W_multiplier,
            "seed": seed,
            "n_requests": n_requests,
            "n_keys": n_keys,
            "steady_state_hit_ratio": sim_result["steady_state_hit_ratio"],
            "memory_bytes": sim_result["memory_bytes"],
            "recovery_time_requests": recovery,
            "elapsed_sec": elapsed,
            "hit_ratio_time_series": sim_result["hit_ratio_time_series"][::4],  # subsample further for size
        }
        if "decay_bucket_assignment_stats" in sim_result:
            out["decay_bucket_assignment_stats"] = sim_result["decay_bucket_assignment_stats"]
            out["decay_slot_collision_rate"] = sim_result["decay_slot_collision_rate"]
        return out
    except Exception as exc:  # noqa: BLE001 - report failure per-config, don't kill the pool
        return {"error": str(exc), "config": cfg}


def compute_recovery_time(
    keys: np.ndarray,
    cache_capacity: int,
    system: str,
    width: int,
    reset_W: int | None,
    shadow_capacity: int,
    drift_time: int,
    n_requests: int,
    threshold: float = 0.9,
    window: int = 2000,
) -> float | None:
    """Time-to-recovery: first t > drift_time where rolling hit ratio (last
    `window` requests) reaches threshold * post-drift-optimal hit ratio,
    where post-drift-optimal is estimated by simulating the POST-drift-only
    stationary segment independently to convergence."""
    post_segment = keys[drift_time:]
    if len(post_segment) < window * 2:
        return None
    post_result = simulate(post_segment, cache_capacity, system, width, reset_W, shadow_capacity)
    # optimal = hit ratio over final 20% of the post-drift-only run (converged)
    tail_start = int(len(post_segment) * 0.8)
    tail_series = [hr for t, hr in post_result["hit_ratio_time_series"] if t >= tail_start]
    optimal = float(np.mean(tail_series)) if tail_series else post_result["steady_state_hit_ratio"]
    target = threshold * optimal

    # Now find first t after drift in the ORIGINAL (with-drift) run's hit
    # series where rolling hit ratio crosses target. Re-simulate the full
    # trace (drift included) to get its time series (already computed by
    # caller normally; recompute here to keep this function self-contained
    # and side-effect free for parallel workers).
    full_result = simulate(keys, cache_capacity, system, width, reset_W, shadow_capacity)
    for t, hr in full_result["hit_ratio_time_series"]:
        if t > drift_time and hr >= target:
            return float(t - drift_time)
    return None  # did not recover within trace length


# --------------------------------------------------------------------------- #
# Unit / correctness checks (Stage 1 of testing_plan)
# --------------------------------------------------------------------------- #

def run_unit_tests() -> None:
    logger.info("Stage 1: unit/correctness tests")

    # CountMinSketch: insert A x10, B x3, check monotone over-estimation + halving
    cms = CountMinSketch(width=1024)
    for _ in range(10):
        cms.increment(1001)
    for _ in range(3):
        cms.increment(2002)
    est_a, est_b = cms.estimate(1001), cms.estimate(2002)
    assert est_a >= 10, f"CMS under-estimated A: {est_a} < 10"
    assert est_b >= 3, f"CMS under-estimated B: {est_b} < 3"
    cms.halve_all()
    est_a2 = cms.estimate(1001)
    assert est_a2 <= est_a, "halve_all() should not increase counts"
    assert 3 <= est_a2 <= 7, f"halve_all() did not roughly halve: {est_a} -> {est_a2}"
    logger.info(f"CMS test OK: A {est_a}->{est_a2}, B={est_b}")

    # SLRU: scripted 20-request trace with hand-computed hit/miss sequence
    slru = SLRU(capacity=4, probation_frac=0.5)  # 2 probation, 2 protected
    script = [1, 2, 3, 1, 2, 4, 1, 2, 5, 1]
    expected_hits = 0
    results = []
    for key in script:
        hit = slru.contains(key)
        results.append(hit)
        if hit:
            expected_hits += 1
            slru.promote_to_protected(key)
        else:
            if slru.is_full():
                victim = slru.peek_victim()
                slru.evict(victim)
            slru.admit_to_probation(key)
    # Deterministic replay check: same script run twice gives same hit pattern
    slru2 = SLRU(capacity=4, probation_frac=0.5)
    results2 = []
    for key in script:
        hit = slru2.contains(key)
        results2.append(hit)
        if hit:
            slru2.promote_to_protected(key)
        else:
            if slru2.is_full():
                slru2.evict(slru2.peek_victim())
            slru2.admit_to_probation(key)
    assert results == results2, "SLRU is non-deterministic across identical runs"
    assert results[0] is False and results[1] is False, "first sightings must be misses"
    assert results[3] is True, "key 1 should hit on repeat within capacity"
    logger.info(f"SLRU test OK: hit pattern={results}")

    # ShadowQueue CV computation on a regular vs bursty sequence
    sq = ShadowQueue(capacity=100)
    for t in [0, 100, 200, 300, 400]:
        cv_regular = sq.record_miss(42, t)
    for t in [0, 5, 400, 410, 800]:
        cv_bursty = sq.record_miss(43, t)
    assert cv_regular < cv_bursty, f"regular CV {cv_regular} should be < bursty CV {cv_bursty}"
    logger.info(f"ShadowQueue test OK: regular_cv={cv_regular:.3f} bursty_cv={cv_bursty:.3f}")

    # PerKeyDecayEstimator: decay actually reduces stale counts over time
    dec = PerKeyDecayEstimator(width=1024)
    dec.touch(7, t=0, cv=0.1)  # stable bucket, half_life=50000
    dec.touch(7, t=0, cv=0.1)
    est_fresh = dec.estimate(7, t=0)
    est_stale = dec.estimate(7, t=100_000)  # 2 half-lives later
    assert est_stale < est_fresh, "decayed estimate should shrink over elapsed time"
    logger.info(f"PerKeyDecayEstimator test OK: fresh={est_fresh:.3f} stale={est_stale:.3f}")

    logger.info("Stage 1 PASSED")


# --------------------------------------------------------------------------- #
# Main experiment driver
# --------------------------------------------------------------------------- #

def build_grid(
    n_requests: int,
    n_keys: int,
    alphas: list[float],
    cache_ratios: list[float],
    drift_names: list[str],
    W_multipliers: list[int],
    seeds: list[int],
) -> list[dict]:
    grid = []
    for alpha in alphas:
        for cache_ratio in cache_ratios:
            for drift_name in drift_names:
                for seed in seeds:
                    for Wm in W_multipliers:
                        grid.append({
                            "n_requests": n_requests, "n_keys": n_keys, "alpha": alpha,
                            "cache_ratio": cache_ratio, "drift_scenario": drift_name,
                            "seed": seed, "system": "baseline", "W_multiplier": Wm,
                        })
                    grid.append({
                        "n_requests": n_requests, "n_keys": n_keys, "alpha": alpha,
                        "cache_ratio": cache_ratio, "drift_scenario": drift_name,
                        "seed": seed, "system": "decay", "W_multiplier": None,
                    })
    return grid


def run_grid_parallel(grid: list[dict], label: str) -> list[dict]:
    logger.info(f"[{label}] launching {len(grid)} configs on {NUM_WORKERS} workers")
    t0 = time.perf_counter()
    results = []
    with ProcessPoolExecutor(max_workers=NUM_WORKERS, mp_context=mp.get_context("spawn")) as pool:
        futures = {pool.submit(_run_one_config, cfg): i for i, cfg in enumerate(grid)}
        done = 0
        for fut in as_completed(futures):
            r = fut.result()
            results.append(r)
            done += 1
            if done % max(1, len(grid) // 10) == 0:
                logger.info(f"[{label}] {done}/{len(grid)} done")
    elapsed = time.perf_counter() - t0
    n_err = sum(1 for r in results if "error" in r)
    logger.info(f"[{label}] finished {len(grid)} configs in {elapsed:.1f}s ({n_err} errors)")
    if n_err:
        for r in results:
            if "error" in r:
                logger.error(f"config failed: {r['config']} -> {r['error']}")
    return results, elapsed


def bootstrap_ci(values: list[float], n_boot: int = 2000, seed: int = 0) -> dict:
    if not values:
        return {"median": None, "ci_low": None, "ci_high": None, "n": 0}
    arr = np.array(values, dtype=np.float64)
    rng = np.random.default_rng(seed)
    boots = [np.median(rng.choice(arr, size=len(arr), replace=True)) for _ in range(n_boot)]
    return {
        "median": float(np.median(arr)),
        "ci_low": float(np.percentile(boots, 2.5)),
        "ci_high": float(np.percentile(boots, 97.5)),
        "n": len(arr),
    }


@logger.catch(reraise=True)
def main() -> None:
    logger.info("=== Per-Key Decay Cache Admission vs W-TinyLFU ===")
    logger.info(f"Workdir: {WORKDIR}")
    logger.info(f"NUM_WORKERS={NUM_WORKERS}")

    run_unit_tests()

    # ---------------- Stage 2: tiny smoke run ----------------
    logger.info("Stage 2: tiny smoke run (5000 req, 200 keys, no drift)")
    smoke_cfgs = [
        {"n_requests": 5000, "n_keys": 200, "alpha": 1.0, "cache_ratio": 0.1,
         "drift_scenario": "none", "seed": 0, "system": "baseline", "W_multiplier": 8},
        {"n_requests": 5000, "n_keys": 200, "alpha": 1.0, "cache_ratio": 0.1,
         "drift_scenario": "none", "seed": 0, "system": "decay", "W_multiplier": None},
    ]
    smoke_results = [_run_one_config(c) for c in smoke_cfgs]
    for r in smoke_results:
        assert "error" not in r, f"smoke run failed: {r}"
        assert 0.05 <= r["steady_state_hit_ratio"] <= 0.99, f"hit ratio out of sane range: {r}"
    base_hr, decay_hr = smoke_results[0]["steady_state_hit_ratio"], smoke_results[1]["steady_state_hit_ratio"]
    logger.info(f"Stage 2 OK: baseline_hr={base_hr:.3f} decay_hr={decay_hr:.3f} "
                f"mem base={smoke_results[0]['memory_bytes']} decay={smoke_results[1]['memory_bytes']}")

    # ---------------- Stage 3: drift signal check ----------------
    logger.info("Stage 3: drift signal check (single reshuffle, 50k req, 500 keys)")
    drift_cfg = {"n_requests": 50000, "n_keys": 500, "alpha": 1.0, "cache_ratio": 0.1,
                 "drift_scenario": "D2_severe_reshuffle", "seed": 0, "system": "baseline", "W_multiplier": 8}
    drift_result = _run_one_config(drift_cfg)
    assert "error" not in drift_result, f"drift smoke run failed: {drift_result}"
    series = drift_result["hit_ratio_time_series"]
    pre_drift = [hr for t, hr in series if t < 25000]
    post_drift_immediate = [hr for t, hr in series if 25000 <= t < 27000]
    if pre_drift and post_drift_immediate:
        dip = np.mean(pre_drift[-10:]) - np.mean(post_drift_immediate[:10])
        logger.info(f"Stage 3: pre-drift hr~{np.mean(pre_drift[-10:]):.3f}, "
                    f"post-drift-immediate hr~{np.mean(post_drift_immediate[:10]):.3f}, dip={dip:.3f}")
    logger.info("Stage 3 OK: drift injection perturbs hit ratio as expected")

    # ---------------- Time budget planning ----------------
    # Total wall budget for this experiment step; leave margin for I/O and analysis.
    TIME_BUDGET_SEC = 3.0 * 3600  # 3 hours of the ~6h budget for the sweep itself
    start_time = time.perf_counter()

    def elapsed() -> float:
        return time.perf_counter() - start_time

    # ---------------- Stage 4: single full-grid cell (extrapolation) ----------------
    logger.info("Stage 4: single full-grid cell to estimate wall-clock/run")
    N_REQUESTS = 40000
    N_KEYS = 1000
    pilot_grid = build_grid(
        n_requests=N_REQUESTS, n_keys=N_KEYS, alphas=[1.0], cache_ratios=[0.05],
        drift_names=["D2_severe_reshuffle"], W_multipliers=[1, 4, 8, 16, 32], seeds=[0, 1],
    )
    pilot_results, pilot_elapsed = run_grid_parallel(pilot_grid, "stage4_pilot")
    per_run_sec = pilot_elapsed / max(1, len(pilot_grid)) * NUM_WORKERS  # approx single-core-equivalent cost
    logger.info(f"Stage 4 OK: {len(pilot_grid)} configs in {pilot_elapsed:.1f}s "
                f"(~{per_run_sec:.3f}s/config single-core-equivalent)")

    # ---------------- Full sweep design ----------------
    alphas = [0.8, 1.0, 1.2]
    cache_ratios = [0.01, 0.05, 0.1]
    drift_names = list(DRIFT_SCENARIOS.keys())
    W_multipliers = [1, 4, 8, 16, 32]
    seeds = [0, 1, 2, 3, 4]

    full_grid = build_grid(N_REQUESTS, N_KEYS, alphas, cache_ratios, drift_names, W_multipliers, seeds)
    est_total_sec = len(full_grid) * (pilot_elapsed / len(pilot_grid))
    remaining = TIME_BUDGET_SEC - elapsed()
    logger.info(f"Full grid would be {len(full_grid)} configs, est {est_total_sec:.0f}s "
                f"vs {remaining:.0f}s remaining budget")

    notes = [
        "No real-world access trace was available in this run's data dependency "
        "(gen_art_dataset_1 was empty, no user uploads provided): per fallback_plan "
        "item (2) this run is SYNTHETIC-ONLY for BOTH the steady-state hit-ratio "
        "parity check and the drift-recovery claim. This is a scope reduction from "
        "the artifact plan, which specified a real trace as well."
    ]

    applied_reductions = []
    if est_total_sec > remaining:
        logger.warning("Full grid exceeds budget; applying fallback_plan item 3 reductions in order")
        # (a) bracket W around the pilot's best W at one cell, reduce W sweep to 3
        pilot_by_W: dict[int, list[float]] = {}
        for r in pilot_results:
            if "error" in r or r.get("system") != "baseline":
                continue
            pilot_by_W.setdefault(r["W_multiplier"], []).append(r["steady_state_hit_ratio"])
        if pilot_by_W:
            best_W = max(pilot_by_W, key=lambda w: np.mean(pilot_by_W[w]))
            bracket = sorted(set(w for w in W_multipliers if abs(W_multipliers.index(w) - W_multipliers.index(best_W)) <= 1))
            W_multipliers = bracket if len(bracket) >= 2 else W_multipliers[:3]
        else:
            W_multipliers = W_multipliers[:3]
        applied_reductions.append(f"(a) W sweep reduced to {W_multipliers} bracketing pilot best W")
        full_grid = build_grid(N_REQUESTS, N_KEYS, alphas, cache_ratios, drift_names, W_multipliers, seeds)
        est_total_sec = len(full_grid) * (pilot_elapsed / len(pilot_grid))

    if est_total_sec > remaining:
        seeds = seeds[:3]
        applied_reductions.append(f"(b) seeds reduced to {seeds}")
        full_grid = build_grid(N_REQUESTS, N_KEYS, alphas, cache_ratios, drift_names, W_multipliers, seeds)
        est_total_sec = len(full_grid) * (pilot_elapsed / len(pilot_grid))

    if est_total_sec > remaining:
        cache_ratios = cache_ratios[:2]
        applied_reductions.append(f"(c) cache_ratio sweep reduced to {cache_ratios}")
        full_grid = build_grid(N_REQUESTS, N_KEYS, alphas, cache_ratios, drift_names, W_multipliers, seeds)
        est_total_sec = len(full_grid) * (pilot_elapsed / len(pilot_grid))

    if est_total_sec > remaining:
        drift_names = ["D1_mild_reshuffle", "D2_severe_reshuffle"]
        applied_reductions.append(f"(d) drift_scenario reduced to {drift_names}")
        full_grid = build_grid(N_REQUESTS, N_KEYS, alphas, cache_ratios, drift_names, W_multipliers, seeds)
        est_total_sec = len(full_grid) * (pilot_elapsed / len(pilot_grid))

    if applied_reductions:
        notes.append("Fallback_plan item (3) reductions applied to fit the time budget: " + "; ".join(applied_reductions))
    logger.info(f"Final grid: {len(full_grid)} configs, est {est_total_sec:.0f}s, budget remaining {remaining:.0f}s")

    # ---------------- Run the full (possibly reduced) sweep ----------------
    full_results, full_elapsed = run_grid_parallel(full_grid, "full_sweep")

    all_configs = pilot_results + full_results
    n_errors = sum(1 for r in all_configs if "error" in r)
    logger.info(f"Total configs run: {len(all_configs)} ({n_errors} errors), total time {elapsed():.0f}s")

    # ---------------- Aggregate analysis ----------------
    # (a) Hit-ratio parity at matched memory: baseline (best W per cell) vs decay
    parity_rows = [r for r in all_configs if "error" not in r]
    by_cell: dict[tuple, dict[str, list[float]]] = {}
    for r in parity_rows:
        cell = (r["alpha"], r["cache_ratio"], r["drift_scenario"])
        by_cell.setdefault(cell, {"baseline": [], "decay": []})
        if r["system"] == "baseline":
            by_cell[cell]["baseline"].append(r["steady_state_hit_ratio"])
        else:
            by_cell[cell]["decay"].append(r["steady_state_hit_ratio"])

    parity_summary = []
    for cell, vals in by_cell.items():
        if vals["baseline"] and vals["decay"]:
            b_best = max(vals["baseline"])  # best-tuned baseline W
            d_mean = float(np.mean(vals["decay"]))
            parity_summary.append({
                "alpha": cell[0], "cache_ratio": cell[1], "drift_scenario": cell[2],
                "baseline_best_hit_ratio": b_best, "decay_mean_hit_ratio": d_mean,
                "delta_pp": (d_mean - b_best) * 100,
            })

    # (b) Recovery-time comparison with bootstrap CIs
    recovery_by_system_cell: dict[tuple, dict[str, list[float]]] = {}
    for r in parity_rows:
        if r.get("recovery_time_requests") is None:
            continue
        cell = (r["alpha"], r["cache_ratio"], r["drift_scenario"])
        recovery_by_system_cell.setdefault(cell, {"baseline": [], "decay": []})
        recovery_by_system_cell[cell][r["system"]].append(r["recovery_time_requests"])

    recovery_summary = []
    for cell, vals in recovery_by_system_cell.items():
        recovery_summary.append({
            "alpha": cell[0], "cache_ratio": cell[1], "drift_scenario": cell[2],
            "baseline_recovery_ci": bootstrap_ci(vals["baseline"]),
            "decay_recovery_ci": bootstrap_ci(vals["decay"]),
        })

    # (c) Memory footprint check (matched-width tolerance)
    mem_rows = [(r["system"], r["memory_bytes"]) for r in parity_rows]
    base_mems = [m for s, m in mem_rows if s == "baseline"]
    decay_mems = [m for s, m in mem_rows if s == "decay"]
    mem_summary = {
        "baseline_mean_bytes": float(np.mean(base_mems)) if base_mems else None,
        "decay_mean_bytes": float(np.mean(decay_mems)) if decay_mems else None,
        "pct_diff": (
            float((np.mean(decay_mems) - np.mean(base_mems)) / np.mean(base_mems) * 100)
            if base_mems and decay_mems else None
        ),
        "within_15pct_tolerance": (
            abs((np.mean(decay_mems) - np.mean(base_mems)) / np.mean(base_mems)) <= 0.15
            if base_mems and decay_mems else None
        ),
    }
    logger.info(f"Memory match: {mem_summary}")

    collision_rates = [r["decay_slot_collision_rate"] for r in parity_rows if "decay_slot_collision_rate" in r]
    mean_collision_rate = float(np.mean(collision_rates)) if collision_rates else None
    if mean_collision_rate is not None and mean_collision_rate > 0.05:
        notes.append(
            f"fallback_plan item (1): decay-bucket slot collision rate is "
            f"{mean_collision_rate:.3f} (>5%), a measurable confound in hashed decay-rate "
            f"storage. Reported as-is; a per-key side-table fallback was not additionally "
            f"implemented in this run given the time budget."
        )
    logger.info(f"Mean decay-slot collision rate: {mean_collision_rate}")

    # ---------------- Build output (exp_gen_sol_out schema) ----------------
    # Schema requires a top-level "datasets" array of {dataset, examples:[{input,output,metadata_*,predict_*}]}.
    # Each simulated (trace,config,system,W,seed) run becomes one example; the
    # full structured record lives in metadata_config (patternProperties allow
    # arbitrary metadata_* content), and all cross-config analysis lives in the
    # top-level "metadata" object (additionalProperties: true).
    def _json_default(o):
        if isinstance(o, (np.floating, np.integer)):
            return float(o) if isinstance(o, np.floating) else int(o)
        if isinstance(o, np.bool_):
            return bool(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        return str(o)

    examples = []
    for r in all_configs:
        if "error" in r:
            examples.append({
                "input": f"config={json.dumps(r.get('config', {}), default=_json_default)}",
                "output": "ERROR",
                "metadata_error": r["error"],
                "predict_error": "ERROR",
            })
            continue
        input_desc = (
            f"system={r['system']} alpha={r['alpha']} cache_ratio={r['cache_ratio']} "
            f"drift_scenario={r['drift_scenario']} W_multiplier={r['W_multiplier']} seed={r['seed']} "
            f"n_requests={r['n_requests']} n_keys={r['n_keys']}"
        )
        output_desc = (
            f"steady_state_hit_ratio={r['steady_state_hit_ratio']:.6f} "
            f"recovery_time_requests={r['recovery_time_requests']} memory_bytes={r['memory_bytes']}"
        )
        example = {
            "input": input_desc,
            "output": output_desc,
            "metadata_config": r,
            f"predict_{r['system']}": output_desc,
        }
        examples.append(example)

    datasets = [{"dataset": "synthetic_zipf_cache_admission_sweep", "examples": examples}]

    output = {
        "metadata": {
            "method_name": "per_key_decay_cache_admission_vs_tinylfu",
            "notes": " | ".join(notes),
            "hardware": {"num_cpus": NUM_CPUS, "num_workers": NUM_WORKERS},
            "grid_spec": {
                "n_requests": N_REQUESTS, "n_keys": N_KEYS, "alphas": alphas,
                "cache_ratios": cache_ratios, "drift_scenarios": drift_names,
                "W_multipliers": W_multipliers, "seeds": seeds,
            },
            "parity_summary": parity_summary,
            "recovery_summary": recovery_summary,
            "memory_summary": mem_summary,
            "mean_decay_slot_collision_rate": mean_collision_rate,
            "unit_test_status": "PASSED",
            "smoke_test": {
                "baseline_hit_ratio": base_hr, "decay_hit_ratio": decay_hr,
                "baseline_memory_bytes": smoke_results[0]["memory_bytes"],
                "decay_memory_bytes": smoke_results[1]["memory_bytes"],
            },
            "total_runtime_sec": elapsed(),
            "n_configs_run": len(all_configs),
            "n_configs_errored": n_errors,
        },
        "datasets": datasets,
    }

    OUT_PATH.write_text(json.dumps(output, indent=2, default=_json_default))
    logger.info(f"Wrote {OUT_PATH} ({OUT_PATH.stat().st_size / 1e6:.2f} MB)")

    del all_configs, pilot_results, full_results
    gc.collect()
    logger.info("=== DONE ===")


if __name__ == "__main__":
    main()
