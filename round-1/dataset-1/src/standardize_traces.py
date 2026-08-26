#!/usr/bin/env python3
"""Standardize real + synthetic traces into the common schema and build the top-level manifest.

Common row schema: (key, arrival_time, trace_id, is_synthetic, drift_scenario_id)
Top-level manifest.json: trace_id -> {source, is_synthetic, alpha, drift_scenario_id,
                                       num_requests, num_unique_keys, drift_event_list, file}
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from loguru import logger

logger.remove()
logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss}|{level:<7}|{message}")
logger.add("logs/standardize_traces.log", rotation="30 MB", level="DEBUG")

DATA_DIR = Path("temp/datasets")
MANIFEST_PATH = DATA_DIR / "manifest.json"


def standardize_twitter_trace() -> dict:
    """Twitter/CMU cache-trace cluster026 sample: timestamp,key,key_size,value_size,client_id,op,ttl."""
    src = DATA_DIR / "twitter_cluster026_raw.csv"
    trace_id = "real_twitter_cache_trace_cluster026"
    out_path = DATA_DIR / f"full_{trace_id}.csv"
    n_rows = 0
    keys_seen = set()
    with src.open(newline="") as f_in, out_path.open("w", newline="") as f_out:
        reader = csv.reader(f_in)
        writer = csv.writer(f_out)
        writer.writerow(["key", "arrival_time", "trace_id", "is_synthetic", "drift_scenario_id"])
        for r in reader:
            if len(r) < 7:
                continue
            timestamp, key = r[0], r[1]
            writer.writerow([key, float(timestamp), trace_id, False, "none"])
            n_rows += 1
            keys_seen.add(key)
    unique_keys = len(keys_seen)
    logger.info(f"Standardized {trace_id}: {n_rows} rows, {unique_keys} unique keys -> {out_path}")
    return {
        trace_id: {
            "source": "twitter/cache-trace GitHub samples/2020Mar/cluster026 "
            "(Yang, Yue, Vinayak, OSDI 2020; github.com/twitter/cache-trace)",
            "is_synthetic": False,
            "alpha": None,
            "drift_scenario_id": "none",
            "num_requests": n_rows,
            "num_unique_keys": unique_keys,
            "drift_event_list": [],
            "provenance_note": "Real production memcached/Pelikan request-level trace, "
            "anonymized keys, one of Twitter's 54 production clusters (Mar 2020 snapshot).",
            "file": out_path.name,
        }
    }


def standardize_wikipedia_trace(max_rows: int | None = None) -> dict:
    """Wikimedia pageviews-by-second, expanded into synthetic per-article arrival timestamps.

    Source rows are (timestamp, site, requests) counts at 1-second resolution, aggregated
    across all English Wikipedia articles (not per-article) -- so "key" here is the
    (site) bucket at that second; each of `requests` counts is expanded into one synthetic
    arrival uniformly within that 1-second window. Every row is flagged is_synthetic=True
    with an explicit provenance note since only the counts are real, not individual timestamps.
    """
    import glob

    candidates = sorted(glob.glob(str(DATA_DIR / "full_wikimedia-community_*.json")))
    if not candidates:
        logger.warning("Wikipedia pageviews file not found; skipping this source.")
        return {}
    src = Path(candidates[0])
    raw = json.loads(src.read_text())
    # Sort by timestamp and take a contiguous 3-week-equivalent window (subsample every
    # Nth bucket) so the derived trace covers real temporal drift without blowing the
    # size budget: source has 7.2M (second, site) count-buckets over ~40 days.
    raw.sort(key=lambda r: r["timestamp"])
    raw = raw[::100]  # keep every 100th bucket -> ~72K buckets spread across the full 40-day window
    if max_rows:
        raw = raw[:max_rows]

    import csv as csv_mod
    import datetime
    import random

    rng = random.Random(20260826)
    trace_id = "real_derived_wikipedia_pageviews_by_second"
    out_path = DATA_DIR / f"full_{trace_id}.csv"
    n_rows = 0
    keys_seen = set()
    with out_path.open("w", newline="") as f:
        writer = csv_mod.writer(f)
        writer.writerow(["key", "arrival_time", "trace_id", "is_synthetic", "drift_scenario_id"])
        for rec in raw:
            ts, site, count = rec["timestamp"], rec["site"], int(rec["requests"])
            base = datetime.datetime.fromisoformat(ts).timestamp()
            n = min(count, 3)  # cap per-bucket expansion tightly to bound total size
            for _ in range(n):
                jitter = rng.uniform(0, 1.0)
                writer.writerow([site, round(base + jitter, 4), trace_id, True, "none"])
                n_rows += 1
                keys_seen.add(site)
    unique_keys = len(keys_seen)
    logger.info(f"Standardized {trace_id}: {n_rows} rows, {unique_keys} unique keys -> {out_path}")
    return {
        trace_id: {
            "source": "wikimedia-community/english-wikipedia-pageviews-by-second (HuggingFace); "
            "original: Os Keyes, datahub.io english-wikipedia-pageviews-by-second, "
            "2015-03-16 to 2015-04-25, 1-second resolution, mobile/desktop site buckets",
            "is_synthetic": True,
            "alpha": None,
            "drift_scenario_id": "none",
            "num_requests": n_rows,
            "num_unique_keys": unique_keys,
            "drift_event_list": [],
            "provenance_note": "Derived from REAL Wikipedia pageview COUNTS aggregated per "
            "(second, site); individual request timestamps were synthesized (uniform jitter "
            "within each 1-second bucket, count capped at 3/bucket, buckets subsampled every "
            "100th to bound file size while preserving the full 2015-03-16..2015-04-25 window) "
            "since the source only records counts, not per-request timestamps. Flagged "
            "is_synthetic=true throughout.",
            "file": out_path.name,
        }
    }


def merge_synthetic_manifest() -> dict:
    syn_manifest_path = DATA_DIR / "synthetic_zipf_manifest.json"
    if not syn_manifest_path.exists():
        logger.warning("Synthetic Zipf manifest not found; skipping.")
        return {}
    syn = json.loads(syn_manifest_path.read_text())
    for tid, meta in syn.items():
        meta["provenance_note"] = (
            "Purely synthetic: deterministic seeded Zipf-distributed key access generator "
            "with injected rank-reshuffle / cold-key-burst drift events; ground-truth drift "
            "event start/end indices and affected keys are recorded per trace."
        )
    logger.info(f"Merged {len(syn)} synthetic Zipf traces into manifest.")
    return syn


def main() -> None:
    manifest: dict = {}
    manifest.update(standardize_twitter_trace())
    manifest.update(standardize_wikipedia_trace())
    manifest.update(merge_synthetic_manifest())
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))
    logger.info(f"Wrote top-level manifest with {len(manifest)} traces to {MANIFEST_PATH}")

    total_bytes = sum((DATA_DIR / m["file"]).stat().st_size for m in manifest.values())
    logger.info(f"Total collection size: {total_bytes / 1e6:.2f} MB")


if __name__ == "__main__":
    Path("logs").mkdir(exist_ok=True)
    main()
