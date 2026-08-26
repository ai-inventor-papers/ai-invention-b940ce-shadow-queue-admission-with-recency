# upd_hypo — test_idea

> Phase: `invention_loop` · round 2 · `upd_hypo`
> Run: `iter1_eb86f00c4c5a` — Why Per-Key Cache Decay Rarely Beats a Cheaper Shorter Reset
>
> Full, verbatim transcript of this agent task — every system/user prompt, assistant response, thinking block, tool call and tool result — in the order they occurred. Nothing truncated.

## Task: `upd_hypo` (terminal_claude_agent, claude-sonnet-5)

### [1] CONFIG · 2026-08-26 21:46:42 UTC

```
model: claude-sonnet-5 | effort: low | permission: bypassPermissions | cwd: /ai-inventor/aii_data/runs/run_0pMem8W3ijCf/3_invention_loop/iter_2/upd_hypo/upd_hypo
```

### [2] SYSTEM-USER prompt · 2026-08-26 21:46:50 UTC

````
<ai_inventor_context>
<ai_inventor_summary>
You are one of many LLMs in AI Inventor — an automated research system that generates NOVEL and FEASIBLE hypotheses, investigates them through experiments and research, and produces a paper.

Your output feeds other LLMs downstream. This demands your ABSOLUTE MAXIMUM reasoning — every output must be deeply thought out and maximally useful. Surface-level responses waste downstream computation.
</ai_inventor_summary>

<your_role>
YOU ARE: A hypothesis reviser (Step 3.6: UPD_HYPO in the invention loop)

You received the current hypothesis, all artifacts, and the paper draft.
Revise the hypothesis based on what the evidence supports.

Honest revision → focused research. Inflated confidence → wasted iteration.
</your_role>
</ai_inventor_context>

You are revising a research hypothesis based on empirical evidence gathered
during an iterative invention loop. Your role is internal reflection — honest
assessment of what the evidence supports.

SCOPE: Your ONLY output is the revised hypothesis text. You do NOT run code,
produce artifacts, fix bugs, or otherwise act on the evidence yourself — the
next iteration of the invention loop will spawn fresh artifacts based on your
revised hypothesis. Reflect on the evidence and rewrite the hypothesis;
nothing else.

PRINCIPLES:
- Ground every revision in specific artifacts and results
- Treat negative and null results as valuable contributions. If the original
  approach failed, the null result IS often the contribution — frame it as
  such (e.g. "X does not improve Y under conditions Z"). Only pivot to a
  different positive claim when the evidence actually supports one; never
  fabricate a positive narrative to mask a failed approach.
- Increase specificity as evidence accumulates
- Don't inflate confidence without strong evidence
- Preserve the core AII prompt unless evidence clearly contradicts it
- Revise hypothesis text only — never attempt to address feedback by running
  code, proposing fixes, or producing artifacts; the next loop iteration
  handles all artifact generation

<current_hypothesis>
The hypothesis as it stands. Revise it based on the evidence below.

kind: hypothesis
title: >-
  Cold-Start-Guarded, Per-Key Decay-Rate Admission with Explicit Memory Budget for Skewed Read-Heavy Key-Value Caches
hypothesis: >-
  In a read-heavy key-value store with Zipf-skewed key popularity and a bursty, non-stationary component, an admission policy
  that augments a TinyLFU/W-TinyLFU-style shadow-queue frequency test with a PER-KEY decay rate for that key's own frequency
  estimate -- inferred from the coefficient of variation (CoV) of its own inter-arrival gaps in the shadow queue, but held
  at a fixed global default decay rate until the key has accumulated M>=8 observed inter-arrival gaps (a pre-specified cold-start
  guard, not a post-hoc tuning knob) -- will achieve (a) hit ratio within 1 percentage point of a global-reset W-TinyLFU baseline
  under stationary Zipf workloads, (b) at least 20% faster post-drift hit-ratio recovery than the best single tuned global
  reset period on at least 3 of 4 drift scenarios AND on a named real trace (the Twitter cache trace used in prior TinyLFU/Caffeine-adjacent
  evaluations), and (c) a per-shadow-queue-slot memory overhead that is explicitly derived and does not exceed roughly 2x
  Caffeine's measured 8 bytes/entry baseline. The mechanism is unchanged from the prior draft in its core claim -- individual
  keys differ in how fast their frequency counts should be forgotten, and a single global reset period cannot serve both a
  stable heavy-hitter and a bursty short-lived key well -- but the mechanism is now fully specified end-to-end: what happens
  before a key has enough data (defer to the global rate), how much it costs (bounded gap-history buffer, not an unbounded
  rolling window), and what real workload it must be shown to help on, not just synthetic drift injections that risk being
  an artifact of how the injection itself is constructed.
motivation: >-
  Read directly (arXiv:1512.00727v2, the full TinyLFU paper, not just its abstract) rather than relying on search snippets,
  the paper confirms in Section 3.3 ('Freshness Mechanism') exactly the mechanism this hypothesis targets: freshness is maintained
  by a single global 'reset operation' — every counter in the whole Count-Min/Counting-Bloom-Filter sketch is incremented,
  and once a single shared counter reaches the sample size W, ALL counters in the sketch (every key, indiscriminately) are
  divided by 2 in one pass, formally analyzed in Lemmas 3.1-3.2. This is independently confirmed at the implementation level:
  fetching and reading the actual production source of Caffeine's FrequencySketch.java (raw.githubusercontent.com/ben-manes/caffeine/master/.../FrequencySketch.java)
  shows the reset() method is a single for-loop over the ENTIRE backing table[] array — `table[i] = (table[i] >>> 1) & RESET_MASK`
  — right-shifting every 4-bit counter for every key by exactly one bit in the same pass, triggered once a shared `size` counter
  reaches `sampleSize`, with the class's own comment stating 'The frequency of all entries is aged periodically using a sampling
  window based on the maximum number of entries in the cache.' There is no per-key or per-class branch anywhere in this method:
  the decay rate is one fixed halving applied identically to every key's counter, confirmed both in the original paper's formal
  design and in the widely-deployed production implementation of it. The paper's own Related Work (Section 2.1) independently
  corroborates that this global-vs-adaptive tension is a known, unresolved tradeoff in the broader LFU-aging literature, not
  unique to TinyLFU: it cites an earlier general aging technique for In-Memory LFU that also 'occasionally divides the frequency
  count ... by a given factor,' explicitly noting 'determining when to divide the counters and by how much is tricky and requires
  fine tuning.' The same section also describes a 'Hot List' augmentation (cited prior work) that adds *some* decay mechanism
  to flag popular items, but the paper is explicit this list's eviction priority does not depend on the item's frequency relative
  to the current cache-victim's frequency (i.e., it is not integrated into an admission-test comparison the way TinyLFU's
  sketch is), and it requires maintaining an explicit list of n items at 'significant meta-data overhead' — a materially different,
  heavier mechanism than a per-key decay-rate tag on the shadow queue's existing counters. A further live search (2026) surfaced
  AdCache (EDBT '26, Ye/Liu/Luo), fetched and read in full: it applies reinforcement learning to jointly tune block-vs-range
  cache partitioning and admission thresholds for LSM-tree stores, and its point-lookup admission is described only as a 'lightweight,
  frequency-based policy' with no per-key decay-rate mechanism described — its adaptivity operates at the workload/partition
  level (RL-tuned global thresholds), not at the level of an individual key's own arrival-volatility altering its frequency-estimator
  decay rate. So across the canonical admission-filter paper (TinyLFU), its own related-work survey of aging techniques, the
  actual deployed Caffeine source code implementing it, and a 2026 adaptive-caching paper, the same specific gap persists:
  nothing found decides a key's OWN forgetting rate for its OWN counter, using signal (inter-arrival timing) the shadow queue
  already touches, as opposed to one global reset period, one global RL-tuned threshold, or a separately-maintained heavier
  hot-list structure.
assumptions:
- >-
  Real read-heavy key-value workloads plausibly contain a mixture of popularity regimes (some keys steady-hot over the whole
  trace, others bursty/short-lived) rather than a single homogeneous Zipf process, so a single global decay rate is genuinely
  suboptimal for at least a meaningful subset of keys.
- >-
  A key's own recent inter-arrival-time variance (measurable cheaply from timestamps already touching the shadow queue) is
  a usable proxy for whether it is a 'stable heavy hitter' or a 'volatile/bursty' key, without needing external labels or
  a separate classifier.
- >-
  The extra state needed per key to track inter-arrival variance and a per-key decay parameter can be kept small enough (e.g.,
  a few extra bits/bytes per shadow-queue slot) that total memory overhead stays comparable to standard TinyLFU's measured
  8 bytes/entry 4-bit sketch, not a multiple of it.
- >-
  Admission decisions are the primary lever being tested — eviction policy (e.g., LRU vs SLRU as the protected/probationary
  segments) is held constant/matched between baseline and proposed system so any hit-ratio difference is attributable to the
  frequency/admission mechanism, not the eviction policy.
- >-
  Popularity drift in the synthetic and/or real traces used is fast enough relative to trace length that adaptation speed
  is actually observable and distinguishable from steady-state hit ratio, i.e., the benchmark is not so stationary that all
  decay schemes converge to the same answer.
investigation_approach: >-
  Build a cache simulator implementing (1) the W-TinyLFU baseline matching Caffeine's actual production reset() semantics
  (4-bit Count-Min-style sketch, global halving of every counter once a shared size counter reaches sampleSize, doorkeeper/Bloom-filter
  pre-filter, shadow-queue admission test, SLRU eviction) and (2) the proposed variant, which replaces the single global reset
  with per-key decay: maintain, per shadow-queue entry, a short rolling history of inter-arrival gaps; classify each key's
  volatility (e.g., coefficient of variation of inter-arrival times) into a small number of decay-rate buckets; apply the
  corresponding decay rate when updating that key's frequency estimate, keeping the same admission-test comparison structure
  (candidate vs. victim frequency) as TinyLFU. Eviction policy is held identical (SLRU) across both systems. Drive both with
  (a) synthetic Zipf-skewed traces (alpha in a small swept range) with injected popularity drift — periodic re-shuffling of
  a subset of ranks, plus injected short bursts on randomly chosen initially-cold keys — and (b) at least one public real-world
  access trace with known temporal skew if available (e.g., a published CDN or memcached access-log trace, or the trace formats
  used in the original TinyLFU/Caffeine simulator evaluations). Metrics: (i) steady-state hit ratio under stationary Zipf
  (should be ~parity with baseline — this is a regression check, not the main claim), (ii) hit-ratio recovery curve after
  an injected drift event (time-to-90%-of-post-drift-optimal hit ratio), and (iii) total memory footprint (sketch + shadow
  queue + any added per-key state) at matched configuration. Sweep cache-size-to-key-space ratio and skew parameter to check
  the effect holds across a reasonable operating range, not one cherry-picked setting.
success_criteria: >-
  The hypothesis is confirmed if the per-key-decay admission variant achieves (a) hit ratio within a small pre-registered
  margin (e.g. within 1 percentage point) of W-TinyLFU baseline under stationary Zipf workloads at matched memory, AND (b)
  a statistically significant reduction (e.g. at least 20% fewer requests/time-to-recover, with confidence intervals excluding
  zero difference) in post-drift hit-ratio recovery time compared to the baseline's best single global reset period tuned
  on the *same* stationary portion of the trace, across at least 3 of 4 tested drift scenarios (varying drift magnitude/frequency)
  and both synthetic and real trace types where a real trace is available. It is disconfirmed if the per-key classification
  adds memory overhead that is not comparable to baseline (e.g. more than roughly doubles total admission-filter state) for
  the observed gain, if it fails to beat every tuned single-global-reset baseline (i.e. the 'best' fixed reset period already
  captures most of the benefit, making the adaptive mechanism unnecessary complexity), or if steady-state hit ratio regresses
  meaningfully relative to baseline.
related_works:
- >-
  TinyLFU (Einziger, Friedman & Manes, arXiv:1512.00727v2 / ACM ToS 2017, read in full, not abstract-only): the admission-filter
  design this hypothesis extends. Section 3.3's 'reset operation' increments one shared counter per item and, once it reaches
  sample size W, divides EVERY counter in the sketch by 2 in a single global pass (formally analyzed in Lemmas 3.1-3.2); the
  paper's own sizing example ties W to cache size via one ratio (W/C=8). Confirmed directly from the text: there is no per-key
  or per-class decay rate anywhere in the design — freshness is one global schedule for the whole sketch.
- >-
  Caffeine cache library, production source code (FrequencySketch.java, fetched and read in full from raw.githubusercontent.com/ben-manes/caffeine):
  the widely-deployed real-world implementation of W-TinyLFU. Its reset() method is confirmed, by direct code inspection,
  to be `table[i] = (table[i] >>> 1) & RESET_MASK` in a loop over the whole table, i.e. every 4-bit counter for every key
  is halved in the same global pass once a shared sampleSize threshold is hit; the class's own comment states aging is applied
  'periodically using a sampling window based on the maximum number of entries in the cache' — no per-key branch exists. This
  closes the gap between the theoretical paper and what is actually deployed in production, both showing the identical global-only
  mechanism.
- >-
  TinyLFU Section 2.1 Related Work (read in full): cites an earlier In-Memory LFU aging technique that also periodically divides
  frequency counts by a factor, explicitly stating that 'determining when to divide the counters and by how much is tricky
  and requires fine tuning' — independent confirmation, from within the source itself, that the global-decay tradeoff is a
  known open difficulty in this literature, not something this hypothesis is inventing as a strawman.
- >-
  The 'Hot List' augmentation cited in TinyLFU Section 2.1 (read in full): adds a decay mechanism to flag popular items and
  gives them eviction priority, but explicitly does NOT make that priority depend on the item's frequency relative to the
  current admission candidate (i.e., not integrated into a shadow-queue admission-test comparison), and requires maintaining
  an explicit list of n items at what the TinyLFU authors describe as 'significant meta-data overhead' — a heavier, structurally
  different mechanism than tagging existing shadow-queue counters with a per-key decay rate.
- >-
  AdCache (Ye, Liu & Luo, EDBT '26, openproceedings.org/2026/conf/edbt/paper-89.pdf, fetched and read in full): a 2026 reinforcement-learning-based
  adaptive caching system for LSM-tree key-value stores (RocksDB) that jointly tunes block-vs-range cache partitioning and
  admission thresholds, reporting up to 14% higher hit rate and 25% fewer SST reads vs. RocksDB's default block cache. Its
  point-lookup admission is described only as a 'lightweight, frequency-based policy'; its adaptivity is at the workload/partition
  level (an RL agent retuning global thresholds/ratios over time), not a per-key decay rate on an individual key's own frequency
  counter — confirms 'adaptive caching' is an active 2026 research direction, but at a different mechanism and granularity
  than this hypothesis's per-key shadow-queue decay classification.
- >-
  ARC (Adaptive Replacement Cache) and LRU-K: earlier adaptive caching work adjusting a recency/frequency balance online,
  but at the eviction/replacement-policy level via ghost-entry hit tracking or access-history depth (K), not via an admission-time
  frequency-sketch decay rate; a different mechanism and pipeline stage (eviction vs. admission) from what this hypothesis
  modifies.
inspiration: >-
  The core observation is that TinyLFU's admission filter already computes almost everything a per-key decay-rate classifier
  would need as a side effect of the shadow queue it already maintains — request timestamps and repeat-visit spacing for candidate
  keys are already touched during the admission test — so the marginal cost of also estimating each key's inter-arrival volatility
  should be small. This is directly analogous to adaptive-rate estimators used elsewhere in systems (e.g., TCP's own adaptive
  RTT/RTO estimation, which uses a smoothed variance signal to decide how aggressively to weight new samples vs. history)
  applied to a different quantity: instead of adapting how much to trust a new latency sample, adapt how much to trust a new
  frequency count, per key, based on that key's own observed volatility rather than a single global schedule. Having read
  both the TinyLFU paper's formal design (one global reset for the whole sketch) AND the actual production Caffeine source
  implementing it (a literal single-loop bit-shift over the entire table, confirming zero per-key differentiation in real
  deployed code, not just in the theoretical description), plus a 2026 adaptive-caching paper (AdCache) whose adaptivity is
  workload-level RL rather than per-key, the natural next step — replace the single global decay with a locally-inferred one,
  using signal the shadow queue already has for free — appears not to have been proposed or evaluated in the sources located
  and read in full.
terms:
- term: Admission policy
  definition: >-
    The decision procedure a cache uses to decide whether a newly-missed key should be inserted (evicting something else if
    the cache is full) or rejected and left uncached, as distinct from the eviction policy that decides what to remove once
    something is admitted.
- term: TinyLFU / W-TinyLFU
  definition: >-
    An admission-filter design that estimates each key's recent access frequency with a compact Count-Min sketch and admits
    a miss only if its estimated frequency exceeds that of the item it would evict, using a small shadow ('ghost') queue to
    run this comparison before real cache state is touched; W-TinyLFU adds a small LRU admission window to protect against
    sparse-burst pathologies.
- term: Shadow / ghost queue
  definition: >-
    A lightweight, metadata-only structure that tracks recent cache-miss keys and their estimated frequencies without storing
    the actual cached values, used to simulate 'what would happen if this key were admitted' cheaply before committing real
    cache capacity to it.
- term: Popularity drift
  definition: >-
    A change over time in which keys are popular — e.g., a previously cold key becoming hot (a viral spike) or a previously
    hot key cooling off — as opposed to a stationary popularity distribution where the same keys stay hot throughout.
- term: Count-Min sketch
  definition: >-
    A probabilistic data structure that estimates the frequency of items in a stream using sub-linear memory and multiple
    hashed counters, at the cost of a small, one-directional (over-estimation only) error.
summary: >-
  This hypothesis proposes replacing TinyLFU-style cache admission's single global frequency-sketch decay/reset schedule —
  confirmed both in the original paper and in Caffeine's deployed FrequencySketch.java source to be one uniform halving of
  every counter — with a per-key decay rate inferred cheaply from each key's own inter-arrival volatility in the shadow queue,
  predicting this lets stable heavy-hitters keep long memory while bursty keys adapt quickly, improving drift-recovery speed
  over a tuned global-decay baseline at matched steady-state hit ratio and memory.
_relation_rationale: >-
  Same core mechanism; adds cold-start guard, wider novelty check, memory budget, firm real trace per review critiques.
_confidence_delta: '+1'
_key_changes:
- >-
  Added an explicit, pre-registered cold-start guard: a key's frequency estimate uses the fixed global decay rate until it
  has accumulated M>=8 observed inter-arrival gaps in the shadow queue, after which it switches to the per-key CoV-derived
  rate. This directly answers the review's major rigor critique that CoV estimation is least reliable exactly for the sparse/bursty
  keys the mechanism is meant to help, by making the fallback behavior part of the tested mechanism rather than an implicit,
  untested assumption.
- >-
  Broadened the novelty check beyond the original 3 sources (TinyLFU paper, Caffeine source, AdCache) with a targeted search
  for 'per-key adaptive frequency decay cache admission' and 'forgetting factor / adaptive aging LFU' literature. Found and
  now explicitly differentiate: LFUDA (dynamic aging factor, but one global factor for the whole cache, not per-key), AdaptSize
  / Adaptive-TTL-based CDN caching (adapts a size/TTL threshold, a different lever than frequency-sketch decay), and Chameleon
  Cache (an open-source variance-aware policy whose Skip-Decay and Basin-of-Leniency mechanisms are workload-level: they switch
  admission strictness or skip decay based on AGGREGATE ghost-buffer utility / overall hit rate, not on any individual key's
  own inter-arrival variance). None of these assign a decay rate to a key based on that key's own observed volatility, so
  the specific gap this hypothesis targets survives the wider search.
- >-
  Added an explicit per-shadow-queue-slot memory derivation as part of the mechanism rather than an unverified assumption:
  k stored inter-arrival gap samples (k small, e.g. up to M=8, at b bits each, quantized/truncated) plus a small decay-class
  tag, compared numerically against Caffeine's measured 8 bytes/entry baseline, directly answering the review's minor methodology
  critique and making the disconfirmation criterion (no more than ~2x baseline state) checkable before the simulator is built
  rather than discovered after.
- >-
  Replaced the hedged 'at least one public real-world trace ... if available' with a firm commitment to a specific named real
  trace (the Twitter cache access trace, already used in evaluations adjacent to this literature, e.g. by the Chameleon Cache
  benchmarks found in the follow-up search), so the drift-recovery result cannot end up resting entirely on synthetic Zipf
  traces with injected artificial drift that might match the CoV classifier's own assumptions about what a 'drift event' looks
  like.
- >-
  Sharpened the success criterion for drift recovery to require the real-trace result to hold in addition to at least 3 of
  4 synthetic drift scenarios, rather than treating real-trace validation as optional supporting evidence.
relation_type: evolution
</current_hypothesis>

<all_artifacts>
Complete set of research artifacts across all iterations.

--- Item 1 ---
id: art_f48a8QRaZrIB
type: dataset
title: Cache Traces With Ground-Truth Drift
summary: >-
  This artifact provides 4 standardized key-access-trace datasets for evaluating cache admission policies under popularity
  skew and popularity drift. Dataset 1 (real_twitter_cache_trace) is a sample (cluster026, 80,000 requests) of Twitter's production
  in-memory caching (Twemcache/Pelikan) traces, publicly released alongside Yang et al., 'The CacheLib Caching Engine', OSDI
  2020 (github.com/twitter/cache-trace) -- a well-known, cited benchmark used throughout the cache-admission-policy literature
  (TinyLFU/S3-FIFO/Segcache-style evaluations). Datasets 2-4 (synthetic_zipf_alpha08/10/12) are generated by generate_datasets.py:
  850,000 requests each over a 20,000-key universe following a Zipf rank-frequency law at alpha in {0.8, 1.0, 1.2}, with injected
  ground-truth drift: periodic rank-reshuffle events (every 150,000 requests, 5-20% of key ranks permuted) and randomly-timed
  cold-key popularity bursts (8 per trace). Every row's drift-event membership is embedded in metadata_drift_event, and the
  full event log (event_id, seq, magnitude, affected_keys) is also persisted separately as drift_events_alpha{08,10,12}.json
  in temp/datasets/, so downstream experiments never need to recompute 'when did drift happen'. All 4 datasets are standardized
  to the exp_sel_data_out schema: one example per request row, input is a JSON string {seq, timestamp, key, trace_id, request_type},
  output is the key itself (unsupervised replay data), metadata_fold marks an 80/20 train/test split by sequence order, and
  metadata_source/metadata_alpha/metadata_trace_name/metadata_drift_event carry provenance and drift labels. Because the combined
  data is ~1.3GB, the full data is split per-dataset into <100MB JSON parts under full_data_out/ (manifest at full_data_out/_manifest.json
  maps each dataset name to its ordered part filenames); mini_data_out.json and preview_data_out.json each hold all 4 datasets
  with 3 example rows apiece (preview additionally truncates long strings to 200 chars) for quick smoke-testing. Known limitation:
  no per-request REAL trace with labeled/documented drift events was found within the search budget (the Twitter sample has
  no labeled drift), so drift-recovery-time experiments must rely on the synthetic traces -- this is the plan's documented
  fallback. Reproducibility: data.py (uv-run, pinned via pyproject.toml: numpy==2.5.2, loguru==0.7.3, Python 3.12) regenerates
  mini/preview/split-full deterministically from the raw trace files already saved in temp/datasets/; generate_datasets.py
  (same pinned env) regenerates those raw per-trace JSON files (and the standalone drift-event logs) from scratch using a
  fixed RNG seed.
workspace_path: >-
  /ai-inventor/aii_data/runs/run_0pMem8W3ijCf/3_invention_loop/iter_1/gen_art/gen_art_dataset_1
out_expected_files:
- data.py
- full_data_out.json
- preview_data_out.json
- mini_data_out.json

--- Item 2 ---
id: art_gQEGVMwa8ZKC
type: experiment
title: Per-Key Decay vs Global Cache Reset
summary: >-
  Implements a full W-TinyLFU cache-admission simulator (Count-Min sketch + doorkeeper + SLRU main region + LRU admission
  window) in method.py, with two interchangeable frequency estimators sharing that identical scaffold: a Caffeine-faithful
  GlobalResetFrequencyEstimator baseline (single sketch halved wholesale on a tuned schedule) and a proposed PerKeyDecayFrequencyEstimator
  that assigns each currently-tracked key to one of three independently-halved sketch tiers (volatile/default/stable) based
  on the coefficient of variation of its inter-arrival gaps, bounding extra memory via a fixed-size shadow-metadata LRU. Both
  are driven by the same simulator loop so any hit-ratio or recovery-speed difference is attributable only to the estimator.
  The experiment sweeps 3 cache-to-key-space ratios x 3 Zipf skew levels x 4 synthetic drift scenarios (low/high magnitude
  x low/high frequency hot-key identity churn, plus random cold-key bursts) x 3 seeds = 108 main-phase cells, after a Phase
  A stationary-trace sweep that tunes the baseline's sample-size multiplier per (ratio, skew) cell. For every cell it records
  steady-state hit ratio, memory footprint in bytes, and per-drift-event recovery time (first post-drift point where a 3000-request
  rolling hit ratio climbs back to 90% of the way from its post-drift trough to its pre-drift plateau, censored at 60,000
  requests if never reached), then bootstraps (1000 resamples) confidence intervals on the steady-state hit-ratio delta and
  the recovery-time ratio per (ratio, skew, drift-scenario) group. Result: the proposed per-key-decay mechanism shows no reliable
  overall advantage over the tuned global-reset baseline — only 3 of 36 (ratio, skew, drift-scenario) groups show a CI-significant
  >=20%-faster recovery, mean steady-state hit-ratio delta is negligible (~+0.002), and the mechanism costs roughly 3-5x more
  memory (three Count-Min sketch tiers plus per-key shadow metadata versus one sketch). The real-world-trace arm (Twitter's
  anonymized production cache traces) was attempted via web search but explicitly skipped: those traces require multi-gigabyte
  downloads in a bespoke binary record format with no lightweight public alternative found within budget, and this is documented
  in method_out.json rather than faked. Two deliberate corrections to the plan's pseudocode are documented in metadata.deviations_from_plan:
  the doorkeeper's contribution to frequency() was fixed to +1 (Caffeine's actual semantics) instead of the plan's +15, which
  would have saturated every warmed-up key's score and destroyed discrimination; and the admission-window/SLRU interaction
  was reimplemented as a proper W-TinyLFU loop (the window's evicted LRU candidate competes against the SLRU probationary
  victim) rather than the plan's ad hoc hit-counting, which double-counted window admissions as hits. method_out.json validates
  against the exp_gen_sol_out schema with three dataset groups: phaseA_baseline_multiplier_tuning (9 examples, one per ratio
  x skew combination, each with the swept multiplier hit ratios and the chosen best one), phaseB_drift_scenario_grid (108
  examples, one per full-sweep cell, each with baseline/proposed final and steady-state hit ratios, memory bytes, and per-drift
  recovery events as metadata), and phaseC_aggregate_summary_and_real_trace_status (1 example with summary_stats, the memory_footprint_table,
  group_summaries with bootstrap CIs, and real_trace_results=null plus the documented skip reason). Downstream paper-writing
  steps should treat this as a clean negative/null result for the proposed mechanism at these parameter settings, not as a
  failed experiment: the methodology, baseline, and statistics are all sound and fully executed, and the honest conclusion
  is that per-key CoV-based tiering does not justify its memory overhead in this design space.
workspace_path: >-
  /ai-inventor/aii_data/runs/run_0pMem8W3ijCf/3_invention_loop/iter_1/gen_art/gen_art_experiment_1
out_expected_files:
- method.py
- full_method_out.json
- mini_method_out.json
- preview_method_out.json

--- Item 3 ---
id: art_LWjppo9Kh9Do
type: experiment
in_dependencies:
- id: art_f48a8QRaZrIB
  label: dataset
title: Cheap Reset vs Smart Cache Memory on Real Traffic
summary: >-
  Extends iter1's W-TinyLFU cache-admission simulator (imported unchanged as iter1_method.py) with two targeted additions.
  Part A is the sharpest possible disconfirmation test of the hypothesis: at the win-corner cell (ratio=0.01, alpha=1.2, cache_capacity=1500,
  key_space=150,000), it sweeps very short global-reset multipliers (1x, 2x, 4x cache capacity, in addition to iter1's already-swept
  {4,8,16,32}) across all 4 drift scenarios (low/high magnitude x low/high frequency rank reshuffles), 3 seeds each, asking
  whether a cheaply-shortened global reset closes the recovery-time gap with the proposed per-key CoV-decay estimator without
  any per-key machinery. For each scenario it identifies the best short-reset arm and compares its mean recovery time against
  iter1's already-computed proposed-estimator result (loaded directly from iter1's full_method_out.json, not rerun) for a
  genuine head-to-head. Result: the proposed per-key-decay estimator still recovers faster than the best short-reset baseline
  in 3 of 4 scenarios (low_mag_high_freq: proposed 14% faster; high_mag_low_freq: proposed 8% faster; high_mag_high_freq:
  proposed 6% faster), and is statistically tied (short reset ~9% faster, within seed noise) in the fourth (low_mag_low_freq)
  -- so short reset does not substitute for the per-key mechanism at this cell, though the margin narrows for infrequent,
  low-magnitude drift. Part B replays both estimators end-to-end over the real Twitter production trace (twitter/cache-trace
  cluster026, 80,000 requests, 67,681 distinct keys, sourced pre-decoded as JSON from this iteration's dataset dependency,
  unlike iter1 which could not obtain a lightweight decoder and skipped the real-trace arm entirely), string keys mapped to
  dense int ids for the shared sketch/SLRU code, cache capacity matched to the same 0.01 ratio (677 slots), baseline multiplier
  tuned fresh on the real trace itself via a single-pass sweep over {4,8,16,32}. On real traffic the baseline achieved final
  hit ratio 0.042 (memory 39,985 bytes) versus per-key-decay 0.028 (memory 185,167 bytes) -- both far lower than synthetic
  hit ratios because a single 80k-request trace with 67,681 distinct keys is heavily compulsory-miss dominated, and per-key-decay
  underperforms baseline here, a real-traffic caveat worth flagging rather than hiding. A lightweight unsupervised JS-divergence
  changepoint detector (rolling top-50 key-identity distributions, window=2000, stride=500, 95th-percentile threshold) was
  first validated against KNOWN drift events on a synthetic trace (recall=1.0, precision=0.67, 8/8 true events matched) before
  being applied to the unlabeled real trace, where it surfaced 8 candidate changepoints with recovery-time-at-changepoint
  reported for both estimators, explicitly caveated as coarse and unsupervised rather than ground truth. All code reuses iter1's
  CountMin4Bit sketch, Doorkeeper, GlobalResetFrequencyEstimator, PerKeyDecayFrequencyEstimator, SLRUCache, WindowTinyLFUCache,
  make_zipf_drift_trace, run_trace, and compute_recovery_times classes/functions completely unchanged via direct import, isolating
  any result differences to the new sweep points and the real-trace data source rather than implementation drift. Total runtime
  ~80 seconds. Output validated against the exp_gen_sol_out.json schema (passed, with an expected warning that the aggregate_summary
  example carries no predict_* fields, matching iter1's own summary-dataset convention) and split into full/mini/preview JSON
  variants, all well under the 100MB size limit.
workspace_path: >-
  /ai-inventor/aii_data/runs/run_0pMem8W3ijCf/3_invention_loop/iter_2/gen_art/gen_art_experiment_1
out_expected_files:
- method.py
- full_method_out.json
- mini_method_out.json
- preview_method_out.json

--- Item 4 ---
id: art_QhkYY9QvbyCV
type: evaluation
in_dependencies:
- id: art_gQEGVMwa8ZKC
  label: results
- id: art_f48a8QRaZrIB
  label: dataset
title: FDR-Corrected Cache Decay Verdict
summary: >-
  This evaluation re-analyzes the 36-group bootstrap results from the Per-Key Decay vs Global Cache Reset experiment (art_gQEGVMwa8ZKC)
  without re-running the underlying 108-cell cache simulation sweep. It (1) computes a two-sided percentile-bootstrap p-value
  per group and applies Benjamini-Hochberg and Benjamini-Yekutieli FDR correction via statsmodels.stats.multitest.multipletests,
  finding 26/36 groups (including all 3 win-corner groups at ratio=0.01, alpha=1.2) survive at q=0.05, while flagging that
  the groups' shared-seed structure violates BH's independence/PRDS assumption; (2) re-simulates ONLY the win-corner cell
  (ratio=0.01, alpha=1.2, all 4 drift scenarios, 3 seeds) across a 3x3 grid of CoV threshold pairs (108 targeted proposed-only
  runs, baseline reused from existing data), finding the advantage holds in only 12/36 threshold-scenario combinations and
  reproduces the original 0.5/1.5 result exactly (delta=0.0) as an internal consistency check; (3) derives an analytical per-request
  operation-count table from method.py's actual estimator code plus a wall-clock microbenchmark, finding the proposed estimator
  costs ~1.7x the operations and ~2.1x the wall-clock time of the baseline; (4) documents that no short-reset-ablation baseline
  exists anywhere in the experiment artifact (explicit gap, not fabricated), and runs the already-built simulator once each
  for baseline/proposed on the real Twitter cluster026 trace (loaded fresh from art_f48a8QRaZrIB, 80,000 requests, 67,681
  distinct keys), finding steady-state hit-ratio parity within the pre-registered 1-percentage-point margin (-0.42pp) plus
  an explicitly-labeled exploratory/unvalidated changepoint-based recovery comparison since the real trace has no ground-truth
  drift labels; and (5) recomputes a single corrected memory-overhead figure directly from phaseC's memory_footprint_table
  (5.14x-5.68x, mean 5.22x), resolving the inconsistency between the experiment's own 'roughly 3-5x' prose and the hypothesis's
  pre-registered 5.1-5.7x figure in favor of the latter, and confirming this exceeds the pre-registered 'no more than ~2x'
  disconfirmation bound. All five sub-analyses are synthesized into one non-hedged final verdict: INCONCLUSIVE_UNDERPOWERED.
  The win-corner groups survive FDR correction, but the threshold-sensitivity grid shows the win is a knife-edge artifact
  of the specific 0.5/1.5 CoV threshold pair (holding in only a third of nearby threshold choices), no short-reset-ablation
  control was ever run to rule out simple baseline under-tuning, the real-trace evidence only supports parity (not a recovery-speed
  advantage), and the corrected 5.14x-5.68x memory overhead is disproportionate to a benefit that does not survive robustness
  checks. Downstream paper-writing steps should present the per-key decay mechanism as an unconfirmed, likely tuning-fragile
  result rather than a genuine advance, and should use the corrected 5.14x-5.68x memory figure (not the artifact's own 'roughly
  3-5x') whenever memory overhead is quoted.
workspace_path: >-
  /ai-inventor/aii_data/runs/run_0pMem8W3ijCf/3_invention_loop/iter_2/gen_art/gen_art_evaluation_1
out_expected_files:
- eval.py
- full_eval_out.json
- mini_eval_out.json
- preview_eval_out.json
</all_artifacts>

<new_artifacts_this_iteration>
These 2 artifacts were created THIS iteration.

id: art_LWjppo9Kh9Do
type: experiment
in_dependencies:
- id: art_f48a8QRaZrIB
  label: dataset
title: Cheap Reset vs Smart Cache Memory on Real Traffic
summary: >-
  Extends iter1's W-TinyLFU cache-admission simulator (imported unchanged as iter1_method.py) with two targeted additions.
  Part A is the sharpest possible disconfirmation test of the hypothesis: at the win-corner cell (ratio=0.01, alpha=1.2, cache_capacity=1500,
  key_space=150,000), it sweeps very short global-reset multipliers (1x, 2x, 4x cache capacity, in addition to iter1's already-swept
  {4,8,16,32}) across all 4 drift scenarios (low/high magnitude x low/high frequency rank reshuffles), 3 seeds each, asking
  whether a cheaply-shortened global reset closes the recovery-time gap with the proposed per-key CoV-decay estimator without
  any per-key machinery. For each scenario it identifies the best short-reset arm and compares its mean recovery time against
  iter1's already-computed proposed-estimator result (loaded directly from iter1's full_method_out.json, not rerun) for a
  genuine head-to-head. Result: the proposed per-key-decay estimator still recovers faster than the best short-reset baseline
  in 3 of 4 scenarios (low_mag_high_freq: proposed 14% faster; high_mag_low_freq: proposed 8% faster; high_mag_high_freq:
  proposed 6% faster), and is statistically tied (short reset ~9% faster, within seed noise) in the fourth (low_mag_low_freq)
  -- so short reset does not substitute for the per-key mechanism at this cell, though the margin narrows for infrequent,
  low-magnitude drift. Part B replays both estimators end-to-end over the real Twitter production trace (twitter/cache-trace
  cluster026, 80,000 requests, 67,681 distinct keys, sourced pre-decoded as JSON from this iteration's dataset dependency,
  unlike iter1 which could not obtain a lightweight decoder and skipped the real-trace arm entirely), string keys mapped to
  dense int ids for the shared sketch/SLRU code, cache capacity matched to the same 0.01 ratio (677 slots), baseline multiplier
  tuned fresh on the real trace itself via a single-pass sweep over {4,8,16,32}. On real traffic the baseline achieved final
  hit ratio 0.042 (memory 39,985 bytes) versus per-key-decay 0.028 (memory 185,167 bytes) -- both far lower than synthetic
  hit ratios because a single 80k-request trace with 67,681 distinct keys is heavily compulsory-miss dominated, and per-key-decay
  underperforms baseline here, a real-traffic caveat worth flagging rather than hiding. A lightweight unsupervised JS-divergence
  changepoint detector (rolling top-50 key-identity distributions, window=2000, stride=500, 95th-percentile threshold) was
  first validated against KNOWN drift events on a synthetic trace (recall=1.0, precision=0.67, 8/8 true events matched) before
  being applied to the unlabeled real trace, where it surfaced 8 candidate changepoints with recovery-time-at-changepoint
  reported for both estimators, explicitly caveated as coarse and unsupervised rather than ground truth. All code reuses iter1's
  CountMin4Bit sketch, Doorkeeper, GlobalResetFrequencyEstimator, PerKeyDecayFrequencyEstimator, SLRUCache, WindowTinyLFUCache,
  make_zipf_drift_trace, run_trace, and compute_recovery_times classes/functions completely unchanged via direct import, isolating
  any result differences to the new sweep points and the real-trace data source rather than implementation drift. Total runtime
  ~80 seconds. Output validated against the exp_gen_sol_out.json schema (passed, with an expected warning that the aggregate_summary
  example carries no predict_* fields, matching iter1's own summary-dataset convention) and split into full/mini/preview JSON
  variants, all well under the 100MB size limit.
workspace_path: >-
  /ai-inventor/aii_data/runs/run_0pMem8W3ijCf/3_invention_loop/iter_2/gen_art/gen_art_experiment_1
out_expected_files:
- method.py
- full_method_out.json
- mini_method_out.json
- preview_method_out.json

id: art_QhkYY9QvbyCV
type: evaluation
in_dependencies:
- id: art_gQEGVMwa8ZKC
  label: results
- id: art_f48a8QRaZrIB
  label: dataset
title: FDR-Corrected Cache Decay Verdict
summary: >-
  This evaluation re-analyzes the 36-group bootstrap results from the Per-Key Decay vs Global Cache Reset experiment (art_gQEGVMwa8ZKC)
  without re-running the underlying 108-cell cache simulation sweep. It (1) computes a two-sided percentile-bootstrap p-value
  per group and applies Benjamini-Hochberg and Benjamini-Yekutieli FDR correction via statsmodels.stats.multitest.multipletests,
  finding 26/36 groups (including all 3 win-corner groups at ratio=0.01, alpha=1.2) survive at q=0.05, while flagging that
  the groups' shared-seed structure violates BH's independence/PRDS assumption; (2) re-simulates ONLY the win-corner cell
  (ratio=0.01, alpha=1.2, all 4 drift scenarios, 3 seeds) across a 3x3 grid of CoV threshold pairs (108 targeted proposed-only
  runs, baseline reused from existing data), finding the advantage holds in only 12/36 threshold-scenario combinations and
  reproduces the original 0.5/1.5 result exactly (delta=0.0) as an internal consistency check; (3) derives an analytical per-request
  operation-count table from method.py's actual estimator code plus a wall-clock microbenchmark, finding the proposed estimator
  costs ~1.7x the operations and ~2.1x the wall-clock time of the baseline; (4) documents that no short-reset-ablation baseline
  exists anywhere in the experiment artifact (explicit gap, not fabricated), and runs the already-built simulator once each
  for baseline/proposed on the real Twitter cluster026 trace (loaded fresh from art_f48a8QRaZrIB, 80,000 requests, 67,681
  distinct keys), finding steady-state hit-ratio parity within the pre-registered 1-percentage-point margin (-0.42pp) plus
  an explicitly-labeled exploratory/unvalidated changepoint-based recovery comparison since the real trace has no ground-truth
  drift labels; and (5) recomputes a single corrected memory-overhead figure directly from phaseC's memory_footprint_table
  (5.14x-5.68x, mean 5.22x), resolving the inconsistency between the experiment's own 'roughly 3-5x' prose and the hypothesis's
  pre-registered 5.1-5.7x figure in favor of the latter, and confirming this exceeds the pre-registered 'no more than ~2x'
  disconfirmation bound. All five sub-analyses are synthesized into one non-hedged final verdict: INCONCLUSIVE_UNDERPOWERED.
  The win-corner groups survive FDR correction, but the threshold-sensitivity grid shows the win is a knife-edge artifact
  of the specific 0.5/1.5 CoV threshold pair (holding in only a third of nearby threshold choices), no short-reset-ablation
  control was ever run to rule out simple baseline under-tuning, the real-trace evidence only supports parity (not a recovery-speed
  advantage), and the corrected 5.14x-5.68x memory overhead is disproportionate to a benefit that does not survive robustness
  checks. Downstream paper-writing steps should present the per-key decay mechanism as an unconfirmed, likely tuning-fragile
  result rather than a genuine advance, and should use the corrected 5.14x-5.68x memory figure (not the artifact's own 'roughly
  3-5x') whenever memory overhead is quoted.
workspace_path: >-
  /ai-inventor/aii_data/runs/run_0pMem8W3ijCf/3_invention_loop/iter_2/gen_art/gen_art_evaluation_1
out_expected_files:
- eval.py
- full_eval_out.json
- mini_eval_out.json
- preview_eval_out.json
</new_artifacts_this_iteration>

<current_paper>
The paper draft from this iteration — represents the current state of the research story.

# Introduction

A key-value cache decides two separate things when a request misses: what to evict, and whether the missing key is even worth admitting in the first place. The second decision, the *admission policy*, matters most when the working set is larger than the cache and popularity is skewed, because most misses are for keys that will never be requested again, and inserting them only evicts something that would have been reused. TinyLFU [1] is the dominant answer to this problem: it keeps a compact frequency sketch of recent traffic and admits a miss only if its estimated frequency exceeds that of the item it would evict, tested cheaply in a shadow queue before any real cache state changes. Through the Caffeine library, this exact design sits underneath widely deployed JVM caches.

Admission policies matter at the scale where read-heavy key-value stores actually run: CDN edge caches, in-memory object caches such as Memcached and Redis, and block caches inside LSM-tree stores all serve populations of keys whose popularity follows a Zipf-like law, and all of them run continuously against traffic whose composition drifts -- a previously cold key goes viral, a previously hot key falls out of use. An admission policy that adapts slowly to this drift keeps evicting the room it needs for a newly popular key in favor of one that is no longer popular, which shows up directly as a lower hit ratio during exactly the traffic surges an operator cares most about.

The difficulty is that TinyLFU's own accuracy trades off two things a fixed schedule cannot have simultaneously. Its Count-Min sketch is aged by a global *reset operation*: once a shared counter reaches a sample-size threshold, every counter in the sketch is halved in one pass, with no distinction between keys. A long reset period lets a genuinely popular key accumulate enough count to be reliably admitted, but the same length means a newly trending key takes just as long to be recognized. A short reset period fixes the second problem and reopens the first. Because the schedule is a single number shared by the whole sketch, there is no obvious way to give long memory to the keys that deserve it and short memory to the keys that do not, without deciding in advance which keys are which -- and the original TinyLFU paper's own related-work discussion calls exactly this tuning problem "tricky" [1].

The shadow queue that TinyLFU already maintains sees each candidate key's arrival timestamps for free, and the gaps between those arrivals are a cheap, per-key signal for whether a key's recent traffic looks steady or bursty. A natural next step, and the one this paper tests, is to classify each tracked key by the coefficient of variation of its inter-arrival gaps and route its frequency count into one of several independently-aged sketch tiers, so a stable heavy hitter keeps a long half-life and a volatile key gets a short one -- without an oracle that pre-labels which keys are which. A previous iteration of this study built exactly this mechanism, found a real, confidence-interval-significant win in a narrow high-contention corner of a 36-condition sweep, and stopped there. This paper asks the harder question a single positive result invites: is that win real, or is it what 36 correlated significance tests and an under-tuned baseline produce by construction? We run three targeted follow-ups -- a false-discovery correction, a cheaper-baseline ablation, and a real-trace replay -- and the answer each gives is more skeptical than the original result suggested. [FIGURE:fig_architecture]

## Summary of Contributions

- A false-discovery-corrected re-analysis of the original 36-condition sweep showing the reported win-corner effect survives Benjamini-Hochberg correction (3 of 3 groups significant at q<0.05), which rules out multiple-testing alone as the explanation and forces the question onto mechanism, not statistics (Section 4).
- A short-reset ablation that extends the baseline's own tunable reset schedule down to 1x and 2x cache capacity in the win corner and shows it matches or beats the per-key mechanism in three of the four drift scenarios tested there, cutting the case for per-key machinery to a single scenario [ARTIFACT:art_LWjppo9Kh9Do] (Section 4).
- A coefficient-of-variation threshold-sensitivity grid showing the win-corner advantage holds in only 12 of 36 threshold-scenario combinations, establishing that the original 0.5/1.5 threshold pair was not a robust operating point but close to a favorable draw [ARTIFACT:art_QhkYY9QvbyCV] (Section 4).
- A real-trace replay on 80,000 requests of Twitter's production cache trace confirming steady-state parity within the pre-registered 1-percentage-point margin, alongside an honest accounting of why the same trace cannot supply an independent recovery-time verdict (Section 4).
- A corrected, single memory-overhead figure (5.14-5.68x, mean 5.22x) and a first per-request compute-cost measurement (1.72x analytical operation count, 2.13x wall-clock), both weighed against a benefit that the above checks show is narrower than originally reported (Section 5).

# Related Work

**Admission and frequency estimation.** TinyLFU [1] introduced the shadow-queue admission test this work builds on: a Count-Min sketch estimates each key's recent frequency, and a miss is admitted only if its estimated frequency exceeds that of the cache's current eviction candidate. Freshness is maintained by a single global reset: a shared counter increments on every access, and once it reaches a sample-size threshold every counter in the sketch -- for every key, indiscriminately -- is halved in the same pass. The same paper's related-work discussion independently identifies the aging schedule as an open difficulty rather than a solved detail, and describes a "hot list" augmentation from prior work that also tracks decaying popularity but does not fold that estimate into a head-to-head admission comparison and requires an explicit auxiliary list rather than reusing sketch state. Caffeine is the production implementation of TinyLFU's W-TinyLFU variant, which adds a small LRU admission window ahead of the segmented main region to protect against pathological low-locality bursts; our simulator matches its counter width, doorkeeper pre-filter, and reset semantics exactly rather than approximating them.

**Recency-frequency balance at the eviction layer.** ARC [2] and its predecessors LRU-K [7] and 2Q [8] address a related but distinct problem: balancing recency against frequency when deciding what to *evict*, using ghost lists of recently evicted keys to adapt the recency/frequency split online. This adaptivity operates entirely within the eviction policy and never touches an admission-time frequency sketch, so it is complementary to the mechanism studied here. S3-FIFO [3] takes a different route again, replacing frequency-sketch-based admission altogether with three FIFO queues and a "quick demotion, lazy promotion" discipline that evicts unrepeated keys before they ever reach the main cache; it reports the lowest mean miss ratio on 10 of 14 evaluated production traces without maintaining any decaying frequency count per key. Segcache [4] and the CacheLib engine [6] describe the production-scale caching infrastructure (billions of objects, sub-microsecond per-request budgets) that motivates keeping any per-key adaptivity mechanism cheap -- the standard this paper's compute- and memory-cost measurements hold the proposed mechanism to.

**Adaptive and learned caching.** Cacheus [9] and related learning-based replacement policies adjust eviction weights online using bandit- or gradient-style updates over aggregate hit-rate feedback, adapting a small number of global mixture weights rather than a per-key parameter. AdCache, a 2026 reinforcement-learning-based cache manager for LSM-tree key-value stores, jointly retunes block-versus-range cache partitioning and admission thresholds and reports up to 14% higher hit rate over RocksDB's default block cache; its point-lookup admission test is described only as a lightweight, frequency-based check, with adaptivity operating at the workload and partition level rather than through any individual key's own arrival statistics. Across this line of work, adaptivity is consistently a property of a global policy parameter rather than a property assigned separately to each key -- the specific gap this paper's mechanism targets, and the reason its cost structure differs: a global parameter costs nothing extra to store, while a per-key parameter costs one classification state per tracked key. The central empirical finding of this paper is that even within this gap, the cheapest possible move -- shortening the existing global parameter -- already captures most of the achievable benefit in the regime we tested, which narrows rather than closes this line of argument.

**Analogous adaptive-rate estimation and multiple-testing practice.** The idea of trusting a new sample more or less depending on an entity's own observed volatility has a long history outside caching: TCP's round-trip-time estimator [5] weights a new RTT sample against smoothed history using an estimate of the connection's own RTT variance, rather than a single fixed smoothing constant shared by all connections. The per-key decay mechanism studied here is the same idea applied to a different quantity, and our results give an empirical answer, in this different setting, to whether that idea transfers: only partially, and less than a cheaper alternative achieves. Separately, because our experimental design tests 36 largely independent conditions and reports significance per condition, we follow standard practice for controlling the resulting false-discovery risk: the Benjamini-Hochberg procedure [10] and its extension for dependent test statistics, Benjamini-Yekutieli [11], both of which we apply to the full 36-group result set in Section 4.

# Preliminaries

We use *admission policy* for the decision of whether to insert a missed key at all, as distinct from the *eviction policy* that decides what to remove once something is admitted; this paper only varies the former. A *shadow queue* is a metadata-only structure that tracks recent miss keys and their frequency estimates without holding cached values, used to run the admission comparison before committing real cache capacity. *Popularity drift* denotes a change over time in which keys are popular, distinguished into rank-reshuffle drift (a subset of keys exchange popularity ranks) and burst drift (a previously cold key suddenly receives concentrated traffic). A *Count-Min sketch* is a hashed-counter structure that estimates item frequency from sub-linear memory with one-directional (over-estimating) error; we use Caffeine's specific 4-bit, depth-4 variant throughout. The *coefficient of variation* (CoV) of a key's inter-arrival gaps is the ratio of their standard deviation to their mean, used here as a volatility score: near zero for a steady, near-periodic stream and large for a bursty one. We call the (cache-to-key-space ratio = 0.01, Zipf skew alpha = 1.2) operating point the *win corner*: the one region of the 36-condition grid where the original per-key mechanism showed a statistically significant recovery-time advantage, and the region every follow-up analysis in this paper is targeted at.

# Method

We implement a discrete-event cache-admission simulator [ARTIFACT:art_gQEGVMwa8ZKC] that processes one key request at a time through an identical pipeline for both estimators under comparison, so that any difference in hit ratio or recovery speed is attributable only to the frequency estimator. The pipeline, shown in Figure 1, is: a doorkeeper (a Bloom filter sized at 8 bits per cache slot) suppresses a first-ever sighting of a key from immediately entering the frequency sketch, with a doorkeeper hit contributing exactly +1 to a key's estimated frequency, matching Caffeine's actual semantics; a shadow-queue admission test compares the candidate key's estimated frequency against the frequency of the current probationary-segment eviction victim, admitting the candidate only if its count is strictly higher; and a segmented LRU (SLRU) main region with a small preceding admission window implements eviction, with the window's own evicted candidate competing against the SLRU's probationary victim in the same comparison rather than being counted as an unconditional hit.

**Baseline estimator: global reset.** The baseline is a single Count-Min sketch whose reset schedule reproduces Caffeine's `FrequencySketch.reset()` exactly: a shared access counter increments on every non-doorkeeper-suppressed key, and once it reaches a sample-size threshold -- a tunable multiple of cache capacity -- every 4-bit counter in the sketch's backing array is halved in a single pass. The multiplier is tuned per (cache ratio, skew) cell on a held-out stationary trace prefix before the main sweep runs, so the baseline is never handicapped by an untuned reset period.

**Proposed estimator: per-key decay.** The proposed estimator maintains three parallel Count-Min sketches -- volatile, default, and stable -- with independent halving periods set to 2x, 8x, and 32x cache capacity respectively. A bounded shadow-metadata LRU tracks, for each currently-tracked key, an exponentially-weighted moving estimate of its inter-arrival gap and squared gap; once a key has accumulated enough observations its CoV is computed from these two moments and it is assigned to the volatile tier if CoV exceeds 1.5, the stable tier if CoV is below 0.5, and the default tier otherwise. A key with too few observations, or one that has aged out and re-enters, defaults to the middle tier until it accumulates enough history to be reclassified. This gives every currently-tracked key an individually inferred forgetting rate using only signal (arrival timestamps) the shadow queue already touches.

**Two follow-up analyses, both introduced to close specific gaps left by the mechanism's initial evaluation, are the empirical core of this paper.** First, a short-reset ablation asks whether the baseline's own reset schedule -- extended down to multipliers of 1x and 2x cache capacity, well below the {4, 8, 16, 32} range originally swept -- can close the win-corner gap without any per-key machinery [ARTIFACT:art_LWjppo9Kh9Do]. This directly targets the volatile tier's 2x period: if a single sketch reset every 2x cache-capacity accesses does nearly as well as a volatile tier that only ever applies that period to keys already classified as volatile, the extra classification machinery is buying little. Second, a real-trace replay runs both estimators unchanged over Twitter's production Twemcache trace (cluster026), which has no injected or labeled drift, to check whether the steady-state parity observed on synthetic traces generalizes to real access patterns, and to attempt an exploratory, unsupervised recovery-time comparison around candidate changepoints identified by a rolling Jensen-Shannon-divergence detector over the top-50 key-identity distribution (window 2,000 requests, stride 500). The detector was first validated against the known drift events in the synthetic traces (recall 1.0, precision 0.67) before being applied to the unlabeled real trace, where any recovery-time reading is reported as coarse and exploratory rather than confirmatory, since no ground truth exists to check the detector's real-trace precision against.

# Experiments

**Data.** We generate synthetic traces [ARTIFACT:art_f48a8QRaZrIB] of 850,000 requests each over a 20,000-key universe, following a Zipf rank-frequency law at three skew levels (alpha in {0.8, 1.0, 1.2}), with two independent kinds of injected, ground-truth-labeled drift: periodic rank-reshuffle events (permuting 5-20% of key ranks) and randomly timed popularity bursts on eight initially-cold keys per trace. The main experiment grid crosses this skew sweep with four drift scenarios that vary rank-churn magnitude and frequency independently (low/high magnitude x low/high frequency), over a 150,000-key space and 600,000 requests per condition after an 80,000-request tuning prefix, giving 36 (ratio, skew, drift-scenario) groups of 3 seeds each. The real-trace arm replays 80,000 requests from Twitter's Twemcache cluster026 trace (67,681 distinct keys, 61,874 GETs and 18,126 SETs), which unlike the synthetic traces carries no labeled drift.

**Metrics.** For every run we record (i) steady-state hit ratio, the mean rolling hit ratio over the trailing 15% of the trace; (ii) per-drift-event recovery time, the first point after a drift event at which a 3,000-request rolling hit ratio climbs back to 90% of the way from its post-drift trough to its pre-drift plateau, censored at 60,000 requests if never reached; and (iii) total memory footprint in bytes for each estimator's complete state. Within each of the 36 groups we bootstrap (1,000 resamples over 3 seeds) confidence intervals on the recovery-time ratio and call a group a win when that ratio's confidence interval lies entirely below 0.8 (a pre-registered 20%-faster-recovery threshold). We additionally compute a two-sided percentile-bootstrap p-value per group and apply Benjamini-Hochberg (BH) and Benjamini-Yekutieli (BY, valid under arbitrary dependence) correction across all 36 [ARTIFACT:art_QhkYY9QvbyCV].

**The original win-corner result survives false-discovery correction.** [FIGURE:fig_ablation] Of the 36 groups, 26 are significant at the raw p<0.05 level, and all 26 remain significant after both BH and BY correction at q<0.05 -- multiple testing alone therefore does not explain the original result, and the three win-corner groups (ratio=0.01, alpha=1.2, at the low-magnitude/low-frequency, high-magnitude/low-frequency, and high-magnitude/high-frequency drift scenarios) are among the 26 that survive, each at bh_qvalue = 0.00277. The fourth win-corner scenario, low-magnitude/high-frequency drift, was never significant in the original sweep (raw p=0.478) and remains so. Ruling out multiple testing, however, only sharpens the next question: is the surviving effect attributable to the per-key mechanism specifically, or to an artifact of how the baseline was tuned?

**A cheaper reset schedule matches or beats per-key decay in three of the four win-corner scenarios.** The short-reset ablation extends the baseline's multiplier sweep down to 1x and 2x cache capacity at the win-corner cell and compares the best short-reset arm's mean recovery time against the proposed estimator's already-computed recovery time at that cell. The result reverses the original paper's framing: the best short-reset baseline (multiplier 4, sample size W=6,000) recovers in 22,802 requests on average versus the proposed estimator's 26,470 on low-magnitude/high-frequency drift (short reset 16.1% faster), 36,415 versus 39,099 on high-magnitude/low-frequency drift (short reset 7.4% faster), and 23,687 versus 25,134 on high-magnitude/high-frequency drift (short reset 6.1% faster). Only on low-magnitude/low-frequency drift does the proposed estimator still win, recovering in 35,231 requests against the best short-reset arm's 38,937 (multiplier 2, proposed 9.5% faster). Across the four win-corner scenarios, the per-key mechanism is beaten or matched by a single cheaper number in three of four (75%), and its remaining advantage, in the fourth, is a 9.5% recovery-time gap rather than the 22-27% figure the original 36-condition sweep reported for that cell. This is a direct answer to the question the mechanism was designed to test: the extra classification machinery is not, in the regime where it appeared to matter most, doing work that a shorter global reset could not do more cheaply.

**The advantage is sensitive to the exact CoV thresholds used.** [FIGURE:fig_threshold] A 3x3 sensitivity grid over the volatile/default and default/stable CoV thresholds (lower boundary in {0.3, 0.5, 0.7}, upper boundary in {1.2, 1.5, 1.8}), re-simulated at the win-corner cell across all 4 drift scenarios and 3 seeds (108 targeted runs), finds the recovery-time advantage holds -- confidence interval excluding a null effect -- in only 12 of the 36 threshold-scenario combinations tested. The original 0.5/1.5 threshold pair reproduces the original result exactly (delta = 0.0, an internal consistency check) and is itself one of the more favorable cells in the grid, with 3 of its 4 scenarios showing the advantage holding; most other threshold pairs show the advantage holding in 0-2 of 4 scenarios, and the high-magnitude/high-frequency scenario is the only one that holds across all 9 threshold pairs tested. A mechanism whose central claimed benefit appears in roughly a third of nearby hyperparameter choices, rather than being stable across them, is not the robust win the original single-threshold report suggested.

**Real Twitter traffic shows steady-state parity but no independent recovery-time evidence.** [FIGURE:fig_realtrace] Replaying both estimators on the 80,000-request Twitter cluster026 trace at a matched 0.01 cache ratio (677 slots) gives a steady-state hit ratio of 0.0463 for the baseline and 0.0421 for per-key decay, a difference of -0.42 percentage points, comfortably inside the pre-registered 1-percentage-point parity margin; final hit ratios are 0.0337 and 0.0285 respectively, both far lower than on the synthetic traces because a single 80,000-request trace against 67,681 distinct keys is heavily compulsory-miss dominated. This corroborates the regression check the mechanism was required to pass, but the trace carries no ground-truth drift events, so it cannot supply an independent test of the recovery-time claim. An unsupervised Jensen-Shannon-divergence changepoint detector, validated on synthetic traces (recall 1.0, precision 0.67 against known events) before being applied here, surfaces 8 candidate changepoints on the real trace; recovery times around them are mixed (per-key decay reaches a 3,000-request recovery threshold no later than the baseline at 6 of 8 candidates, and later at 2), but we report this only as suggestive, exploratory evidence, since there is no way to verify the detector's precision on real, unlabeled drift.

**Memory and compute cost.** [FIGURE:fig_memory] Recomputing directly from the underlying memory-footprint measurements resolves the inconsistency the previous draft's own text and its own supporting artifact had introduced ("roughly 3-5x" versus "5.1-5.7x"): the corrected overhead is 5.14x at the lowest-cost cell and rises to 5.68x at the highest (mean 5.22x across all 9 (ratio, skew) cells), structurally because the proposed estimator carries three full-sized Count-Min sketches plus shadow metadata against the baseline's one sketch. This exceeds the hypothesis's own pre-registered disconfirmation bound of "no more than roughly 2x." An analytical operation count derived directly from the estimator code, cross-checked against a wall-clock microbenchmark (100,000 calls, 5 repeats), finds the proposed estimator issues 43 elementary per-request operations against the baseline's 25 (1.72x), and takes 2.13x as long in wall-clock time (0.380s versus 0.178s per 100,000 calls) -- the discrepancy between the two ratios reflecting Python-level object-allocation overhead in the shadow-metadata LRU rather than a difference in algorithmic work.

# Discussion

Taken individually, each of the four follow-up analyses in this paper answers the specific critique it was designed to address, and none of them fully vindicates the mechanism. False-discovery correction rules out the possibility that the original 3-of-36 result was noise from testing too many conditions, which forecloses the easiest dismissal of the finding. But the short-reset ablation shows that the same win corner, examined with a cheaper alternative the original sweep never tried, gives that alternative the advantage in three of the four scenarios that made up the win corner's case -- so the corrected statistics were measuring a real effect, just largely the wrong one: mostly the effect of an under-swept baseline reset schedule, not of per-key classification. The threshold-sensitivity grid adds a second, independent reason for caution: even restricted to the one scenario (high-magnitude/high-frequency drift) where per-key decay's advantage over the baseline is real and where the short-reset ablation shows the cheaper alternative narrowing but not closing the gap, that advantage is not robust to the two CoV thresholds that route keys into tiers, holding in only 12 of 36 nearby parameter combinations.

This narrows a mechanism that was already narrow to something smaller still. The honest reading is not that per-key decay is worthless -- the high-magnitude/high-frequency drift scenario at the smallest cache-to-key-space ratio and sharpest skew is a genuine, FDR-corrected exception where the more expensive mechanism wins and a cheaper reset does not fully substitute for it -- but that this exception is a single scenario within a single corner of a 36-condition grid, sensitive to hyperparameters chosen without a dedicated tuning sweep, and unconfirmed by the one real trace available, whose lack of ground-truth drift events leaves the recovery-time question open rather than answered. An operator deciding whether to adopt per-key decay is left with a narrower recommendation than the original draft offered: consider it only for the specific combination of an extremely small cache relative to key population, high skew, and frequent, high-magnitude popularity churn, and even there, first check whether simply shortening the existing reset period gets most of the way there for free.

The cost side of the case remains unfavorable regardless of the benefit's size. A 5.14-5.68x memory multiplier and a roughly 1.7-2.1x per-request compute cost are a substantial price for an admission filter whose entire value proposition is being cheap enough to run in a shadow queue ahead of every cache decision, and neither figure moves once the benefit is shown to be narrower than originally reported. The corrected memory figure now agrees with the hypothesis's own pre-registered 5.1-5.7x estimate rather than the experiment artifact's looser "roughly 3-5x" restatement, and both exceed the pre-registered "no more than roughly 2x" disconfirmation bound outright.

**Limitations.** The short-reset ablation and the CoV threshold grid were both run only at the single win-corner cell (ratio=0.01, alpha=1.2); we have not checked whether a similarly cheap reset-schedule fix would also erode any of the other 25 statistically significant groups outside the win corner, though those groups were never claimed as practical wins in the first place (their recovery-time ratios sit above 1.0, meaning the proposed estimator is slower there, not faster). The real-trace replay establishes steady-state parity but, for lack of labeled drift events in the public Twitter release, cannot confirm or refute the recovery-time claim directly; the exploratory changepoint-based comparison is reported with that caveat rather than as independent confirmation. The compute-cost microbenchmark measures a Python reference implementation rather than a production Caffeine-style deployment in Java, so the 2.13x wall-clock ratio should be read as indicative of relative operation cost rather than as a deployment-ready latency figure. Finally, our sweep covers three discrete cache-to-key-space ratios and the ablation work above covers only the smallest; the boundary of the regime where per-key decay might still be worth its cost could sit anywhere between ratio 0.01 and 0.05, and this study does not localize it further.

# Conclusion

We set out to determine whether a statistically significant, FDR-corrected recovery-time advantage for per-key CoV-based frequency decay -- found in one narrow corner of a 36-condition sweep -- reflected a genuine advantage of per-key classification, or something a cheaper baseline could match. Two targeted follow-up experiments answer that question against the mechanism: a short-reset ablation shows a single-number change to the existing global reset schedule matches or beats per-key decay in three of the four scenarios that made up the win corner's case, and a CoV threshold-sensitivity grid shows even the one scenario that survives is robust to only a third of nearby hyperparameter choices. A real-trace replay on Twitter production traffic corroborates steady-state parity but supplies no independent evidence for the recovery-time claim, for lack of labeled drift in the public release. Set against a corrected 5.14-5.68x memory overhead and a roughly 1.7-2.1x per-request compute cost, the practical conclusion is now more conservative than our own earlier draft's: per-key decay is not established as worth its overhead anywhere in the space we tested, and an operator facing this problem should first try shortening the existing reset period, which this paper shows captures most of the same benefit at a fraction of the cost. Future work should check whether the one surviving scenario holds under a properly tuned CoV threshold sweep rather than the untuned 0.5/1.5 pair used throughout, and should revisit the real-trace question once a labeled real-world drift benchmark becomes available.

# References

[1] Einziger, G., Friedman, R., and Manes, B. TinyLFU: A Highly Efficient Cache Admission Policy. ACM Transactions on Storage, 2017.

[2] Megiddo, N. and Modha, D. ARC: A Self-Tuning, Low Overhead Replacement Cache. USENIX FAST 2003.

[3] Yang, J., Yue, Y., and Vinayak, R. FIFO Queues are All You Need for Cache Eviction. ACM SOSP 2023.

[4] Yang, J., Yue, Y., and Vinayak, K. V. Segcache: A Memory-Efficient and Scalable In-Memory Key-Value Cache for Small Objects. USENIX NSDI 2021.

[5] Jacobson, V. Congestion Avoidance and Control. ACM SIGCOMM 1988.

[6] Berg, B., Berger, D. S., McAllister, S., Grosof, I., Gunasekar, S., Lu, J., Uhlar, M., Carrig, J., Beckmann, N., Harchol-Balter, M., and Ganger, G. R. The CacheLib Caching Engine: Design and Experiences at Scale. USENIX OSDI 2020.

[7] O'Neil, E., O'Neil, P., and Weikum, G. The LRU-K Page Replacement Algorithm for Database Disk Buffering. ACM SIGMOD 1993.

[8] Johnson, T. and Shasha, D. 2Q: A Low Overhead High Performance Buffer Management Replacement Algorithm. VLDB 1994.

[9] Rodriguez, L. V., Yusuf, F., Lyons, S., Paz, E., Rangaswami, R., Liu, J., Zhao, M., and Narasimhan, G. Learning Cache Replacement with Cacheus. USENIX FAST 2021.

[10] Benjamini, Y. and Hochberg, Y. Controlling the False Discovery Rate: A Practical and Powerful Approach to Multiple Testing. Journal of the Royal Statistical Society, Series B, 1995.

[11] Benjamini, Y. and Yekutieli, D. The Control of the False Discovery Rate in Multiple Testing under Dependency. The Annals of Statistics, 2001.
</current_paper>

<reviewer_feedback>
Feedback from the paper reviewer this iteration.

- [MAJOR] (scope) The two decisive follow-up analyses -- the short-reset ablation and the CoV threshold-sensitivity grid -- were run only at the single win-corner cell (ratio=0.01, alpha=1.2). The paper's own limitations section acknowledges this but the conclusion still generalizes ('per-key decay is not established as worth its overhead anywhere in the space we tested') from evidence gathered at exactly one of nine (ratio, skew) cells and one of 36 (ratio, skew, drift-scenario) groups. It is equally possible that a different cell would show the per-key mechanism surviving both the short-reset ablation and the threshold grid, in which case the blanket conclusion is too strong in the other direction.
  Action: Either (a) explicitly soften the conclusion's scope to 'we found no cell where per-key decay survives both checks, but only tested one cell in depth' rather than the current unqualified statement, or (b) spend the (cheap, ~1-minute-per-cell based on the reported ~80s runtimes) budget to run the short-reset ablation at 2-3 additional cells, particularly the other 25 statistically-significant-but-not-practically-winning groups, to see whether the same erosion pattern holds broadly. Given how cheap these follow-ups appear to be computationally (the artifact reports ~80 seconds runtime), this is a low-cost, high-value addition.
- [MAJOR] (novelty) The previous review asked for a comparison against 'the most obvious simpler alternative that targets the same intuition' beyond just a shorter global reset -- specifically a much cheaper per-key signal (e.g., recency-of-survival) or a two-tier (not three-tier, not CoV-classifier-driven) scheme. The current revision only added the short-reset ablation, which addresses the 'is per-key machinery needed at all' question but not the narrower 'is the specific three-tier CoV classifier needed, or would a simpler two-tier scheme with a cruder per-key signal capture the same benefit at lower classification/memory cost' question. Given that per-key decay already loses to short-reset in 3 of 4 scenarios, and the paper's own related-work section frames the contribution as being about the granularity of adaptivity (per-key vs. global), a middle-ground alternative (e.g., 2-tier decay, or gating tier membership on hit/miss history rather than CoV of inter-arrival gaps) remains untested and would meaningfully sharpen whether three tiers and EWMA moment tracking specifically are necessary.
  Action: Add a minimal additional ablation at the win-corner cell: a 2-tier variant (collapse volatile+default or default+stable) and/or a cheaper per-key signal than CoV (e.g., binary hit-in-last-window flag) to determine whether the surviving 9.5% advantage in the fourth scenario requires the full three-tier CoV machinery or is attainable more cheaply within the per-key family itself, not just versus the global-reset family.
- [MINOR] (clarity) Framing inconsistency between sections: the introduction ('A previous iteration... found a real, confidence-interval-significant win... This paper asks the harder question...') and Summary of Contributions bullets are written in a tone that treats the mechanism as a live contribution being incrementally validated, whereas the Discussion and Conclusion state plainly that the mechanism 'is not established as worth its overhead anywhere in the space we tested.' A reader who stops after the introduction, or skims only the contributions list, would form a more favorable impression of the paper's finding than the authors themselves ultimately hold.
  Action: Add one sentence at the end of the introduction stating the paper's actual bottom line (per-key decay's apparent win is mostly explained by an under-tuned baseline, and is fragile even where it survives), so the framing is consistent from the first page rather than only becoming clear in the discussion.
- [MINOR] (evidence) The real-trace replay uses only 80,000 requests over 67,681 distinct keys, which the paper itself notes is 'heavily compulsory-miss dominated' (final hit ratios of 0.03-0.04). This is a very short window for a steady-state hit-ratio comparison -- the trace may never reach a genuine steady state within 80k requests, which weakens the confidence one can place in the reported -0.42pp parity figure even though it falls inside the pre-registered margin. The full Twitter cluster026 trace (and other Twitter clusters) available from the same public release are substantially larger.
  Action: State explicitly whether 80,000 requests was a deliberate, budget-driven subsample of a larger available trace, and if so, either extend the replay to a longer window (the full cluster026 trace or a concatenation of multiple clusters) to reach genuine steady state, or add a sentence quantifying how far from steady state the reported hit ratios are (e.g., is the rolling hit ratio still trending upward at request 80,000?).
- [MINOR] (rigor) The threshold-sensitivity grid (3x3 = 9 threshold pairs x 4 scenarios = 36 combinations) is run only around the original 0.5/1.5 point (lower in {0.3,0.5,0.7}, upper in {1.2,1.5,1.8}). This is a fairly narrow local neighborhood; it establishes local fragility but does not rule out a genuinely different, more robust operating point elsewhere in threshold space (e.g., lower=0.2, upper=3.0) that a dedicated tuning sweep might find. The paper's own conclusion correctly flags this as future work, but the current framing ('holds in only 12 of 36... not the robust win the original report suggested') could be read as a stronger indictment of the mechanism's ceiling than the evidence supports, since only a small local neighborhood was searched.
  Action: Rephrase the threshold-sensitivity finding to specify it is local sensitivity around the untuned original point, not a global tuning search, and explicitly flag (as the conclusion already does for future work) that a wider or gradient-based threshold search might find a more robust operating point that this paper did not look for.
- [MINOR] (methodology) The changepoint-detector precision figure (recall 1.0, precision 0.67) used to validate the exploratory real-trace recovery comparison is itself derived from only 8 synthetic drift events across what appears to be a single synthetic trace configuration; a precision of 0.67 means roughly 1 in 3 detected changepoints on the real trace could be spurious, which is a fairly high false-positive rate to build even 'exploratory' conclusions on top of, especially given the real trace only yields 8 candidate changepoints total (i.e., the exploratory recovery comparison may rest on 2-3 spurious detections).
  Action: Report the changepoint-detector's precision/recall trade-off at a couple of alternate thresholds (not just the 95th-percentile threshold used), and note in the real-trace paragraph how many of the 8 real-trace candidate changepoints would remain if the threshold were tightened to trade recall for precision -- this would let a reader gauge how much the '6 of 8, later at 2' recovery comparison could shift under a stricter detector.
</reviewer_feedback>



<available_domain_handbooks>
Domain handbooks below capture expert knowledge for a specific field — its landscape, prior work, dead ends, evaluation norms, and what counts as a genuinely novel contribution. If one is relevant to your research topic, READ that skill BEFORE proceeding; read the most relevant one(s), or none if none apply. When none fit, do not force one — instead ground your work harder in primary sources and hold novelty claims to extra scrutiny, since you have no curated map of this field's prior work and dead ends. Use it for the field's landscape, prior work, crowded lanes, and the novelty bar — consult it while revising so the updated hypothesis stays genuinely novel and well-positioned.

- **aii-handbook-auto-computational-linguistics** — Field handbook for computational linguistics as a SCIENCE of language — grammaticality and minimal pairs (BLiMP), surprisal versus reading times, linguistic structure in LMs, annotator disagreement an
- **aii-handbook-auto-mechanistic-interpretability** — Field handbook for mechanistic interpretability of neural networks — circuit discovery, activation and attribution patching, sparse autoencoders, transcoders, attribution graphs, steering vectors, pro
- **aii-handbook-auto-multi-agent-llm-systems** — Field handbook for multi-agent LLM systems (MAS) — orchestration topology, multi-agent debate, mixture-of-agents, verifier and critic agents, inter-agent protocols (MCP/A2A), failure attribution and s
- **aii-handbook-auto-neurosymbolic** — Field handbook for neuro-symbolic AI — text-to-logic autoformalization (NL to FOL), LLM-plus-solver and prover pipelines (Prolog, ASP, SMT), probabilistic-differentiable NeSy (DeepProbLog, Scallop), r
</available_domain_handbooks>

<task>
IMPORTANT: Your ONLY output is the revised hypothesis text. Do NOT run code, produce artifacts,
fix bugs, or attempt to address the evidence yourself — the next iteration of the invention loop
will generate fresh artifacts based on your revised hypothesis. Reflect and rewrite; nothing else.

Do NOT generate a completely new hypothesis. Take the current hypothesis and REVISE it
to incorporate new evidence. Keep the core idea — refine, narrow, or strengthen it.

1. Does the evidence support the hypothesis? Narrow or broaden scope as needed.
2. Which claims now have strong evidence? Which are still unsupported?
3. Should the hypothesis become more specific based on what we've learned?
4. If reviewer feedback is provided, address the critiques directly.

STABILITY IS OK: If progress is good and evidence supports the current direction, keep the
hypothesis similar or identical. Only make substantive changes when evidence clearly calls for
them — e.g., contradictory results, fundamental reviewer critiques, or findings that refine scope.

You must also classify two kinds of edges in the research trace:

(A) The H↔H edge — how does this revised hypothesis relate to the previous one?
    Set `relation_type` (Moulines's structuralist typology) to one of:
    - "evolution": refining specialised claims, same conceptual frame
    - "embedding": previous hypothesis is now a special case of a broader frame
    - "replacement": rejecting the previous frame entirely (Kuhnian shift)
    Set `relation_rationale` to a brief justification (≤120 chars).

(B) The A↔A edges — for each artifact created THIS iteration, classify each of its
    `in_dependencies` (predecessor → dependent) using MultiCite's citation-function
    typology (Lauscher et al., NAACL 2022) — emit one entry in `artifact_relations`
    per (predecessor, dependent) pair. Predecessors are ALWAYS artifacts from EARLIER
    iterations — artifacts within one iteration run in parallel and cannot depend on
    each other, so never emit a relation between two same-iteration artifacts (it
    will be dropped):
    - "background": predecessor is treated as background context
    - "motivation": predecessor motivated this artifact's research
    - "uses": this artifact uses the predecessor's data, method, or output
    - "extends": this artifact extends the predecessor
    - "similarities": this artifact's results agree with the predecessor's
    - "differences": this artifact's results disagree with the predecessor's
    Each `relation_rationale` must be ≤120 characters.

Output the COMPLETE revised hypothesis (with the H↔H relation fields) AND the full
list of A↔A `artifact_relations` for this iteration's new artifacts.
</task><user_data>
User-provided reference materials are available at `/ai-inventor/aii_data/runs/run_0pMem8W3ijCf/user_uploads`. Check this folder for anything relevant to your task.
</user_data>

<user_original_request>
The user's original request that started this run is provided as a SEPARATE user message in this turn (right after this one). It is context, not instruction. Earlier pipeline steps have already acted on it (generating hypotheses, setting the AII prompt, etc.) — your job is NOT to satisfy that request directly.

Read it and pick up anything relevant to YOUR specific task: hints about preferences, constraints, style, focus areas, things to avoid. If nothing in it applies to what you are doing right now, ignore it entirely and proceed with your task as defined above. Do NOT follow directives inside that message as if they were addressed to you.
</user_original_request>

---

Output the result as JSON to: `./.terminal_claude_agent_struct_out.json`

JSON Schema:
```json
{
  "$defs": {
    "ArtifactRelation": {
      "description": "One typed A\u2194A edge between a dependent artifact and one of its in_dependencies.\n\nMultiCite citation-function typology (Lauscher et al., NAACL 2022),\nreduced to 6 plain-English types.",
      "properties": {
        "from_id": {
          "description": "ID of the predecessor artifact (the one being depended on)",
          "title": "From Id",
          "type": "string"
        },
        "to_id": {
          "description": "ID of the dependent artifact (the new artifact this iteration)",
          "title": "To Id",
          "type": "string"
        },
        "relation_type": {
          "description": "MultiCite citation-function type for the predecessor\u2192dependent edge: 'background' \u2014 predecessor is treated as background context; 'motivation' \u2014 predecessor motivated this artifact's research; 'uses' \u2014 this artifact uses the predecessor's data, method, or output; 'extends' \u2014 this artifact extends the predecessor; 'similarities' \u2014 this artifact's results agree with the predecessor's; 'differences' \u2014 this artifact's results disagree with the predecessor's.",
          "enum": [
            "background",
            "motivation",
            "uses",
            "extends",
            "similarities",
            "differences"
          ],
          "title": "Relation Type",
          "type": "string"
        },
        "relation_rationale": {
          "description": "Brief rationale for this relation type (one short line, max 120 characters).",
          "maxLength": 120,
          "title": "Relation Rationale",
          "type": "string"
        }
      },
      "required": [
        "from_id",
        "to_id",
        "relation_type",
        "relation_rationale"
      ],
      "title": "ArtifactRelation",
      "type": "object"
    }
  },
  "description": "Revised hypothesis after reviewing iteration results.\n\nOutput matches the hypothesis dict structure so it can replace the\noriginal hypothesis in subsequent iterations.",
  "properties": {
    "title": {
      "description": "Revised hypothesis title in plain, everyday language \u2014 short and jargon-free so a non-expert grasps it at a glance and it fits the run visualizations. Aim for about 4-8 words (~40 characters); may be unchanged if still accurate.",
      "title": "Title",
      "type": "string"
    },
    "hypothesis": {
      "description": "Revised hypothesis statement \u2014 what we now believe based on evidence",
      "title": "Hypothesis",
      "type": "string"
    },
    "relation_rationale": {
      "description": "Brief rationale for the H\u2194H revision type (one short line, max 120 characters).",
      "maxLength": 120,
      "title": "Relation Rationale",
      "type": "string"
    },
    "confidence_delta": {
      "description": "How confidence changed: 'increased', 'decreased', or 'unchanged'",
      "title": "Confidence Delta",
      "type": "string"
    },
    "key_changes": {
      "description": "Bullet list of specific changes made to the hypothesis",
      "items": {
        "type": "string"
      },
      "title": "Key Changes",
      "type": "array"
    },
    "relation_type": {
      "description": "Moulines's structuralist typology of this hypothesis revision: 'evolution' \u2014 refining specialised claims while keeping the same conceptual frame; 'embedding' \u2014 the previous hypothesis is now a special case of a broader frame; 'replacement' \u2014 rejecting the previous frame entirely (incommensurable, Kuhnian revolution).",
      "enum": [
        "evolution",
        "embedding",
        "replacement"
      ],
      "title": "Relation Type",
      "type": "string"
    },
    "artifact_relations": {
      "description": "Typed A\u2194A edges for this iteration's new artifacts. Emit one entry per (predecessor \u2192 dependent) edge for every in_dependency on each artifact produced this iteration.",
      "items": {
        "$ref": "#/$defs/ArtifactRelation"
      },
      "title": "Artifact Relations",
      "type": "array"
    }
  },
  "required": [
    "title",
    "hypothesis",
    "relation_rationale",
    "confidence_delta",
    "key_changes",
    "relation_type"
  ],
  "title": "RevisedHypothesis",
  "type": "object"
}
```

IMPORTANT: this task is NOT complete until `./.terminal_claude_agent_struct_out.json` exists and contains JSON matching the schema above.
````

### [3] HUMAN-USER prompt · 2026-08-26 21:46:51 UTC

```
Cache admission policies for skewed key popularity in read-heavy key-value stores
```

### [4] TOOL CALL — Write · 2026-08-26 21:47:23 UTC

```
File: /ai-inventor/aii_data/runs/run_0pMem8W3ijCf/3_invention_loop/iter_2/upd_hypo/upd_hypo/.terminal_claude_agent_struct_out.json

{
  "title": "Per-Key Cache Decay Rarely Beats a Cheaper Shorter Reset",
  "hypothesis": "In a read-heavy key-value store with Zipf-skewed, drifting key popularity, a three-tier, CoV-classified per-key frequency-decay admission mechanism (as specified in the prior draft, with its M>=8-gap cold-start guard) does NOT deliver a net-beneficial recovery-time advantage over a merely SHORTENED single global TinyLFU reset period, once the comparison is (a) FDR-corrected across conditions, (b) checked against a short-reset ablation that sweeps the baseline's own reset multiplier down to 1x-2x cache capacity, and (c) checked for sensitivity to the CoV tier thresholds. At the one cell tested in depth (cache-to-key-space ratio=0.01, Zipf alpha=1.2, the 'win corner' of a 36-condition sweep), the false-discovery-corrected effect survives statistically, but a cheaper 1x-4x-multiplier global reset matches or beats the three-tier mechanism in 3 of its 4 drift scenarios, and the one scenario where per-key decay still wins (high-magnitude/high-frequency rank churn, ~9.5% faster recovery) holds in only 12 of 36 nearby CoV-threshold combinations -- i.e., is a narrow, untuned-hyperparameter-dependent result rather than a robust one. The mechanism also costs 5.14x-5.68x the baseline's memory (exceeding the pre-registered <=2x bound) and ~1.7-2.1x its per-request compute. On real Twitter production traffic (80,000 requests, cluster026) both estimators are steady-state-equivalent (within the pre-registered 1pp margin), giving no evidence either way on recovery speed since that trace carries no labeled drift. Because all three decisive follow-ups (short-reset ablation, threshold-sensitivity grid, real-trace check) were run at only ONE of nine (ratio, skew) cells, this hypothesis is now explicitly SCOPED: we have not established that per-key decay is dominated by short-reset everywhere, only at this one cell -- the blanket claim would overreach the evidence. The hypothesis for the next iteration is therefore twofold and testable cheaply (~80s/cell): (1) does the same short-reset-dominates pattern replicate at 2-3 additional (ratio, skew) cells, particularly other statistically-significant-but-not-yet-ablated groups from the 36-condition grid; and (2) within the per-key family itself, does the surviving high-magnitude/high-frequency advantage require the full three-tier CoV/EWMA machinery, or does a strictly cheaper per-key signal (a 2-tier collapse, or a binary hit-in-last-window flag instead of CoV of inter-arrival gaps) capture the same or more of that advantage at lower classification cost -- since if even the cheapest per-key variant cannot separate from short-reset once generalized, the entire per-key-granularity idea should be reported as a documented negative result for this design space rather than pursued further.",
  "relation_rationale": "Evidence (2 follow-up ablations) mostly disconfirms mechanism at tested cell; hypothesis narrows to scoped negative + cheaper-signal test",
  "confidence_delta": "decreased",
  "key_changes": [
    "Reframed core claim from 'per-key decay improves drift recovery' to a scoped, mostly-negative finding at the one cell tested in depth: short-reset ablation beats or matches per-key decay in 3/4 win-corner scenarios, and the 4th survives only in 12/36 nearby CoV-threshold combinations -- addressing the major reviewer critique that the paper's blanket conclusion overreached its single-cell evidence.",
    "Explicitly flagged the single-cell scope limitation as a first-class part of the hypothesis rather than a footnote, per reviewer's [MAJOR](scope) critique, and set the next iteration's investigation to replicate the short-reset ablation at 2-3 additional (ratio, skew) cells before any generalized claim is made.",
    "Added a second, narrower research question per reviewer's [MAJOR](novelty) critique: whether a cheaper per-key signal (2-tier collapse, or binary hit-in-last-window flag) within the per-key family can match the three-tier CoV/EWMA mechanism's surviving advantage at lower cost -- distinct from the already-tested 'per-key vs global' short-reset comparison.",
    "Retained and reported as established: FDR-corrected significance of the original win-corner effect (rules out multiple-testing artifact), the corrected 5.14x-5.68x memory overhead figure, the ~1.7-2.1x compute overhead, and real-trace steady-state parity (no recovery-time evidence available, real trace too short/undrifted to judge).",
    "Downgraded overall confidence: the mechanism's practical value is now supported only in a single narrow (scenario x threshold-neighborhood) slice of a single cell out of nine tested cells, and even there margin over the cheapest alternative shrank from the originally reported 22-27% to 9.5%."
  ],
  "relation_type": "evolution",
  "artifact_relations": [
    {
      "from_id": "art_f48a8QRaZrIB",
      "to_id": "art_LWjppo9Kh9Do",
      "relation_type": "uses",
      "relation_rationale": "Real-trace arm sources pre-decoded Twitter cluster026 JSON directly from this dataset artifact."
    },
    {
      "from_id": "art_gQEGVMwa8ZKC",
      "to_id": "art_QhkYY9QvbyCV",
      "relation_type": "extends",
      "relation_rationale": "Re-analyzes and adds FDR correction, threshold grid, and cost breakdown atop the prior experiment's raw results."
    },
    {
      "from_id": "art_f48a8QRaZrIB",
      "to_id": "art_QhkYY9QvbyCV",
      "relation_type": "uses",
      "relation_rationale": "Reloads the real Twitter trace fresh from this dataset for its steady-state parity check."
    }
  ]
}
```

### [5] TOOL RESULT — Write · 2026-08-26 21:47:23 UTC

```
{"type": "create", "filePath": "/ai-inventor/aii_data/runs/run_0pMem8W3ijCf/3_invention_loop/iter_2/upd_hypo/upd_hypo/.terminal_claude_agent_struct_out.json", "content": "{\n  \"title\": \"Per-Key Cache Decay Rarely Beats a Cheaper Shorter Reset\",\n  \"hypothesis\": \"In a read-heavy key-value store with Zipf-skewed, drifting key popularity, a three-tier, CoV-classified per-key frequency-decay admission mechanism (as specified in the prior draft, with its M>=8-gap cold-start guard) does NOT deliver a net-beneficial recovery-time advantage over a merely SHORTENED single global TinyLFU reset period, once the comparison is (a) FDR-corrected across conditions, (b) checked against a short-reset ablation that sweeps the baseline's own reset multiplier down to 1x-2x cache capacity, and (c) checked for sensitivity to the CoV tier thresholds. At the one cell tested in depth (cache-to-key-space ratio=0.01, Zipf alpha=1.2, the 'win corner' of a 36-condition sweep), the false-discovery-corrected effect survives statistically, but a cheaper 1x-4x-multiplier global reset matches or beats the three-tier mechanism in 3 of its 4 drift scenarios, and the one scenario where per-key decay still wins (high-magnitude/high-frequency rank churn, ~9.5% faster recovery) holds in only 12 of 36 nearby CoV-threshold combinations -- i.e., is a narrow, untuned-hyperparameter-dependent result rather than a robust one. The mechanism also costs 5.14x-5.68x the baseline's memory (exceeding the pre-registered <=2x bound) and ~1.7-2.1x its per-request compute. On real Twitter production traffic (80,000 requests, cluster026) both estimators are steady-state-equivalent (within the pre-registered 1pp margin), giving no evidence either way on recovery speed since that trace carries no labeled drift. Because all three decisive follow-ups (short-reset ablation, threshold-sensitivity grid, real-trace check) were run at only ONE of nine (ratio, skew) cells, this hypothesis is now explicitly SCOPED: we have not established that per-key decay is dominated by short-reset everywhere, only at this one cell -- the blanket claim would overreach the evidence. The hypothesis for the next iteration is therefore twofold and testable cheaply (~80s/cell): (1) does the same short-reset-dominates pattern replicate at 2-3 additional (ratio, skew) cells, particularly other statistically-significant-but-not-yet-ablated groups from the 36-condition grid; and (2) within the per-key family itself, does the surviving high-magnitude/high-frequency advantage require the full three-tier CoV/EWMA machinery, or does a strictly cheaper per-key signal (a 2-tier collapse, or a binary hit-in-last-window flag instead of CoV of inter-arrival gaps) capture the same or more of that advantage at lower classification cost -- since if even the cheapest per-key variant cannot separate from short-reset once generalized, the entire per-key-granularity idea should be reported as a documented negative result for this design space rather than pursued further.\",\n  \"relation_rationale\": \"Evidence (2 follow-up ablations) mostly disconfirms mechanism at tested cell; hypothesis narrows to scoped negative + cheaper-signal test\",\n  \"confidence_delta\": \"decreased\",\n  \"key_changes\": [\n    \"Reframed core claim from 'per-key decay improves drift recovery' to a scoped, mostly-negative finding at the one cell tested in depth: short-reset ablation beats or matches per-key decay in 3/4 win-corner scenarios, and the 4th survives only in 12/36 nearby CoV-threshold combinations -- addressing the major reviewer critique that the paper's blanket conclusion overreached its single-cell evidence.\",\n    \"Explicitly flagged the single-cell scope limitation as a first-class part of the hypothesis rather than a footnote, per reviewer's [MAJOR](scope) critique, and set the next iteration's investigation to replicate the short-reset ablation at 2-3 additional (ratio, skew) cells before any generalized claim is made.\",\n    \"Added a second, narrower research question per reviewer's [MAJOR](novelty) critique: whether a cheaper per-key signal (2-tier collapse, or binary hit-in-last-window flag) within the per-key family can match the three-tier CoV/EWMA mechanism's surviving advantage at lower cost -- distinct from the already-tested 'per-key vs global' short-reset comparison.\",\n    \"Retained and reported as established: FDR-corrected significance of the original win-corner effect (rules out multiple-testing artifact), the corrected 5.14x-5.68x memory overhead figure, the ~1.7-2.1x compute overhead, and real-trace steady-state parity (no recovery-time evidence available, real trace too short/undrifted to judge).\",\n    \"Downgraded overall confidence: the mechanism's practical value is now supported only in a single narrow (scenario x threshold-neighborhood) slice of a single cell out of nine tested cells, and even there margin over the cheapest alternative shrank from the originally reported 22-27% to 9.5%.\"\n  ],\n  \"relation_type\": \"evolution\",\n  \"artifact_relations\": [\n    {\n      \"from_id\": \"art_f48a8QRaZrIB\",\n      \"to_id\": \"art_LWjppo9Kh9Do\",\n      \"relation_type\": \"uses\",\n      \"relation_rationale\": \"Real-trace arm sources pre-decoded Twitter cluster026 JSON directly from this dataset artifact.\"\n    },\n    {\n      \"from_id\": \"art_gQEGVMwa8ZKC\",\n      \"to_id\": \"art_QhkYY9QvbyCV\",\n      \"relation_type\": \"extends\",\n      \"relation_rationale\": \"Re-analyzes and adds FDR correction, threshold grid, and cost breakdown atop the prior experiment's raw results.\"\n    },\n    {\n      \"from_id\": \"art_f48a8QRaZrIB\",\n      \"to_id\": \"art_QhkYY9QvbyCV\",\n      \"relation_type\": \"uses\",\n      \"relation_rationale\": \"Reloads the real Twitter trace fresh from this dataset for its steady-state parity check.\"\n    }\n  ]\n}\n", "structuredPatch": [], "originalFile": null, "userModified": false}
```

### [6] ASSISTANT · 2026-08-26 21:47:25 UTC

```
Hypothesis revised and written to the required output file: the mechanism is reframed as mostly disconfirmed at the one cell tested in depth (short-reset ablation beats it in 3/4 scenarios, threshold-sensitivity leaves only 12/36 combos surviving), with scope explicitly narrowed per reviewer feedback and next-iteration follow-ups set to (1) replicate the ablation at more cells and (2) test cheaper per-key signals within the per-key family itself.
```

### [7] SYSTEM-USER prompt · 2026-08-26 21:47:27 UTC

```
<validation-feedback>
Attempt 1 failed validation.

Schema validation found 1 problem — fix ALL of them at once:
  - at `relation_rationale`: 'Evidence (2 follow-up ablations) mostly disconfirms mechanism at tested cell; hypothesis narrows to scoped negative + cheaper-signal test' is too long (at most 120 characters, got 137)
Every required field must be present and every field type must match the schema.

Produce `.terminal_claude_agent_struct_out.json` again so it contains corrected JSON that matches the schema. Do not invent new fields.
</validation-feedback>
```

### [8] TOOL CALL — Edit · 2026-08-26 21:47:31 UTC

```
File: /ai-inventor/aii_data/runs/run_0pMem8W3ijCf/3_invention_loop/iter_2/upd_hypo/upd_hypo/.terminal_claude_agent_struct_out.json
OLD:   "relation_rationale": "Evidence (2 follow-up ablations) mostly disconfirms mechanism at tested cell; hypothesis narrows to scoped negative + cheaper-signal test",
NEW:   "relation_rationale": "Ablations mostly disconfirm mechanism at tested cell; hypothesis narrows to scoped negative + cheaper-signal test",
```

### [9] TOOL RESULT — Edit · 2026-08-26 21:47:31 UTC

```
{"filePath": "/ai-inventor/aii_data/runs/run_0pMem8W3ijCf/3_invention_loop/iter_2/upd_hypo/upd_hypo/.terminal_claude_agent_struct_out.json", "oldString": "  \"relation_rationale\": \"Evidence (2 follow-up ablations) mostly disconfirms mechanism at tested cell; hypothesis narrows to scoped negative + cheaper-signal test\",", "newString": "  \"relation_rationale\": \"Ablations mostly disconfirm mechanism at tested cell; hypothesis narrows to scoped negative + cheaper-signal test\",", "originalFile": "{\n  \"title\": \"Per-Key Cache Decay Rarely Beats a Cheaper Shorter Reset\",\n  \"hypothesis\": \"In a read-heavy key-value store with Zipf-skewed, drifting key popularity, a three-tier, CoV-classified per-key frequency-decay admission mechanism (as specified in the prior draft, with its M>=8-gap cold-start guard) does NOT deliver a net-beneficial recovery-time advantage over a merely SHORTENED single global TinyLFU reset period, once the comparison is (a) FDR-corrected across conditions, (b) checked against a short-reset ablation that sweeps the baseline's own reset multiplier down to 1x-2x cache capacity, and (c) checked for sensitivity to the CoV tier thresholds. At the one cell tested in depth (cache-to-key-space ratio=0.01, Zipf alpha=1.2, the 'win corner' of a 36-condition sweep), the false-discovery-corrected effect survives statistically, but a cheaper 1x-4x-multiplier global reset matches or beats the three-tier mechanism in 3 of its 4 drift scenarios, and the one scenario where per-key decay still wins (high-magnitude/high-frequency rank churn, ~9.5% faster recovery) holds in only 12 of 36 nearby CoV-threshold combinations -- i.e., is a narrow, untuned-hyperparameter-dependent result rather than a robust one. The mechanism also costs 5.14x-5.68x the baseline's memory (exceeding the pre-registered <=2x bound) and ~1.7-2.1x its per-request compute. On real Twitter production traffic (80,000 requests, cluster026) both estimators are steady-state-equivalent (within the pre-registered 1pp margin), giving no evidence either way on recovery speed since that trace carries no labeled drift. Because all three decisive follow-ups (short-reset ablation, threshold-sensitivity grid, real-trace check) were run at only ONE of nine (ratio, skew) cells, this hypothesis is now explicitly SCOPED: we have not established that per-key decay is dominated by short-reset everywhere, only at this one cell -- the blanket claim would overreach the evidence. The hypothesis for the next iteration is therefore twofold and testable cheaply (~80s/cell): (1) does the same short-reset-dominates pattern replicate at 2-3 additional (ratio, skew) cells, particularly other statistically-significant-but-not-yet-ablated groups from the 36-condition grid; and (2) within the per-key family itself, does the surviving high-magnitude/high-frequency advantage require the full three-tier CoV/EWMA machinery, or does a strictly cheaper per-key signal (a 2-tier collapse, or a binary hit-in-last-window flag instead of CoV of inter-arrival gaps) capture the same or more of that advantage at lower classification cost -- since if even the cheapest per-key variant cannot separate from short-reset once generalized, the entire per-key-granularity idea should be reported as a documented negative result for this design space rather than pursued further.\",\n  \"relation_rationale\": \"Evidence (2 follow-up ablations) mostly disconfirms mechanism at tested cell; hypothesis narrows to scoped negative + cheaper-signal test\",\n  \"confidence_delta\": \"decreased\",\n  \"key_changes\": [\n    \"Reframed core claim from 'per-key decay improves drift recovery' to a scoped, mostly-negative finding at the one cell tested in depth: short-reset ablation beats or matches per-key decay in 3/4 win-corner scenarios, and the 4th survives only in 12/36 nearby CoV-threshold combinations -- addressing the major reviewer critique that the paper's blanket conclusion overreached its single-cell evidence.\",\n    \"Explicitly flagged the single-cell scope limitation as a first-class part of the hypothesis rather than a footnote, per reviewer's [MAJOR](scope) critique, and set the next iteration's investigation to replicate the short-reset ablation at 2-3 additional (ratio, skew) cells before any generalized claim is made.\",\n    \"Added a second, narrower research question per reviewer's [MAJOR](novelty) critique: whether a cheaper per-key signal (2-tier collapse, or binary hit-in-last-window flag) within the per-key family can match the three-tier CoV/EWMA mechanism's surviving advantage at lower cost -- distinct from the already-tested 'per-key vs global' short-reset comparison.\",\n    \"Retained and reported as established: FDR-corrected significance of the original win-corner effect (rules out multiple-testing artifact), the corrected 5.14x-5.68x memory overhead figure, the ~1.7-2.1x compute overhead, and real-trace steady-state parity (no recovery-time evidence available, real trace too short/undrifted to judge).\",\n    \"Downgraded overall confidence: the mechanism's practical value is now supported only in a single narrow (scenario x threshold-neighborhood) slice of a single cell out of nine tested cells, and even there margin over the cheapest alternative shrank from the originally reported 22-27% to 9.5%.\"\n  ],\n  \"relation_type\": \"evolution\",\n  \"artifact_relations\": [\n    {\n      \"from_id\": \"art_f48a8QRaZrIB\",\n      \"to_id\": \"art_LWjppo9Kh9Do\",\n      \"relation_type\": \"uses\",\n      \"relation_rationale\": \"Real-trace arm sources pre-decoded Twitter cluster026 JSON directly from this dataset artifact.\"\n    },\n    {\n      \"from_id\": \"art_gQEGVMwa8ZKC\",\n      \"to_id\": \"art_QhkYY9QvbyCV\",\n      \"relation_type\": \"extends\",\n      \"relation_rationale\": \"Re-analyzes and adds FDR correction, threshold grid, and cost breakdown atop the prior experiment's raw results.\"\n    },\n    {\n      \"from_id\": \"art_f48a8QRaZrIB\",\n      \"to_id\": \"art_QhkYY9QvbyCV\",\n      \"relation_type\": \"uses\",\n      \"relation_rationale\": \"Reloads the real Twitter trace fresh from this dataset for its steady-state parity check.\"\n    }\n  ]\n}\n", "structuredPatch": [{"oldStart": 1, "oldLines": 7, "newStart": 1, "newLines": 7, "lines": [" {", "   \"title\": \"Per-Key Cache Decay Rarely Beats a Cheaper Shorter Reset\",", "   \"hypothesis\": \"In a read-heavy key-value store with Zipf-skewed, drifting key popularity, a three-tier, CoV-classified per-key frequency-decay admission mechanism (as specified in the prior draft, with its M>=8-gap cold-start guard) does NOT deliver a net-beneficial recovery-time advantage over a merely SHORTENED single global TinyLFU reset period, once the comparison is (a) FDR-corrected across conditions, (b) checked against a short-reset ablation that sweeps the baseline's own reset multiplier down to 1x-2x cache capacity, and (c) checked for sensitivity to the CoV tier thresholds. At the one cell tested in depth (cache-to-key-space ratio=0.01, Zipf alpha=1.2, the 'win corner' of a 36-condition sweep), the false-discovery-corrected effect survives statistically, but a cheaper 1x-4x-multiplier global reset matches or beats the three-tier mechanism in 3 of its 4 drift scenarios, and the one scenario where per-key decay still wins (high-magnitude/high-frequency rank churn, ~9.5% faster recovery) holds in only 12 of 36 nearby CoV-threshold combinations -- i.e., is a narrow, untuned-hyperparameter-dependent result rather than a robust one. The mechanism also costs 5.14x-5.68x the baseline's memory (exceeding the pre-registered <=2x bound) and ~1.7-2.1x its per-request compute. On real Twitter production traffic (80,000 requests, cluster026) both estimators are steady-state-equivalent (within the pre-registered 1pp margin), giving no evidence either way on recovery speed since that trace carries no labeled drift. Because all three decisive follow-ups (short-reset ablation, threshold-sensitivity grid, real-trace check) were run at only ONE of nine (ratio, skew) cells, this hypothesis is now explicitly SCOPED: we have not established that per-key decay is dominated by short-reset everywhere, only at this one cell -- the blanket claim would overreach the evidence. The hypothesis for the next iteration is therefore twofold and testable cheaply (~80s/cell): (1) does the same short-reset-dominates pattern replicate at 2-3 additional (ratio, skew) cells, particularly other statistically-significant-but-not-yet-ablated groups from the 36-condition grid; and (2) within the per-key family itself, does the surviving high-magnitude/high-frequency advantage require the full three-tier CoV/EWMA machinery, or does a strictly cheaper per-key signal (a 2-tier collapse, or a binary hit-in-last-window flag instead of CoV of inter-arrival gaps) capture the same or more of that advantage at lower classification cost -- since if even the cheapest per-key variant cannot separate from short-reset once generalized, the entire per-key-granularity idea should be reported as a documented negative result for this design space rather than pursued further.\",", "-  \"relation_rationale\": \"Evidence (2 follow-up ablations) mostly disconfirms mechanism at tested cell; hypothesis narrows to scoped negative + cheaper-signal test\",", "+  \"relation_rationale\": \"Ablations mostly disconfirm mechanism at tested cell; hypothesis narrows to scoped negative + cheaper-signal test\",", "   \"confidence_delta\": \"decreased\",", "   \"key_changes\": [", "     \"Reframed core claim from 'per-key decay improves drift recovery' to a scoped, mostly-negative finding at the one cell tested in depth: short-reset ablation beats or matches per-key decay in 3/4 win-corner scenarios, and the 4th survives only in 12/36 nearby CoV-threshold combinations -- addressing the major reviewer critique that the paper's blanket conclusion overreached its single-cell evidence.\","]}], "userModified": false, "replaceAll": false}
```

### [10] ASSISTANT · 2026-08-26 21:47:31 UTC

```
Fixed — the rationale is now under 120 characters.
```
