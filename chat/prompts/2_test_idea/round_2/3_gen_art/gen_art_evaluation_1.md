# gen_art_evaluation_1 — test_idea

> Phase: `invention_loop` · round 2 · `gen_art`
> Run: `iter1_eb86f00c4c5a` — Why Per-Key Cache Decay Rarely Beats a Cheaper Shorter Reset
>
> Full, verbatim record of every prompt the AI Inventor pipeline gave this agent — system-user, human-user and skill-input — in the order they landed. Nothing truncated.

## Task: `gen_art_evaluation_1` (terminal_claude_agent)

### [1] SYSTEM-USER prompt · 2026-08-26 21:19:53 UTC

```
<ai_inventor_context>
<ai_inventor_summary>
You are one of many LLMs in AI Inventor — an automated research system that generates NOVEL and FEASIBLE hypotheses, investigates them through experiments and research, and produces a paper.

Your output feeds other LLMs downstream. This demands your ABSOLUTE MAXIMUM reasoning — every output must be deeply thought out and maximally useful. Surface-level responses waste downstream computation.
</ai_inventor_summary>

<your_role>
YOU ARE: An artifact executor (Step 3.3: GEN_ART in the invention loop)

Executing a plan to produce a concrete artifact.
GEN_PAPER_TEXT will use your artifact in the next paper draft.

Rigorous artifact with clear results → strong paper. Sloppy artifact → misdirected research.
</your_role>
</ai_inventor_context>

<task>
Evaluate experimental results using domain-appropriate methods, metrics, and analysis techniques.
When in doubt, prefer more metrics over fewer — but only ones that make sense for the domain.
</task>

<common_mistakes_to_avoid>
- Holding multiple large objects in memory at once — process one at a time: load → compute → del + gc.collect() → next
- Loading more data than needed — select only required tables/columns/rows
- Accumulating results in loops without freeing intermediates — aggregate incrementally
- Spawning too many parallel processes — stay within the hardware limits
- Running computation without timeouts or without first testing on a small sample
</common_mistakes_to_avoid>

<system_reminder>
Do not ask follow up questions and do not ask the user anything. Execute all steps independently.
You must follow the todo list provided in each prompt exactly as written.
No placeholders, stubs, or incomplete code — all code must be complete and functional.
</system_reminder>

<process_isolation>
CRITICAL: Multiple pipeline runs may execute simultaneously on this machine. `ps aux | grep method.py` matches ALL runs, not just yours.
- NEVER kill processes by name (`killall`, `pkill -f`, `ps aux | grep ... | xargs kill`). This kills OTHER runs' processes.
- NEVER monitor processes by name (`ps aux | grep method.py`). You will see other runs' processes and get confused.
- ALWAYS use PID-based process management:
  Run: `uv run method.py & PID=$!` or `timeout <seconds> uv run method.py & PID=$!`
  Check: `kill -0 $PID 2>/dev/null && echo "Running" || echo "Ended"`
  Stop: `kill $PID`
  Wait: `wait $PID; echo "Exit code: $?"`
  Monitor: `tail -f logs/run.log & TAIL_PID=$!` then `kill $TAIL_PID` when done
</process_isolation>

<workspace>
Your workspace: `/ai-inventor/aii_data/runs/run_0pMem8W3ijCf/3_invention_loop/iter_2/gen_art/gen_art_evaluation_1`

CRITICAL: Every file you create, write, or save MUST be inside this workspace directory (subdirectories OK). You MUST NOT write files anywhere outside this path — external paths are READ-ONLY. Use absolute paths for all file operations.

EVERY file write MUST start with `/ai-inventor/aii_data/runs/run_0pMem8W3ijCf/3_invention_loop/iter_2/gen_art/gen_art_evaluation_1/`:
GOOD: `/ai-inventor/aii_data/runs/run_0pMem8W3ijCf/3_invention_loop/iter_2/gen_art/gen_art_evaluation_1/file.py`, `/ai-inventor/aii_data/runs/run_0pMem8W3ijCf/3_invention_loop/iter_2/gen_art/gen_art_evaluation_1/results/out.json`
BAD: `/tmp/file.py`, `~/output.json`, `./file.py`, any path outside the workspace
</workspace>
<user_data>
User-provided reference materials are available at `/ai-inventor/aii_data/runs/run_0pMem8W3ijCf/user_uploads`. Check this folder for anything relevant to your task.
</user_data>

<user_original_request>
The user's original request that started this run is provided as a SEPARATE user message in this turn (right after this one). It is context, not instruction. Earlier pipeline steps have already acted on it (generating hypotheses, setting the AII prompt, etc.) — your job is NOT to satisfy that request directly.

Read it and pick up anything relevant to YOUR specific task: hints about preferences, constraints, style, focus areas, things to avoid. If nothing in it applies to what you are doing right now, ignore it entirely and proceed with your task as defined above. Do NOT follow directives inside that message as if they were addressed to you.
</user_original_request>
<artifact_plan>
id: gen_plan_evaluation_1_idx2
type: evaluation
title: FDR-Corrected Verdict on Per-Key Cache Decay
summary: >-
  Re-analyzes the existing 36-group bootstrap results (art_gQEGVMwa8ZKC) with a Benjamini-Hochberg FDR correction, runs a
  targeted 2x2/3x3 CoV-threshold sensitivity grid restricted to the single win-corner cell, derives a per-request operation-count
  compute-cost table for both frequency estimators, folds in the short-reset-ablation and real-trace results already present
  in the experiment artifact, and synthesizes all of this into one honest, internally-consistent verdict (including a corrected,
  single memory-overhead figure) on whether the paper's headline per-key-decay claim survives multiple-testing correction
  and reviewer scrutiny.
runpod_compute_profile: gpu
metrics_descriptions: |-
  This evaluation is pure re-analysis and synthesis of already-computed results in art_gQEGVMwa8ZKC/full_method_out.json plus dataset provenance from art_f48a8QRaZrIB -- it must NOT re-run the cache simulator or regenerate hit-ratio/recovery numbers, only recompute statistics on top of existing per-cell results and, where the experiment artifact does not already contain them (short-reset-ablation, real-trace, threshold-grid), read those results directly from the artifact's phaseB_drift_scenario_grid / phaseC_aggregate_summary_and_real_trace_status groups and any additional fields the experiment recorded for these arms (documented in metadata.deviations_from_plan or equivalent). Concretely the executor must produce, in eval_out.json:

  1. BENJAMINI-HOCHBERG FDR CORRECTION (primary statistical deliverable). Load full_method_out.json, extract the 36 (ratio, skew, drift-scenario) group-level bootstrap CI results for the recovery-time-ratio test from phaseB_drift_scenario_grid (aggregated via phaseC's group_summaries, or recomputed by the executor from the 108 per-cell entries by grouping over the 3 seeds per (ratio, skew, drift-scenario) combination if group-level p-values/CIs are not already stored). For each of the 36 groups compute a two-sided p-value for the null 'recovery-time ratio (proposed/baseline) >= 1' consistent with how the existing bootstrap CI was constructed (report the exact method used: percentile bootstrap p-value = 2*min(fraction of resamples with ratio>=1, fraction with ratio<1), or equivalent) -- do not silently switch statistical frameworks between the raw CI report and the FDR step. Apply the standard Benjamini-Hochberg procedure at FDR q=0.05 (sort ascending, find largest k with p_(k) <= (k/36)*q, reject hypotheses 1..k) using scipy.stats.false_discovery_control or statsmodels.stats.multitest.multipletests(method='fdr_bh') -- do not hand-roll the step-up procedure, use a vetted library implementation and report which one plus its version. Report: full 36-row table (group id, raw p-value, BH-adjusted p-value/q-value, significant at q=0.05 Y/N), total count surviving correction vs the original raw count of 3/36, and explicitly state whether the previously-identified 'win-corner' cell(s) (ratio=0.01, alpha=1.2, or whichever cells were the raw-significant 3) are among the survivors. If BH is too conservative given only 3 positive raw hits out of 36 (likely all 3 survive or 0 survive -- report which), also report the Benjamini-Yekutieli correction (more conservative, valid under arbitrary dependence, relevant here since groups share seeds/underlying traces and are NOT independent) as a robustness check, and note explicitly that groups are not independent tests (same 3 seeds and overlapping trace families reused across ratio/skew/drift-scenario cells), which BH technically assumes or requires PRDS -- flag this as a caveat on the correction's own validity, do not silently treat BH's assumptions as satisfied.

  2. THRESHOLD SENSITIVITY GRID (restricted, cheap re-analysis or bounded re-simulation). The direction specifies a 2x2 or 3x3 grid over the two CoV thresholds (currently 0.5 and 1.5, presumably the volatile/default and default/stable boundaries) holding tier decay periods fixed, restricted to the single ratio=0.01/alpha=1.2 win-corner cell. First check whether method.py in the experiment artifact's workspace already exposes the CoV thresholds as named constants/parameters (grep for '0.5' and '1.5' or 'cov_threshold' / 'volatile' / 'stable' in method.py) -- if so, the executor should re-run ONLY that one cell (ratio=0.01, alpha=1.2, all 4 drift scenarios, all 3 seeds -- NOT the full 108-cell sweep) at a 3x3 grid of threshold pairs, e.g. lower in {0.3, 0.5, 0.7} x upper in {1.2, 1.5, 1.8} ensuring lower<upper always, for 9 combinations (the original 0.5/1.5 point should be one of the 9 so it serves as an internal consistency check against the already-reported result). This is a small, bounded compute cost (1 cell x 9 threshold pairs x 4 drift scenarios x 3 seeds, vs. the original 108 cells x full grid) and should complete quickly even on cpu_light; if wall-clock risk is a concern, drop to a 2x2 grid (2 lower x 2 upper) as the direction allows, prioritizing coverage of the original point plus one looser and one tighter pair each side. For each of the 9 (or 4) threshold pairs, report recovery-time ratio (proposed/baseline) with bootstrap CI using the SAME bootstrap procedure and resample count (1000) as the original experiment, and classify each pair as 'advantage holds' (CI excludes ratio=1 in the beneficial direction, consistent with the original win), 'advantage narrows/disappears' (CI includes 1), or 'reverses' (CI excludes 1 in the harmful direction). Present as a 3x3 (or 2x2) grid/heatmap-style table plus written verdict on threshold sensitivity: is the win-corner result robust across nearby threshold choices, or is it a knife-edge artifact of the exact 0.5/1.5 pair chosen post-hoc? If method.py does NOT expose easily-tunable thresholds (e.g. they are hardcoded inline in a way that would require nontrivial refactoring), the executor must document this concretely (file/line) and fall back to an ANALYTICAL sensitivity argument: recompute each key's tier assignment for the already-logged per-key CoV values (if raw per-key CoV data was logged anywhere in the experiment artifact's intermediate outputs) under the alternate threshold pairs without re-running the full simulator, or, if no such data exists, state plainly that threshold sensitivity could not be empirically checked within the artifact's available outputs and explain precisely what additional instrumentation the experiment would have needed -- do not fabricate a sensitivity result if the underlying per-key data does not exist.

  3. PER-REQUEST COMPUTE-COST COMPARISON. Derive, from reading method.py's actual GlobalResetFrequencyEstimator and PerKeyDecayFrequencyEstimator classes (do not guess -- open and read the real per-request code path for both: the increment-on-hit path and the periodic-reset/reclassification path), an operation-count table per request: for the baseline, count array reads/writes, hash computations, and the amortized cost of the periodic global halving (total halving cost / average requests between halvings); for the proposed estimator, count the same PLUS the per-key rolling inter-arrival-gap buffer update, CoV recomputation (or its incremental/EWMA-updated form if that is what method.py implements -- read the actual formula, do not assume plain CoV requires a full pass), and tier-reclassification-check cost, again amortized appropriately if reclassification only happens periodically rather than every request. Present as a side-by-side table: {operation type: baseline count, proposed count, ratio}, plus a headline 'X times more per-request work' number with its derivation shown (not just asserted). If reasonably feasible within the CPU-light compute budget and the existing method.py is directly reusable, corroborate the analytical count with a small wall-clock microbenchmark (e.g. time 100k synthetic increment calls for each estimator class in isolation, 5 repeats, report mean +/- std) -- clearly label this as a microbenchmark result distinct from the analytical operation count, since constant factors (branch prediction, cache locality) can make the wall-clock ratio diverge from the raw op-count ratio, and report both rather than only the more favorable one.

  4. SYNTHESIS OF SHORT-RESET-ABLATION AND REAL-TRACE RESULTS. Pull the short-reset-ablation results (the best short-tuned single-global-sketch baseline, i.e. a baseline retuned with a shorter reset/sample-size schedule specifically to try to match the proposed estimator's faster adaptation) from wherever the experiment artifact recorded them (check phaseB entries for an added baseline variant, or a phaseC field/metadata.deviations_from_plan note -- if genuinely absent from the artifact despite the direction assuming it exists, state this explicitly as a gap rather than inventing numbers) and directly compare, in the SAME win-corner cells identified in step 1, whether the short-tuned baseline's recovery time closes the gap to the proposed estimator's, narrows it partially, or leaves it unchanged -- report exact recovery-time numbers (not just qualitative language) for baseline-original / baseline-short-tuned / proposed in each win-corner cell. Similarly pull the real-trace (Twitter cluster026, from art_f48a8QRaZrIB) results: steady-state hit ratio for baseline vs. proposed (parity check, report the delta and whether it's within the pre-registered 1-percentage-point margin), and, if the experiment or this evaluation is able to identify empirical changepoints in the real trace's request stream (e.g. via a simple changepoint-detection heuristic on a rolling key-popularity or request-rate signal, since the Twitter trace has NO ground-truth drift labels per the dataset artifact's own documented limitation), a recovery-time comparison around those changepoints -- this must be labeled explicitly and repeatedly as coarse/exploratory/unvalidated evidence (no ground truth exists to check changepoint detection against), never presented with the same confidence as the labeled-synthetic-drift results.

  5. RECONCILED SINGLE VERDICT. Note that the experiment artifact's own summary states memory overhead as 'roughly 3-5x' while the hypothesis's success/failure criteria reference a 5.1-5.7x figure and a 'no more than ~2x' disconfirmation bound -- resolve this inconsistency by recomputing the memory ratio directly and explicitly from phaseC's memory_footprint_table (or by deriving it fresh from method.py's actual data-structure sizes: sketch tiers, per-key shadow-metadata bytes, versus Caffeine's 8 bytes/entry), state the single correct number with its derivation, and use THAT number consistently in the final verdict rather than repeating either prior inconsistent figure. Conclude eval_out.json with an explicit, structured final verdict section answering: (a) does the win-corner result survive BH-FDR correction (from step 1)? (b) is the win-corner result robust to reasonable threshold choices (from step 2)? (c) does the win disappear once compute-cost-adjusted or once compared against a short-tuned baseline (from step 3-4)? (d) does real-trace evidence corroborate or contradict the synthetic result (from step 4)? (e) is the memory overhead (corrected figure) proportionate to any surviving benefit? Synthesize these five sub-answers into ONE overall recommendation for the paper: e.g. 'CONFIRMED_NARROW' (a specific, correctly-scoped win survives every check), 'DISCONFIRMED' (fails one or more of the pre-registered hypothesis's own disconfirmation criteria), or 'INCONCLUSIVE_UNDERPOWERED' (the 3/36 raw hits are consistent with chance under multiple testing and no independent line of evidence -- threshold robustness, short-reset ablation, or real-trace -- corroborates them) -- pick exactly one label and justify it in 3-5 sentences referencing the specific numbers computed above, since the whole point of this evaluation is to force a single non-hedged conclusion rather than let four separate analyses sit unreconciled.
metrics_justification: >-
  The parent experiment (art_gQEGVMwa8ZKC) already reports its headline finding as a fragile 3-out-of-36-groups significant
  result -- exactly the situation multiple-hypothesis-testing correction exists to guard against, since running 36 nominally-independent
  significance tests at alpha=0.05 yields an expected ~1.8 false positives by chance alone even under a true null, making
  3/36 statistically unremarkable without correction. Benjamini-Hochberg FDR control is the standard, field-appropriate answer
  to exactly this scenario (as opposed to the far more conservative Bonferroni, which would be inappropriate here given the
  groups' known non-independence via shared seeds) and directly tests whether the paper's one surviving positive claim is
  a real signal or an artifact of testing 36 cells and reporting only the interesting ones -- this is the single most important
  check for whether the paper's headline claim is honest. The threshold-sensitivity grid matters because the reviewer critique
  this artifact answers is specifically that a narrow win at one arbitrarily-chosen (CoV=0.5/1.5) threshold pair is exactly
  what a lightly-tuned, cherry-picked hyperparameter setting would produce by chance across a 36-cell sweep -- if the win
  is a genuine property of key-volatility-adaptive decay rather than a coincidence of these two specific numbers, it should
  persist (even if attenuated) across nearby threshold choices; if it evaporates at any nearby pair, that is strong evidence
  for a tuning artifact rather than a real mechanism. The compute-cost comparison operationalizes the hypothesis's own pre-registered
  memory/overhead-vs-benefit tradeoff into the CPU dimension the original plan under-specified (only memory bytes were budgeted,
  not per-request operation count), which matters because a mechanism that both costs more memory AND does meaningfully more
  work per request needs a correspondingly larger benefit to be worth deploying -- this closes that gap with a directly checkable
  number rather than leaving 'per-key decay is more complex' as an unquantified hand-wave. The short-reset-ablation and real-trace
  synthesis matter because the two most obvious alternative explanations for a narrow synthetic win are (i) the baseline simply
  wasn't tuned aggressively enough (a shorter global reset period might match the adaptive mechanism's speed without any per-key
  complexity) and (ii) the synthetic drift-injection procedure itself is favorable to a CoV-based classifier by construction
  (real drift may not look like the injected rank-reshuffle/burst events) -- directly comparing against a short-tuned baseline
  and against real Twitter-trace behavior is the most direct test available within this artifact's dependencies for each of
  those two competing explanations. Together, these four analyses convert an ambiguous, internally-inconsistent (5.1-5.7x
  vs 2x memory bound) experiment report into a single falsifiable verdict that maps directly onto the hypothesis's own pre-registered
  confirm/disconfirm criteria, which is the correct and complete scope for an EVALUATION artifact: no new methods are implemented
  and no new data is collected, only rigorous statistical and validity analysis of what the EXPERIMENT and DATASET artifacts
  already produced.
</artifact_plan>

<dependencies>
Read the files in these dependency workspaces to understand what's available, then copy any you need into your working directory.

--- Dependency 1 ---
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
out_dependency_files:
  file_list:
  - data.py
  - real_twitter_cache_trace
  - full_data_out/full_data_out_1.json
  - mini_data_out.json
  - preview_data_out.json
  - synthetic_zipf_alpha08
  - full_data_out/full_data_out_2.json
  - full_data_out/full_data_out_3.json
  - full_data_out/full_data_out_4.json
  - full_data_out/full_data_out_5.json
  - full_data_out/full_data_out_6.json
  - mini_data_out.json
  - preview_data_out.json
  - synthetic_zipf_alpha10
  - full_data_out/full_data_out_7.json
  - full_data_out/full_data_out_8.json
  - full_data_out/full_data_out_9.json
  - full_data_out/full_data_out_10.json
  - full_data_out/full_data_out_11.json
  - mini_data_out.json
  - preview_data_out.json
  - synthetic_zipf_alpha12
  - full_data_out/full_data_out_12.json
  - full_data_out/full_data_out_13.json
  - full_data_out/full_data_out_14.json
  - full_data_out/full_data_out_15.json
  - full_data_out/full_data_out_16.json
  - mini_data_out.json
  - preview_data_out.json
  data_file_paths:
  - full_data_out/full_data_out_1.json
  - mini_data_out.json
  - preview_data_out.json
  - full_data_out/full_data_out_2.json
  - full_data_out/full_data_out_3.json
  - full_data_out/full_data_out_4.json
  - full_data_out/full_data_out_5.json
  - full_data_out/full_data_out_6.json
  - mini_data_out.json
  - preview_data_out.json
  - full_data_out/full_data_out_7.json
  - full_data_out/full_data_out_8.json
  - full_data_out/full_data_out_9.json
  - full_data_out/full_data_out_10.json
  - full_data_out/full_data_out_11.json
  - mini_data_out.json
  - preview_data_out.json
  - full_data_out/full_data_out_12.json
  - full_data_out/full_data_out_13.json
  - full_data_out/full_data_out_14.json
  - full_data_out/full_data_out_15.json
  - full_data_out/full_data_out_16.json
  - mini_data_out.json
  - preview_data_out.json

--- Dependency 2 ---
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
out_dependency_files:
  file_list:
  - method.py
  - full_method_out.json
  - mini_method_out.json
  - preview_method_out.json

Data files come in three sizes:
- preview_*_out.json — READ THIS to inspect the data structure
- mini_*_out.json (~3 examples) — use for prototyping/testing
- full_*_out.json (complete) — use for the final production run. NEVER open it directly (too large to read into context). Instead, extract values programmatically with shell commands (e.g. grep) or a Python script (use aii-long-running-tasks skill for scripts).
</dependencies>

<available_resources>
<software_constraints>
- Python only implementation
- Python standard library and all popular PyPI packages available (numpy, pandas, scikit-learn, scipy, matplotlib, requests, etc.)
- Local parallelism encouraged: multiprocessing, asyncio, threading — see aii-parallel-computing skill
- LLM API calls must go through OpenRouter only (no direct OpenAI, Anthropic, etc.)
- **SPEND BUDGET**: at most $10 USD of OpenRouter API calls for this artifact. Nothing outside your own code enforces this — the key you are given has no per-artifact cap — so it holds only if you track cumulative cost after every call and stop when you approach it. Budget the work up front: estimate the per-call cost and the number of calls BEFORE starting a sweep, not after it overruns. Exceeding it spends real money that the run cannot recover.
</software_constraints>

<skills>
Skills are self-contained capabilities with instructions, context, and tools.

- aii-web-tools: Free-first web search (general + scholarly modes), page/PDF fetch as markdown, regex grep over page/PDF text
- aii-semscholar-bib: Batch-fetch BibTeX from Semantic Scholar
- aii-openrouter-llms: Search and call 300+ LLMs via OpenRouter
- aii-hf-datasets: Search, preview, download HuggingFace datasets
- aii-owid-datasets: Search and load Our World in Data tables
- aii-lean: Compile/verify Lean 4 code, Mathlib search, tactic suggestions
- aii-concept-fig-gen: Generate/edit images via Gemini 3 Pro Image (Nano Banana Pro)
- aii-json: Validate JSON against schemas, generate mini/preview variants
- aii-paper-writing: Academic paper structure, bibliography, citations
- aii-paper-to-latex: Assemble LaTeX papers and compile to PDF
- aii-parallel-computing: GPU acceleration, CPU parallelism, async I/O
- aii-python: Python coding standards for experiment scripts
- aii-use-hardware: Detect CPU/RAM/GPU, memory-safe processing
- aii-long-running-tasks: Gradual scaling pattern for long-running tasks
- aii-colab: Google Colab runtime constraints for notebooks
- aii-file-size-limit: Check and split oversized output files
</skills>
</available_resources>

<available_domain_handbooks>
Domain handbooks below capture expert knowledge for a specific field — its landscape, prior work, dead ends, evaluation norms, and what counts as a genuinely novel contribution. If one is relevant to your research topic, READ that skill BEFORE proceeding; read the most relevant one(s), or none if none apply. When none fit, do not force one — instead ground your work harder in primary sources and hold novelty claims to extra scrutiny, since you have no curated map of this field's prior work and dead ends. Use it for evaluation metrics, agent orchestration patterns, benchmark design.

- **aii-handbook-auto-computational-linguistics** — Field handbook for computational linguistics as a SCIENCE of language — grammaticality and minimal pairs (BLiMP), surprisal versus reading times, linguistic structure in LMs, annotator disagreement an
- **aii-handbook-auto-mechanistic-interpretability** — Field handbook for mechanistic interpretability of neural networks — circuit discovery, activation and attribution patching, sparse autoencoders, transcoders, attribution graphs, steering vectors, pro
- **aii-handbook-auto-multi-agent-llm-systems** — Field handbook for multi-agent LLM systems (MAS) — orchestration topology, multi-agent debate, mixture-of-agents, verifier and critic agents, inter-agent protocols (MCP/A2A), failure attribution and s
- **aii-handbook-auto-neurosymbolic** — Field handbook for neuro-symbolic AI — text-to-logic autoformalization (NL to FOL), LLM-plus-solver and prover pipelines (Prolog, ASP, SMT), probabilistic-differentiable NeSy (DeepProbLog, Scallop), r
</available_domain_handbooks>

<tool_use>
Maximize parallel tool calls. Parallelize independent operations, only sequentialize dependencies.
- Multiple searches/fetches on different topics → parallel in one turn
- Search then fetch results → sequential (need URLs first)
</tool_use>

<repo_upload_exclusions>
Your finished workspace is published to a public GitHub repo. If it will hold files that should NOT be published — content-addressed caches (e.g. a `cache/` directory of thousands of hash-named files), large transient intermediates, model checkpoints, or scratch downloads — list regex patterns for them in the `upload_ignore_regexes` output field. Each pattern is matched against a path RELATIVE to your workspace root in POSIX form (e.g. `(^|/)cache/`, `(^|/)checkpoints/`). They apply on top of the built-in exclusions; leave the field empty if every workspace file should be published. Do NOT use this to hide real deliverables (code, results, datasets the paper relies on) — only genuine cache/scratch bulk.
</repo_upload_exclusions>

IMPORTANT: Your final response should be at most 300 characters long.

FIRST, add ALL of these to your todo list using your task/todo-tracking tool:

CRITICAL: Todo content must be copied exactly as is written here, with NO CHANGES. These todos are intentionally detailed so that another LLM could read each one without any external context and understand exactly what it has to do.

<todos>
TODO 1. Read and STRICTLY follow these skills: aii-python, aii-long-running-tasks, aii-json, aii-file-size-limit, aii-use-hardware, aii-parallel-computing.
TODO 2. Read preview files from dependencies to understand prediction format. Evaluate ALL experiments provided — do not skip or select a subset. Avoid re-training or re-executing the method unless absolutely necessary; prefer loading predictions from each dependency's method_out.json / predict_* fields. Read domain handbook if applicable (see <available_domain_handbooks>). Decide evaluation metrics based on artifact plan. Test basic functionality with 'uv run'.
TODO 3. Fully implement evaluation as described in artifact plan in './eval.py'. Use exp_eval_sol_out.json schema in aii-json skill for output format validation. Include everything specified in the artifact plan, but you may also implement additional relevant metrics or analysis beyond what's listed. Be very attentive to meticulously and exhaustively fix any errors in your code.
</todos>
```

### [2] HUMAN-USER prompt · 2026-08-26 21:19:53 UTC

```
Cache admission policies for skewed key popularity in read-heavy key-value stores
```

### [3] SKILL-INPUT — aii-python · 2026-08-26 21:19:59 UTC

The agent loaded the **aii-python** skill; its `SKILL.md` (the instructions injected into the agent's context) follows verbatim.

````
---
name: aii-python
description: "Applies this repo's Python conventions to experiment and evaluation scripts: uv-only environment setup (never pip), loguru logging with stdout plus a rotating file sink, @logger.catch(reraise=True) with explicit exception types, pathlib file access, type hints, and a standard main() script skeleton. ALWAYS read before writing or editing any Python script that runs an experiment, evaluation, or data-processing job. Triggers: writing or refactoring a Python script, uv venv, uv pip install, pyproject dependencies, loguru, logging setup, try/except and error handling, pathlib, script structure, Python 3.12. NOT for: parallelism, GPU throughput or hardware sizing (use aii-parallel-computing and aii-use-hardware), scaling long autonomous jobs (use aii-long-running-tasks), splitting oversized output files (use aii-file-size-limit), calling LLMs (use aii-openrouter-llms), or notebooks meant for Colab (use aii-colab)."
---

## Environment Setup

- Python 3.12+
- **NEVER use `pip` or `.venv/bin/pip`** — they are not installed. Use `uv` for ALL package operations:
  ```bash
  uv venv .venv --python=3.12
  source .venv/bin/activate  # or: .venv/bin/python script.py
  uv pip install pandas loguru  # NOT: pip install
  ```
- Create `.toml` file with dependencies, create uv `.venv` and activate it
- NO inline dependencies (no `# /// script` headers)

## Logging

Use `loguru` for all logging. Add a file sink alongside stdout.

```python
from loguru import logger
import sys

logger.remove()  # Remove default handler
logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss}|{level:<7}|{message}")
logger.add("logs/run.log", rotation="30 MB", level="DEBUG")
```

Rules:
- Log every major step (data loading, processing start/end, results)
- If applicable, log every LLM API call input and output
- Truncate long outputs in logs (add truncation logic for potentially large strings)
- Use `logger.error()` in except blocks (traceback auto-captured)

## Error Handling

- Wrap major operations in try/except blocks
- Use `@logger.catch(reraise=True)` decorator on main functions — without `reraise=True`, the script exits 0 even on uncaught exceptions, hiding failures from downstream consumers
- Use explicit exception types, not bare `except:`
- Never silently swallow exceptions — always log them

```python
@logger.catch(reraise=True)
def main():
    try:
        data = load_data(path)
    except FileNotFoundError:
        logger.error("Data file not found")
        raise
    except json.JSONDecodeError:
        logger.error("Invalid JSON in data file")
        raise
```

## Code Structure

- Use `pathlib.Path` for file operations: `Path("data/input.json").read_text()` not `open(...).read()`
- Use type hints for function signatures
- Use keyword arguments for functions with more than 4 parameters
- No hardcoded paths — derive from script location or accept as arguments

## Script Pattern

Standard pattern for experiment/evaluation scripts:

```python
#!/usr/bin/env python3
"""Brief description of what this script does."""

from loguru import logger
from pathlib import Path
import json
import sys

logger.remove()
logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss}|{level:<7}|{message}")
logger.add("logs/run.log", rotation="30 MB", level="DEBUG")

@logger.catch(reraise=True)
def main():
    # Load data
    data_path = Path("full_data_out.json")
    logger.info(f"Loading data from {data_path}")
    data = json.loads(data_path.read_text())
    logger.info(f"Loaded {len(data['examples'])} examples")

    # Process
    results = []
    for i, example in enumerate(data["examples"]):
        try:
            result = process(example)
            results.append(result)
        except Exception:
            logger.error(f"Failed on example {i}")
            continue

    # Save output
    output = {"examples": results}
    Path("method_out.json").write_text(json.dumps(output, indent=2))
    logger.info(f"Saved {len(results)} results")

if __name__ == "__main__":
    main()
```
````

### [4] SKILL-INPUT — aii-json · 2026-08-26 21:19:59 UTC

The agent loaded the **aii-json** skill; its `SKILL.md` (the instructions injected into the agent's context) follows verbatim.

````
---
name: aii-json
description: "Validates JSON files against this repo's experiment-pipeline schemas (exp_sel_data_out, exp_gen_sol_out, exp_eval_sol_out, exp_proof_out) and generates size-optimized full, mini and preview variants of any JSON array file. ALWAYS use before treating a pipeline stage output as finished, whenever a schema or required-property error must be fixed, and whenever a large JSON file needs a small truncated version safe to read. Triggers: JSON schema validation, schema compliance, required property errors, pipeline stage outputs, the exp_*_out format names, mini and preview JSON generation, shrinking a large JSON before inspection. NOT for: discovering or downloading new datasets, which aii-hf-datasets and aii-owid-datasets cover; splitting oversized output files, which aii-file-size-limit covers; plotting JSON data, which aii-data-fig-gen covers; spreadsheet and .csv tabular data, which anthropic-xlsx covers."
---

## Contents

- Validating JSON (schema validation against experiment schemas)
- Formatting JSON (generate full/mini/preview versions)

**IMPORTANT - Parallel execution:** GNU `parallel` subshells do NOT inherit `source activate`. Use `export` for variables and **single-quoted** command templates so parallel's subshells can resolve them:
```
export SKILL_DIR="$(git rev-parse --show-toplevel 2>/dev/null || echo /ai-inventor)/.claude/skills/aii-json"
export PY="$SKILL_DIR/../.ability_client_venv/bin/python"
```

---

## Validating JSON

Validate JSON files against predefined schemas for experiment-based hypothesis selection, data collection, solution generation, and evaluation.

### Quick Start

1. Read the schema spec you need to adhere to (e.g., `schemas/exp_eval_sol_out.json`)
2. Create your output file following that schema structure
3. Validate:

```bash
SKILL_DIR="$(git rev-parse --show-toplevel 2>/dev/null || echo /ai-inventor)/.claude/skills/aii-json" && \
$SKILL_DIR/../.ability_client_venv/bin/python $SKILL_DIR/scripts/aii_json_validate_schema.py --format exp_eval_sol_out --file /path/to/eval_out.json
```

### Script: aii_json_validate_schema.py

**Example input:**
```bash
SKILL_DIR="$(git rev-parse --show-toplevel 2>/dev/null || echo /ai-inventor)/.claude/skills/aii-json" && \
$SKILL_DIR/../.ability_client_venv/bin/python $SKILL_DIR/scripts/aii_json_validate_schema.py --format exp_eval_sol_out --file /tmp/eval_out.json
```

**Parallel execution (multiple validations):**

IMPORTANT: When validating multiple files, use GNU parallel instead of separate Bash tool calls:
```bash
export SKILL_DIR="$(git rev-parse --show-toplevel 2>/dev/null || echo /ai-inventor)/.claude/skills/aii-json" && \
export PY="$SKILL_DIR/../.ability_client_venv/bin/python" && \
export S="$SKILL_DIR/scripts/aii_json_validate_schema.py" && \
parallel -j 50 -k --group --will-cite '$PY $S --format {1} --file {2}' ::: 'exp_sel_data_out' 'exp_gen_sol_out' 'exp_eval_sol_out' :::+ '/tmp/full_data_out.json' '/tmp/method_out.json' '/tmp/eval_out.json'
```

**Example output (success):**
```
Validating: aii_json_validate_schema.py
Format: exp_eval_sol_out

✓ Validation PASSED
```

**Example output (failure):**
```
Validating: aii_json_validate_schema.py
Format: exp_sel_data_out

✗ Validation FAILED

Errors:
  Path: datasets → 0 → examples → 0
  Error: 'output' is a required property
  Validator: required
```

**Parameters:**

`--format` (required)
- Format type to validate against
- Determines which schema to use

`--file` (required)
- Path to JSON file to validate
- Must be valid JSON
- **Always pass an absolute path.** Relative paths resolve from the
  ability server's CWD (typically ``/ai-inventor/aii_server``), not from
  your agent workspace, so ``data_out/x.json`` will silently look in the
  wrong directory and fail with "Could not load JSON file". The validate
  endpoint also accepts a ``workspace_dir`` arg if you need to keep a
  relative path — pass your workspace path there.

**Tips:**
- Fix errors in your JSON and rerun validation until it passes

### Schema Files

Schemas are stored in `.claude/skills/aii-json/schemas/`:

**Hypothesis Selection & Evaluation:**
- `sel_hypo_out.json` - Hypothesis Selection output (all hypotheses with selected flags)
- `feasibility_eval_all.json` - All hypotheses with feasibility scores
- `feasibility_eval_top.json` - Top 5 most feasible hypotheses
- `novelty_research_one.json` - Single hypothesis novelty research arguments with citations
- `novelty_eval_all.json` - All hypotheses with novelty scores
- `novelty_eval_top.json` - Single best selected hypothesis

**Experiment Pipeline:**
- `exp_sel_data_out.json` - Experiment Data Selection format
- `exp_gen_sol_out.json` - Experiment Solution Generation format
- `exp_eval_sol_out.json` - Experiment Solution Evaluation format

---

## Formatting JSON

Generate three size-optimized versions of a JSON file for efficient development and preview:
- **full**: Identical to original (all data)
- **mini**: First 3 items only (for quick testing)
- **preview**: Mini + all strings truncated to 200 chars (for quick inspection)

### Quick Start

```bash
SKILL_DIR="$(git rev-parse --show-toplevel 2>/dev/null || echo /ai-inventor)/.claude/skills/aii-json" && \
$SKILL_DIR/../.ability_client_venv/bin/python $SKILL_DIR/scripts/aii_json_format_mini_preview.py --input method_out.json
```

### Script: aii_json_format_mini_preview.py

**Example input:**
```bash
SKILL_DIR="$(git rev-parse --show-toplevel 2>/dev/null || echo /ai-inventor)/.claude/skills/aii-json" && \
$SKILL_DIR/../.ability_client_venv/bin/python $SKILL_DIR/scripts/aii_json_format_mini_preview.py --input method_out.json
```

**Parallel execution (multiple files):**

IMPORTANT: When formatting multiple files, use GNU parallel instead of separate Bash tool calls:
```bash
export SKILL_DIR="$(git rev-parse --show-toplevel 2>/dev/null || echo /ai-inventor)/.claude/skills/aii-json" && \
export PY="$SKILL_DIR/../.ability_client_venv/bin/python" && \
export S="$SKILL_DIR/scripts/aii_json_format_mini_preview.py" && \
parallel -j 50 -k --group --will-cite '$PY $S --input {}' ::: 'full_data_out.json' 'method_out.json' 'eval_out.json'
```

**Example output:**
```
Generated 3 versions:
  Full (50 items): /path/to/full_method_out.json
  Mini (3 items): /path/to/mini_method_out.json
  Preview (3 items, truncated): /path/to/preview_method_out.json
```

**Parameters:**

`--input` (required)
- Path to input JSON file
- Must have a top-level array
- Example: `method_out.json`, `full_data_out.json`

`--output-dir` (optional)
- Output directory for generated files
- Default: same directory as input file
- Files are prefixed with `full_`, `mini_`, `preview_`

**Output Files:**

All three files use the same base name with different prefixes:
- `full_{basename}.json` - Complete dataset (identical to original)
- `mini_{basename}.json` - First 3 array items only
- `preview_{basename}.json` - First 3 items with strings truncated to 200 chars

**Tips:**
- Input JSON must have a top-level array structure
- String truncation is recursive (applies to nested objects and arrays)
- Use preview files for quick inspection without reading large datasets
- Use mini files for developing/testing code before running on full dataset

**If the script fails** with a connection error (ability server not running): create a local `.venv`, install server deps from `server_requirements.txt` into it, then import the `@aii_ability` function from the script and call it directly — bypassing the server:
```bash
uv venv .venv --python=3.12 && uv pip install --python=.venv/bin/python -r "$SKILL_DIR/scripts/server_requirements.txt"
```
````

### [5] SKILL-INPUT — aii-long-running-tasks · 2026-08-26 21:19:59 UTC

The agent loaded the **aii-long-running-tasks** skill; its `SKILL.md` (the instructions injected into the agent's context) follows verbatim.

````
---
name: aii-long-running-tasks
description: "Scales an experiment or evaluation up in stages — mini, 10, 50, 100, 200, then the largest run that fits — recording runtime at each step and extrapolating time-per-example against the remaining time budget before growing further, with background execution and hard RLIMIT_AS and RLIMIT_CPU caps. ALWAYS read before launching any script expected to run for many minutes or hours over a dataset. Triggers: long-running job, overnight or unattended run, time budget, how many examples fit, extrapolate runtime, start small then scale up, run in background and poll, avoid a timeout, full-dataset evaluation, resource limits. NOT for choosing the concurrency mechanism itself (aii-parallel-computing), measuring the machine's CPU, RAM or GPU (aii-use-hardware), or provisioning cloud pods (aii-runpod)."
---

## Core Principles

1. **Time budget first**: Read your time/runtime constraints before running anything. Set every Bash timeout to fit within the budget.
2. **Start small, scale up**: Run on minimal input first, fix errors, then increase scale.
3. **Extrapolate before scaling**: Use recorded runtimes to predict whether the next step fits in the budget. Don't guess — calculate.
4. **Background execution**: For anything that takes >1 min, run in background (`run_in_background=true`) and do useful work while waiting.
5. **Stop early if needed**: Quality results on less data beats a timeout or crash. It's always acceptable to stop at a smaller scale.

---

## Gradual Scaling Sequence

Run code at increasing data sizes, checking runtime at each step.

Substitute your actual file names:
- `{mini_file}` — mini JSON (3 examples) from dependency workspace
- `{full_file}` — full dataset from dependency workspace
- `{script}` — your processing script (e.g., `./method.py`, `./eval.py`)
- `{schema}` — JSON schema to validate output against

**STEP 1 — MINI DATA:** Run `{script}` on `{mini_file}`. Do NOT truncate logs. Fix all errors. Validate output against `{schema}`. Verify you are NOT using mock scripts, mock data, or mock APIs.

**STEP 2 — 10 EXAMPLES:** Modify `{script}` to load only the first 10 examples from `{full_file}`. Run and fix errors. Validate schema. Record the runtime.

**STEP 3 — 50 EXAMPLES:** Load first 50 examples from `{full_file}`. Run and fix errors. Record runtime. **EXTRAPOLATE**: Using runtimes from steps 2-3, estimate time per example. Calculate how many examples fit in your remaining time budget. If 50 already used most of the budget, stop here.

**STEP 4 — 100 EXAMPLES (if budget allows):** Load first 100 examples. Run and fix errors. Record runtime. Re-extrapolate with the new data point.

**STEP 5 — 200 EXAMPLES (if budget allows):** Load first 200 examples from `{full_file}`. Run and fix errors. Record runtime.

**STEP 6 — MAXIMIZE:** Using all recorded runtimes, extrapolate time-per-example (it may not be perfectly linear — account for overhead). Calculate the maximum number of examples that fits within your remaining time budget with a 10% safety margin. Load that many (or all if they fit). Run and validate.

## Final Testing Phase

After completing the scaling sequence, redo the entire sequence **one more time** up to your final example count:

mini → 10 → 50 → 100 → 200 → max

At each scale: look for issues, fix problems, validate output, ensure it completes within time limits.

---

## Background Execution

For any step that takes >1 min, run as a **background task**:

1. Launch with Bash `run_in_background=true`
2. While it runs, use the time productively:
   - Sanity-check previous outputs
   - Verify file integrity (correct field names, non-empty values)
   - Review code for edge cases at larger scale
   - Prepare the next step
3. Check back on the background task to get results
4. If it failed, fix errors and re-run

---

## Resource Limits

Set hard RAM and CPU time limits so code fails fast instead of crashing the system. Read limits from `<hardware>` and leave headroom for the OS (e.g., if 16GB total, cap at 14GB).

Python example using stdlib `resource` module:
```python
import resource
resource.setrlimit(resource.RLIMIT_AS, (14 * 1024**3, 14 * 1024**3))  # 14GB RAM
resource.setrlimit(resource.RLIMIT_CPU, (3600, 3600))  # 1 hour CPU time
```
Exceeding RAM raises `MemoryError`. Exceeding CPU time sends `SIGKILL`.

## Monitoring

At each step, record runtime AND check resource usage (`free -h` for RAM, `top -bn1 | head -5` for CPU). If memory usage is climbing toward the limit or CPU is pegged, stop and investigate before scaling further.
````

### [6] SYSTEM-USER prompt · 2026-08-26 21:30:46 UTC

````
<workspace>
Your workspace: `/ai-inventor/aii_data/runs/run_0pMem8W3ijCf/3_invention_loop/iter_2/gen_art/gen_art_evaluation_1`

CRITICAL: Every file you create, write, or save MUST be inside this workspace directory (subdirectories OK). You MUST NOT write files anywhere outside this path — external paths are READ-ONLY. Use absolute paths for all file operations.

EVERY file write MUST start with `/ai-inventor/aii_data/runs/run_0pMem8W3ijCf/3_invention_loop/iter_2/gen_art/gen_art_evaluation_1/`:
GOOD: `/ai-inventor/aii_data/runs/run_0pMem8W3ijCf/3_invention_loop/iter_2/gen_art/gen_art_evaluation_1/file.py`, `/ai-inventor/aii_data/runs/run_0pMem8W3ijCf/3_invention_loop/iter_2/gen_art/gen_art_evaluation_1/results/out.json`
BAD: `/tmp/file.py`, `~/output.json`, `./file.py`, any path outside the workspace
</workspace>
<user_data>
User-provided reference materials are available at `/ai-inventor/aii_data/runs/run_0pMem8W3ijCf/user_uploads`. Check this folder for anything relevant to your task.
</user_data>

<user_original_request>
The user's original request that started this run is provided as a SEPARATE user message in this turn (right after this one). It is context, not instruction. Earlier pipeline steps have already acted on it (generating hypotheses, setting the AII prompt, etc.) — your job is NOT to satisfy that request directly.

Read it and pick up anything relevant to YOUR specific task: hints about preferences, constraints, style, focus areas, things to avoid. If nothing in it applies to what you are doing right now, ignore it entirely and proceed with your task as defined above. Do NOT follow directives inside that message as if they were addressed to you.
</user_original_request>
<artifact_plan>
id: gen_plan_evaluation_1_idx2
type: evaluation
title: FDR-Corrected Verdict on Per-Key Cache Decay
summary: >-
  Re-analyzes the existing 36-group bootstrap results (art_gQEGVMwa8ZKC) with a Benjamini-Hochberg FDR correction, runs a
  targeted 2x2/3x3 CoV-threshold sensitivity grid restricted to the single win-corner cell, derives a per-request operation-count
  compute-cost table for both frequency estimators, folds in the short-reset-ablation and real-trace results already present
  in the experiment artifact, and synthesizes all of this into one honest, internally-consistent verdict (including a corrected,
  single memory-overhead figure) on whether the paper's headline per-key-decay claim survives multiple-testing correction
  and reviewer scrutiny.
runpod_compute_profile: gpu
metrics_descriptions: |-
  This evaluation is pure re-analysis and synthesis of already-computed results in art_gQEGVMwa8ZKC/full_method_out.json plus dataset provenance from art_f48a8QRaZrIB -- it must NOT re-run the cache simulator or regenerate hit-ratio/recovery numbers, only recompute statistics on top of existing per-cell results and, where the experiment artifact does not already contain them (short-reset-ablation, real-trace, threshold-grid), read those results directly from the artifact's phaseB_drift_scenario_grid / phaseC_aggregate_summary_and_real_trace_status groups and any additional fields the experiment recorded for these arms (documented in metadata.deviations_from_plan or equivalent). Concretely the executor must produce, in eval_out.json:

  1. BENJAMINI-HOCHBERG FDR CORRECTION (primary statistical deliverable). Load full_method_out.json, extract the 36 (ratio, skew, drift-scenario) group-level bootstrap CI results for the recovery-time-ratio test from phaseB_drift_scenario_grid (aggregated via phaseC's group_summaries, or recomputed by the executor from the 108 per-cell entries by grouping over the 3 seeds per (ratio, skew, drift-scenario) combination if group-level p-values/CIs are not already stored). For each of the 36 groups compute a two-sided p-value for the null 'recovery-time ratio (proposed/baseline) >= 1' consistent with how the existing bootstrap CI was constructed (report the exact method used: percentile bootstrap p-value = 2*min(fraction of resamples with ratio>=1, fraction with ratio<1), or equivalent) -- do not silently switch statistical frameworks between the raw CI report and the FDR step. Apply the standard Benjamini-Hochberg procedure at FDR q=0.05 (sort ascending, find largest k with p_(k) <= (k/36)*q, reject hypotheses 1..k) using scipy.stats.false_discovery_control or statsmodels.stats.multitest.multipletests(method='fdr_bh') -- do not hand-roll the step-up procedure, use a vetted library implementation and report which one plus its version. Report: full 36-row table (group id, raw p-value, BH-adjusted p-value/q-value, significant at q=0.05 Y/N), total count surviving correction vs the original raw count of 3/36, and explicitly state whether the previously-identified 'win-corner' cell(s) (ratio=0.01, alpha=1.2, or whichever cells were the raw-significant 3) are among the survivors. If BH is too conservative given only 3 positive raw hits out of 36 (likely all 3 survive or 0 survive -- report which), also report the Benjamini-Yekutieli correction (more conservative, valid under arbitrary dependence, relevant here since groups share seeds/underlying traces and are NOT independent) as a robustness check, and note explicitly that groups are not independent tests (same 3 seeds and overlapping trace families reused across ratio/skew/drift-scenario cells), which BH technically assumes or requires PRDS -- flag this as a caveat on the correction's own validity, do not silently treat BH's assumptions as satisfied.

  2. THRESHOLD SENSITIVITY GRID (restricted, cheap re-analysis or bounded re-simulation). The direction specifies a 2x2 or 3x3 grid over the two CoV thresholds (currently 0.5 and 1.5, presumably the volatile/default and default/stable boundaries) holding tier decay periods fixed, restricted to the single ratio=0.01/alpha=1.2 win-corner cell. First check whether method.py in the experiment artifact's workspace already exposes the CoV thresholds as named constants/parameters (grep for '0.5' and '1.5' or 'cov_threshold' / 'volatile' / 'stable' in method.py) -- if so, the executor should re-run ONLY that one cell (ratio=0.01, alpha=1.2, all 4 drift scenarios, all 3 seeds -- NOT the full 108-cell sweep) at a 3x3 grid of threshold pairs, e.g. lower in {0.3, 0.5, 0.7} x upper in {1.2, 1.5, 1.8} ensuring lower<upper always, for 9 combinations (the original 0.5/1.5 point should be one of the 9 so it serves as an internal consistency check against the already-reported result). This is a small, bounded compute cost (1 cell x 9 threshold pairs x 4 drift scenarios x 3 seeds, vs. the original 108 cells x full grid) and should complete quickly even on cpu_light; if wall-clock risk is a concern, drop to a 2x2 grid (2 lower x 2 upper) as the direction allows, prioritizing coverage of the original point plus one looser and one tighter pair each side. For each of the 9 (or 4) threshold pairs, report recovery-time ratio (proposed/baseline) with bootstrap CI using the SAME bootstrap procedure and resample count (1000) as the original experiment, and classify each pair as 'advantage holds' (CI excludes ratio=1 in the beneficial direction, consistent with the original win), 'advantage narrows/disappears' (CI includes 1), or 'reverses' (CI excludes 1 in the harmful direction). Present as a 3x3 (or 2x2) grid/heatmap-style table plus written verdict on threshold sensitivity: is the win-corner result robust across nearby threshold choices, or is it a knife-edge artifact of the exact 0.5/1.5 pair chosen post-hoc? If method.py does NOT expose easily-tunable thresholds (e.g. they are hardcoded inline in a way that would require nontrivial refactoring), the executor must document this concretely (file/line) and fall back to an ANALYTICAL sensitivity argument: recompute each key's tier assignment for the already-logged per-key CoV values (if raw per-key CoV data was logged anywhere in the experiment artifact's intermediate outputs) under the alternate threshold pairs without re-running the full simulator, or, if no such data exists, state plainly that threshold sensitivity could not be empirically checked within the artifact's available outputs and explain precisely what additional instrumentation the experiment would have needed -- do not fabricate a sensitivity result if the underlying per-key data does not exist.

  3. PER-REQUEST COMPUTE-COST COMPARISON. Derive, from reading method.py's actual GlobalResetFrequencyEstimator and PerKeyDecayFrequencyEstimator classes (do not guess -- open and read the real per-request code path for both: the increment-on-hit path and the periodic-reset/reclassification path), an operation-count table per request: for the baseline, count array reads/writes, hash computations, and the amortized cost of the periodic global halving (total halving cost / average requests between halvings); for the proposed estimator, count the same PLUS the per-key rolling inter-arrival-gap buffer update, CoV recomputation (or its incremental/EWMA-updated form if that is what method.py implements -- read the actual formula, do not assume plain CoV requires a full pass), and tier-reclassification-check cost, again amortized appropriately if reclassification only happens periodically rather than every request. Present as a side-by-side table: {operation type: baseline count, proposed count, ratio}, plus a headline 'X times more per-request work' number with its derivation shown (not just asserted). If reasonably feasible within the CPU-light compute budget and the existing method.py is directly reusable, corroborate the analytical count with a small wall-clock microbenchmark (e.g. time 100k synthetic increment calls for each estimator class in isolation, 5 repeats, report mean +/- std) -- clearly label this as a microbenchmark result distinct from the analytical operation count, since constant factors (branch prediction, cache locality) can make the wall-clock ratio diverge from the raw op-count ratio, and report both rather than only the more favorable one.

  4. SYNTHESIS OF SHORT-RESET-ABLATION AND REAL-TRACE RESULTS. Pull the short-reset-ablation results (the best short-tuned single-global-sketch baseline, i.e. a baseline retuned with a shorter reset/sample-size schedule specifically to try to match the proposed estimator's faster adaptation) from wherever the experiment artifact recorded them (check phaseB entries for an added baseline variant, or a phaseC field/metadata.deviations_from_plan note -- if genuinely absent from the artifact despite the direction assuming it exists, state this explicitly as a gap rather than inventing numbers) and directly compare, in the SAME win-corner cells identified in step 1, whether the short-tuned baseline's recovery time closes the gap to the proposed estimator's, narrows it partially, or leaves it unchanged -- report exact recovery-time numbers (not just qualitative language) for baseline-original / baseline-short-tuned / proposed in each win-corner cell. Similarly pull the real-trace (Twitter cluster026, from art_f48a8QRaZrIB) results: steady-state hit ratio for baseline vs. proposed (parity check, report the delta and whether it's within the pre-registered 1-percentage-point margin), and, if the experiment or this evaluation is able to identify empirical changepoints in the real trace's request stream (e.g. via a simple changepoint-detection heuristic on a rolling key-popularity or request-rate signal, since the Twitter trace has NO ground-truth drift labels per the dataset artifact's own documented limitation), a recovery-time comparison around those changepoints -- this must be labeled explicitly and repeatedly as coarse/exploratory/unvalidated evidence (no ground truth exists to check changepoint detection against), never presented with the same confidence as the labeled-synthetic-drift results.

  5. RECONCILED SINGLE VERDICT. Note that the experiment artifact's own summary states memory overhead as 'roughly 3-5x' while the hypothesis's success/failure criteria reference a 5.1-5.7x figure and a 'no more than ~2x' disconfirmation bound -- resolve this inconsistency by recomputing the memory ratio directly and explicitly from phaseC's memory_footprint_table (or by deriving it fresh from method.py's actual data-structure sizes: sketch tiers, per-key shadow-metadata bytes, versus Caffeine's 8 bytes/entry), state the single correct number with its derivation, and use THAT number consistently in the final verdict rather than repeating either prior inconsistent figure. Conclude eval_out.json with an explicit, structured final verdict section answering: (a) does the win-corner result survive BH-FDR correction (from step 1)? (b) is the win-corner result robust to reasonable threshold choices (from step 2)? (c) does the win disappear once compute-cost-adjusted or once compared against a short-tuned baseline (from step 3-4)? (d) does real-trace evidence corroborate or contradict the synthetic result (from step 4)? (e) is the memory overhead (corrected figure) proportionate to any surviving benefit? Synthesize these five sub-answers into ONE overall recommendation for the paper: e.g. 'CONFIRMED_NARROW' (a specific, correctly-scoped win survives every check), 'DISCONFIRMED' (fails one or more of the pre-registered hypothesis's own disconfirmation criteria), or 'INCONCLUSIVE_UNDERPOWERED' (the 3/36 raw hits are consistent with chance under multiple testing and no independent line of evidence -- threshold robustness, short-reset ablation, or real-trace -- corroborates them) -- pick exactly one label and justify it in 3-5 sentences referencing the specific numbers computed above, since the whole point of this evaluation is to force a single non-hedged conclusion rather than let four separate analyses sit unreconciled.
metrics_justification: >-
  The parent experiment (art_gQEGVMwa8ZKC) already reports its headline finding as a fragile 3-out-of-36-groups significant
  result -- exactly the situation multiple-hypothesis-testing correction exists to guard against, since running 36 nominally-independent
  significance tests at alpha=0.05 yields an expected ~1.8 false positives by chance alone even under a true null, making
  3/36 statistically unremarkable without correction. Benjamini-Hochberg FDR control is the standard, field-appropriate answer
  to exactly this scenario (as opposed to the far more conservative Bonferroni, which would be inappropriate here given the
  groups' known non-independence via shared seeds) and directly tests whether the paper's one surviving positive claim is
  a real signal or an artifact of testing 36 cells and reporting only the interesting ones -- this is the single most important
  check for whether the paper's headline claim is honest. The threshold-sensitivity grid matters because the reviewer critique
  this artifact answers is specifically that a narrow win at one arbitrarily-chosen (CoV=0.5/1.5) threshold pair is exactly
  what a lightly-tuned, cherry-picked hyperparameter setting would produce by chance across a 36-cell sweep -- if the win
  is a genuine property of key-volatility-adaptive decay rather than a coincidence of these two specific numbers, it should
  persist (even if attenuated) across nearby threshold choices; if it evaporates at any nearby pair, that is strong evidence
  for a tuning artifact rather than a real mechanism. The compute-cost comparison operationalizes the hypothesis's own pre-registered
  memory/overhead-vs-benefit tradeoff into the CPU dimension the original plan under-specified (only memory bytes were budgeted,
  not per-request operation count), which matters because a mechanism that both costs more memory AND does meaningfully more
  work per request needs a correspondingly larger benefit to be worth deploying -- this closes that gap with a directly checkable
  number rather than leaving 'per-key decay is more complex' as an unquantified hand-wave. The short-reset-ablation and real-trace
  synthesis matter because the two most obvious alternative explanations for a narrow synthetic win are (i) the baseline simply
  wasn't tuned aggressively enough (a shorter global reset period might match the adaptive mechanism's speed without any per-key
  complexity) and (ii) the synthetic drift-injection procedure itself is favorable to a CoV-based classifier by construction
  (real drift may not look like the injected rank-reshuffle/burst events) -- directly comparing against a short-tuned baseline
  and against real Twitter-trace behavior is the most direct test available within this artifact's dependencies for each of
  those two competing explanations. Together, these four analyses convert an ambiguous, internally-inconsistent (5.1-5.7x
  vs 2x memory bound) experiment report into a single falsifiable verdict that maps directly onto the hypothesis's own pre-registered
  confirm/disconfirm criteria, which is the correct and complete scope for an EVALUATION artifact: no new methods are implemented
  and no new data is collected, only rigorous statistical and validity analysis of what the EXPERIMENT and DATASET artifacts
  already produced.
</artifact_plan>

<dependencies>
Read the files in these dependency workspaces to understand what's available, then copy any you need into your working directory.

--- Dependency 1 ---
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
out_dependency_files:
  file_list:
  - data.py
  - real_twitter_cache_trace
  - full_data_out/full_data_out_1.json
  - mini_data_out.json
  - preview_data_out.json
  - synthetic_zipf_alpha08
  - full_data_out/full_data_out_2.json
  - full_data_out/full_data_out_3.json
  - full_data_out/full_data_out_4.json
  - full_data_out/full_data_out_5.json
  - full_data_out/full_data_out_6.json
  - mini_data_out.json
  - preview_data_out.json
  - synthetic_zipf_alpha10
  - full_data_out/full_data_out_7.json
  - full_data_out/full_data_out_8.json
  - full_data_out/full_data_out_9.json
  - full_data_out/full_data_out_10.json
  - full_data_out/full_data_out_11.json
  - mini_data_out.json
  - preview_data_out.json
  - synthetic_zipf_alpha12
  - full_data_out/full_data_out_12.json
  - full_data_out/full_data_out_13.json
  - full_data_out/full_data_out_14.json
  - full_data_out/full_data_out_15.json
  - full_data_out/full_data_out_16.json
  - mini_data_out.json
  - preview_data_out.json
  data_file_paths:
  - full_data_out/full_data_out_1.json
  - mini_data_out.json
  - preview_data_out.json
  - full_data_out/full_data_out_2.json
  - full_data_out/full_data_out_3.json
  - full_data_out/full_data_out_4.json
  - full_data_out/full_data_out_5.json
  - full_data_out/full_data_out_6.json
  - mini_data_out.json
  - preview_data_out.json
  - full_data_out/full_data_out_7.json
  - full_data_out/full_data_out_8.json
  - full_data_out/full_data_out_9.json
  - full_data_out/full_data_out_10.json
  - full_data_out/full_data_out_11.json
  - mini_data_out.json
  - preview_data_out.json
  - full_data_out/full_data_out_12.json
  - full_data_out/full_data_out_13.json
  - full_data_out/full_data_out_14.json
  - full_data_out/full_data_out_15.json
  - full_data_out/full_data_out_16.json
  - mini_data_out.json
  - preview_data_out.json

--- Dependency 2 ---
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
out_dependency_files:
  file_list:
  - method.py
  - full_method_out.json
  - mini_method_out.json
  - preview_method_out.json

Data files come in three sizes:
- preview_*_out.json — READ THIS to inspect the data structure
- mini_*_out.json (~3 examples) — use for prototyping/testing
- full_*_out.json (complete) — use for the final production run. NEVER open it directly (too large to read into context). Instead, extract values programmatically with shell commands (e.g. grep) or a Python script (use aii-long-running-tasks skill for scripts).
</dependencies>

<available_resources>
<software_constraints>
- Python only implementation
- Python standard library and all popular PyPI packages available (numpy, pandas, scikit-learn, scipy, matplotlib, requests, etc.)
- Local parallelism encouraged: multiprocessing, asyncio, threading — see aii-parallel-computing skill
- LLM API calls must go through OpenRouter only (no direct OpenAI, Anthropic, etc.)
- **SPEND BUDGET**: at most $10 USD of OpenRouter API calls for this artifact. Nothing outside your own code enforces this — the key you are given has no per-artifact cap — so it holds only if you track cumulative cost after every call and stop when you approach it. Budget the work up front: estimate the per-call cost and the number of calls BEFORE starting a sweep, not after it overruns. Exceeding it spends real money that the run cannot recover.
</software_constraints>

<skills>
Skills are self-contained capabilities with instructions, context, and tools.

- aii-web-tools: Free-first web search (general + scholarly modes), page/PDF fetch as markdown, regex grep over page/PDF text
- aii-semscholar-bib: Batch-fetch BibTeX from Semantic Scholar
- aii-openrouter-llms: Search and call 300+ LLMs via OpenRouter
- aii-hf-datasets: Search, preview, download HuggingFace datasets
- aii-owid-datasets: Search and load Our World in Data tables
- aii-lean: Compile/verify Lean 4 code, Mathlib search, tactic suggestions
- aii-concept-fig-gen: Generate/edit images via Gemini 3 Pro Image (Nano Banana Pro)
- aii-json: Validate JSON against schemas, generate mini/preview variants
- aii-paper-writing: Academic paper structure, bibliography, citations
- aii-paper-to-latex: Assemble LaTeX papers and compile to PDF
- aii-parallel-computing: GPU acceleration, CPU parallelism, async I/O
- aii-python: Python coding standards for experiment scripts
- aii-use-hardware: Detect CPU/RAM/GPU, memory-safe processing
- aii-long-running-tasks: Gradual scaling pattern for long-running tasks
- aii-colab: Google Colab runtime constraints for notebooks
- aii-file-size-limit: Check and split oversized output files
</skills>
</available_resources>

<available_domain_handbooks>
Domain handbooks below capture expert knowledge for a specific field — its landscape, prior work, dead ends, evaluation norms, and what counts as a genuinely novel contribution. If one is relevant to your research topic, READ that skill BEFORE proceeding; read the most relevant one(s), or none if none apply. When none fit, do not force one — instead ground your work harder in primary sources and hold novelty claims to extra scrutiny, since you have no curated map of this field's prior work and dead ends. Use it for evaluation metrics, agent orchestration patterns, benchmark design.

- **aii-handbook-auto-computational-linguistics** — Field handbook for computational linguistics as a SCIENCE of language — grammaticality and minimal pairs (BLiMP), surprisal versus reading times, linguistic structure in LMs, annotator disagreement an
- **aii-handbook-auto-mechanistic-interpretability** — Field handbook for mechanistic interpretability of neural networks — circuit discovery, activation and attribution patching, sparse autoencoders, transcoders, attribution graphs, steering vectors, pro
- **aii-handbook-auto-multi-agent-llm-systems** — Field handbook for multi-agent LLM systems (MAS) — orchestration topology, multi-agent debate, mixture-of-agents, verifier and critic agents, inter-agent protocols (MCP/A2A), failure attribution and s
- **aii-handbook-auto-neurosymbolic** — Field handbook for neuro-symbolic AI — text-to-logic autoformalization (NL to FOL), LLM-plus-solver and prover pipelines (Prolog, ASP, SMT), probabilistic-differentiable NeSy (DeepProbLog, Scallop), r
</available_domain_handbooks>

<tool_use>
Maximize parallel tool calls. Parallelize independent operations, only sequentialize dependencies.
- Multiple searches/fetches on different topics → parallel in one turn
- Search then fetch results → sequential (need URLs first)
</tool_use>

<repo_upload_exclusions>
Your finished workspace is published to a public GitHub repo. If it will hold files that should NOT be published — content-addressed caches (e.g. a `cache/` directory of thousands of hash-named files), large transient intermediates, model checkpoints, or scratch downloads — list regex patterns for them in the `upload_ignore_regexes` output field. Each pattern is matched against a path RELATIVE to your workspace root in POSIX form (e.g. `(^|/)cache/`, `(^|/)checkpoints/`). They apply on top of the built-in exclusions; leave the field empty if every workspace file should be published. Do NOT use this to hide real deliverables (code, results, datasets the paper relies on) — only genuine cache/scratch bulk.
</repo_upload_exclusions>

IMPORTANT: Your final response should be at most 300 characters long.

FIRST, add ALL of these to your todo list using your task/todo-tracking tool:

CRITICAL: Todo content must be copied exactly as is written here, with NO CHANGES. These todos are intentionally detailed so that another LLM could read each one without any external context and understand exactly what it has to do.

<todos>
TODO 1. Use aii-json skill's format script with `--input eval_out.json` to generate full, mini, and preview versions. If not in your workspace (see <workspace> above), copy them there. Run 'ls -lh' to verify these three files exist (DO NOT read them).
TODO 2. Apply aii-file-size-limit skill's file size check procedure (100MB limit) to eval_out.json and full_eval_out.json.
TODO 3. Ensure a `pyproject.toml` exists in your workspace with ALL dependencies pinned to the exact versions installed in your .venv (run `.venv/bin/pip freeze` to get them). This is required for reproducibility. The [project] section must include name, version, requires-python, and a dependencies list with pinned versions (e.g. `numpy==2.0.2`, not `numpy>=2.0`).
</todos>

---

Output the result as JSON to: `./.terminal_claude_agent_struct_out.json`

JSON Schema:
```json
{
  "$defs": {
    "EvaluationExpectedFiles": {
      "description": "All expected output files from evaluation artifact.",
      "properties": {
        "script": {
          "description": "Path to eval.py script. Example: 'eval.py'",
          "title": "Script",
          "type": "string"
        },
        "full_output": {
          "description": "Full evaluation JSON file. Example: 'full_eval_out.json'",
          "title": "Full Output",
          "type": "string"
        },
        "mini_output": {
          "description": "Mini evaluation JSON file. Example: 'mini_eval_out.json'",
          "title": "Mini Output",
          "type": "string"
        },
        "preview_output": {
          "description": "Preview evaluation JSON file. Example: 'preview_eval_out.json'",
          "title": "Preview Output",
          "type": "string"
        }
      },
      "required": [
        "script",
        "full_output",
        "mini_output",
        "preview_output"
      ],
      "title": "EvaluationExpectedFiles",
      "type": "object"
    }
  },
  "description": "Evaluation artifact \u2014 structured output + file metadata.\n\nEvaluates both proposed and baseline methods with appropriate metrics.\nProduces eval.py and eval_out.json files.",
  "properties": {
    "title": {
      "default": "",
      "description": "Artifact title in plain, everyday language \u2014 short and jargon-free so a non-expert grasps it at a glance and it fits the run visualizations. Aim for about 4-8 words (~40 characters); describe the content, not a status.",
      "maxLength": 90,
      "minLength": 12,
      "title": "Title",
      "type": "string"
    },
    "layman_summary": {
      "default": "",
      "description": "One-sentence plain-language summary of what this artifact does, accessible to non-experts. Used only in the per-artifact README, not in downstream prompts.",
      "maxLength": 250,
      "minLength": 80,
      "title": "Layman Summary",
      "type": "string"
    },
    "summary": {
      "default": "",
      "description": "Summary for downstream artifacts: what this artifact provides",
      "maxLength": 5000,
      "minLength": 500,
      "title": "Summary",
      "type": "string"
    },
    "out_expected_files": {
      "$ref": "#/$defs/EvaluationExpectedFiles",
      "description": "All output files you created. Must include eval.py script plus full/mini/preview evaluation JSON files."
    },
    "upload_ignore_regexes": {
      "description": "Regex patterns for workspace paths that must NOT be published to the GitHub repo, matched against each file's path relative to this artifact's workspace root (POSIX form, e.g. 'cache/abc.json'). Applied ON TOP OF the deploy step's built-in exclusions. Use this for executor-specific caches, large transient intermediates, or content-addressed blob stores (e.g. a cache/ dir of thousands of hash-named files) that would bloat the repo. Examples: ['(^|/)cache/', '(^|/)\\\\.weight_cache/', '(^|/)checkpoints/']. Leave empty if every workspace file should be published.",
      "items": {
        "type": "string"
      },
      "title": "Upload Ignore Regexes",
      "type": "array"
    }
  },
  "required": [
    "out_expected_files"
  ],
  "title": "EvaluationArtifact",
  "type": "object"
}
```

IMPORTANT: this task is NOT complete until `./.terminal_claude_agent_struct_out.json` exists and contains JSON matching the schema above.
````
