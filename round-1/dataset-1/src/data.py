#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["loguru"]
# ///
"""Standardize cache-access traces from temp/datasets/ into exp_sel_data_out.json schema.

One example per request row (key, arrival_time, trace_id, is_synthetic, drift_scenario_id).
Examples are grouped by dataset (= trace_id). Row count per trace is capped at
MAX_EXAMPLES_PER_TRACE to keep the output file tractable; the full uncapped trace CSVs
remain in temp/datasets/ for any downstream code that needs the complete stream.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from loguru import logger

logger.remove()
logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss}|{level:<7}|{message}")
logger.add("logs/data.log", rotation="30 MB", level="DEBUG")

DATA_DIR = Path("temp/datasets")
MANIFEST_PATH = DATA_DIR / "manifest.json"
OUT_PATH = Path("full_data_out.json")
MAX_EXAMPLES_PER_TRACE = 20_000

# FINAL 10 (down from the 15 candidates reviewed via preview_full_data_out.json): both
# real sources kept (irreplaceable ground truth), plus one no-drift control per alpha
# (0.8/1.0/1.2) and 5 drift scenarios spanning both event types (rank_reshuffle /
# cold_key_burst) and both magnitude/frequency combos, so every alpha, every drift type,
# and every magnitude x frequency cell is represented at least once.
SELECTED_TRACE_IDS = [
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


def load_trace_examples(trace_id: str, meta: dict) -> list[dict]:
    csv_path = DATA_DIR / meta["file"]
    examples = []
    with csv_path.open(newline="") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= MAX_EXAMPLES_PER_TRACE:
                break
            input_obj = {
                "key": row["key"],
                "arrival_time": float(row["arrival_time"]),
                "row_index": i,
            }
            example = {
                "input": json.dumps(input_obj),
                "output": row["key"],
                "metadata_trace_id": trace_id,
                "metadata_is_synthetic": row["is_synthetic"] == "True",
                "metadata_drift_scenario_id": row["drift_scenario_id"],
                "metadata_row_index": i,
            }
            if meta.get("alpha") is not None:
                example["metadata_alpha"] = meta["alpha"]
            examples.append(example)
    return examples


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text())
    datasets = []
    for trace_id in SELECTED_TRACE_IDS:
        if trace_id not in manifest:
            logger.error(f"Trace id {trace_id} not found in manifest; skipping")
            continue
        meta = manifest[trace_id]
        logger.info(f"Loading {trace_id} (source={meta['source'][:60]}...)")
        examples = load_trace_examples(trace_id, meta)
        logger.info(f"  -> {len(examples)} examples (of {meta['num_requests']} total rows)")
        datasets.append({"dataset": trace_id, "examples": examples})

    output = {
        "metadata": {
            "description": "Standardized cache-access request traces for evaluating "
            "cache admission policies under skewed and time-varying key popularity.",
            "num_datasets": len(datasets),
            "max_examples_per_trace": MAX_EXAMPLES_PER_TRACE,
        },
        "datasets": datasets,
    }
    OUT_PATH.write_text(json.dumps(output))
    total_examples = sum(len(d["examples"]) for d in datasets)
    logger.info(f"Wrote {OUT_PATH} with {len(datasets)} datasets, {total_examples} total examples "
                f"({OUT_PATH.stat().st_size / 1e6:.2f} MB)")


if __name__ == "__main__":
    Path("logs").mkdir(exist_ok=True)
    main()
