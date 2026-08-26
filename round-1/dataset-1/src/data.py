#!/usr/bin/env python3
"""Build the final cache-access-trace dataset (best 10 of 13 candidate traces):
9 synthetic Zipf-drift traces (loaded via a deterministic seeded generator) +
1 real e-commerce clickstream trace (RetailRocket events.csv, itemid-as-key,
loaded from temp/datasets/), standardized into the exp_sel_data_out.json
schema (datasets[].examples[].input/output/metadata_*).
"""
from __future__ import annotations

import csv
import json
import resource
import sys
from pathlib import Path

import numpy as np
from loguru import logger

logger.remove()
logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss}|{level:<7}|{message}")
Path("logs").mkdir(exist_ok=True)
logger.add("logs/run.log", rotation="30 MB", level="DEBUG")

# RAM budget: this box has a 57GB container limit; cap this script well under it.
RAM_BUDGET_BYTES = 8 * 1024**3
resource.setrlimit(resource.RLIMIT_AS, (RAM_BUDGET_BYTES * 3, RAM_BUDGET_BYTES * 3))

WORKSPACE = Path(__file__).resolve().parent
EVENTS_CSV = WORKSPACE / "temp" / "datasets" / "full_retailrocket_events.csv"
OUT_DIR = WORKSPACE / "full_data_out"
# Split point: 6 synthetic traces in part 1 (~87MB), remaining 3 synthetic +
# the real trace in part 2 (~91MB) -- both under the 100MB file size limit.
SPLIT_AT = 6

# ---------------------------------------------------------------------------
# Synthetic Zipf-drift generator
# ---------------------------------------------------------------------------

KEY_SPACE = 50_000          # distinct keys per synthetic trace
TRACE_LEN = 80_000          # requests per synthetic trace (size-budgeted down
                             # from the plan's 1-2M target; documented in README)
DRIFT_TYPES = ["rank_shuffle", "cold_burst", "combined", "slow_drift"]

# Best-10 selection (from the prior 13-dataset candidate pool): cover all 4
# drift types at the canonical alpha=1.0, repeat at alpha=0.8 for robustness
# across the heavy-tail regime that numpy's native zipf() cannot represent,
# and add the single alpha=1.2 variant of the best-covered/most-informative
# scenario ("combined", since it stresses both abrupt-drift mechanisms at
# once) rather than the full 3x4 matrix — per the plan's own fallback
# instruction ("prioritize covering all 4 drift types at one canonical alpha,
# then add alpha variants only for the best-covered scenario if time/budget
# is constrained"). This drops synthetic_alpha0.8_slow_drift and
# synthetic_alpha1.2_{rank_shuffle,cold_burst,slow_drift} relative to the
# full 12-trace matrix, keeping the 9 most informative synthetic configs.
SELECTED_SYNTHETIC = [
    (0.8, "rank_shuffle"), (0.8, "cold_burst"), (0.8, "combined"),
    (1.0, "rank_shuffle"), (1.0, "cold_burst"), (1.0, "combined"), (1.0, "slow_drift"),
    (1.2, "combined"),
    (0.8, "slow_drift"),
]  # 9 synthetic traces


_ZIPF_CDF_CACHE: dict[tuple[float, int], np.ndarray] = {}


def _zipf_cdf(alpha: float, key_space: int) -> np.ndarray:
    """Finite-support Zipf(alpha) CDF over ranks 1..key_space, cached per
    (alpha, key_space). Works for any alpha > 0 (numpy's rng.zipf requires
    alpha > 1, which excludes the plan's alpha=0.8 heavy-tail configs used in
    TinyLFU/Caffeine-style evaluations), via explicit inverse-CDF sampling."""
    cache_key = (alpha, key_space)
    if cache_key not in _ZIPF_CDF_CACHE:
        ranks = np.arange(1, key_space + 1, dtype=np.float64)
        weights = ranks ** (-alpha)
        cdf = np.cumsum(weights)
        cdf /= cdf[-1]
        _ZIPF_CDF_CACHE[cache_key] = cdf
    return _ZIPF_CDF_CACHE[cache_key]


def zipf_ranks_to_keys(rng: np.random.Generator, n: int, key_space: int, alpha: float) -> np.ndarray:
    """Sample n draws from a finite-support Zipf(alpha) law over `key_space`
    ranks via inverse-CDF, mapped to a fixed random key-id permutation so
    'rank 0' isn't always key-id 0."""
    cdf = _zipf_cdf(alpha, key_space)
    u = rng.random(n)
    ranks = np.searchsorted(cdf, u, side="right")
    return np.clip(ranks, 0, key_space - 1)


def build_permutation(rng: np.random.Generator, key_space: int) -> np.ndarray:
    """rank -> key_id mapping."""
    return rng.permutation(key_space)


def generate_trace(seed: int, alpha: float, drift_type: str, key_space: int = KEY_SPACE,
                    length: int = TRACE_LEN) -> dict:
    rng = np.random.default_rng(seed)
    perm = build_permutation(rng, key_space)  # rank -> key_id, mutated in place on shuffle events

    keys = np.empty(length, dtype=np.int64)
    drift_events = []  # list of {request_index, type, magnitude, affected_keys}

    if drift_type == "rank_shuffle":
        interval = 50_000
        frac = 0.20
        top_k = 1000
        pos = 0
        while pos < length:
            seg_end = min(pos + interval, length)
            ranks = zipf_ranks_to_keys(rng, seg_end - pos, key_space, alpha)
            keys[pos:seg_end] = perm[ranks]
            pos = seg_end
            if pos < length:
                n_shuf = int(top_k * frac)
                idx = rng.choice(top_k, size=n_shuf, replace=False)
                shuffled = rng.permutation(idx)
                perm[:top_k][idx] = perm[:top_k][shuffled]
                drift_events.append({
                    "request_index": int(pos), "type": "rank_shuffle",
                    "magnitude": frac, "affected_key_count": int(n_shuf),
                })

    elif drift_type == "cold_burst":
        burst_every = 40_000
        burst_len = 5_000
        burst_starts = set(range(burst_every, length, burst_every))
        pos = 0
        while pos < length:
            if pos in burst_starts:
                cold_rank = rng.integers(int(key_space * 0.5), key_space)
                cold_key = int(perm[cold_rank])
                seg_end = min(pos + burst_len, length)
                keys[pos:seg_end] = cold_key
                drift_events.append({
                    "request_index": int(pos), "type": "cold_burst",
                    "magnitude": burst_len, "affected_key_count": 1,
                    "burst_key_id": cold_key,
                })
                pos = seg_end
            else:
                nxt = min([b for b in burst_starts if b > pos] + [length])
                ranks = zipf_ranks_to_keys(rng, nxt - pos, key_space, alpha)
                keys[pos:nxt] = perm[ranks]
                pos = nxt

    elif drift_type == "combined":
        interval = 50_000
        frac = 0.20
        top_k = 1000
        burst_every = 40_000
        burst_len = 3_000
        pos = 0
        next_shuffle = interval
        next_burst = burst_every
        while pos < length:
            nxt = min(next_shuffle, next_burst, length)
            if nxt > pos:
                ranks = zipf_ranks_to_keys(rng, nxt - pos, key_space, alpha)
                keys[pos:nxt] = perm[ranks]
                pos = nxt
            if pos == next_shuffle and pos < length:
                n_shuf = int(top_k * frac)
                idx = rng.choice(top_k, size=n_shuf, replace=False)
                shuffled = rng.permutation(idx)
                perm[:top_k][idx] = perm[:top_k][shuffled]
                drift_events.append({
                    "request_index": int(pos), "type": "rank_shuffle",
                    "magnitude": frac, "affected_key_count": int(n_shuf),
                })
                next_shuffle += interval
            if pos == next_burst and pos < length:
                cold_rank = rng.integers(int(key_space * 0.5), key_space)
                cold_key = int(perm[cold_rank])
                seg_end = min(pos + burst_len, length)
                keys[pos:seg_end] = cold_key
                drift_events.append({
                    "request_index": int(pos), "type": "cold_burst",
                    "magnitude": burst_len, "affected_key_count": 1,
                    "burst_key_id": cold_key,
                })
                pos = seg_end
                next_burst += burst_every

    elif drift_type == "slow_drift":
        step = 10_000
        n_swaps_per_step = 20
        top_k = 2000
        pos = 0
        while pos < length:
            seg_end = min(pos + step, length)
            ranks = zipf_ranks_to_keys(rng, seg_end - pos, key_space, alpha)
            keys[pos:seg_end] = perm[ranks]
            pos = seg_end
            if pos < length:
                swap_idx = rng.integers(0, top_k - 1, size=n_swaps_per_step)
                perm[swap_idx], perm[swap_idx + 1] = perm[swap_idx + 1].copy(), perm[swap_idx].copy()
                drift_events.append({
                    "request_index": int(pos), "type": "slow_drift",
                    "magnitude": n_swaps_per_step, "affected_key_count": n_swaps_per_step * 2,
                })
    else:
        raise ValueError(drift_type)

    timestamps = np.arange(length, dtype=np.int64)  # sequential index stands in for time
    trace_id = f"synthetic_alpha{alpha}_{drift_type}"
    return {
        "trace_id": trace_id,
        "keys": keys,
        "timestamps": timestamps,
        "drift_events": drift_events,
        "meta": {
            "generator": "zipf_drift_v1", "seed": seed, "alpha": alpha,
            "drift_type": drift_type, "key_space": key_space, "trace_length": length,
        },
    }


def trace_to_examples(trace: dict, is_synthetic: bool, fold_boundaries=(0.7, 0.85)) -> list[dict]:
    """One example per request row (row-level granularity, not per-dataset)."""
    n = len(trace["keys"])
    train_end = int(n * fold_boundaries[0])
    val_end = int(n * fold_boundaries[1])
    drift_by_idx: dict[int, list[dict]] = {}
    for ev in trace["drift_events"]:
        drift_by_idx.setdefault(ev["request_index"], []).append(ev)

    examples = []
    for i in range(n):
        fold = "train" if i < train_end else ("val" if i < val_end else "test")
        row = {"t": int(trace["timestamps"][i]), "k": int(trace["keys"][i])}
        ex = {
            "input": json.dumps(row, separators=(",", ":")),
            "output": "",
            "metadata_fold": fold,
            "metadata_trace_id": trace["trace_id"],
            "metadata_is_synthetic": is_synthetic,
            "metadata_row_index": i,
        }
        if i in drift_by_idx:
            ex["metadata_drift_event"] = drift_by_idx[i]
        examples.append(ex)
    return examples


def build_synthetic_datasets() -> list[dict]:
    datasets = []
    for seed, (alpha, drift_type) in enumerate(SELECTED_SYNTHETIC):
        logger.info(f"Generating synthetic trace alpha={alpha} drift={drift_type}")
        trace = generate_trace(seed=seed, alpha=alpha, drift_type=drift_type)
        examples = trace_to_examples(trace, is_synthetic=True)
        datasets.append({"dataset": trace["trace_id"], "examples": examples})
        logger.info(
            f"  -> {len(examples)} rows (examples), {len(trace['drift_events'])} drift "
            f"events, params={trace['meta']}"
        )
    return datasets


# ---------------------------------------------------------------------------
# Real trace: RetailRocket e-commerce clickstream events.csv (itemid-as-key)
# ---------------------------------------------------------------------------

REAL_SAMPLE_STRIDE = 12     # keep every Nth row -> spans full time range
REAL_MAX_ROWS = 250_000


def build_real_dataset() -> dict:
    if not EVENTS_CSV.exists():
        raise FileNotFoundError(
            f"{EVENTS_CSV} not found. Expected the RetailRocket events.csv "
            "downloaded from DanielKiani/RetailRocket-Recommender-Data (HF "
            "mirror of the Kaggle RetailRocket dataset) at temp/datasets/."
        )
    logger.info(f"Loading real trace from {EVENTS_CSV}")
    rows = []
    with EVENTS_CSV.open() as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i % REAL_SAMPLE_STRIDE != 0:
                continue
            rows.append((int(row["timestamp"]), int(row["itemid"]), row["event"], row["visitorid"]))
            if len(rows) >= REAL_MAX_ROWS:
                break
    rows.sort(key=lambda r: r[0])  # ensure chronological order after striding
    logger.info(f"Loaded {len(rows)} real events (strided from full 2,756,101-row file)")

    n = len(rows)
    train_end = int(n * 0.7)
    val_end = int(n * 0.85)
    examples = []
    for i, (ts, itemid, event, visitor) in enumerate(rows):
        fold = "train" if i < train_end else ("val" if i < val_end else "test")
        payload = {"t": ts, "k": itemid, "event": event}
        examples.append({
            "input": json.dumps(payload, separators=(",", ":")),
            "output": "",
            "metadata_fold": fold,
            "metadata_trace_id": "real_retailrocket_events",
            "metadata_is_synthetic": False,
            "metadata_row_index": i,
        })
    return {"dataset": "real_retailrocket_events", "examples": examples}


def main() -> None:
    synthetic = build_synthetic_datasets()
    real = build_real_dataset()
    datasets = synthetic + [real]

    total_rows = sum(len(d["examples"]) for d in datasets)
    logger.info(f"Total datasets={len(datasets)} (best-10 selection), total examples={total_rows}")

    out = {
        "metadata": {
            "description": "Cache access traces for W-TinyLFU vs. per-key-decay admission "
                            "policy evaluation: best-10 selection (of 13 candidates) -- 9 "
                            "synthetic Zipf-skewed traces (drift-type coverage at alpha=1.0 "
                            "and alpha=0.8, plus one alpha=1.2 'combined' variant) + 1 real "
                            "e-commerce clickstream trace (RetailRocket events, itemid-as-key) "
                            "with genuine measured Zipf-like skew (top 1% of items receive "
                            "22.9% of accesses in the full 2.75M-row source file).",
            "selection_rationale": "Dropped synthetic_alpha1.2_{rank_shuffle,cold_burst,"
                                    "slow_drift} from the full 3-alpha x 4-drift-type matrix "
                                    "to reach 10 total datasets, per the plan's fallback "
                                    "instruction to prioritize full drift-type coverage at a "
                                    "canonical alpha (1.0) plus a robustness alpha (0.8), then "
                                    "add further alpha variants only for the most-informative "
                                    "scenario (combined, since it stresses both abrupt-drift "
                                    "mechanisms simultaneously).",
            "synthetic_generator_params": {
                "key_space": KEY_SPACE, "trace_length": TRACE_LEN,
                "selected_configs": [f"alpha={a}_{d}" for a, d in SELECTED_SYNTHETIC],
                "drift_types": DRIFT_TYPES,
                "note": "trace_length reduced from the plan's 1-2M target to 80k "
                        "requests/trace to respect the 300MB artifact size budget; "
                        "drift-event schedules (request-index, magnitude, affected-key-count) "
                        "are fully explicit per trace so recovery-time metrics remain exactly "
                        "reproducible at this scale.",
            },
            "real_trace_provenance": {
                "source": "DanielKiani/RetailRocket-Recommender-Data (HuggingFace mirror of "
                           "the RetailRocket e-commerce recommender dataset, originally "
                           "released for a Kaggle recommender-systems competition)",
                "file": "events.csv",
                "full_file_rows": 2_756_101,
                "full_file_unique_items": 235_061,
                "sampling": f"every {REAL_SAMPLE_STRIDE}th row kept (stride sample preserving "
                            f"chronological span), capped at {REAL_MAX_ROWS} rows, re-sorted "
                            "by timestamp",
                "measured_skew": "top 1% of items account for 22.9% of all view/addtocart/"
                                  "transaction events in the full file (Zipf-like)",
                "adaptation_note": "itemid is used as the cache 'key' and each row (view/"
                                    "addtocart/transaction) as one cache request; this is a "
                                    "genuine real-world skewed access log but is a "
                                    "recommender-clickstream proxy, not a native memcached/"
                                    "Redis trace -- no cache-native trace under 300MB was "
                                    "found reachable via HF search (see README).",
            },
        },
        "datasets": datasets,
    }

    OUT_DIR.mkdir(exist_ok=True)
    parts = [datasets[:SPLIT_AT], datasets[SPLIT_AT:]]
    for i, part in enumerate(parts, start=1):
        part_path = OUT_DIR / f"full_data_out_{i}.json"
        with part_path.open("w") as f:
            json.dump({"metadata": out["metadata"], "datasets": part}, f, separators=(",", ":"))
        size_mb = part_path.stat().st_size / 1e6
        logger.info(f"Wrote {part_path} ({size_mb:.1f} MB, {len(part)} datasets)")


if __name__ == "__main__":
    main()
