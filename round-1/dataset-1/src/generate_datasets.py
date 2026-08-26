#!/usr/bin/env python3
"""Build 4 cache-access-trace datasets: 1 real (Twitter memcached sample) + 3 synthetic
Zipf-with-drift traces (alpha in {0.8, 1.0, 1.2}), standardized to a shared JSON schema
with embedded ground-truth drift-event metadata for cache-admission-policy experiments.
"""
import json
import sys
from pathlib import Path

import numpy as np
from loguru import logger

logger.remove()
logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss}|{level:<7}|{message}")
logger.add("logs/run.log", rotation="30 MB", level="DEBUG")

WS = Path(__file__).parent
OUT_DIR = WS / "temp" / "datasets"
OUT_DIR.mkdir(parents=True, exist_ok=True)

RNG_SEED = 42


def make_zipf_ranks(num_keys: int, alpha: float, rng: np.random.Generator) -> np.ndarray:
    """Rank-based Zipf probability table over `num_keys` keys (ranks 1..num_keys)."""
    ranks = np.arange(1, num_keys + 1, dtype=np.float64)
    weights = 1.0 / np.power(ranks, alpha)
    return weights / weights.sum()


def generate_synthetic_trace(
    alpha: float,
    num_keys: int = 20_000,
    num_requests: int = 850_000,
    drift_period: int = 150_000,
    drift_frac_range: tuple[float, float] = (0.05, 0.20),
    num_bursts: int = 8,
    burst_window: tuple[int, int] = (5_000, 20_000),
    seed: int = RNG_SEED,
) -> tuple[list[tuple[int, int]], list[dict], np.ndarray]:
    """Generate one Zipf-with-drift trace. Returns (rows, drift_event_log, key_ids).

    Sampling is fully vectorized: the timeline is cut at every drift-reshuffle
    boundary and every burst start/end, each resulting sub-range has a FIXED
    per-key probability vector, and all keys for that sub-range are drawn in a
    single batched `rng.choice(..., size=seg_len, p=probs)` call. A running
    `rank_order` array (rank_order[rank] = key_idx currently holding that rank)
    is advanced in lockstep with the segments so later segments see prior drift.
    """
    rng = np.random.default_rng(seed)
    key_ids = np.array([f"k{alpha_tag(alpha)}_{i:06d}" for i in range(num_keys)])
    rank_order = np.arange(num_keys)  # rank_order[r] = key index currently at rank r
    base_probs = make_zipf_ranks(num_keys, alpha, rng)

    events: list[dict] = []

    # schedule periodic reshuffle drift events (magnitude + affected keys logged
    # against the rank_order state AT THE TIME the event fires, computed below)
    drift_seqs = list(range(drift_period, num_requests, drift_period))
    drift_plans = []
    for eidx, dseq in enumerate(drift_seqs):
        frac = rng.uniform(*drift_frac_range)
        n_affect = max(2, int(frac * num_keys))
        affected_ranks = rng.choice(num_keys, size=n_affect, replace=False)
        perm = rng.permutation(affected_ranks)
        drift_plans.append((dseq, affected_ranks, perm, frac, n_affect))

    # schedule random cold-key bursts (key chosen from the bottom 40% of the
    # ORIGINAL rank order — "previously cold" by construction)
    burst_starts = sorted(rng.choice(num_requests, size=num_bursts, replace=False).tolist())
    burst_defs = []
    for bidx, bstart in enumerate(burst_starts):
        cold_rank_start = int(num_keys * 0.6)
        cold_key_idx = int(rng.integers(cold_rank_start, num_keys))
        blen = int(rng.integers(*burst_window))
        weight_mult = float(rng.uniform(20, 80))
        bend = min(num_requests - 1, bstart + blen)
        burst_defs.append((bstart, bend, cold_key_idx, weight_mult, bidx))
        events.append(
            {
                "event_id": f"burst_{alpha_tag(alpha)}_{bidx:03d}",
                "type": "cold_key_burst",
                "seq": int(bstart),
                "end_seq": int(bend),
                "magnitude": weight_mult,
                "affected_keys": [str(key_ids[cold_key_idx])],
                "num_affected": 1,
            }
        )

    cutpoints = sorted(
        set([0, num_requests] + drift_seqs + [b[0] for b in burst_defs] + [min(b[1] + 1, num_requests) for b in burst_defs])
    )

    key_seq = np.empty(num_requests, dtype=np.int64)
    drift_by_seq = {dseq: plan for dseq, *plan in [(p[0], *p) for p in drift_plans]}

    for seg_start, seg_end in zip(cutpoints[:-1], cutpoints[1:]):
        seg_len = seg_end - seg_start
        if seg_len <= 0:
            continue
        # apply any drift reshuffle scheduled exactly at seg_start, so this
        # segment (and all later ones) sample under the updated ranking
        if seg_start in drift_by_seq:
            dseq, affected_ranks, perm, frac, n_affect = drift_by_seq[seg_start]
            old_key_at_rank = rank_order[affected_ranks].copy()
            rank_order[affected_ranks] = rank_order[perm]
            eidx = drift_seqs.index(dseq)
            events.append(
                {
                    "event_id": f"drift_{alpha_tag(alpha)}_{eidx:03d}",
                    "type": "rank_reshuffle",
                    "seq": int(dseq),
                    "magnitude": float(frac),
                    "affected_keys": [str(key_ids[k]) for k in old_key_at_rank[:50]],
                    "num_affected": int(n_affect),
                }
            )

        probs = np.empty(num_keys, dtype=np.float64)
        probs[rank_order] = base_probs  # key at rank_order[r] gets base_probs[r]
        active_bursts = [(ckey, wmult) for bs, be, ckey, wmult, _ in burst_defs if bs <= seg_start <= be]
        if active_bursts:
            probs = probs.copy()
            for ckey, wmult in active_bursts:
                probs[ckey] *= wmult
            probs = probs / probs.sum()
        sampled = rng.choice(num_keys, size=seg_len, p=probs)
        key_seq[seg_start:seg_end] = sampled

    events.sort(key=lambda e: e["seq"])
    rows = list(zip(range(num_requests), key_seq.tolist()))
    logger.info(f"alpha={alpha}: generated {len(rows)} rows, {len(events)} drift events")
    return rows, events, key_ids


def alpha_tag(alpha: float) -> str:
    return str(alpha).replace(".", "")


def rows_to_records(
    rows: list[tuple[int, int]],
    key_ids: np.ndarray,
    events: list[dict],
    alpha: float,
    trace_name: str,
) -> list[dict]:
    """Standardize (seq, key_idx) pairs into the shared JSON row schema."""
    n = len(rows)
    train_cut = int(n * 0.8)
    # sort events by seq for interval lookup
    event_starts = sorted(
        (
            (e["seq"], e.get("end_seq", e["seq"] + 2000), e["event_id"])
            for e in events
        )
    )
    records = []
    ev_ptr = 0
    active_events: list[tuple[int, int, str]] = []
    for i, (seq, key_idx) in enumerate(rows):
        while ev_ptr < len(event_starts) and event_starts[ev_ptr][0] <= seq:
            active_events.append(event_starts[ev_ptr])
            ev_ptr += 1
        active_events = [e for e in active_events if e[1] >= seq]
        drift_event = None
        for estart, eend, eid in active_events:
            if estart <= seq <= eend:
                drift_event = eid
                break
        key = str(key_ids[key_idx])
        records.append(
            {
                "input": {
                    "seq": seq,
                    "timestamp": float(seq),
                    "key": key,
                    "trace_id": trace_name,
                    "request_type": "GET",
                },
                "output": key,
                "metadata_fold": "train" if i < train_cut else "test",
                "metadata": {
                    "source": "synthetic",
                    "drift_event": drift_event,
                    "alpha": alpha,
                    "trace_name": trace_name,
                },
            }
        )
    return records


def load_real_trace(path: Path, trace_name: str = "twitter_cluster026") -> list[dict]:
    """Standardize the Twitter production memcached trace sample (OSDI'20 CacheLib paper)
    into the shared row schema. Columns: timestamp,key,key_size,value_size,client_id,op,ttl
    """
    lines = path.read_text().splitlines()
    n = len(lines)
    train_cut = int(n * 0.8)
    records = []
    for i, line in enumerate(lines):
        parts = line.split(",")
        if len(parts) != 7:
            continue
        ts, key, ksize, vsize, client_id, op, ttl = parts
        records.append(
            {
                "input": {
                    "seq": i,
                    "timestamp": float(ts),
                    "key": key,
                    "trace_id": trace_name,
                    "request_type": op,
                },
                "output": key,
                "metadata_fold": "train" if i < train_cut else "test",
                "metadata": {
                    "source": "real",
                    "drift_event": None,
                    "alpha": None,
                    "trace_name": trace_name,
                    "key_size": int(ksize),
                    "value_size": int(vsize),
                    "client_id": int(client_id),
                    "ttl": int(ttl),
                    "provenance": (
                        "Twitter production in-memory caching (Twemcache/Pelikan) trace, "
                        "sample cluster026 from github.com/twitter/cache-trace, "
                        "released alongside Yang et al. 'The CacheLib Caching Engine' OSDI 2020"
                    ),
                },
            }
        )
    logger.info(f"real trace {trace_name}: {len(records)} rows loaded")
    return records


def save_dataset(records: list[dict], name: str):
    out_path = OUT_DIR / f"full_{name}.json"
    out_path.write_text(json.dumps(records))
    logger.info(f"saved {name}: {len(records)} rows -> {out_path} ({out_path.stat().st_size/1e6:.1f} MB)")
    return out_path


def main():
    import resource

    resource.setrlimit(resource.RLIMIT_AS, (8 * 1024**3, 8 * 1024**3))

    # Real trace
    real_path = OUT_DIR / "twitter_cluster026.txt"
    real_records = load_real_trace(real_path)
    save_dataset(real_records, "real_twitter_cache_trace")

    # Synthetic traces
    for alpha in (0.8, 1.0, 1.2):
        rows, events, key_ids = generate_synthetic_trace(alpha, seed=RNG_SEED + int(alpha * 10))
        trace_name = f"synthetic_zipf_alpha{alpha}"
        records = rows_to_records(rows, key_ids, events, alpha, trace_name)
        # persist ground-truth event log separately too
        events_path = OUT_DIR / f"drift_events_alpha{alpha_tag(alpha)}.json"
        events_path.write_text(json.dumps(events, indent=2))
        save_dataset(records, f"synthetic_zipf_alpha{alpha_tag(alpha)}")

    logger.info("DONE")


if __name__ == "__main__":
    main()
