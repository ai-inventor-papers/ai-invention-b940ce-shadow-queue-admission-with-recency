#!/usr/bin/env python3
"""Generate deterministic synthetic Zipf cache-access traces with injected popularity drift.

For each alpha in {0.8, 1.0, 1.2}: one no-drift control + 4 drift scenarios
(2 magnitude levels x 2 frequency levels), each with explicit ground-truth
drift-event metadata (start/end index, event type, affected keys).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from loguru import logger

logger.remove()
logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss}|{level:<7}|{message}")
logger.add("logs/gen_synthetic_zipf.log", rotation="30 MB", level="DEBUG")

OUT_DIR = Path("temp/datasets")
OUT_DIR.mkdir(parents=True, exist_ok=True)

NUM_KEYS = 20_000
NUM_REQUESTS = 100_000
ALPHAS = [0.8, 1.0, 1.2]
TOP_K = 1_000  # top-K keys eligible for rank-reshuffle drift
SEED_BASE = 20260826

# 4 drift scenarios per alpha: 2 magnitude levels x 2 frequency levels, each also
# varying event_type so both rank_reshuffle and cold_key_burst are covered.
DRIFT_SCENARIOS = [
    {"mag_name": "low", "magnitude_frac": 0.10, "freq_name": "rare", "freq_frac": 0.20, "event_type": "rank_reshuffle"},
    {"mag_name": "high", "magnitude_frac": 0.40, "freq_name": "rare", "freq_frac": 0.20, "event_type": "cold_key_burst"},
    {"mag_name": "low", "magnitude_frac": 0.10, "freq_name": "frequent", "freq_frac": 0.05, "event_type": "cold_key_burst"},
    {"mag_name": "high", "magnitude_frac": 0.40, "freq_name": "frequent", "freq_frac": 0.05, "event_type": "rank_reshuffle"},
]


def zipf_probs(num_keys: int, alpha: float) -> np.ndarray:
    ranks = np.arange(1, num_keys + 1, dtype=np.float64)
    weights = 1.0 / np.power(ranks, alpha)
    return weights / weights.sum()


def make_drift_events(
    rng: np.random.Generator,
    num_requests: int,
    event_type: str,
    magnitude_frac: float,
    freq_frac: float,
    num_keys: int,
    top_k: int,
) -> list[dict]:
    """Build a list of drift events with explicit start/end indices and affected keys."""
    period = max(int(num_requests * freq_frac), 1)
    events = []
    idx = period
    eid = 0
    while idx < num_requests:
        end = min(idx + period // 4, num_requests - 1)  # each event acts over a short window
        if event_type == "rank_reshuffle":
            n_affected = max(int(top_k * magnitude_frac), 1)
            affected = rng.choice(top_k, size=n_affected, replace=False).tolist()
        else:  # cold_key_burst
            n_affected = max(int(num_keys * magnitude_frac * 0.02), 1)  # small absolute burst set
            cold_pool = np.arange(top_k, num_keys)
            n_affected = min(n_affected, len(cold_pool))
            affected = rng.choice(cold_pool, size=n_affected, replace=False).tolist()
        events.append(
            {
                "event_id": eid,
                "event_type": event_type,
                "start_index": int(idx),
                "end_index": int(end),
                "magnitude_frac": magnitude_frac,
                "affected_keys": affected,
            }
        )
        idx += period
        eid += 1
    return events


def generate_trace_vectorized(
    trace_id: str,
    alpha: float,
    seed: int,
    has_drift: bool,
    event_type: str | None,
    magnitude_frac: float | None,
    freq_frac: float | None,
) -> tuple[np.ndarray, np.ndarray, list[dict]]:
    """Vectorized generator: samples ranks in chunks between drift events, remaps to key ids."""
    rng = np.random.default_rng(seed)
    probs = zipf_probs(NUM_KEYS, alpha)
    rank_to_key = rng.permutation(NUM_KEYS).astype(np.int64)  # rank r -> key id

    drift_events: list[dict] = []
    if has_drift:
        drift_events = make_drift_events(
            rng, NUM_REQUESTS, event_type, magnitude_frac, freq_frac, NUM_KEYS, TOP_K
        )

    boundaries = sorted({0, NUM_REQUESTS} | {e["start_index"] for e in drift_events} | {e["end_index"] for e in drift_events})
    keys_out = np.empty(NUM_REQUESTS, dtype=np.int64)
    times_out = np.empty(NUM_REQUESTS, dtype=np.float64)

    cur_probs = probs.copy()
    active_burst_keys: set[int] = set()
    t_cursor = 0.0
    inter_arrival_mean = 1.0  # 1 time unit per request baseline

    for seg_start, seg_end in zip(boundaries[:-1], boundaries[1:]):
        # apply any events starting exactly at seg_start
        for ev in drift_events:
            if ev["start_index"] == seg_start:
                if ev["event_type"] == "rank_reshuffle":
                    affected_ranks = np.array(ev["affected_keys"])
                    shuffled = rng.permutation(affected_ranks)
                    rank_to_key[affected_ranks] = rank_to_key[shuffled]
                else:
                    active_burst_keys.update(ev["affected_keys"])
            if ev["end_index"] == seg_start and ev["event_type"] == "cold_key_burst":
                active_burst_keys.difference_update(ev["affected_keys"])

        n = seg_end - seg_start
        if n <= 0:
            continue
        if active_burst_keys:
            boosted = cur_probs.copy()
            burst_idx = np.array(sorted(active_burst_keys))
            boosted[burst_idx] += 50.0 * probs[0]
            boosted /= boosted.sum()
            ranks = rng.choice(NUM_KEYS, size=n, p=boosted)
        else:
            ranks = rng.choice(NUM_KEYS, size=n, p=cur_probs)
        keys_out[seg_start:seg_end] = rank_to_key[ranks]
        # Poisson-ish inter-arrival times
        gaps = rng.exponential(inter_arrival_mean, size=n)
        times_out[seg_start:seg_end] = t_cursor + np.cumsum(gaps)
        t_cursor = times_out[seg_end - 1] if n > 0 else t_cursor

    return keys_out, times_out, drift_events


def main() -> None:
    manifest: dict[str, dict] = {}
    trace_counter = 0
    for alpha in ALPHAS:
        # --- control (no drift) ---
        trace_id = f"synthetic_zipf_alpha{alpha}_control"
        seed = SEED_BASE + trace_counter
        logger.info(f"Generating {trace_id} (seed={seed})")
        keys, times, events = generate_trace_vectorized(trace_id, alpha, seed, False, None, None, None)
        save_trace(trace_id, keys, times, events, alpha, False, manifest)
        trace_counter += 1

        for sc in DRIFT_SCENARIOS:
            event_type, mag, mag_name, freq, freq_name = (
                sc["event_type"], sc["magnitude_frac"], sc["mag_name"], sc["freq_frac"], sc["freq_name"]
            )
            trace_id = f"synthetic_zipf_alpha{alpha}_{event_type}_mag-{mag_name}_freq-{freq_name}"
            seed = SEED_BASE + trace_counter
            logger.info(f"Generating {trace_id} (seed={seed})")
            keys, times, events = generate_trace_vectorized(
                trace_id, alpha, seed, True, event_type, mag, freq
            )
            save_trace(trace_id, keys, times, events, alpha, True, manifest)
            trace_counter += 1

    manifest_path = OUT_DIR / "synthetic_zipf_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    logger.info(f"Wrote manifest with {len(manifest)} synthetic traces to {manifest_path}")


def save_trace(
    trace_id: str,
    keys: np.ndarray,
    times: np.ndarray,
    events: list[dict],
    alpha: float,
    is_drift: bool,
    manifest: dict,
) -> None:
    """Save as CSV (key,arrival_time,trace_id,is_synthetic,drift_scenario_id) -- far more
    compact than JSON-list-of-dicts for 200K-row traces, keeping the collection under budget."""
    import csv as csv_mod

    scenario_id = trace_id if is_drift else "none"
    out_path = OUT_DIR / f"full_{trace_id}.csv"
    with out_path.open("w", newline="") as f:
        writer = csv_mod.writer(f)
        writer.writerow(["key", "arrival_time", "trace_id", "is_synthetic", "drift_scenario_id"])
        for k, t in zip(keys, times):
            writer.writerow([f"k{int(k)}", round(float(t), 4), trace_id, True, scenario_id])
    manifest[trace_id] = {
        "source": "synthetic_zipf_generator",
        "is_synthetic": True,
        "alpha": alpha,
        "drift_scenario_id": scenario_id,
        "num_requests": int(len(keys)),
        "num_unique_keys": int(len(set(keys.tolist()))),
        "drift_event_list": events,
        "file": out_path.name,
    }
    logger.info(f"  saved {out_path} ({out_path.stat().st_size / 1e6:.2f} MB, {len(keys)} rows)")


if __name__ == "__main__":
    Path("logs").mkdir(exist_ok=True)
    main()
