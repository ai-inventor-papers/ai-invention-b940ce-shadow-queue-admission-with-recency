"""Synthetic Zipf(+drift) trace generation and a real-trace loader/adapter.

Drift types (each returns explicit (start, end, type) event windows so recovery time
can be scored against a known ground-truth event rather than guessed from the curve):
  - none: stationary control, no drift events.
  - periodic_reshuffle: every T requests, a random subset of keys get a freshly
    permuted rank->popularity mapping.
  - burst_cold_keys: initially-cold keys get a short dense access burst.
  - gradual_rank_shift: rank->popularity mapping linearly interpolates to a new
    permutation over a window.
  - combined: reshuffle + bursts overlaid on the same base trace.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class Scenario:
    name: str
    n_keys: int
    trace: np.ndarray  # int64 array of key ids, length n_requests
    drift_events: list[tuple[int, int, str]] = field(default_factory=list)
    meta: dict = field(default_factory=dict)


def _zipf_probs(n_keys: int, alpha: float) -> np.ndarray:
    ranks = np.arange(1, n_keys + 1, dtype=np.float64)
    weights = 1.0 / (ranks ** alpha)
    return weights / weights.sum()


def _sample_from_mapping(rng: np.random.Generator, probs: np.ndarray, rank_to_key: np.ndarray, n: int) -> np.ndarray:
    ranks_drawn = rng.choice(len(probs), size=n, p=probs)
    return rank_to_key[ranks_drawn]


def make_zipf_drift_trace(
    n_keys: int,
    n_requests: int,
    alpha: float,
    drift_type: str,
    seed: int,
) -> Scenario:
    rng = np.random.default_rng(seed)
    probs = _zipf_probs(n_keys, alpha)
    rank_to_key = rng.permutation(n_keys)  # initial rank->key assignment

    if drift_type == "none":
        trace = _sample_from_mapping(rng, probs, rank_to_key, n_requests)
        return Scenario(f"stationary_a{alpha}", n_keys, trace, [], {"alpha": alpha, "drift_type": drift_type})

    if drift_type == "periodic_reshuffle":
        period = max(2000, n_requests // 10)
        events: list[tuple[int, int, str]] = []
        chunks = []
        pos = 0
        while pos < n_requests:
            n = min(period, n_requests - pos)
            chunks.append(_sample_from_mapping(rng, probs, rank_to_key, n))
            pos += n
            if pos < n_requests:
                n_shuffle = max(1, int(0.10 * n_keys))
                idx = rng.choice(n_keys, size=n_shuffle, replace=False)
                shuffled = rank_to_key[idx].copy()
                rng.shuffle(shuffled)
                rank_to_key[idx] = shuffled
                events.append((pos, pos + 1, "periodic_reshuffle"))
        trace = np.concatenate(chunks)
        return Scenario(f"periodic_reshuffle_a{alpha}", n_keys, trace, events, {"alpha": alpha, "drift_type": drift_type})

    if drift_type == "burst_cold_keys":
        trace = _sample_from_mapping(rng, probs, rank_to_key, n_requests)
        n_bursts = 4
        cold_keys_pool = rank_to_key[int(0.7 * n_keys):]  # low-popularity ranks = cold keys
        events = []
        burst_width = max(1000, n_requests // 40)
        burst_size = burst_width // 2
        for b in range(n_bursts):
            start = int((b + 1) * n_requests / (n_bursts + 1))
            end = min(n_requests, start + burst_width)
            cold_keys = rng.choice(cold_keys_pool, size=min(50, len(cold_keys_pool)), replace=False)
            burst_positions = rng.choice(np.arange(start, end), size=min(burst_size, end - start), replace=False)
            burst_positions.sort()
            trace[burst_positions] = rng.choice(cold_keys, size=len(burst_positions))
            events.append((start, end, "burst_cold_keys"))
        return Scenario(f"burst_cold_keys_a{alpha}", n_keys, trace, events, {"alpha": alpha, "drift_type": drift_type})

    if drift_type == "gradual_rank_shift":
        window = max(4000, n_requests // 5)
        target_mapping = rng.permutation(n_keys)
        events = []
        chunks = []
        pos = 0
        step = max(1000, window // 8)
        n_steps = max(1, window // step)
        while pos < n_requests:
            n = min(step, n_requests - pos)
            frac = min(1.0, pos / window)
            n_swap = int(frac * n_keys)
            cur_mapping = rank_to_key.copy()
            if n_swap > 0:
                cur_mapping[:n_swap] = target_mapping[:n_swap]
            chunks.append(_sample_from_mapping(rng, probs, cur_mapping, n))
            pos += n
        trace = np.concatenate(chunks)
        events.append((0, window, "gradual_rank_shift"))
        return Scenario(f"gradual_rank_shift_a{alpha}", n_keys, trace, events, {"alpha": alpha, "drift_type": drift_type})

    if drift_type == "combined":
        reshuffle = make_zipf_drift_trace(n_keys, n_requests, alpha, "periodic_reshuffle", seed)
        trace = reshuffle.trace.copy()
        n_bursts = 3
        events = list(reshuffle.drift_events)
        burst_width = max(1000, n_requests // 40)
        cold_keys_pool = rank_to_key[int(0.7 * n_keys):]
        for b in range(n_bursts):
            start = int((b + 1) * n_requests / (n_bursts + 2))
            end = min(n_requests, start + burst_width)
            cold_keys = rng.choice(cold_keys_pool, size=min(50, len(cold_keys_pool)), replace=False)
            burst_size = (end - start) // 2
            burst_positions = rng.choice(np.arange(start, end), size=min(burst_size, end - start), replace=False)
            burst_positions.sort()
            trace[burst_positions] = rng.choice(cold_keys, size=len(burst_positions))
            events.append((start, end, "burst_cold_keys"))
        events.sort(key=lambda e: e[0])
        return Scenario(f"combined_a{alpha}", n_keys, trace, events, {"alpha": alpha, "drift_type": drift_type})

    raise ValueError(f"unknown drift_type: {drift_type}")


def _read_key_column(path: "Path", skip_lines: int, n_lines: int | None) -> list[int]:
    keys: list[int] = []
    with path.open("r", errors="ignore") as f:
        for i, line in enumerate(f):
            if i < skip_lines:
                continue
            line = line.strip()
            if not line:
                continue
            token = line.replace(",", " ").split()[0]
            try:
                keys.append(int(token))
            except ValueError:
                # Fall back to a stable string hash for non-numeric keys (e.g. URLs).
                keys.append(abs(hash(token)) % (2**31))
            if n_lines is not None and len(keys) >= n_lines:
                break
    return keys


def load_real_trace(path: str, max_requests: int | None = None, skip_lines: int = 0, name_suffix: str = "") -> Scenario | None:
    """Loads a whitespace/CSV-delimited real access trace where each line/row's first
    integer-like field is a key id. `skip_lines` lets the caller draw multiple
    non-overlapping windows from one file for replicate/variance runs. Returns None if
    the file is missing or unreadable (caller should fall back to synthetic-only)."""
    from pathlib import Path

    p = Path(path)
    if not p.exists():
        return None
    try:
        keys = _read_key_column(p, skip_lines, max_requests)
        if len(keys) < 1000:
            return None
        arr = np.array(keys, dtype=np.int64)
        # Remap to dense 0..n_keys-1 ids for fixed-size sketch/tracker sizing.
        uniq, remapped = np.unique(arr, return_inverse=True)
        n_keys = len(uniq)
        name = f"real_trace_{p.stem}{name_suffix}"
        return Scenario(name, n_keys, remapped.astype(np.int64), [], {"source": str(p), "skip_lines": skip_lines})
    except OSError:
        return None


def count_lines(path: str) -> int:
    from pathlib import Path

    n = 0
    with Path(path).open("r", errors="ignore") as f:
        for _ in f:
            n += 1
    return n
