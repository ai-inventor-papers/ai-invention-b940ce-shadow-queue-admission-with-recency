# Cache access traces: synthetic drift + real key-value logs

`full_data_out.json` (170 MB, 949,676 row-level examples, schema
`exp_sel_data_out`) holds the **best 10** of 13 candidate traces. Each example
is one request: `input` = `{"t": timestamp/sequence-index, "k": key_id}` JSON
string, `output` = `""` (unlabeled request stream, not a supervised task).
`mini_full_data_out.json` / `preview_full_data_out.json` hold 3
examples/dataset for quick inspection. Regenerate with `uv run data.py`
(reads the real trace CSV from `temp/datasets/`).

## Selection: 9 synthetic + 1 real (dropped from the full 3x4 matrix)
Full drift-type coverage kept at the canonical alpha=1.0 and the robustness
alpha=0.8, plus one alpha=1.2 variant of the most-informative scenario
(`combined`, since it stresses both abrupt-drift mechanisms at once) — per
the plan's fallback instruction. Dropped: `alpha1.2_{rank_shuffle,cold_burst,
slow_drift}`.

## Synthetic family (9 traces): `synthetic_alpha{0.8,1.0,1.2}_{drift_type}`
- Deterministic, seeded (`numpy.random.default_rng`), finite-support Zipf(alpha)
  sampler over a 50,000-key space via inverse-CDF (numpy's `rng.zipf` requires
  alpha>1, excluding the plan's alpha=0.8 heavy-tail config).
- 80,000 requests/trace (reduced from the plan's 1-2M target to fit the 300MB
  budget across 10 datasets; exact generator params and drift schedule are in
  `metadata.synthetic_generator_params` and per-row `metadata_drift_event`
  markers, so recovery-time metrics stay reproducible).
- 4 drift types, each parameterized and logged as explicit drift events
  (`request_index`, `type`, `magnitude`, `affected_key_count`):
  - `rank_shuffle` — periodic 20%-of-top-1000 rank reshuffle every 50k requests
  - `cold_burst` — bursts on randomly chosen initially-cold keys (rank >= 50th
    percentile) every 40k requests
  - `combined` — both of the above overlaid
  - `slow_drift` — gradual linear rank walk (20 adjacent-rank swaps near the
    top every 10k requests)

## Real family (1 trace): `real_retailrocket_events`
- Source: RetailRocket e-commerce recommender dataset (Kaggle competition
  data), mirrored on HuggingFace as
  `DanielKiani/RetailRocket-Recommender-Data/data/events.csv`, saved locally
  at `temp/datasets/full_retailrocket_events.csv`.
- Real, timestamped clickstream: 2,756,101 view/addtocart/transaction events,
  235,061 unique items. Measured genuine Zipf-like skew: top 1% of items
  receive 22.9% of all events.
- itemid is used as the cache "key"; each row is one cache request.
  **Adaptation note**: real-world skewed access log but a
  recommender-clickstream proxy, not a native memcached/Redis trace — no
  cache-native trace under 300MB was found on HuggingFace search.
- Standardized subset: every 12th row kept (stride sample spanning the full
  time range), capped at 250,000 rows, re-sorted by timestamp -> 229,676 rows
  shipped.

## Search notes (real cache-native traces)
HF Hub searches for "cache trace", "memcached", "CDN access log", "web proxy
log", "network traffic trace" all returned 0 results. No public Twitter/
Twemcache-style production cache trace was found reachable within a 300MB
budget via HF search. `vtasca/wikipedia-pageviews` (top-100/day aggregates)
and `mindweave/web-server-logs` (explicitly synthetic) were considered and
rejected as weaker substitutes than RetailRocket's genuine per-event
clickstream, per the plan's documented fallback priority order.
