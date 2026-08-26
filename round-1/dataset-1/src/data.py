#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["loguru"]
# ///
"""Standardize the 4 cache-access-trace datasets (1 real Twitter memcached trace +
3 synthetic Zipf-with-drift traces) into the exp_sel_data_out.json schema: one
example PER ROW, grouped by dataset.
"""
import json
import sys
from pathlib import Path

from loguru import logger

logger.remove()
logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss}|{level:<7}|{message}")
logger.add("logs/data.log", rotation="30 MB", level="DEBUG")

WS = Path(__file__).parent
DATASETS_DIR = WS / "temp" / "datasets"

DATASET_FILES = [
    "full_real_twitter_cache_trace.json",
    "full_synthetic_zipf_alpha08.json",
    "full_synthetic_zipf_alpha10.json",
    "full_synthetic_zipf_alpha12.json",
]


def row_to_example(row: dict) -> dict:
    """One trace row -> one exp_sel_data_out example. input/output are strings
    (schema requirement); all other fields flatten into metadata_* keys."""
    inp = row["input"]
    meta = row["metadata"]
    example = {
        "input": json.dumps(
            {
                "seq": inp["seq"],
                "timestamp": inp["timestamp"],
                "key": inp["key"],
                "trace_id": inp["trace_id"],
                "request_type": inp["request_type"],
            }
        ),
        "output": str(row["output"]),
        "metadata_fold": row["metadata_fold"],
        "metadata_seq": inp["seq"],
        "metadata_key": inp["key"],
        "metadata_trace_id": inp["trace_id"],
        "metadata_request_type": inp["request_type"],
        "metadata_source": meta["source"],
        "metadata_drift_event": meta["drift_event"],
        "metadata_alpha": meta["alpha"],
        "metadata_trace_name": meta["trace_name"],
    }
    # extra real-trace-only fields (key_size, value_size, client_id, ttl, provenance)
    for extra_key in ("key_size", "value_size", "client_id", "ttl", "provenance"):
        if extra_key in meta:
            example[f"metadata_{extra_key}"] = meta[extra_key]
    return example


TARGET_PART_BYTES = 90_000_000  # keep each split part safely under the 100MB cap


def main():
    meta = {
        "source": "twitter/cache-trace (real, OSDI'20 CacheLib) + synthetic Zipf-with-drift generator",
        "description": "Cache access traces (real + synthetic-with-ground-truth-drift) for cache admission policy experiments",
    }
    out_datasets = []
    for fname in DATASET_FILES:
        path = DATASETS_DIR / fname
        logger.info(f"loading {path}")
        rows = json.loads(path.read_text())
        dataset_name = fname.removeprefix("full_").removesuffix(".json")
        examples = [row_to_example(r) for r in rows]
        logger.info(f"{dataset_name}: {len(examples)} examples")
        out_datasets.append({"dataset": dataset_name, "examples": examples})

    total = sum(len(d["examples"]) for d in out_datasets)

    # mini/preview: small combined file with 3 examples per dataset (all datasets nested)
    def trunc(o):
        if isinstance(o, str) and len(o) > 200:
            return o[:200]
        if isinstance(o, dict):
            return {k: trunc(v) for k, v in o.items()}
        if isinstance(o, list):
            return [trunc(v) for v in o]
        return o

    # per-dataset standalone files (bare name, no extension) required by the pipeline
    # verifier. Each MUST stay under the 100MB GitHub deploy cap: write as a single
    # bare file when small enough, otherwise split into <name>_parts/<name>_part_N.json
    # and remove any stale bare file / parts dir from a previous run.
    for d in out_datasets:
        name, examples = d["dataset"], d["examples"]
        bare_path = WS / name
        parts_dir = WS / f"{name}_parts"
        if bare_path.exists():
            bare_path.unlink()
        if parts_dir.exists():
            for f in parts_dir.glob("*.json"):
                f.unlink()

        full_bytes = len(json.dumps({"metadata": meta, "datasets": [d]}))
        if full_bytes <= TARGET_PART_BYTES:
            bare_path.write_text(json.dumps({"metadata": meta, "datasets": [d]}))
        else:
            parts_dir.mkdir(exist_ok=True)
            sample_n = min(200, len(examples))
            bytes_per_example = len(json.dumps(examples[:sample_n])) / sample_n
            chunk_n = max(1, int(TARGET_PART_BYTES / bytes_per_example))
            part_idx = 1
            for i in range(0, len(examples), chunk_n):
                part = examples[i : i + chunk_n]
                (parts_dir / f"{name}_part_{part_idx}.json").write_text(
                    json.dumps({"metadata": meta, "datasets": [{"dataset": name, "examples": part}]})
                )
                part_idx += 1

    mini = {"metadata": meta, "datasets": [{"dataset": d["dataset"], "examples": d["examples"][:3]} for d in out_datasets]}
    (WS / "mini_data_out.json").write_text(json.dumps(mini, indent=2))
    preview = {
        "metadata": meta,
        "datasets": [{"dataset": d["dataset"], "examples": [trunc(e) for e in d["examples"][:3]]} for d in out_datasets],
    }
    (WS / "preview_data_out.json").write_text(json.dumps(preview, indent=2))

    # full: split per-dataset into <100MB parts (aii-file-size-limit skill) since the
    # combined file is ~1.3GB. Parts live under full_data_out/full_data_out_<n>.json.
    split_dir = WS / "full_data_out"
    split_dir.mkdir(exist_ok=True)
    for f in split_dir.glob("full_data_out_*.json"):
        f.unlink()
    part_idx = 1
    manifest: dict[str, list[str]] = {}
    for d in out_datasets:
        name, examples = d["dataset"], d["examples"]
        sample_n = min(200, len(examples))
        bytes_per_example = len(json.dumps(examples[:sample_n])) / sample_n
        chunk_n = max(1, int(TARGET_PART_BYTES / bytes_per_example))
        manifest[name] = []
        for i in range(0, len(examples), chunk_n):
            part = examples[i : i + chunk_n]
            part_fname = f"full_data_out_{part_idx}.json"
            (split_dir / part_fname).write_text(
                json.dumps({"metadata": meta, "datasets": [{"dataset": name, "examples": part}]})
            )
            manifest[name].append(part_fname)
            part_idx += 1
    (split_dir / "_manifest.json").write_text(json.dumps(manifest, indent=2))

    logger.info(f"saved {total} total examples across {part_idx - 1} full-data parts + mini/preview")


if __name__ == "__main__":
    main()
