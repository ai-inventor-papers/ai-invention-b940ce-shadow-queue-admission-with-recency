# gen_full_paper — report_results

> Phase: `gen_paper_repo` · `gen_full_paper`
> Run: `iter1_eb86f00c4c5a` — Why Per-Key Cache Decay Rarely Beats a Cheaper Shorter Reset
>
> Full, verbatim record of every prompt the AI Inventor pipeline gave this agent — system-user, human-user and skill-input — in the order they landed. Nothing truncated.

## Task: `gen_full_paper` (terminal_claude_agent)

### [1] SYSTEM-USER prompt · 2026-08-26 22:30:08 UTC

````
<system-prompt>
<research_methodology>
Write like an experienced academic. Reviewers judge both the science and the writing.

- Claims must be proportional to evidence. Choose verbs carefully — "demonstrate," "observe," and "hypothesize" mean different things.
- Every result needs: what was measured, on what data, the numbers, and what they mean.
- Methodology must be specific enough to reproduce. Related work must be organized by theme, not a literature dump.
- State limitations honestly. Avoid both overclaiming and excessive hedging.
</research_methodology>

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
</system-prompt>

<prompt>
<workspace>
Your workspace: `/ai-inventor/aii_data/runs/run_0pMem8W3ijCf/4_gen_paper_repo/_4_assemble_paper/paper/workspace`

CRITICAL: Every file you create, write, or save MUST be inside this workspace directory (subdirectories OK). You MUST NOT write files anywhere outside this path — external paths are READ-ONLY. Use absolute paths for all file operations.

EVERY file write MUST start with `/ai-inventor/aii_data/runs/run_0pMem8W3ijCf/4_gen_paper_repo/_4_assemble_paper/paper/workspace/`:
GOOD: `/ai-inventor/aii_data/runs/run_0pMem8W3ijCf/4_gen_paper_repo/_4_assemble_paper/paper/workspace/file.py`, `/ai-inventor/aii_data/runs/run_0pMem8W3ijCf/4_gen_paper_repo/_4_assemble_paper/paper/workspace/results/out.json`
BAD: `/tmp/file.py`, `~/output.json`, `./file.py`, any path outside the workspace
</workspace>

<task>
Create a publication-ready top-conference LaTeX paper with BibTeX from <paper_text> and <available_figures>, compile to PDF.
</task>

<tool_use>
Maximize parallel tool calls. Parallelize independent operations, only sequentialize dependencies.
- Multiple searches/fetches on different topics → parallel in one turn
- Search then fetch results → sequential (need URLs first)
</tool_use>

<paper_text>
title: Why Per-Key Cache Decay Rarely Beats a Cheaper Shorter Reset
abstract: >-
  TinyLFU-style cache admission ages its frequency sketch with a single global reset period, so every key is forgotten at
  the same rate regardless of whether it is a stable heavy hitter or a short-lived spike. We test whether inferring each key's
  own forgetting rate from the coefficient of variation (CoV) of its inter-arrival gaps -- signal already visible in the admission
  shadow queue -- improves post-drift recovery over a well-tuned single reset. Across 36 (cache ratio, skew, drift-scenario)
  conditions, per-key decay shows a statistically significant 22-27% recovery-time improvement in exactly one corner: the
  smallest cache-to-key-space ratio combined with the sharpest skew, and this holds after Benjamini-Hochberg false-discovery
  correction. Three targeted follow-up analyses, however, undercut the mechanism's necessity in that corner. First, a much
  cheaper alternative -- simply shortening the baseline's own global reset period -- matches or beats per-key decay in three
  of the four win-corner drift scenarios, closing 6-16 percentage points of the gap the more elaborate mechanism was credited
  with. Second, the advantage is sensitive to the two coefficient-of-variation thresholds that route keys into tiers: across
  a 3x3 sensitivity grid it survives in only 12 of 36 threshold-scenario combinations. Third, replaying both estimators on
  80,000 real Twitter production cache requests shows steady-state parity (within 1 percentage point, as pre-registered) but
  gives no independent evidence of faster recovery, because the trace carries no ground-truth drift labels. Set against this
  narrow and fragile benefit, per-key decay costs 5.14-5.68x the memory of the single-sketch baseline (mean 5.22x) and roughly
  1.7-2.1x its per-request compute. We conclude that the mechanism does not clear its own pre-registered bar: in the one regime
  where it appeared to win, a five-line change to the existing reset schedule captures most of the same benefit at a fraction
  of the cost.
paper_text: |-
  # Introduction

  A key-value cache decides two separate things when a request misses: what to evict, and whether the missing key is even worth admitting in the first place. The second decision, the *admission policy*, matters most when the working set is larger than the cache and popularity is skewed, because most misses are for keys that will never be requested again, and inserting them only evicts something that would have been reused. TinyLFU [1] is the dominant answer to this problem: it keeps a compact frequency sketch of recent traffic and admits a miss only if its estimated frequency exceeds that of the item it would evict, tested cheaply in a shadow queue before any real cache state changes. Through the Caffeine library, this exact design sits underneath widely deployed JVM caches.

  Admission policies matter at the scale where read-heavy key-value stores actually run: CDN edge caches, in-memory object caches such as Memcached and Redis, and block caches inside LSM-tree stores all serve populations of keys whose popularity follows a Zipf-like law, and all of them run continuously against traffic whose composition drifts -- a previously cold key goes viral, a previously hot key falls out of use. An admission policy that adapts slowly to this drift keeps evicting the room it needs for a newly popular key in favor of one that is no longer popular, which shows up directly as a lower hit ratio during exactly the traffic surges an operator cares most about.

  The difficulty is that TinyLFU's own accuracy trades off two things a fixed schedule cannot have simultaneously. Its Count-Min sketch is aged by a global *reset operation*: once a shared counter reaches a sample-size threshold, every counter in the sketch is halved in one pass, with no distinction between keys. A long reset period lets a genuinely popular key accumulate enough count to be reliably admitted, but the same length means a newly trending key takes just as long to be recognized. A short reset period fixes the second problem and reopens the first. Because the schedule is a single number shared by the whole sketch, there is no obvious way to give long memory to the keys that deserve it and short memory to the keys that do not, without deciding in advance which keys are which -- and the original TinyLFU paper's own related-work discussion calls exactly this tuning problem "tricky" [1].

  The shadow queue that TinyLFU already maintains sees each candidate key's arrival timestamps for free, and the gaps between those arrivals are a cheap, per-key signal for whether a key's recent traffic looks steady or bursty. A natural next step, and the one this paper tests, is to classify each tracked key by the coefficient of variation of its inter-arrival gaps and route its frequency count into one of several independently-aged sketch tiers, so a stable heavy hitter keeps a long half-life and a volatile key gets a short one -- without an oracle that pre-labels which keys are which. A previous iteration of this study built exactly this mechanism, found a real, confidence-interval-significant win in a narrow high-contention corner of a 36-condition sweep, and stopped there. This paper asks the harder question a single positive result invites: is that win real, or is it what 36 correlated significance tests and an under-tuned baseline produce by construction? We run three targeted follow-ups -- a false-discovery correction, a cheaper-baseline ablation, and a real-trace replay -- and the answer each gives is more skeptical than the original result suggested. [FIGURE:fig_architecture]

  ## Summary of Contributions

  - A false-discovery-corrected re-analysis of the original 36-condition sweep showing the reported win-corner effect survives Benjamini-Hochberg correction (3 of 3 groups significant at q<0.05), which rules out multiple-testing alone as the explanation and forces the question onto mechanism, not statistics (Section 4).
  - A short-reset ablation that extends the baseline's own tunable reset schedule down to 1x and 2x cache capacity in the win corner and shows it matches or beats the per-key mechanism in three of the four drift scenarios tested there, cutting the case for per-key machinery to a single scenario \footnote{Code: \url{https://github.com/ai-inventor-outputs/ai-invention-b940ce-shadow-queue-admission-with-recency/tree/main/round-2/experiment-1}} (Section 4).
  - A coefficient-of-variation threshold-sensitivity grid showing the win-corner advantage holds in only 12 of 36 threshold-scenario combinations, establishing that the original 0.5/1.5 threshold pair was not a robust operating point but close to a favorable draw \footnote{Code: \url{https://github.com/ai-inventor-outputs/ai-invention-b940ce-shadow-queue-admission-with-recency/tree/main/round-2/evaluation-1}} (Section 4).
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

  We implement a discrete-event cache-admission simulator \footnote{Code: \url{https://github.com/ai-inventor-outputs/ai-invention-b940ce-shadow-queue-admission-with-recency/tree/main/round-1/experiment-1}} that processes one key request at a time through an identical pipeline for both estimators under comparison, so that any difference in hit ratio or recovery speed is attributable only to the frequency estimator. The pipeline, shown in Figure 1, is: a doorkeeper (a Bloom filter sized at 8 bits per cache slot) suppresses a first-ever sighting of a key from immediately entering the frequency sketch, with a doorkeeper hit contributing exactly +1 to a key's estimated frequency, matching Caffeine's actual semantics; a shadow-queue admission test compares the candidate key's estimated frequency against the frequency of the current probationary-segment eviction victim, admitting the candidate only if its count is strictly higher; and a segmented LRU (SLRU) main region with a small preceding admission window implements eviction, with the window's own evicted candidate competing against the SLRU's probationary victim in the same comparison rather than being counted as an unconditional hit.

  **Baseline estimator: global reset.** The baseline is a single Count-Min sketch whose reset schedule reproduces Caffeine's `FrequencySketch.reset()` exactly: a shared access counter increments on every non-doorkeeper-suppressed key, and once it reaches a sample-size threshold -- a tunable multiple of cache capacity -- every 4-bit counter in the sketch's backing array is halved in a single pass. The multiplier is tuned per (cache ratio, skew) cell on a held-out stationary trace prefix before the main sweep runs, so the baseline is never handicapped by an untuned reset period.

  **Proposed estimator: per-key decay.** The proposed estimator maintains three parallel Count-Min sketches -- volatile, default, and stable -- with independent halving periods set to 2x, 8x, and 32x cache capacity respectively. A bounded shadow-metadata LRU tracks, for each currently-tracked key, an exponentially-weighted moving estimate of its inter-arrival gap and squared gap; once a key has accumulated enough observations its CoV is computed from these two moments and it is assigned to the volatile tier if CoV exceeds 1.5, the stable tier if CoV is below 0.5, and the default tier otherwise. A key with too few observations, or one that has aged out and re-enters, defaults to the middle tier until it accumulates enough history to be reclassified. This gives every currently-tracked key an individually inferred forgetting rate using only signal (arrival timestamps) the shadow queue already touches.

  **Two follow-up analyses, both introduced to close specific gaps left by the mechanism's initial evaluation, are the empirical core of this paper.** First, a short-reset ablation asks whether the baseline's own reset schedule -- extended down to multipliers of 1x and 2x cache capacity, well below the {4, 8, 16, 32} range originally swept -- can close the win-corner gap without any per-key machinery . This directly targets the volatile tier's 2x period: if a single sketch reset every 2x cache-capacity accesses does nearly as well as a volatile tier that only ever applies that period to keys already classified as volatile, the extra classification machinery is buying little. Second, a real-trace replay runs both estimators unchanged over Twitter's production Twemcache trace (cluster026), which has no injected or labeled drift, to check whether the steady-state parity observed on synthetic traces generalizes to real access patterns, and to attempt an exploratory, unsupervised recovery-time comparison around candidate changepoints identified by a rolling Jensen-Shannon-divergence detector over the top-50 key-identity distribution (window 2,000 requests, stride 500). The detector was first validated against the known drift events in the synthetic traces (recall 1.0, precision 0.67) before being applied to the unlabeled real trace, where any recovery-time reading is reported as coarse and exploratory rather than confirmatory, since no ground truth exists to check the detector's real-trace precision against.

  # Experiments

  **Data.** We generate synthetic traces \footnote{Code: \url{https://github.com/ai-inventor-outputs/ai-invention-b940ce-shadow-queue-admission-with-recency/tree/main/round-1/dataset-1}} of 850,000 requests each over a 20,000-key universe, following a Zipf rank-frequency law at three skew levels (alpha in {0.8, 1.0, 1.2}), with two independent kinds of injected, ground-truth-labeled drift: periodic rank-reshuffle events (permuting 5-20% of key ranks) and randomly timed popularity bursts on eight initially-cold keys per trace. The main experiment grid crosses this skew sweep with four drift scenarios that vary rank-churn magnitude and frequency independently (low/high magnitude x low/high frequency), over a 150,000-key space and 600,000 requests per condition after an 80,000-request tuning prefix, giving 36 (ratio, skew, drift-scenario) groups of 3 seeds each. The real-trace arm replays 80,000 requests from Twitter's Twemcache cluster026 trace (67,681 distinct keys, 61,874 GETs and 18,126 SETs), which unlike the synthetic traces carries no labeled drift.

  **Metrics.** For every run we record (i) steady-state hit ratio, the mean rolling hit ratio over the trailing 15% of the trace; (ii) per-drift-event recovery time, the first point after a drift event at which a 3,000-request rolling hit ratio climbs back to 90% of the way from its post-drift trough to its pre-drift plateau, censored at 60,000 requests if never reached; and (iii) total memory footprint in bytes for each estimator's complete state. Within each of the 36 groups we bootstrap (1,000 resamples over 3 seeds) confidence intervals on the recovery-time ratio and call a group a win when that ratio's confidence interval lies entirely below 0.8 (a pre-registered 20%-faster-recovery threshold). We additionally compute a two-sided percentile-bootstrap p-value per group and apply Benjamini-Hochberg (BH) and Benjamini-Yekutieli (BY, valid under arbitrary dependence) correction across all 36 .

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
summary: >-
  This paper stress-tests a prior finding that per-key, coefficient-of-variation-based frequency decay improves TinyLFU-style
  cache-admission drift recovery in a narrow high-contention regime. The win-corner effect survives Benjamini-Hochberg correction
  for multiple testing, but two new targeted experiments substantially undercut it: a cheaper short-reset baseline matches
  or beats the per-key mechanism in 3 of the 4 win-corner drift scenarios, and the remaining advantage holds in only 12 of
  36 nearby CoV-threshold choices. A real Twitter-trace replay confirms steady-state parity but, lacking labeled drift events,
  cannot independently confirm the recovery-time claim. Weighed against a corrected 5.14-5.68x memory cost and ~1.7-2.1x compute
  cost, the paper concludes per-key decay is not established as worth its overhead anywhere tested, and that shortening the
  existing global reset period captures most of the same benefit far more cheaply.
</paper_text>

<available_figures>
--- Item 1 ---
id: fig_architecture
figure_type: concept
title: Cache Admission Simulator Pipeline
caption: >-
  The shared W-TinyLFU simulator pipeline used for both estimators: a doorkeeper pre-filter, a shadow-queue admission test
  comparing candidate versus victim frequency, and a segmented LRU main region with an admission window. The baseline uses
  one global-reset Count-Min sketch; the proposed estimator replaces it with three CoV-routed sketch tiers (volatile / default
  / stable) fed by a shadow-metadata LRU that tracks each key's inter-arrival-gap statistics.
image_gen_detailed_description: >-
  Horizontal flow diagram, left to right, clean white background, sans-serif labels, no 3D effects, 21:9 aspect ratio. Stage
  1: box labeled 'Incoming Request (key)'. Arrow to Stage 2: box labeled 'Doorkeeper (Bloom filter, 8 bits/slot)' 
  [1.5]=3, [1.8]=1. Row 0.7: [1.2]=0, [1.5]=1, [1.8]=1. Use a sequential color scale from light (0) to dark blue (3), with
  the numeric count printed in the center of each cell in white or black for contrast. Add a small star or outline marker
  on the (0.5, 1.5) cell with the label 'original threshold pair used in Sections 3-4'. Axis titles: x-axis 'Upper CoV threshold
  (volatile boundary)', y-axis 'Lower CoV threshold (stable boundary)'. Title above the heatmap: 'Scenarios (of 4) where advantage
  holds, by CoV threshold pair'.
aspect_ratio: '1:1'
summary: >-
  Shows the per-key decay win-corner advantage depends on the specific CoV thresholds chosen, holding in only 12 of 36 threshold-scenario
  combinations.
figure_path: figures/fig_threshold_v0.pdf

--- Item 4 ---
id: fig_memory
figure_type: data
title: Memory and Compute Overhead
caption: >-
  Left: memory-footprint overhead of the per-key-decay estimator relative to the global-reset baseline, at three cache-to-key-space
  ratios (Zipf alpha=1.0). Right: per-request compute cost, both an analytical elementary-operation count and a wall-clock
  microbenchmark over 100,000 calls. Both cost measures exceed the hypothesis's own pre-registered disconfirmation bound of
  roughly 2x memory.
image_gen_detailed_description: >-
  Two-panel figure, 16:9 aspect ratio, side by side. Left panel: grouped bar chart, x-axis 'Cache-to-key-space ratio' with
  three categories '0.01', '0.05', '0.10', y-axis 'Memory overhead (proposed / baseline)', range 0 to 6, single bar series
  'Memory overhead ratio' with values 5.137, 5.169, 5.271, with a horizontal dashed reference line at y=2.0 labeled 'pre-registered
  disconfirmation bound (~2x)' and at y=1.0 labeled 'parity'. Annotate the overall measured range across all 9 (ratio, skew)
  cells as a text box: 'full range across 9 cells: 5.14x - 5.68x, mean 5.22x'. Right panel: grouped bar chart, x-axis with
  two categories 'Analytical op count' and 'Wall-clock (100k calls)', y-axis left 'Baseline (elementary ops or seconds)' and
  paired bars per category: for 'Analytical op count' baseline=25 ops, proposed=43 ops (ratio 1.72x); for 'Wall-clock (100k
  calls)' baseline=0.178 seconds, proposed=0.380 seconds (ratio 2.13x). Use two distinct colors for 'Baseline' and 'Proposed
  per-key decay' series consistent across both panels, with a shared legend. Add ratio labels above each pair: '1.72x' and
  '2.13x'.
aspect_ratio: '16:9'
summary: >-
  Quantifies the corrected 5.14x-5.68x memory overhead and the 1.72x-2.13x compute overhead of per-key decay versus the global-reset
  baseline.
figure_path: figures/fig_memory_v0.pdf

--- Item 5 ---
id: fig_realtrace
figure_type: data
title: Real Twitter Trace Replay
caption: >-
  Steady-state and final hit ratio for both estimators replayed on 80,000 requests of Twitter's production Twemcache cluster026
  trace (67,681 distinct keys, cache capacity 677 slots, ratio 0.01). Both estimators show low hit ratios typical of a short,
  high-cardinality trace, and the steady-state difference (-0.42 percentage points) falls well within the pre-registered 1-percentage-point
  parity margin -- but the trace carries no labeled drift events, so it cannot independently confirm or refute the recovery-time
  claim.
image_gen_detailed_description: >-
  Grouped bar chart, 16:9 aspect ratio. X-axis: two categories 'Steady-state hit ratio' and 'Final hit ratio'. Y-axis label
  'Hit ratio', range 0 to 0.06. Two bar series: 'Baseline (global-reset)' and 'Proposed (per-key decay)'. Values: Steady-state
  hit ratio: baseline=0.0463, proposed=0.0421. Final hit ratio: baseline=0.0337, proposed=0.0285. Add a horizontal bracket
  annotation between the two 'Steady-state hit ratio' bars labeled '-0.42 percentage points (within +/-1pp pre-registered
  parity margin)'. Small text footnote below chart: 'Twitter Twemcache cluster026, 80,000 requests, 67,681 distinct keys,
  cache capacity 677 slots (ratio 0.01)'. Colorblind-safe two-color palette matching other figures in the paper.
aspect_ratio: '16:9'
summary: >-
  Shows steady-state hit-ratio parity between the two estimators on real Twitter production traffic, within the pre-registered
  margin.
figure_path: figures/fig_realtrace_v0.pdf
</available_figures>

<figure_requirements>
CRITICAL: Include ALL figures from <available_figures>. No exceptions.

- Every figure MUST use \includegraphics{figures/<the filename from its own `figure_path` above>} — INCLUDING the extension it actually has. Data figures are delivered as `.pdf` (vector, so their axis labels stay sharp) and concept figures as `.jpg`. Writing `.jpg` for a `.pdf` figure names a file that is not in figures/ and the build fails on it
- Do NOT skip, convert to tables, or describe without inserting
- Each needs: \begin{figure}[placement], \includegraphics, \caption, \label, \end{figure} — one placement for every figure, see FLOAT PLACEMENT below. Constrain every \includegraphics with `width=\linewidth,height=0.85\textheight,keepaspectratio`. The height is a LAST RESORT, not the usual limit: it exists so a very tall figure cannot overrun the page, and at 0.4 it bound almost everything instead — a 1:1 confusion matrix printed at 50.9% and its 11 pt axis labels reached the page at 5.6 pt, below what any venue accepts. At 0.85 every ratio the paper prompt prescribes (21:9, 16:9, 4:3, 1:1) is limited by WIDTH, prints at 93% and keeps its text above 10 pt. Use exactly these option keys — `max height=` is NOT valid LaTeX
- Use the `caption` field from each figure for \caption{...} — do NOT invent new captions
- Place figures where their [FIGURE:fig_id] markers appear in paper_text
- VERIFICATION: paper.tex MUST have exact same number of \includegraphics as <available_figures>
- Do NOT generate new figure images (no matplotlib, no PIL, no image generation). Use ONLY the pre-generated figures from <available_figures>. They were already created by a previous pipeline step.

FLOAT PLACEMENT: every figure gets \begin{figure}[!htbp]. Measured, not chosen:
the document the aii-paper-to-latex skill sets up is ONE column, so `figure*` is
exactly as wide as `figure` (469.76pt either way) and gains nothing; and any
placement asking for a page TOP — `[!t]`, `[!tbp]` — floated the hero diagram above
the paper's own title on page 1, while `[!htbp]` did not. `[!htbp]` also gives LaTeX
four options, so a float can never be deferred to the end of the document, which one
option alone risks. Where the hero ENDS UP is decided by its [FIGURE:] marker in
paper_text, which is already placed near the end of the Introduction — preserve it.
</figure_requirements>

<artifact_links>
The paper_text contains \footnote{Code: \url{...}} references linking to artifact source code
on GitHub. Include \usepackage{hyperref} and \usepackage{url}.
Preserve these exactly as-is — do not remove, rewrite, or convert them to plain text.
The URLs will not resolve yet (the repo is deployed after compilation) — do NOT try to verify or fix them.
</artifact_links>

<headings>
NEVER use inline math (``$...$``) inside ``\section{...}`` / ``\subsection{...}`` / ``\subsubsection{...}`` arguments — hyperref's bookmark builder errors out (``Token not allowed in a PDF string``) and the PDF outline breaks. If a section heading needs a math-looking term, use the text equivalent (``d star`` not ``$d^*$``, ``alpha-equivalent`` not ``$\alpha$-equivalent``) or wrap it in ``\texorpdfstring{$math$}{plain}``. Inline math inside body paragraphs is fine.
</headings>

FIRST, add ALL of these to your todo list using your task/todo-tracking tool:

CRITICAL: Todo content must be copied exactly as is written here, with NO CHANGES. These todos are intentionally detailed so that another LLM could read each one without any external context and understand exactly what it has to do.

<todos>
TODO 1. Read and STRICTLY follow these skills: aii-paper-to-latex, aii-semscholar-bib.
TODO 2. Review <paper_text> and <available_figures>. Copy all figure images into ./figures/ in your workspace. Count figures — MUST include every one. Plan placements per section. Build `./references.bib` via aii_semscholar_bib__fetch — collect DOIs/ArXiv IDs from <paper_text> and batch-fetch all BibTeX in one call. Do NOT fabricate entries.
TODO 3. Create `./paper.tex` per aii-paper-to-latex skill's setup, write ALL sections, insert ALL figures from <available_figures>, include `./references.bib` via \bibliography. Compile to PDF per skill's process. Fix errors.
TODO 4. CRITICAL VERIFICATION: Run `grep -c 'includegraphics' paper.tex`, confirm count equals figures in <available_figures>. If not, add missing figures. Verify `./paper.pdf` was created.
TODO 5. VISUAL REVIEW: Write Python script to convert EVERY page of paper.pdf to PNG at 150 DPI (use pdf2image or pymupdf). Then read ALL page screenshots — each page image costs ~1,600 tokens so a 15-page paper is only ~24K tokens. You MUST read every page. The ONLY exception is if all page images would not fit in your remaining context — in that case, read as many as fit and state which pages you are skipping and why. Check every page for layout issues, overlapping figures, cut-off text, bad spacing, formatting problems. Fix issues and recompile.
TODO 6. FINAL READ: Check page count (`pdfinfo paper.pdf` or pymupdf). Read entire paper.pdf — check for missing sections, unclear explanations, inconsistencies, typos. Fix and recompile. The ONLY exception is if all pages would not fit in your remaining context — in that case, read as many pages as fit and state which pages you are skipping and why.
</todos>

---

Output the result as JSON to: `./.terminal_claude_agent_struct_out.json`

JSON Schema:
```json
{
  "$defs": {
    "FullPaperExpectedFiles": {
      "description": "All expected output files from full paper generation.",
      "properties": {
        "paper_tex_path": {
          "description": "Path to LaTeX source file. Example: 'paper.tex'",
          "title": "Paper Tex Path",
          "type": "string"
        },
        "paper_pdf_path": {
          "description": "Path to compiled PDF. Example: 'paper.pdf'",
          "title": "Paper Pdf Path",
          "type": "string"
        },
        "references_bib_path": {
          "description": "Path to BibTeX bibliography file. Example: 'references.bib'",
          "title": "References Bib Path",
          "type": "string"
        },
        "figure_paths": {
          "description": "Paths to all figure image files. Example: ['figures/fig1_v0.jpg', 'figures/fig2_v0.jpg']",
          "items": {
            "type": "string"
          },
          "title": "Figure Paths",
          "type": "array"
        }
      },
      "required": [
        "paper_tex_path",
        "paper_pdf_path",
        "references_bib_path",
        "figure_paths"
      ],
      "title": "FullPaperExpectedFiles",
      "type": "object"
    }
  },
  "description": "Full paper \u2014 structured output from paper generation.",
  "properties": {
    "title": {
      "description": "Paper title in plain, everyday language \u2014 short and jargon-free so a non-expert grasps it at a glance. Aim for about 4-8 words (~40 characters).",
      "maxLength": 90,
      "minLength": 12,
      "title": "Title",
      "type": "string"
    },
    "summary": {
      "description": "Brief summary of the generated paper: sections written, figures included, compilation status",
      "maxLength": 5000,
      "minLength": 500,
      "title": "Summary",
      "type": "string"
    },
    "out_expected_files": {
      "$ref": "#/$defs/FullPaperExpectedFiles",
      "description": "All output files you created. Must include paper.tex, paper.pdf, references.bib, and paths to all figure files."
    }
  },
  "required": [
    "title",
    "summary",
    "out_expected_files"
  ],
  "title": "FullPaper",
  "type": "object"
}
```

IMPORTANT: this task is NOT complete until `./.terminal_claude_agent_struct_out.json` exists and contains JSON matching the schema above.

Cache admission policies for skewed key popularity in read-heavy key-value stores
</prompt>in light
  gray, with a small side annotation '+1 on repeat sighting'. Arrow forks into two parallel labeled paths both feeding into
  a box labeled 'Frequency Estimator' in blue: Path A (top, labeled 'Baseline: Global-Reset Estimator') shows one rectangle
  'Count-Min Sketch (4-bit, depth-4)' with a small clock icon and label 'reset: halve ALL counters every W accesses (single
  shared schedule)'. Path B (bottom, labeled 'Proposed: Per-Key Decay Estimator') shows three small parallel rectangles side
  by side labeled 'Volatile tier (halve every 2x cache capacity)', 'Default tier (halve every 8x)', 'Stable tier (halve every
  32x)', all three feeding from a smaller box above them labeled 'Shadow-Metadata LRU: EWMA of inter-arrival gap + gap^2 ->
  Coefficient of Variation -> tier assignment (CoV<0.5 stable, CoV>1.5 volatile, else default)'. Both paths converge into
  a green box 'Shadow-Queue Admission Test: candidate frequency > victim frequency?'. Arrow from there to a final orange box
  'SLRU Main Region + Admission Window (eviction)'. Below the whole diagram, small text banner: 'Identical pipeline for both
  estimators -- only the Frequency Estimator stage differs'.
aspect_ratio: '21:9'
summary: >-
  Shows the shared simulator pipeline and where the global-reset baseline and per-key decay estimator differ.
figure_path: figures/fig_architecture_v0.jpg

--- Item 2 ---
id: fig_ablation
figure_type: data
title: Short Reset vs Per-Key Decay
caption: >-
  Mean recovery time (requests to reach 90% of pre-drift hit ratio) at the win-corner cell (cache ratio 0.01, Zipf alpha 1.2),
  comparing the proposed per-key-decay estimator against the best short-reset global baseline (multiplier swept down to 1x-4x
  cache capacity) for each of the four drift scenarios. The cheaper short-reset baseline matches or beats per-key decay in
  3 of 4 scenarios.
image_gen_detailed_description: >-
  Grouped bar chart, 16:9 aspect ratio. X-axis: four drift-scenario categories, in this order: 'Low-mag / Low-freq', 'Low-mag
  / High-freq', 'High-mag / Low-freq', 'High-mag / High-freq'. Y-axis label: 'Mean recovery time (requests to reach 90% recovery)',
  range 0 to 55000. Two bar series per category, colored distinctly: series 'Best short-reset baseline (multiplier <=4x)'
  and series 'Proposed per-key decay estimator'. Values: Low-mag/Low-freq: short-reset=38937.3, proposed=35231.2 (proposed
  faster). Low-mag/High-freq: short-reset=22802.2, proposed=26469.6 (short-reset faster). High-mag/Low-freq: short-reset=36415.2,
  proposed=39099.0 (short-reset faster). High-mag/High-freq: short-reset=23686.7, proposed=25134.1 (short-reset faster). Add
  a small percentage-difference annotation above each category pair: '+9.5% proposed faster', '-16.1% short-reset faster',
  '-7.4% short-reset faster', '-6.1% short-reset faster'. Legend in top right. Clean grid lines, colorblind-safe palette.
aspect_ratio: '16:9'
summary: >-
  Shows a cheap shortened global reset matches or beats the more expensive per-key mechanism in 3 of 4 win-corner drift scenarios.
figure_path: figures/fig_ablation_v0.pdf

--- Item 3 ---
id: fig_threshold
figure_type: data
title: CoV Threshold Sensitivity Grid
caption: >-
  Number of drift scenarios (out of 4) where the per-key-decay recovery-time advantage over baseline holds (95% confidence
  interval excludes a null effect), across a 3x3 grid of CoV classification thresholds at the win-corner cell. The original
  0.5 / 1.5 threshold pair used throughout the paper (row 2, column 2) is one of the more favorable cells, not a robust interior
  optimum: only 12 of the 36 threshold-scenario combinations tested show the advantage holding.
image_gen_detailed_description: >-
  Heatmap, 1:1 aspect ratio, 3 rows by 3 columns. Row labels (lower CoV threshold, i.e. stable/default boundary): '0.3', '0.5',
  '0.7'. Column labels (upper CoV threshold, i.e. default/volatile boundary): '1.2', '1.5', '1.8'. Cell values are 'count
  of scenarios (out of 4) where the recovery-time advantage holds': row 0.3: [1.2]=1, [1.5]=2, [1.8]=2. Row 0.5: [1.2]=1,
````

### [2] SKILL-INPUT — aii-paper-to-latex · 2026-08-26 22:30:10 UTC

The agent loaded the **aii-paper-to-latex** skill; its `SKILL.md` (the instructions injected into the agent's context) follows verbatim.

````
---
name: aii-paper-to-latex
description: "Assembles and compiles a LaTeX paper into paper.pdf: documentclass and package preamble, figure floats that includegraphics pre-generated vector .pdf and .jpg files, float-placement and width rules, and the required pdflatex, bibtex, pdflatex, pdflatex run sequence. Use whenever pre-written text and pre-generated figures must become a compiled PDF, and whenever a build misbehaves — citations printing as question marks, figures drifting to the end or above the title, shrunken axis labels, undefined references. Triggers: latex, tex, pdflatex, bibtex, natbib, includegraphics, figure float, htbp, compile or build the paper, paper.tex, paper.pdf. NOT for: writing the paper's text or deciding its structure (use aii-paper-writing), creating the figure images (aii-data-fig-gen, aii-concept-fig-gen), or fetching bibliography entries (use aii-semscholar-bib); NOT for reshaping a PDF that already exists — merging, splitting, form filling, table extraction (use anthropic-pdf)."
---

## LaTeX Paper Assembly

Assembles a research paper from paper text, pre-generated figures (vector `.pdf` for data figures, `.jpg` for concept figures) and a bibliography into a compiled PDF.

### Document Setup

```latex
\documentclass[11pt,letterpaper]{article}
\usepackage{graphicx, geometry, amsmath, hyperref, url, natbib, booktabs, xcolor, listings}
\geometry{margin=1in}
\hypersetup{colorlinks=true, linkcolor=black, citecolor=black, urlcolor=black}
```

### Figure Inclusion

CRITICAL: Include ALL figures. Every figure MUST appear in the paper.

```latex
\begin{figure}[!htbp]
  \centering
  \includegraphics[width=0.92\textwidth,keepaspectratio]{figures/filename.pdf}
  \caption{Descriptive caption.}
  \label{fig:label}
\end{figure}
```

Rules:
- ALWAYS `[!htbp]` — all four options, so a float can never be deferred to the end of the
  document, which `[t]` or `[h]` alone risks. Do not ask for a page TOP: `[!t]` and
  `[!tbp]` both floated a figure ABOVE the paper's own title on page 1, where `[!htbp]`
  on the same document did not. Where a figure lands is decided by where it is declared
  in the text
- Use `figure`, never `figure*`. This document class is ONE column, so `figure*` is exactly
  as wide as `figure` (469.76pt either way) and gains nothing, while restricting the float
  to a page top
- ALWAYS constrain with `width` and `keepaspectratio`. Add `height` only as a
  LAST RESORT against a very tall figure overrunning the page, and keep it
  generous — `0.85\textheight`. A tight height cap binds on ordinary figures
  and LaTeX then shrinks the TEXT with them: at `0.4\textheight` a square
  figure printed at 50.9%, putting 11 pt axis labels on the page at 5.6 pt.
  The figure generator measures legibility at the figure's OWN size, so it
  cannot see this happen
- Every figure needs `\caption`, `\label`, and a `\ref` in the text
- Do NOT convert figures to tables or describe them without inserting the image
- Do NOT skip any figures

### Compilation Process

Run each command separately (do NOT chain with `&&` — pdflatex often exits non-zero on warnings, which would skip bibtex and leave citations as `??`):

```bash
pdflatex -interaction=nonstopmode paper.tex
bibtex paper
pdflatex -interaction=nonstopmode paper.tex
pdflatex -interaction=nonstopmode paper.tex
```

All four commands are required. Skipping bibtex causes `??` in all citations.
Fix any errors between runs. Verify `./paper.pdf` was created.

### Output Files

- `./paper.tex` — LaTeX source
- `./references.bib` — bibliography file
- `./paper.pdf` — compiled PDF
- `./figures/` — all figure images (pre-generated, copied into workspace). Data
  figures are `.pdf` (vector — LaTeX renders their text at page resolution, which
  is what keeps axis labels sharp in print); concept figures are `.jpg`. Use each
  file's OWN extension in `\includegraphics`; there is no conversion step.
````

### [3] SKILL-INPUT — aii-semscholar-bib · 2026-08-26 22:30:10 UTC

The agent loaded the **aii-semscholar-bib** skill; its `SKILL.md` (the instructions injected into the agent's context) follows verbatim.

````
---
name: aii-semscholar-bib
description: "Fetches real BibTeX entries in one batch from Semantic Scholar by DOI, ArXiv ID or title via aii_semscholar_bib__fetch, normalises citation keys to AuthorYYYY, injects DOIs, and writes the result into references.bib, with a mandatory web-search fallback for anything not found. ALWAYS use whenever a bibliography, reference list or .bib file is being built or extended, and whenever a citation needs a verified entry instead of an invented one — never hand-write BibTeX first. Triggers: bibliography, references.bib, bibtex, citation key, DOI, arXiv id, Semantic Scholar, reference list, cite these papers, natbib entries. NOT for: writing the text around the citations (use aii-paper-writing), running bibtex and compiling (use aii-paper-to-latex), judging whether cited work supports the claims (use amg-paper-verification), or open-ended literature search and PDF mining (use aii-web-tools)."
---

## Tool: `aii_semscholar_bib__fetch`

Batch-fetch BibTeX entries from Semantic Scholar. Pass all references in a single call — the tool handles batching internally.

### How it works

1. **DOI/ArXiv refs** → batched into POST /paper/batch calls (up to 500 per API call, auto-chunked)
2. **Title-only refs** → individual GET /paper/search/match (1s delay between)
3. **Post-process** → fix entry type, fix citation key (AuthorYYYY), inject DOI

The ability server runs a single worker (`max_threads: 1`). Multiple concurrent tool calls are queued — each runs independently (no cross-request aggregation). Batching happens within each request.

### Input format

```json
{
  "references": [
    {"doi": "10.48550/arXiv.1706.03762", "author": "Vaswani", "year": 2017},
    {"arxiv": "2201.11903", "author": "Wei", "year": 2022},
    {"title": "Tree of Thoughts", "author": "Yao", "year": 2023}
  ]
}
```

Each reference object can have:
- `doi` — DOI string (ArXiv DOIs like `10.48550/arXiv.XXXX.XXXXX` auto-convert to ArXiv IDs)
- `arxiv` — ArXiv ID (e.g. `"2305.14325"`)
- `title` — Paper title (used for search/match when no DOI/ArXiv)
- `author` — First author last name (for cleaner citation key)
- `year` — Publication year (int, for citation key)

At least one of `doi`, `arxiv`, or `title` is required per reference.

### Output format

```json
{
  "success": true,
  "bib_text": "@inproceedings{Vaswani2017, ...}\n\n@article{Wei2022, ...}",
  "total": 3,
  "found": 3,
  "failed_count": 0,
  "entries": [{"citation_key": "Vaswani2017", "bibtex": "...", "title": "...", "doi": "...", "arxiv": ""}],
  "failed": []
}
```

### Workflow

1. Collect DOIs, ArXiv IDs, or titles for all papers you need to cite
2. Call `aii_semscholar_bib__fetch` with the full list in **one call**
3. Save `bib_text` from the response to your `references.bib` file
4. Check `failed` — for any missed papers, follow the **fallback procedure** below

### Fallback for failed references (MANDATORY)

NEVER fabricate BibTeX. For each failed reference:
1. **WebSearch** for `"Title" author year` (try `site:arxiv.org` too)
2. **WebFetch** the paper page → extract title, authors, year, venue, DOI/ArXiv ID
3. If DOI/ArXiv found → retry `aii_semscholar_bib__fetch` with it
4. Last resort: write BibTeX by hand using **only verified info from the actual paper page**

---

### CLI (for manual use / debugging)

```bash
SKILL_DIR="$(git rev-parse --show-toplevel 2>/dev/null || echo /ai-inventor)/.claude/skills/aii-semscholar-bib" && \
$SKILL_DIR/../.ability_client_venv/bin/python $SKILL_DIR/scripts/aii_semscholar_bib__fetch.py --refs '[
  {"doi": "10.48550/arXiv.1706.03762", "author": "Vaswani", "year": 2017},
  {"arxiv": "2201.11903", "author": "Wei", "year": 2022},
  {"title": "Tree of Thoughts", "author": "Yao", "year": 2023}
]'
```

`--json, -j` — output raw JSON instead of .bib text

**If the script fails** with a connection error (ability server not running): create a local `.venv`, install server deps from `server_requirements.txt` into it, then import the `@aii_ability` function from the script and call it directly — bypassing the server:
```bash
uv venv .venv --python=3.12 && uv pip install --python=.venv/bin/python -r "$SKILL_DIR/scripts/server_requirements.txt"
```
````
