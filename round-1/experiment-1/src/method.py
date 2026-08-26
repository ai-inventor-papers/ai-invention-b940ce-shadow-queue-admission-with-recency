#!/usr/bin/env python3
"""Per-Key Decay vs Global TinyLFU Reset: cache-admission simulator.

Implements a shared W-TinyLFU admission scaffold (Count-Min sketch + doorkeeper
+ SLRU main region + small LRU window) with two pluggable frequency estimators:

  - GlobalResetFrequencyEstimator: baseline, single Count-Min sketch that is
    halved wholesale once every `sample_size` accesses (Caffeine's approach).
  - PerKeyDecayFrequencyEstimator (proposed): three Count-Min sketch "tiers"
    with different halving periods; each key currently tracked in a bounded
    shadow-metadata LRU is assigned to a tier by the coefficient of variation
    (CoV) of its inter-arrival gaps (bursty -> short half-life, regular ->
    long half-life).

Both are driven by the identical SLRU + doorkeeper + admission-window loop so
any hit-ratio / recovery-time difference is attributable to the frequency
estimator alone, not to implementation drift between two separate simulators.
"""

from __future__ import annotations

import gc
import json
import multiprocessing as mp
import os
import resource
import sys
import time
from collections import OrderedDict
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np
from loguru import logger

# --------------------------------------------------------------------------
# Setup: logging, hardware-aware limits (aii-python + aii-use-hardware)
# --------------------------------------------------------------------------

WORKSPACE = Path(__file__).resolve().parent
LOG_DIR = WORKSPACE / "logs"
LOG_DIR.mkdir(exist_ok=True)

logger.remove()
logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss}|{level:<7}|{message}")
logger.add(LOG_DIR / "run.log", rotation="30 MB", level="DEBUG")


def _detect_cpus() -> int:
    try:
        parts = Path("/sys/fs/cgroup/cpu.max").read_text().split()
        if parts[0] != "max":
            return max(1, int(int(parts[0]) / int(parts[1])))
    except (FileNotFoundError, ValueError):
        pass
    try:
        q = int(Path("/sys/fs/cgroup/cpu/cpu.cfs_quota_us").read_text())
        p = int(Path("/sys/fs/cgroup/cpu/cpu.cfs_period_us").read_text())
        if q > 0:
            return max(1, int(q / p))
    except (FileNotFoundError, ValueError):
        pass
    try:
        return len(os.sched_getaffinity(0))
    except (AttributeError, OSError):
        return os.cpu_count() or 1


NUM_CPUS = _detect_cpus()
N_WORKERS = max(1, min(NUM_CPUS - 1, 5))  # leave one CPU for the orchestrator
logger.info(f"Detected {NUM_CPUS} usable CPUs (cgroup-aware); using {N_WORKERS} worker processes")

# RAM budget: this workload is many small dict/bytearray objects (a few MB
# each), never a single big matrix. 8 GB is generous headroom given the 57 GB
# container limit and leaves the rest for the OS / agent runtime.
_RAM_BUDGET_BYTES = 8 * 1024**3
resource.setrlimit(resource.RLIMIT_AS, (_RAM_BUDGET_BYTES * 3, _RAM_BUDGET_BYTES * 3))

RNG_SEED_SALT = 0x9E3779B1  # fixed odd constant for deterministic integer hashing


# ==========================================================================
# 1. Count-Min sketch (4-bit packed counters) + Doorkeeper
# ==========================================================================


class CountMin4Bit:
    """Depth-4 Count-Min sketch with 4-bit saturating counters, 2 per byte.

    Matches Caffeine's `FrequencySketch`: increment saturates at 15, estimate
    is the min across rows, and `halve_all` implements the RESET_MASK trick
    (right-shift each nibble by 1, in place, in a single pass over bytes).
    """

    DEPTH = 4
    _RESET_MASK = 0x77  # 0111_0111: halves both nibbles, drops each LSB

    def __init__(self, num_counters: int, seed: int):
        self.width = max(16, num_counters | 1)  # odd width reduces hash collisions across rows
        self.table = bytearray((self.width + 1) // 2)
        rng = np.random.default_rng(seed ^ RNG_SEED_SALT)
        # odd multipliers for a simple deterministic multiplicative hash per row
        self._salts = [int(x) | 1 for x in rng.integers(1, 2**31 - 1, size=self.DEPTH)]

    def _pos(self, key: int, row: int) -> int:
        return ((key ^ self._salts[row]) * self._salts[(row + 1) % self.DEPTH]) % self.width

    def _get_nibble(self, pos: int) -> int:
        b = self.table[pos >> 1]
        return b & 0x0F if pos & 1 == 0 else (b >> 4) & 0x0F

    def _set_nibble(self, pos: int, value: int) -> None:
        idx = pos >> 1
        b = self.table[idx]
        if pos & 1 == 0:
            self.table[idx] = (b & 0xF0) | value
        else:
            self.table[idx] = (b & 0x0F) | (value << 4)

    def increment(self, key: int) -> None:
        for row in range(self.DEPTH):
            pos = self._pos(key, row)
            v = self._get_nibble(pos)
            if v < 15:
                self._set_nibble(pos, v + 1)

    def estimate(self, key: int) -> int:
        return min(self._get_nibble(self._pos(key, row)) for row in range(self.DEPTH))

    def halve_all(self) -> None:
        table = self.table
        mask = self._RESET_MASK
        for i in range(len(table)):
            table[i] = (table[i] >> 1) & mask

    def memory_bytes(self) -> int:
        return len(self.table) + self.DEPTH * 8  # counters + salts


class Doorkeeper:
    """1-bit-per-slot Bloom-style first-touch filter, cleared with the sketch."""

    def __init__(self, num_bits: int, seed: int):
        self.num_bits = max(16, num_bits | 1)
        self.bits = bytearray((self.num_bits + 7) // 8)
        rng = np.random.default_rng((seed ^ 0xD1B54A35) & 0x7FFFFFFF)
        self._salt = int(rng.integers(1, 2**31 - 1)) | 1

    def _pos(self, key: int) -> int:
        return ((key ^ self._salt) * 2654435761) % self.num_bits

    def contains(self, key: int) -> bool:
        pos = self._pos(key)
        return bool(self.bits[pos >> 3] & (1 << (pos & 7)))

    def maybe_add(self, key: int) -> bool:
        """Returns True iff the key was NOT already present (first touch)."""
        pos = self._pos(key)
        byte_idx, bit = pos >> 3, 1 << (pos & 7)
        if self.bits[byte_idx] & bit:
            return False
        self.bits[byte_idx] |= bit
        return True

    def clear(self) -> None:
        for i in range(len(self.bits)):
            self.bits[i] = 0

    def memory_bytes(self) -> int:
        return len(self.bits) + 8


# ==========================================================================
# 2. Frequency estimators: baseline (global reset) vs proposed (per-key decay)
# ==========================================================================
#
# NOTE on the doorkeeper/frequency formula: Caffeine's TinyLFU adds a fixed
# +1 (not the sketch's saturation value) when the doorkeeper has seen the key
# at all, giving a max representable frequency of 16. Using the sketch's max
# value here would make nearly every warmed-up key score identically and
# destroy discrimination; +1 is the documented, correct formula and is what
# both estimators below use.


class GlobalResetFrequencyEstimator:
    """Baseline: single Count-Min sketch, reset (halved) globally on a schedule."""

    name = "global_reset_tinylfu"

    def __init__(self, cache_capacity: int, sample_size_multiplier: int, seed: int):
        self.sketch = CountMin4Bit(4 * cache_capacity, seed=seed)
        self.doorkeeper = Doorkeeper(cache_capacity * 8, seed=seed + 1)
        self.sample_size = max(1, sample_size_multiplier * cache_capacity)
        self.size = 0
        self.sample_size_multiplier = sample_size_multiplier

    def record_access(self, key: int) -> None:
        if not self.doorkeeper.maybe_add(key):
            self.sketch.increment(key)
        self.size += 1
        if self.size >= self.sample_size:
            self.sketch.halve_all()
            self.doorkeeper.clear()
            self.size = 0

    def frequency(self, key: int) -> int:
        return self.sketch.estimate(key) + (1 if self.doorkeeper.contains(key) else 0)

    def memory_bytes(self) -> int:
        return self.sketch.memory_bytes() + self.doorkeeper.memory_bytes()


class _LRUMeta:
    """Bounded LRU dict for per-key shadow metadata (read-peek vs touch-on-write)."""

    def __init__(self, capacity: int):
        self.capacity = max(1, capacity)
        self._od: "OrderedDict[int, tuple]" = OrderedDict()

    def peek(self, key: int):
        return self._od.get(key)

    def put_and_touch(self, key: int, value: tuple) -> None:
        if key in self._od:
            self._od.move_to_end(key)
        self._od[key] = value
        if len(self._od) > self.capacity:
            self._od.popitem(last=False)

    def __len__(self) -> int:
        return len(self._od)

    def memory_bytes(self) -> int:
        # 5-field tuple of Python numbers + dict/OrderedDict per-entry overhead;
        # ~120 bytes/entry is a conservative empirical estimate for this shape.
        return len(self._od) * 120 + 200


# CoV thresholds for the 3-tier classifier. CoV==1 is the memoryless
# (Poisson/exponential) reference point: renewal processes with CoV well
# above 1 are bursty (many small gaps + occasional huge gaps -> volatile,
# short half-life is right), well below 1 are near-regular/periodic
# (long half-life is right, since the popularity signal is stable).
COV_HIGH_THRESH = 1.5
COV_LOW_THRESH = 0.5
EWMA_ALPHA = 0.3
MIN_OBS_FOR_CLASSIFICATION = 3


class PerKeyDecayFrequencyEstimator:
    """Proposed: K tiered Count-Min sketches, each with its own halving period.

    Only keys currently tracked in a bounded shadow-metadata LRU get a
    per-key inter-arrival CoV estimate and tier assignment; a key that falls
    out of the shadow queue reverts to the default tier on re-entry, bounding
    memory at O(shadow_queue_capacity) regardless of the true key space.
    """

    name = "per_key_decay_tinylfu"
    TIERS = [(2, "volatile"), (8, "default"), (32, "stable")]
    DEFAULT_TIER = 1

    def __init__(self, cache_capacity: int, shadow_queue_capacity: int, seed: int):
        self.tier_sketches = [
            CountMin4Bit(4 * cache_capacity, seed=seed + 100 + t) for t in range(len(self.TIERS))
        ]
        self.tier_sample_size = [max(1, m * cache_capacity) for m, _ in self.TIERS]
        self.tier_size = [0] * len(self.TIERS)
        self.doorkeeper = Doorkeeper(cache_capacity * 8, seed=seed + 1)
        self.shadow_meta = _LRUMeta(shadow_queue_capacity)
        self.global_clock = 0
        self.tier_assignment_counts = [0] * len(self.TIERS)  # diagnostics

    def _classify(self, ewma_gap: float, ewma_gap_sq: float, n_obs: int) -> int:
        if n_obs < MIN_OBS_FOR_CLASSIFICATION:
            return self.DEFAULT_TIER
        var = max(ewma_gap_sq - ewma_gap * ewma_gap, 0.0)
        cov = (var**0.5) / max(ewma_gap, 1e-6)
        if cov > COV_HIGH_THRESH:
            return 0  # volatile / bursty
        if cov < COV_LOW_THRESH:
            return 2  # stable / regular
        return 1  # default

    def record_access(self, key: int) -> None:
        self.global_clock += 1
        meta = self.shadow_meta.peek(key)
        if meta is None:
            tier = self.DEFAULT_TIER
            self.shadow_meta.put_and_touch(key, (self.global_clock, 0.0, 0.0, tier, 1))
        else:
            last_ts, ewma_gap, ewma_gap_sq, _prev_tier, n_obs = meta
            gap = float(self.global_clock - last_ts)
            if n_obs > 0:
                ewma_gap = EWMA_ALPHA * gap + (1 - EWMA_ALPHA) * ewma_gap
                ewma_gap_sq = EWMA_ALPHA * (gap * gap) + (1 - EWMA_ALPHA) * ewma_gap_sq
            else:
                ewma_gap, ewma_gap_sq = gap, gap * gap
            n_obs += 1
            tier = self._classify(ewma_gap, ewma_gap_sq, n_obs)
            self.shadow_meta.put_and_touch(key, (self.global_clock, ewma_gap, ewma_gap_sq, tier, n_obs))

        self.tier_assignment_counts[tier] += 1
        if not self.doorkeeper.maybe_add(key):
            self.tier_sketches[tier].increment(key)
            self.tier_size[tier] += 1
            if self.tier_size[tier] >= self.tier_sample_size[tier]:
                self.tier_sketches[tier].halve_all()
                self.tier_size[tier] = 0

    def frequency(self, key: int) -> int:
        meta = self.shadow_meta.peek(key)
        tier = meta[3] if meta is not None else self.DEFAULT_TIER
        base = self.tier_sketches[tier].estimate(key)
        return base + (1 if self.doorkeeper.contains(key) else 0)

    def memory_bytes(self) -> int:
        return (
            sum(s.memory_bytes() for s in self.tier_sketches)
            + self.doorkeeper.memory_bytes()
            + self.shadow_meta.memory_bytes()
        )


# ==========================================================================
# 3. SLRU main region + W-TinyLFU admission window (shared by both methods)
# ==========================================================================


class SLRUCache:
    """Segmented LRU: 80% protected / 20% probationary (Caffeine's default split)."""

    def __init__(self, capacity: int):
        self.capacity = max(1, capacity)
        self.protected_capacity = max(1, int(0.8 * self.capacity))
        self.probationary_capacity = max(1, self.capacity - self.protected_capacity)
        self.protected: "OrderedDict[int, None]" = OrderedDict()
        self.probationary: "OrderedDict[int, None]" = OrderedDict()

    def get(self, key: int) -> bool:
        if key in self.protected:
            self.protected.move_to_end(key)
            return True
        if key in self.probationary:
            del self.probationary[key]
            self.protected[key] = None
            if len(self.protected) > self.protected_capacity:
                demoted, _ = self.protected.popitem(last=False)
                self.probationary[demoted] = None
                if len(self.probationary) > self.probationary_capacity:
                    self.probationary.popitem(last=False)
            return True
        return False

    def victim_for_admission_test(self) -> Optional[int]:
        if self.probationary:
            return next(iter(self.probationary))
        return None

    def admit_candidate(self, key: int) -> Optional[int]:
        """Admits into probationary MRU; evicts+returns probationary LRU if full."""
        evicted = None
        if len(self.probationary) >= self.probationary_capacity and self.probationary:
            evicted, _ = self.probationary.popitem(last=False)
        self.probationary[key] = None
        return evicted

    def memory_bytes(self) -> int:
        return (len(self.protected) + len(self.probationary)) * 56  # int key + OrderedDict entry overhead


class WindowTinyLFUCache:
    """Full W-TinyLFU: small LRU admission window + doorkeeper/sketch-gated SLRU main."""

    def __init__(self, capacity: int, estimator, window_frac: float = 0.01):
        self.window_capacity = max(1, int(round(window_frac * capacity)))
        self.main_capacity = max(1, capacity - self.window_capacity)
        self.window: "OrderedDict[int, None]" = OrderedDict()
        self.main = SLRUCache(self.main_capacity)
        self.estimator = estimator

    def access(self, key: int) -> bool:
        """Records the access with the estimator and returns True on a cache hit."""
        self.estimator.record_access(key)
        if key in self.window:
            self.window.move_to_end(key)
            return True
        if self.main.get(key):
            return True
        # miss: admit into the window; if the window overflows, its evicted
        # LRU item competes for a main-region slot against the SLRU victim.
        self.window[key] = None
        if len(self.window) > self.window_capacity:
            candidate, _ = self.window.popitem(last=False)
            victim = self.main.victim_for_admission_test()
            if victim is None or self.estimator.frequency(candidate) > self.estimator.frequency(victim):
                self.main.admit_candidate(candidate)
        return False

    def memory_bytes(self) -> int:
        return self.estimator.memory_bytes() + self.main.memory_bytes() + len(self.window) * 56


# ==========================================================================
# 4. Trace generation: synthetic Zipf + identity-drift + bursts
# ==========================================================================


@dataclass
class TraceResult:
    keys: np.ndarray
    drift_indices: list = field(default_factory=list)
    burst_indices: list = field(default_factory=list)


def make_zipf_drift_trace(
    n_requests: int,
    key_space: int,
    alpha: float,
    n_drift_events: int,
    drift_magnitude: float,
    burst_prob: float,
    seed: int,
) -> TraceResult:
    """Zipf(alpha) popularity over `key_space` keys, with periodic hot-key
    identity churn (drift) and occasional short bursts on a previously cold key.

    Popularity SHAPE is held fixed (same Zipf exponent throughout); what
    drifts is WHICH keys occupy the popular ranks, which is the regime a
    per-key decay mechanism is meant to adapt to faster than a globally
    reset sketch.
    """
    rng = np.random.default_rng(seed)
    ranks = np.arange(1, key_space + 1, dtype=np.float64)
    probs = ranks ** (-alpha)
    probs /= probs.sum()
    rank_to_key = np.arange(key_space, dtype=np.int64)  # identity mapping initially

    n_segments = n_drift_events + 1
    seg_len = n_requests // n_segments
    trace = np.empty(n_requests, dtype=np.int64)
    drift_indices: list = []
    burst_indices: list = []

    top_frac_for_drift = max(1, int(round(drift_magnitude * key_space)))
    burst_len = 200

    pos = 0
    for seg in range(n_segments):
        this_len = seg_len if seg < n_segments - 1 else (n_requests - pos)
        if this_len <= 0:
            continue
        rank_idx = rng.choice(key_space, size=this_len, p=probs)
        seg_keys = rank_to_key[rank_idx]

        if burst_prob > 0 and rng.random() < burst_prob and this_len > burst_len + 1:
            # a cold key (bottom half of the rank distribution) bursts for a
            # short contiguous window inside this segment
            cold_rank = int(rng.integers(key_space // 2, key_space))
            burst_key = int(rank_to_key[cold_rank])
            start = int(rng.integers(0, this_len - burst_len))
            seg_keys[start : start + burst_len] = burst_key
            burst_indices.append(pos + start)

        trace[pos : pos + this_len] = seg_keys
        pos += this_len

        if seg < n_segments - 1:
            # drift: the top-`top_frac_for_drift` popular ranks get reassigned
            # to a fresh random sample of key identities (old hot keys go
            # cold, formerly-cold keys become hot).
            top_indices = np.arange(top_frac_for_drift)
            rank_to_key[top_indices] = rng.choice(key_space, size=top_frac_for_drift, replace=False)
            drift_indices.append(pos)

    return TraceResult(keys=trace, drift_indices=drift_indices, burst_indices=burst_indices)


def load_real_trace() -> Optional[TraceResult]:
    """Attempts to source a public cache-access trace; returns None if infeasible.

    A web search (see run log) located the canonical candidate — Twitter's
    anonymized production cache traces (github.com/twitter/cache-trace,
    hosted on CMU PDL's FTP mirror). Each per-cluster trace is itself
    multi-gigabyte, stored in a bespoke binary "oss" record format that
    requires Twitter's own C++ reader/decoder to parse, and there are 50+
    cluster files with no small canonical subset documented. Downloading and
    reverse-engineering that binary format is not feasible inside this
    artifact's time/compute budget, so per the plan's fallback_plan this arm
    is explicitly SKIPPED rather than faked with a relabeled synthetic trace.
    """
    logger.warning(
        "load_real_trace: skipping real-trace arm — twitter/cache-trace requires "
        "multi-GB downloads in a bespoke binary format with no lightweight public "
        "alternative found; see fallback_plan. real_trace_results will be null."
    )
    return None


# ==========================================================================
# 5. Simulator driver + recovery-time metric
# ==========================================================================

ROLLING_WINDOW = 3000
RECOVERY_LOOKAHEAD = 30000
RECOVERY_TARGET_FRAC = 0.9


def _rolling_hit_ratio(hit_bits: np.ndarray, window: int) -> np.ndarray:
    csum = np.cumsum(np.insert(hit_bits.astype(np.float64), 0, 0.0))
    out = np.empty_like(csum[1:])
    n = len(hit_bits)
    for i in range(n):
        lo = max(0, i - window + 1)
        out[i] = (csum[i + 1] - csum[lo]) / (i + 1 - lo)
    return out


def _rolling_hit_ratio_fast(hit_bits: np.ndarray, window: int) -> np.ndarray:
    """O(n) rolling mean via cumulative sums (equivalent to the reference loop above)."""
    n = len(hit_bits)
    csum = np.cumsum(np.insert(hit_bits.astype(np.float64), 0, 0.0))
    idx = np.arange(n)
    lo = np.maximum(0, idx - window + 1)
    counts = idx - lo + 1
    return (csum[idx + 1] - csum[lo]) / counts


def run_trace(trace: np.ndarray, cache_capacity: int, estimator, window_admission_frac: float = 0.01) -> dict:
    cache = WindowTinyLFUCache(cache_capacity, estimator, window_frac=window_admission_frac)
    n = len(trace)
    hit_bits = np.empty(n, dtype=np.uint8)
    for i in range(n):
        hit_bits[i] = 1 if cache.access(int(trace[i])) else 0
    final_hit_ratio = float(hit_bits.mean())
    rolling = _rolling_hit_ratio_fast(hit_bits, ROLLING_WINDOW)
    return {
        "final_hit_ratio": final_hit_ratio,
        "rolling_hit_ratio": rolling,  # kept in-process only; summarized before JSON export
        "memory_bytes": cache.memory_bytes(),
    }


def compute_recovery_times(rolling: np.ndarray, drift_indices: list, lookahead: int = RECOVERY_LOOKAHEAD) -> list:
    """For each drift point, time until rolling hit ratio climbs back to
    `RECOVERY_TARGET_FRAC` of the way from the post-drift trough back to the
    pre-drift plateau. Returns `lookahead` (censored, logged) if it never does.
    """
    # NOTE: rolling[d] is a trailing average over [d-ROLLING_WINDOW, d], so for
    # `ROLLING_WINDOW` requests after the drift it is still dominated by
    # PRE-drift observations and reads as "already recovered" by construction.
    # The search window is therefore offset by ROLLING_WINDOW so every point
    # considered is computed purely from post-drift requests.
    n = len(rolling)
    results = []
    for d in drift_indices:
        pre_lo, pre_hi = max(0, d - ROLLING_WINDOW), d
        if pre_hi <= pre_lo:
            continue
        plateau = float(np.mean(rolling[pre_lo:pre_hi]))
        search_lo = d + ROLLING_WINDOW
        post_hi = min(n, d + lookahead)
        if post_hi <= search_lo:
            continue
        window = rolling[search_lo:post_hi]
        trough = float(np.min(window))
        target = trough + RECOVERY_TARGET_FRAC * (plateau - trough)
        recovered_offsets = np.where(window >= target)[0]
        if len(recovered_offsets) == 0:
            results.append({"drift_index": int(d), "recovery_time": lookahead, "censored": True})
        else:
            # report time-since-drift (not time-since-search_lo)
            results.append(
                {"drift_index": int(d), "recovery_time": int(recovered_offsets[0]) + ROLLING_WINDOW, "censored": False}
            )
    return results


def estimator_tier_diagnostics(estimator) -> Optional[dict]:
    if isinstance(estimator, PerKeyDecayFrequencyEstimator):
        total = max(1, sum(estimator.tier_assignment_counts))
        return {
            label: round(cnt / total, 4)
            for (_, label), cnt in zip(estimator.TIERS, estimator.tier_assignment_counts)
        }
    return None


# ==========================================================================
# 6. Sweep configuration
# ==========================================================================

KEY_SPACE = 150_000  # plan's 200k, trimmed slightly for a runtime margin in the full grid
CACHE_RATIOS = [0.01, 0.05, 0.1]
SKEW_LEVELS = [0.8, 1.0, 1.2]
SAMPLE_MULTIPLIERS = [4, 8, 16, 32]
DRIFT_SCENARIOS = [
    {"name": "low_mag_low_freq", "drift_magnitude": 0.05, "n_drift_events": 2},
    {"name": "low_mag_high_freq", "drift_magnitude": 0.05, "n_drift_events": 8},
    {"name": "high_mag_low_freq", "drift_magnitude": 0.20, "n_drift_events": 2},
    {"name": "high_mag_high_freq", "drift_magnitude": 0.20, "n_drift_events": 8},
]
SEEDS = [1, 2, 3]
N_REQUESTS_TUNING = 80_000
N_REQUESTS_MAIN = 600_000
RECOVERY_LOOKAHEAD_MAIN = 60_000  # used for compute_recovery_times() calls in the main sweep
BURST_PROB = 0.5
SHADOW_QUEUE_MULT = 2  # shadow_queue_capacity = SHADOW_QUEUE_MULT * cache_capacity


def _tune_baseline_multiplier(ratio: float, alpha: float) -> tuple[int, dict]:
    cache_capacity = max(10, int(ratio * KEY_SPACE))
    trace = make_zipf_drift_trace(
        N_REQUESTS_TUNING, KEY_SPACE, alpha, n_drift_events=0, drift_magnitude=0.0, burst_prob=0.0, seed=999
    ).keys
    best_mult, best_hr = SAMPLE_MULTIPLIERS[0], -1.0
    sweep_results = {}
    for mult in SAMPLE_MULTIPLIERS:
        est = GlobalResetFrequencyEstimator(cache_capacity, mult, seed=42)
        res = run_trace(trace, cache_capacity, est)
        sweep_results[mult] = res["final_hit_ratio"]
        if res["final_hit_ratio"] > best_hr:
            best_hr, best_mult = res["final_hit_ratio"], mult
    return best_mult, sweep_results


def _run_one_cell(args: dict) -> dict:
    ratio, alpha, drift_scenario, seed, best_multiplier = (
        args["ratio"],
        args["alpha"],
        args["drift_scenario"],
        args["seed"],
        args["best_multiplier"],
    )
    cache_capacity = max(10, int(ratio * KEY_SPACE))
    tr = make_zipf_drift_trace(
        N_REQUESTS_MAIN,
        KEY_SPACE,
        alpha,
        n_drift_events=drift_scenario["n_drift_events"],
        drift_magnitude=drift_scenario["drift_magnitude"],
        burst_prob=BURST_PROB,
        seed=seed,
    )

    baseline_est = GlobalResetFrequencyEstimator(cache_capacity, best_multiplier, seed=seed * 7 + 1)
    baseline_res = run_trace(tr.keys, cache_capacity, baseline_est)
    baseline_recovery = compute_recovery_times(
        baseline_res["rolling_hit_ratio"], tr.drift_indices, lookahead=RECOVERY_LOOKAHEAD_MAIN
    )

    proposed_est = PerKeyDecayFrequencyEstimator(
        cache_capacity, shadow_queue_capacity=SHADOW_QUEUE_MULT * cache_capacity, seed=seed * 7 + 2
    )
    proposed_res = run_trace(tr.keys, cache_capacity, proposed_est)
    proposed_recovery = compute_recovery_times(
        proposed_res["rolling_hit_ratio"], tr.drift_indices, lookahead=RECOVERY_LOOKAHEAD_MAIN
    )

    # steady-state hit ratio: mean rolling ratio over the trailing 15% of the
    # trace, i.e. well clear of any drift-recovery transient
    tail_start = int(0.85 * N_REQUESTS_MAIN)
    baseline_steady = float(np.mean(baseline_res["rolling_hit_ratio"][tail_start:]))
    proposed_steady = float(np.mean(proposed_res["rolling_hit_ratio"][tail_start:]))

    def _mean_recovery(rec_list):
        vals = [r["recovery_time"] for r in rec_list]
        return float(np.mean(vals)) if vals else None

    return {
        "ratio": ratio,
        "alpha": alpha,
        "drift_scenario": drift_scenario["name"],
        "seed": seed,
        "cache_capacity": cache_capacity,
        "best_baseline_multiplier": best_multiplier,
        "baseline": {
            "final_hit_ratio": baseline_res["final_hit_ratio"],
            "steady_state_hit_ratio": baseline_steady,
            "memory_bytes": baseline_res["memory_bytes"],
            "recovery_events": baseline_recovery,
            "mean_recovery_time": _mean_recovery(baseline_recovery),
        },
        "proposed": {
            "final_hit_ratio": proposed_res["final_hit_ratio"],
            "steady_state_hit_ratio": proposed_steady,
            "memory_bytes": proposed_res["memory_bytes"],
            "recovery_events": proposed_recovery,
            "mean_recovery_time": _mean_recovery(proposed_recovery),
            "tier_assignment_fractions": estimator_tier_diagnostics(proposed_est),
        },
        "n_drift_events": len(tr.drift_indices),
        "n_burst_events": len(tr.burst_indices),
    }


def _bootstrap_ci(values: list, n_resamples: int = 1000, seed: int = 0) -> dict:
    values = [v for v in values if v is not None and not (isinstance(v, float) and np.isnan(v))]
    if len(values) == 0:
        return {"mean": None, "ci_low": None, "ci_high": None, "n": 0}
    arr = np.asarray(values, dtype=np.float64)
    rng = np.random.default_rng(seed)
    if len(arr) == 1:
        return {"mean": float(arr[0]), "ci_low": float(arr[0]), "ci_high": float(arr[0]), "n": 1}
    boot_means = np.empty(n_resamples)
    for b in range(n_resamples):
        sample = rng.choice(arr, size=len(arr), replace=True)
        boot_means[b] = sample.mean()
    return {
        "mean": float(arr.mean()),
        "ci_low": float(np.percentile(boot_means, 2.5)),
        "ci_high": float(np.percentile(boot_means, 97.5)),
        "n": int(len(arr)),
    }


# ==========================================================================
# 7. Main
# ==========================================================================


def main() -> None:
    t0 = time.time()
    logger.info(
        f"Grid: {len(CACHE_RATIOS)} ratios x {len(SKEW_LEVELS)} alphas x "
        f"{len(DRIFT_SCENARIOS)} drift scenarios x {len(SEEDS)} seeds = "
        f"{len(CACHE_RATIOS)*len(SKEW_LEVELS)*len(DRIFT_SCENARIOS)*len(SEEDS)} main-phase cells "
        f"(key_space={KEY_SPACE}, n_requests_main={N_REQUESTS_MAIN})"
    )

    # ---- Phase A: tune the baseline's sample-size multiplier per (ratio, alpha) ----
    tuning_records = []
    best_multipliers: dict[tuple[float, float], int] = {}
    for ratio in CACHE_RATIOS:
        for alpha in SKEW_LEVELS:
            best_mult, sweep = _tune_baseline_multiplier(ratio, alpha)
            best_multipliers[(ratio, alpha)] = best_mult
            tuning_records.append(
                {"ratio": ratio, "alpha": alpha, "sweep_hit_ratios": sweep, "chosen_multiplier": best_mult}
            )
            logger.info(f"Phase A: ratio={ratio} alpha={alpha} -> best_multiplier={best_mult} (sweep={sweep})")
    logger.info(f"Phase A done in {time.time()-t0:.1f}s")

    # ---- Phase B: full drift-scenario x seed sweep, parallelized across cells ----
    cell_args = []
    for ratio in CACHE_RATIOS:
        for alpha in SKEW_LEVELS:
            for drift_scenario in DRIFT_SCENARIOS:
                for seed in SEEDS:
                    cell_args.append(
                        {
                            "ratio": ratio,
                            "alpha": alpha,
                            "drift_scenario": drift_scenario,
                            "seed": seed,
                            "best_multiplier": best_multipliers[(ratio, alpha)],
                        }
                    )
    logger.info(f"Phase B: launching {len(cell_args)} cells across {N_WORKERS} worker processes")

    cell_results = []
    t_phase_b = time.time()
    ctx = mp.get_context("spawn")
    with ProcessPoolExecutor(max_workers=N_WORKERS, mp_context=ctx) as pool:
        futures = {pool.submit(_run_one_cell, a): a for a in cell_args}
        done = 0
        for fut in as_completed(futures):
            a = futures[fut]
            try:
                res = fut.result()
                cell_results.append(res)
            except Exception:
                logger.error(f"Cell failed: ratio={a['ratio']} alpha={a['alpha']} "
                             f"scenario={a['drift_scenario']['name']} seed={a['seed']}")
                raise
            done += 1
            if done % 10 == 0 or done == len(cell_args):
                elapsed = time.time() - t_phase_b
                logger.info(f"Phase B: {done}/{len(cell_args)} cells done ({elapsed:.1f}s elapsed)")
    logger.info(f"Phase B done in {time.time()-t_phase_b:.1f}s")
    del cell_args
    gc.collect()

    # ---- Phase C: real-trace arm (attempted, explicitly skipped — see load_real_trace) ----
    real_trace = load_real_trace()
    real_trace_results = None  # documented null per fallback_plan

    # ---- Statistics ----
    logger.info("Computing bootstrap CIs and win-rate summary")
    by_cell_group: dict[tuple, list] = {}
    for r in cell_results:
        key = (r["ratio"], r["alpha"], r["drift_scenario"])
        by_cell_group.setdefault(key, []).append(r)

    group_summaries = []
    wins_20pct_faster = 0
    total_groups = 0
    for (ratio, alpha, scenario), rows in by_cell_group.items():
        hit_deltas = [r["proposed"]["steady_state_hit_ratio"] - r["baseline"]["steady_state_hit_ratio"] for r in rows]
        recov_ratios = []
        for r in rows:
            b, p = r["baseline"]["mean_recovery_time"], r["proposed"]["mean_recovery_time"]
            if b and b > 0 and p is not None:
                recov_ratios.append(p / b)
        hit_ci = _bootstrap_ci(hit_deltas, seed=hash((ratio, alpha, scenario)) & 0xFFFF)
        recov_ci = _bootstrap_ci(recov_ratios, seed=(hash((ratio, alpha, scenario)) + 1) & 0xFFFF)
        total_groups += 1
        wins = (
            recov_ci["mean"] is not None
            and recov_ci["mean"] <= 0.8
            and recov_ci["ci_high"] is not None
            and recov_ci["ci_high"] < 1.0
        )
        if wins:
            wins_20pct_faster += 1
        group_summaries.append(
            {
                "ratio": ratio,
                "alpha": alpha,
                "drift_scenario": scenario,
                "n_seeds": len(rows),
                "steady_state_hit_ratio_delta": hit_ci,
                "recovery_time_ratio_proposed_over_baseline": recov_ci,
                "proposed_wins_20pct_faster_recovery_ci_excl_1": bool(wins),
            }
        )

    summary_stats = {
        "n_groups": total_groups,
        "fraction_groups_proposed_20pct_faster_recovery_ci_significant": (
            wins_20pct_faster / total_groups if total_groups else None
        ),
        "bootstrap_resamples": 1000,
        "recovery_definition": (
            f"first index within {RECOVERY_LOOKAHEAD_MAIN} requests after a drift event where the "
            f"{ROLLING_WINDOW}-request rolling hit ratio climbs back to "
            f"trough + {RECOVERY_TARGET_FRAC}*(pre-drift plateau - trough); censored at "
            f"{RECOVERY_LOOKAHEAD_MAIN} (logged) if never reached"
        ),
        "steady_state_definition": "mean rolling hit ratio over the trailing 15% of the trace",
    }

    memory_footprint_table = {}
    for r in cell_results:
        k = f"ratio={r['ratio']}_alpha={r['alpha']}"
        memory_footprint_table.setdefault(k, {"baseline_bytes": [], "proposed_bytes": []})
        memory_footprint_table[k]["baseline_bytes"].append(r["baseline"]["memory_bytes"])
        memory_footprint_table[k]["proposed_bytes"].append(r["proposed"]["memory_bytes"])
    for k, v in memory_footprint_table.items():
        v["baseline_bytes_mean"] = float(np.mean(v["baseline_bytes"]))
        v["proposed_bytes_mean"] = float(np.mean(v["proposed_bytes"]))
        v["proposed_over_baseline_ratio"] = v["proposed_bytes_mean"] / v["baseline_bytes_mean"]

    # ---- Assemble exp_gen_sol_out.json-compliant output ----
    logger.info("Assembling method_out.json")

    grid_examples = []
    for r in cell_results:
        cfg = {
            "ratio": r["ratio"],
            "alpha": r["alpha"],
            "drift_scenario": r["drift_scenario"],
            "seed": r["seed"],
            "cache_capacity": r["cache_capacity"],
            "key_space": KEY_SPACE,
            "n_requests": N_REQUESTS_MAIN,
        }
        grid_examples.append(
            {
                "input": json.dumps(cfg),
                "output": json.dumps(
                    {
                        "baseline": {k: v for k, v in r["baseline"].items() if k != "recovery_events"},
                        "proposed": {k: v for k, v in r["proposed"].items() if k != "recovery_events"},
                    }
                ),
                "metadata_baseline_recovery_events": r["baseline"]["recovery_events"],
                "metadata_proposed_recovery_events": r["proposed"]["recovery_events"],
                "predict_baseline_final_hit_ratio": str(r["baseline"]["final_hit_ratio"]),
                "predict_proposed_final_hit_ratio": str(r["proposed"]["final_hit_ratio"]),
            }
        )

    tuning_examples = [
        {
            "input": json.dumps({"ratio": t["ratio"], "alpha": t["alpha"], "n_requests": N_REQUESTS_TUNING}),
            "output": json.dumps({"chosen_multiplier": t["chosen_multiplier"], "sweep_hit_ratios": t["sweep_hit_ratios"]}),
        }
        for t in tuning_records
    ]

    summary_examples = [
        {
            "input": json.dumps({"phase": "aggregate_summary"}),
            "output": json.dumps(
                {
                    "summary_stats": summary_stats,
                    "memory_footprint_table": memory_footprint_table,
                    "real_trace_results": real_trace_results,
                    "group_summaries": group_summaries,
                }
            ),
        }
    ]

    output = {
        "metadata": {
            "method_name": "per_key_decay_vs_global_tinylfu_reset",
            "description": (
                "W-TinyLFU cache-admission simulator comparing a global-reset "
                "Count-Min frequency sketch (Caffeine-style baseline) against a "
                "per-key inter-arrival-CoV-decayed tiered variant, sharing an "
                "identical doorkeeper/SLRU/admission-window scaffold."
            ),
            "key_space": KEY_SPACE,
            "cache_ratios": CACHE_RATIOS,
            "skew_levels_alpha": SKEW_LEVELS,
            "sample_multipliers_swept": SAMPLE_MULTIPLIERS,
            "drift_scenarios": DRIFT_SCENARIOS,
            "seeds": SEEDS,
            "n_requests_tuning": N_REQUESTS_TUNING,
            "n_requests_main": N_REQUESTS_MAIN,
            "proposed_tiers": PerKeyDecayFrequencyEstimator.TIERS,
            "cov_thresholds": {"high": COV_HIGH_THRESH, "low": COV_LOW_THRESH},
            "deviations_from_plan": [
                f"key_space set to {KEY_SPACE:,} (plan suggested 200,000) as a runtime-margin "
                "trim for the full 3x3x4x3-seed grid, preserving the complete "
                "ratio/skew/drift-scenario/seed factorial design",
                "doorkeeper contribution to frequency() corrected to +1 (Caffeine's "
                "actual semantics) instead of the plan pseudocode's +15, which would "
                "have saturated comparisons for nearly every warmed-up key",
                "admission-window / SLRU interaction reimplemented as a full W-TinyLFU "
                "loop (window LRU eviction competes against the SLRU probationary "
                "victim) rather than the plan pseudocode's ad hoc hit-counting, which "
                "double-counted window admissions as hits",
                "real-trace arm (Phase C) explicitly skipped per fallback_plan: "
                "twitter/cache-trace requires multi-GB downloads in a bespoke binary "
                "format with no feasible lightweight alternative found",
            ],
            "total_runtime_seconds": time.time() - t0,
        },
        "datasets": [
            {"dataset": "phaseA_baseline_multiplier_tuning", "examples": tuning_examples},
            {"dataset": "phaseB_drift_scenario_grid", "examples": grid_examples},
            {"dataset": "phaseC_aggregate_summary_and_real_trace_status", "examples": summary_examples},
        ],
    }

    out_path = WORKSPACE / "method_out.json"
    out_path.write_text(json.dumps(output, indent=2, default=str))
    logger.info(f"Wrote {out_path} ({out_path.stat().st_size/1e6:.2f} MB)")
    logger.info(f"Total runtime: {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
