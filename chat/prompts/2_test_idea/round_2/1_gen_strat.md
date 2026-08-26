# gen_strat_1 — test_idea

> Phase: `invention_loop` · round 2 · `gen_strat`
> Run: `iter1_eb86f00c4c5a` — Why Per-Key Cache Decay Rarely Beats a Cheaper Shorter Reset
>
> Full, verbatim record of every prompt the AI Inventor pipeline gave this agent — system-user, human-user and skill-input — in the order they landed. Nothing truncated.

## Task: `gen_strat_1` (terminal_claude_agent)

### [1] SYSTEM-USER prompt · 2026-08-26 21:16:02 UTC

````
<ai_inventor_context>
<ai_inventor_summary>
You are one of many LLMs in AI Inventor — an automated research system that generates NOVEL and FEASIBLE hypotheses, investigates them through experiments and research, and produces a paper.

Your output feeds other LLMs downstream. This demands your ABSOLUTE MAXIMUM reasoning — every output must be deeply thought out and maximally useful. Surface-level responses waste downstream computation.
</ai_inventor_summary>

<your_role>
YOU ARE: A strategy planner (Step 3.1: GEN_STRAT in the invention loop)

Each iteration of the invention loop runs: GEN_STRAT → GEN_PLAN → GEN_ART → GEN_PAPER_TEXT → REVIEW_PAPER → UPD_HYPO
Artifact types: RESEARCH (web search), EXPERIMENT (code), DATASET (data collection), EVALUATION (metrics), PROOF (Lean 4)
State persists across iterations: strategies, plans, artifacts, paper_texts (read from the run tree)

You received the hypothesis, iteration status (current + remaining), previous iteration's strategies, available artifact types, existing artifacts, and reviewer feedback.
Your strategy governs THIS iteration only. You define what artifacts to create NOW.

Focused strategy → efficient progress. Scattered strategy → wasted iteration.
</your_role>
</ai_inventor_context>

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

<time_budgets>

Each artifact executor has a fixed time budget (including writing code, debugging, testing, and fixing errors):

- research: 3h
- dataset: 6h
- experiment: 6h
- evaluation: 3h
- proof: 3h

</time_budgets>

<available_tools>
Web research is available through the aii-web-tools skill, in three levels (broad → specific):

1. web search — Returns titles, URLs, snippets. Use first to discover and scan the landscape. Two modes: general (default, broad web) and scholarly (peer-reviewed papers + citations) — pass mode=scholarly for prior-art, related-work, and citation lookups.
2. web fetch — Reads a page and returns its content as markdown (HTML or PDF). Use to understand a source. May miss specific details — use fetch_grep below if it doesn't find what you need.
3. fetch_grep — Regex search over a page/PDF's full text. Returns exact matching sections with context. Use for precise details, exact numbers, methodology, or PDFs.

Workflow: search → fetch (understand) → fetch_grep (extract specifics).
</available_tools>

<tool_use>
Maximize parallel tool calls. Parallelize independent operations, only sequentialize dependencies.
- Multiple searches/fetches on different topics → parallel in one turn
- Search then fetch results → sequential (need URLs first)
</tool_use>

<research_methodology>
Think like a researcher planning a study for a top venue.

- All strategies run in parallel and their artifacts combine into one pool. Together they must build toward a publishable paper — each strategy contributes a distinct, necessary piece. No strategy should be a standalone island.
- Ask yourself: what would a reviewer need to see? Proper baselines, controlled comparisons, ablations that isolate what matters. Plan artifacts that preempt reviewer objections.
- Depth over breadth. One well-designed experiment with proper controls beats five shallow ones.
- Match your evaluation to your claims. Measure what the hypothesis actually asserts.
- When results are weak or partial, vary the approach before writing it off. One failed method doesn't falsify the hypothesis.
- If iterations remain, think about what the NEXT iteration will need. Leave useful building blocks — datasets, baselines, preliminary results — that future strategies can build on, refine, or compare against.
</research_methodology>

<principles>
1. FOCUS ON NOVELTY - every strategy must lead to a genuinely novel contribution
2. MAXIMIZE PARALLELIZATION - all artifacts in your strategy run in parallel
3. BUILD ON EXISTING WORK - use completed artifacts from previous iterations, learn from failures
4. ITERATE ON THE METHOD - a negative result is about the approach, not the hypothesis. Try different methods, parameters, data, or formulations within the hypothesis bounds.
5. DIAGNOSE BEFORE DECIDING - before each iteration, review what worked, what didn't, and why. Use that to choose what to try next. Gaps are action items, not conclusions.
6. SET DEPENDENCIES WISELY - depends_on is a list of {id, label} objects referencing existing artifacts; each label is a short free-text type (a word or two, e.g. "dataset", "validates", "extends") that tags how the dep is used
7. PLAN FOR DEPENDENCIES - if an artifact depends on another (e.g. experiments need datasets), ensure prerequisites exist first or plan them this iteration for the next
</principles>

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

<hypothesis>
Your strategy should advance this hypothesis.

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
</hypothesis>

<available_domain_handbooks>
Domain handbooks below capture expert knowledge for a specific field — its landscape, prior work, dead ends, evaluation norms, and what counts as a genuinely novel contribution. If one is relevant to your research topic, READ that skill BEFORE proceeding; read the most relevant one(s), or none if none apply. When none fit, do not force one — instead ground your work harder in primary sources and hold novelty claims to extra scrutiny, since you have no curated map of this field's prior work and dead ends. Use it for study design, proper baselines, and the evaluation/validity norms this field demands.

- **aii-handbook-auto-computational-linguistics** — Field handbook for computational linguistics as a SCIENCE of language — grammaticality and minimal pairs (BLiMP), surprisal versus reading times, linguistic structure in LMs, annotator disagreement an
- **aii-handbook-auto-mechanistic-interpretability** — Field handbook for mechanistic interpretability of neural networks — circuit discovery, activation and attribution patching, sparse autoencoders, transcoders, attribution graphs, steering vectors, pro
- **aii-handbook-auto-multi-agent-llm-systems** — Field handbook for multi-agent LLM systems (MAS) — orchestration topology, multi-agent debate, mixture-of-agents, verifier and critic agents, inter-agent protocols (MCP/A2A), failure attribution and s
- **aii-handbook-auto-neurosymbolic** — Field handbook for neuro-symbolic AI — text-to-logic autoformalization (NL to FOL), LLM-plus-solver and prover pipelines (Prolog, ASP, SMT), probabilistic-differentiable NeSy (DeepProbLog, Scallop), r
</available_domain_handbooks>

<iteration_status>
Current iteration: 2 of 2
Remaining (including this one): 1
</iteration_status>

<previous_strategies>
Strategies from the PREVIOUS iteration. You can CONTINUE these directions,
ADAPT based on what worked and what didn't in the artifacts produced, or PIVOT if results suggest a better path.

--- Strategy 1 ---
kind: strategy
id: gen_strat_1_idx1
title: Per-key decay vs global reset cache admission
objective: >-
  Build a validated cache-simulator testbed and run the head-to-head comparison between a faithful W-TinyLFU baseline (global
  periodic sketch halving, matching Caffeine's production reset() semantics) and the proposed per-key inter-arrival-variance-decayed
  frequency estimator, on both real skewed access traces and synthetic Zipf traces with injected popularity drift, to determine
  whether per-key decay genuinely buys faster drift recovery at matched steady-state hit ratio and memory.
rationale: >-
  The hypothesis's entire empirical claim rests on one controlled comparison: same shadow-queue/admission-test/SLRU-eviction
  scaffolding, only the frequency-decay mechanism differs. The single biggest reviewer objection this needs to preempt is
  'is the baseline actually faithful to real TinyLFU/Caffeine, and is the drift benchmark strong enough that decay schemes
  actually diverge' — so the dataset must contain a real-world trace with genuine temporal skew (not only synthetic) and the
  synthetic generator must sweep drift magnitude/frequency as the success criteria require (>=4 drift scenarios). The experiment
  must implement the baseline exactly as specified (4-bit CM sketch, doorkeeper, shared sampleSize threshold, SLRU) so any
  hit-ratio delta is attributable to decay policy, not implementation drift. The evaluation must separate the pre-registered
  regression check (steady-state parity) from the main claim (recovery-time reduction with CIs), and compute memory overhead
  explicitly, since two of the three disconfirmation conditions in success_criteria are about memory and about beating the
  best single tuned baseline — both need to be measured, not asserted.
artifact_directions:
- id: dataset_iter1_dir1
  type: dataset
  objective: >-
    Assemble a dataset of key-access traces spanning real-world and synthetic sources: at least one real public trace with
    documented temporal/popularity skew (e.g. a memcached/CDN/Wikipedia-pageview-derived key-access log, or a published block-storage/cache-benchmark
    trace such as those distributed with Caffeine's own simulator or SNIA/UMass trace repositories), plus a parameterized
    synthetic Zipf-with-drift generator producing traces at multiple skew levels (alpha swept) with controlled drift events
    (periodic rank re-shuffling of a rank subset, and randomly injected short bursts on initially-cold keys), each event's
    timestamp/magnitude/affected-key-set recorded as ground truth so drift-recovery time can later be measured against a known
    injection point.
  approach: >-
    Search HuggingFace/UMass Trace Repository/SNIA IOTTA/public CDN-log releases for a real trace with per-request key/object
    IDs and timestamps at a size feasible to replay (target 1-10M requests, well under 300MB); if no suitable real trace is
    found within the time budget, fall back to a documented synthetic-only dataset but flag this explicitly as a limitation.
    For the synthetic generator: implement a Zipf sampler with time-varying rank permutation (a drift schedule) and burst
    injection (previously-cold keys given a temporary elevated sampling weight for a fixed window), parameterize alpha in
    {0.8, 1.0, 1.2}, drift period, and burst rate, and emit ground-truth drift-event metadata (timestamp, affected keys, magnitude)
    alongside each trace so evaluation can align recovery windows to true injection points. Split into full/mini/preview per
    the DATASET schema.
  depends_on: []
- id: experiment_iter1_dir2
  type: experiment
  objective: >-
    Implement a cache admission simulator with two competing frequency-decay mechanisms sharing identical scaffolding (doorkeeper,
    shadow-queue admission test, SLRU eviction, matched sketch width), and run both over every trace in the dataset at swept
    cache-size-to-key-space ratios, recording hit-ratio time series and per-mechanism memory footprint.
  approach: >-
    Implement (1) the W-TinyLFU baseline exactly per Caffeine's FrequencySketch semantics: 4-bit Count-Min-style counters,
    a shared size counter incrementing on every access, global `table[i] = (table[i] >>> 1) & mask` halving of the ENTIRE
    sketch once size reaches sampleSize (sweep sampleSize/W as a tunable baseline, since success_criteria requires comparing
    against the *best* tuned global-reset period), plus doorkeeper Bloom filter and SLRU (protected/probationary) eviction;
    and (2) the proposed variant, identical except each shadow-queue entry additionally tracks a short rolling window of inter-arrival
    gaps, computes a coefficient-of-variation-based volatility score, buckets it into a small number of decay-rate tiers,
    and applies that key's own decay rate to its frequency counter instead of the global reset (implemented as per-key floating-point
    EMA counters or per-bucket independent Count-Min sketches with different halving periods, whichever keeps memory within
    ~2x of baseline). Run both mechanisms over every dataset trace at 2-3 cache-size-to-key-space ratios and 3+ skew levels,
    log hit/miss per request and admission-test decisions, and record total bytes used by each mechanism's state (sketch +
    doorkeeper + shadow queue + any added per-key decay state) for the memory-overhead check.
  depends_on: []
- id: evaluation_iter1_dir3
  type: evaluation
  objective: >-
    Quantify, with statistical rigor, whether the per-key-decay variant matches baseline steady-state hit ratio within the
    pre-registered 1pp margin, and whether it significantly reduces post-drift hit-ratio recovery time (>=20% fewer requests-to-90%-of-post-drift-optimal,
    CI excluding zero) across drift scenarios and trace types, and separately verify the memory-overhead bound (must not roughly
    double total admission-filter state) is not violated for the observed gain.
  approach: >-
    From each run's hit/miss log and the dataset's ground-truth drift-event timestamps, compute (i) steady-state hit ratio
    in stationary windows (paired comparison + CI per trace/config), (ii) time-to-90%-of-post-drift-optimal-hit-ratio after
    every labeled drift event, aggregated with bootstrap CIs across repeated trace replays/seeds, comparing the proposed variant
    against BOTH the default-tuned baseline AND the best-of-swept-sampleSize baseline (the 'best tuned single global reset'
    the success criteria specifically requires beating), and (iii) total memory footprint ratio between the two mechanisms
    at matched sketch width. Report pass/fail against each of the three success-criteria clauses explicitly (steady-state
    parity, recovery-time reduction with CI, memory ratio), broken out per drift scenario (varying magnitude/frequency, expect
    >=4) and per trace type (synthetic vs real, if a real trace exists), and flag confounds (e.g. whether recovery-time gains
    are actually just a side-effect of a wider effective window rather than genuine per-key adaptivity) via an ablation comparing
    against a fixed non-global two-tier (fast/slow) decay scheme as a sanity baseline.
  depends_on: []
expected_outcome: >-
  A faithful W-TinyLFU baseline and the per-key-decay variant implemented on shared scaffolding, benchmarked across real and
  synthetic drift-injected traces at swept skew/cache-size settings, with a rigorous statistical verdict on steady-state parity,
  drift-recovery speedup (vs. both default and best-tuned-global-reset baselines), and memory overhead — directly resolving
  the hypothesis's three success/disconfirmation conditions and surfacing whether the mechanism's gain survives an ablation
  against a simple fixed-tier decay control.
summary: >-
  Build a real+synthetic drift-labeled trace dataset, implement matched W-TinyLFU baseline and per-key-decay admission variants
  in one simulator, and statistically evaluate steady-state parity, drift-recovery speed, and memory overhead against the
  hypothesis's pre-registered success criteria.
</previous_strategies>

<dependency_rules>
- depends_on is a list of objects {id, label} — each entry references an existing artifact and tags how it is being used
- "id" can ONLY reference IDs from <existing_artifacts> — never IDs you are proposing (all new artifacts run in parallel)
- "label" is a SHORT free-text type label (a word or two, NOT a sentence) describing what role the dep plays — e.g. "dataset", "validates", "extends", "supersedes". Required on every dep.
- Setting depends_on provides the dependency's out_dependency_files to your artifact at execution time
- If no suitable existing artifacts exist, use empty depends_on
- New artifact IDs are assigned by the system after submission — do not invent IDs for your proposed artifacts
</dependency_rules>

<available_artifact_types>
Artifact types you can plan. Use this to choose the right types for your strategy objectives.

<artifact_types>
RESEARCH
Web research to answer key questions — like a researcher making decisions.
Runtime: LLM Agent, no code execution.
Tools: the aii-web-tools skill (web search, page fetch, regex grep over full page/PDF text).
Capabilities: Find, synthesize, and compare information across sources; survey SOTA and best practices.
Deps: REQUIRED none | OPTIONAL other RESEARCH to build on prior findings

EXPERIMENT
Run code to test hypotheses, implement methods, and collect empirical results.
Runtime: Python 3.12, UV (any pip package), isolated workspace, gradual scaling (mini → full data).
Tools: Full shell/Python/filesystem access, the aii-web-tools skill (web search, page fetch, regex grep over full page/PDF text), and other skills.
Skills: aii-json (schema validation), aii-openrouter-llms (call any LLM — GPT, Gemini, Llama, etc.), domain-specific as needed.
Capabilities: Implement and run any code-based experiment, compare method vs baselines.
Deps: REQUIRED at least one DATASET | OPTIONAL RESEARCH for methodology guidance

DATASET
Collect, prepare, and merge datasets for experiments and analysis.
Runtime: Python 3.12, UV, isolated workspace.
Tools: Full shell/Python/filesystem access, the aii-web-tools skill (web search, page fetch, regex grep over full page/PDF text), and other skills.
Skills: aii-hf-datasets (HuggingFace Hub — ML datasets, many UCI/OpenML/Kaggle mirrors), aii-owid-datasets (Our World in Data — global statistics), aii-json (schema validation). Also any Python source (sklearn.datasets, openml, direct URLs, APIs) — must verify within 300MB limit.
Capabilities: Search, acquire, transform, combine, and standardize data from any available source.
Deps: REQUIRED none | OPTIONAL RESEARCH for guidance on what data to collect

EVALUATION
Evaluate experiment results with metrics, statistical analysis, and validity checks.
Runtime: Python 3.12, UV (any evaluation library), isolated workspace, gradual scaling matching experiment.
Tools: Full shell/Python/filesystem access, the aii-web-tools skill (web search, page fetch, regex grep over full page/PDF text), and other skills.
Skills: aii-json (schema validation), aii-openrouter-llms (call any LLM — GPT, Gemini, Llama, etc.), domain-specific as needed.
Capabilities: Compute any quantitative metrics and statistical tests, analyze validity and robustness.
Deps: REQUIRED at least one EXPERIMENT | OPTIONAL DATASET if reference data needed

PROOF
Formally prove mathematical statements in Lean 4 with automated iteration.
Runtime: LLM agent with Lean 4 compiler feedback loop.
Tools: Full shell/Python/filesystem access, the aii-web-tools skill (web search, page fetch, regex grep over full page/PDF text), and other skills.
Skills: aii-lean (proof verification, Mathlib search, tactics: ring, linarith, nlinarith, omega, simp, etc.)
Capabilities: Formally verify properties and inequalities, iterative proof development, lemma decomposition.
Deps: REQUIRED none | OPTIONAL RESEARCH for mathematical background
</artifact_types>
</available_artifact_types>

<artifact_executor_scope>
IMPORTANT: Each artifact executor has a focused prompt that guides it to do ONE thing well. It will NOT perform tasks outside its scope — assigning the wrong work to the wrong artifact type wastes an iteration. Match the task to the right executor.

RESEARCH executor scope:
  Output: research_out.json with {answer, sources, follow_up_questions} + research_report.md
  DOES: Web research — search, read, synthesize information from papers/docs/APIs into a structured report
  DOES NOT: Run code, download files, execute scripts, compute anything — no shell/Python access
  Use for literature surveys, API documentation, technical specifications — pure information gathering

EXPERIMENT executor scope:
  Output: method_out.json with results (metrics, predictions, analysis) — the core computational work
  DOES: Implement and run methods/algorithms, compute metrics, compare approaches, produce quantitative results
  DOES NOT: Collect new datasets (depends on DATASET artifacts for input data), write formal proofs
  This is the right artifact for any code that processes data and produces results

DATASET executor scope:
  Output: data_out.json with rows of {input, output, metadata_fold, ...} — raw data only, no derived computations
  DOES: Download/generate datasets, analyze candidates to pick the best ones, standardize to JSON schema (features, labels, folds, metadata), validate schema, split into full/mini/preview
  DOES NOT: Run experiments, train models, compute derived statistics (PID/MI/correlations/synergy matrices) as final output
  If you need to COMPUTE something from data (synergy matrices, MI scores, timing benchmarks), use an EXPERIMENT artifact instead

EVALUATION executor scope:
  Output: eval_out.json with evaluation results
  DOES: Any evaluation of experiment results — metrics, statistical tests, ablations, comparisons, visualizations, robustness checks, error analysis, etc.
  DOES NOT: Implement new methods (use EXPERIMENT), collect data (use DATASET)
  This is for analyzing experiment outputs from any angle

PROOF executor scope:
  Output: Lean 4 proof files (.lean) with verified theorems
  DOES: Write and verify Lean 4 formal proofs with Mathlib, iterative compilation
  DOES NOT: Run Python experiments, collect data, do empirical analysis
  Use only when formal mathematical guarantees are needed
</artifact_executor_scope>

<artifact_planning_rules>
RESEARCH: Plan early — findings guide dataset selection, experiment design, and methodology.
EXPERIMENT: Must depend on at least one DATASET. Define clear metrics and baselines before running. Consider trying multiple method variations rather than a single approach.
DATASET:
- Plan for REAL third-party datasets (HuggingFace, Kaggle, direct-download URLs) — downloadable within time and size constraints
- Describe dataset criteria (domain, size, format) — executors find exact sources, but you can suggest candidates or search directions
- ALWAYS prefer real datasets over synthetic. Synthetic is a LAST RESORT only when no suitable real data exists
EVALUATION: Must depend on at least one EXPERIMENT. Focus on statistical rigor and validity checks.
PROOF: Use only when the hypothesis requires formal mathematical guarantees. Lean 4 + Mathlib.
</artifact_planning_rules>

<existing_artifacts>
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
out_dependency_files:
  file_list:
  - method.py
  - full_method_out.json
  - mini_method_out.json
  - preview_method_out.json
</existing_artifacts>

<current_paper>
The current paper draft — represents the research story so far.

Use this to understand what's working, what's not, and what gaps remain.
Gaps and weak results signal what to try differently — not what to conclude.

# Introduction

A key-value cache decides two separate things when a request misses: what to evict, and whether the missing key is even worth admitting in the first place. The second decision, the *admission policy*, matters most when the working set is larger than the cache and popularity is skewed, because most misses are for keys that will never be requested again, and inserting them only evicts something that would have been reused. TinyLFU [1] is the dominant answer to this problem: it keeps a compact frequency sketch of recent traffic and admits a miss only if its estimated frequency exceeds that of the item it would evict, tested cheaply in a shadow queue before any real cache state changes. Through the Caffeine library, this exact design sits underneath widely deployed JVM caches.

Admission policies matter at the scale where read-heavy key-value stores actually run: CDN edge caches, in-memory object caches such as Memcached and Redis, and block caches inside LSM-tree stores such as RocksDB all serve populations of keys whose popularity follows a Zipf-like law, and all of them run continuously against traffic whose composition drifts — a previously cold key goes viral, a previously hot key falls out of use, and the ranking that was accurate an hour ago is stale now. An admission policy that adapts slowly to this drift keeps evicting the room it needs for a newly popular key in favor of one that is no longer popular, which shows up directly as a lower hit ratio during exactly the traffic surges an operator cares most about.

The difficulty is that TinyLFU's own accuracy trades off two things a fixed schedule cannot have simultaneously. Its Count-Min sketch is aged by a *reset operation*: once a shared counter reaches a sample-size threshold, every counter in the sketch is halved in one pass, with no distinction between keys. A long reset period lets a genuinely popular key accumulate enough count to be reliably admitted, but the same length means a newly trending key takes just as long to be recognized and a key that has gone cold keeps its inflated score for just as long. A short reset period fixes the second problem and reopens the first. Because the schedule is a single number shared by the whole sketch, there is no way to give long memory to the keys that deserve it and short memory to the keys that do not, without deciding in advance which keys are which.

This tension is not a gap in TinyLFU's original design so much as an acknowledged, unresolved one: the original paper's own related work cites an earlier frequency-aging technique and states directly that "determining when to divide the counters and by how much is tricky and requires fine tuning" [1]. Later systems have moved adaptivity elsewhere rather than into the frequency estimator itself — S3-FIFO [3] separates cold and hot items with two FIFO queues and lazy re-promotion instead of a frequency sketch at all; a reinforcement-learning-based cache manager for LSM-tree stores retunes block-versus-range partitioning and admission thresholds at the workload level [10] but still uses, by its own description, a lightweight frequency-based test for individual keys. None of these give an individual key control over its own forgetting rate.

We test whether they should. The shadow queue that TinyLFU already maintains sees each candidate key's arrival timestamps for free, and the gaps between those arrivals are a cheap, per-key signal for exactly the property a fixed reset schedule cannot see: whether a key's recent traffic looks like a steady stream or a bursty one. We classify each tracked key by the coefficient of variation of its inter-arrival gaps and route its frequency count into one of three independently-aged sketch tiers, so a stable heavy hitter keeps a long half-life and a volatile key gets a short one, without an oracle that pre-labels which keys are which and without a second, structurally different hot-list. We build a simulator that reproduces Caffeine's production semantics exactly, hold every other pipeline component fixed, and measure both steady-state hit ratio and post-drift recovery time across 36 combinations of cache-to-key-space ratio, Zipf skew, and drift scenario. The headline result is not the clean win the mechanism was designed to produce: averaged over the full grid, per-key decay changes almost nothing while costing five times the memory, and it wins clearly in only one corner of the space we tested — the smallest cache paired with the sharpest skew, where it cuts drift-recovery time by roughly a quarter. We report both facts, because the negative result over most of the space is exactly what tells an implementer when the added state does and does not pay for itself.

[FIGURE:fig_architecture]

## Summary of Contributions

- A drift-aware benchmark methodology for cache admission that separates a stationary steady-state hit ratio from an explicit post-drift recovery-time metric, evaluated under a full factorial design of cache ratio, skew, and drift type rather than a single operating point (Section 3).
- A per-key decay frequency estimator that infers each key's forgetting rate from inter-arrival volatility already visible in the admission shadow queue, requiring no external labels and reusing the shadow queue's existing state rather than adding a second structure (Section 3).
- A controlled comparison against a Caffeine-faithful global-reset baseline sharing an identical eviction pipeline, showing no reliable overall benefit across 36 conditions but a confidence-interval-significant 22-27% recovery-time reduction concentrated at the smallest cache-to-key-space ratio and highest skew tested, at a measured 5.1-5.7x memory cost (Section 4).
- An honest accounting of where the mechanism's memory overhead is and is not justified, arguing against per-key adaptive decay as a general-purpose replacement for TinyLFU's global reset and for it as a targeted addition for the specific regime where cache capacity is a small fraction of an extremely skewed key population (Section 5).

# Related Work

**Admission and frequency estimation.** TinyLFU [1] introduced the shadow-queue admission test this work builds on: a Count-Min sketch estimates each key's recent frequency, and a miss is admitted only if its estimated frequency exceeds that of the cache's current eviction candidate. Freshness is maintained by a single global reset: a shared counter increments on every access, and once it reaches a sample-size threshold every counter in the sketch — for every key, indiscriminately — is halved in the same pass. The same paper's related-work discussion independently identifies the aging schedule as an open difficulty rather than a solved detail, and describes a "hot list" augmentation from prior work that also tracks decaying popularity but does not fold that estimate into a head-to-head admission comparison and requires an explicit auxiliary list rather than reusing sketch state. Caffeine is the production implementation of TinyLFU's W-TinyLFU variant, which adds a small LRU admission window ahead of the segmented main region to protect against pathological low-locality bursts; our simulator matches its counter width, doorkeeper pre-filter, and reset semantics exactly rather than approximating them.

**Recency-frequency balance at the eviction layer.** ARC [2] and its predecessors LRU-K [7] and 2Q [8] address a related but distinct problem: balancing recency against frequency when deciding what to *evict*, using ghost lists of recently evicted keys to adapt the recency/frequency split online. This adaptivity operates entirely within the eviction policy and never touches an admission-time frequency sketch, so it is complementary to, rather than competing with, the mechanism studied here — a system could use ARC's ghost-list balancing for eviction alongside either frequency estimator we compare. S3-FIFO [3] takes a different route again, replacing frequency-sketch-based admission altogether with three FIFO queues and a "quick demotion, lazy promotion" discipline that evicts unrepeated keys before they ever reach the main cache; it reports the lowest mean miss ratio on 10 of 14 evaluated production traces without maintaining any decaying frequency count per key. Segcache [4] and the CacheLib engine [6] describe production-scale caching infrastructure that this line of admission-policy work targets, giving the scale (billions of objects, sub-microsecond per-request budgets) that motivates keeping any per-key adaptivity mechanism cheap.

**Adaptive and learned caching.** Cacheus [9] and related learning-based replacement policies adjust eviction weights online using bandit- or gradient-style updates over aggregate hit-rate feedback, adapting a small number of global mixture weights rather than a per-key parameter. AdCache [10], a 2026 reinforcement-learning-based cache manager for LSM-tree key-value stores, jointly retunes block-versus-range cache partitioning and global admission thresholds and reports up to 14% higher hit rate over RocksDB's default block cache; its point-lookup admission test is described only as a lightweight, frequency-based check, with adaptivity operating at the workload and partition level rather than through any individual key's own arrival statistics. Across this line of work, adaptivity is consistently a property of a global policy parameter (a mixture weight, a partition ratio, an RL-tuned threshold) rather than a property assigned separately to each key, which is the specific gap this paper's mechanism targets and the specific reason its cost structure differs: a global parameter costs nothing extra to store, while a per-key parameter costs one classification state per tracked key.

**Analogous adaptive-rate estimation.** The idea of trusting a new sample more or less depending on an entity's own observed volatility has a long history outside caching: TCP's round-trip-time estimator [5] weights a new RTT sample against smoothed history using an estimate of the connection's own RTT variance, rather than a single fixed smoothing constant shared by all connections. The per-key decay mechanism studied here is the same idea applied to a different quantity — trusting a new frequency count more or less depending on the key's own observed inter-arrival variance — and our results give an empirical answer, in this different setting, to whether that idea transfers: mostly not, except in the highest-contention regime.

# Preliminaries

We use *admission policy* for the decision of whether to insert a missed key at all, as distinct from the *eviction policy* that decides what to remove once something is admitted; this paper only varies the former. A *shadow queue* is a metadata-only structure that tracks recent miss keys and their frequency estimates without holding cached values, used to run the admission comparison before committing real cache capacity. *Popularity drift* denotes a change over time in which keys are popular, distinguished into rank-reshuffle drift (a subset of keys exchange popularity ranks) and burst drift (a previously cold key suddenly receives concentrated traffic). A *Count-Min sketch* is a hashed-counter structure that estimates item frequency from sub-linear memory with one-directional (over-estimating) error; we use Caffeine's specific 4-bit, depth-4 variant throughout. The *coefficient of variation* (CoV) of a key's inter-arrival gaps is the ratio of their standard deviation to their mean, used here as a volatility score: near zero for a steady, near-periodic stream and large for a bursty one.

# Method

We implement a discrete-event cache-admission simulator [ARTIFACT:art_gQEGVMwa8ZKC] that processes one key request at a time through an identical pipeline for both estimators under comparison, so that any difference in hit ratio or recovery speed is attributable only to the frequency estimator and not to incidental differences between two separately written simulators. The pipeline, shown in Figure 1, is: a doorkeeper (a Bloom filter sized at 8 bits per cache slot) suppresses a first-ever sighting of a key from immediately entering the frequency sketch, matching Caffeine's actual semantics in which a doorkeeper hit contributes exactly +1 to a key's estimated frequency rather than saturating it; a shadow-queue admission test compares the candidate key's estimated frequency against the frequency of the current probationary-segment eviction victim, admitting the candidate only if its count is strictly higher; and a segmented LRU (SLRU) main region with a small preceding admission window implements eviction, with the window's own evicted candidate competing against the SLRU's probationary victim in the same comparison rather than being counted as an unconditional hit.

**Baseline estimator: global reset.** The baseline is a single Count-Min sketch whose reset schedule reproduces a production TinyLFU cache's reset operation exactly: a shared access counter increments on every non-doorkeeper-suppressed key, and once it reaches a sample-size threshold — a tunable multiple of cache capacity — every 4-bit counter in the sketch's backing array is halved in a single pass, aging every key's count identically. The sample-size multiplier (swept over 4, 8, 16, and 32 times cache capacity) is tuned per (cache ratio, skew) cell on a held-out 80,000-request stationary prefix of each trace before the main drift-scenario grid runs, so the baseline is never handicapped by an untuned reset period; Table 1 reports the multiplier chosen for the three cells at cache-to-key-space ratio 0.01.

**Proposed estimator: per-key decay.** The proposed estimator maintains three parallel Count-Min sketches — "volatile," "default," and "stable" — with independent halving periods set to 2x, 8x, and 32x cache capacity respectively. A bounded shadow-metadata LRU (sized to the shadow queue's own capacity, so total state stays O(shadow-queue size) rather than O(true key space)) tracks, for each currently-tracked key, an exponentially-weighted moving estimate of its inter-arrival gap and squared gap. Once a key has accumulated enough observations, its coefficient of variation is computed from these two moments and it is assigned to the volatile tier if CoV exceeds 1.5, the stable tier if CoV is below 0.5, and the default tier (matching the baseline's own typical reset multiplier) otherwise; a key with too few observations, or one that has aged out of the shadow-metadata LRU and re-enters, defaults to the middle tier until it accumulates enough history to be reclassified. A key's frequency estimate at query time is read from whichever tier's sketch it is currently assigned to, plus the doorkeeper's +1 contribution if applicable. This gives every currently-tracked key an individually inferred forgetting rate using only signal (arrival timestamps) the shadow queue already touches, without a separate hot-list structure and without external popularity labels.

**Deviations from the original design.** Two corrections were made during implementation and are reported for transparency. First, an early version of the pipeline gave the doorkeeper a +15 contribution to a key's frequency score, which would have saturated the comparison for nearly every warmed-up key and destroyed discrimination between candidates; this was corrected to the +1 contribution that matches Caffeine's actual behavior. Second, an early version of the admission-window logic counted every window admission directly as a cache hit; this double-counted hits and was replaced with the proper competition described above, in which the window's own evicted LRU candidate must still win the frequency comparison against the SLRU's probationary victim.

# Experiments

**Data.** We generate synthetic traces [ARTIFACT:art_f48a8QRaZrIB] of 850,000 requests each over a 20,000-key universe, following a Zipf rank-frequency law at three skew levels (\(\alpha \in \{0.8, 1.0, 1.2\}\)), with two independent kinds of injected, ground-truth-labeled drift: periodic rank-reshuffle events (every 150,000 requests, permuting 5-20% of key ranks) and randomly timed popularity bursts on eight initially-cold keys per trace. For the main experiment grid we additionally cross this skew sweep with four drift scenarios that vary the magnitude and frequency of rank churn independently (low-magnitude/low-frequency, low-magnitude/high-frequency, high-magnitude/low-frequency, and high-magnitude/high-frequency reshuffling, each also carrying the cold-key bursts), over a fixed key-space of 150,000 keys and 600,000 requests per condition after an 80,000-request tuning prefix. A companion real-world arm using Twitter's production Twemcache traces [6] was planned but explicitly not run: the public release ships as multi-gigabyte binary records with no lightweight decoded alternative found within the available search budget, and we report this as a documented limitation rather than substitute a result that was not obtained.

**Design and metrics.** We sweep three cache-to-key-space ratios (0.01, 0.05, 0.10, giving cache capacities of 1,500, 7,500, and 15,000 slots against the 150,000-key space), three skew levels, four drift scenarios, and three random seeds, giving 36 (ratio, skew, drift-scenario) groups of 3 seeds each, 108 simulation runs in total, run identically for both estimators. For every run we record (i) the steady-state hit ratio, taken as the mean rolling hit ratio over the trailing 15% of the trace; (ii) a per-drift-event recovery time, defined as the first point after a drift event at which a 3,000-request rolling hit ratio climbs back to 90% of the way from its post-drift trough to its pre-drift plateau, censored at 60,000 requests if never reached; and (iii) total memory footprint in bytes for each estimator's complete state (sketch tables, doorkeeper, and any shadow metadata). Within each of the 36 groups we bootstrap (1,000 resamples over the 3 seeds) 95%-equivalent confidence intervals on the steady-state hit-ratio difference and on the ratio of proposed-to-baseline recovery time, and call a group a win for the proposed estimator when that ratio's confidence interval lies entirely below 0.8 (a pre-registered 20%-faster-recovery threshold).

**Baseline tuning sanity check.** Table 1 shows the sample-size multiplier chosen for the baseline at the smallest cache ratio: at low skew (\(\alpha=0.8\)) the best multiplier is 4, reaching a stationary hit ratio of 0.242; at moderate skew (\(\alpha=1.0\)) it is 8, reaching 0.547; at high skew (\(\alpha=1.2\)) it is 32, reaching 0.807. This confirms the baseline is not a strawman: its reset schedule is re-tuned for each skew level exactly as an operator would tune it in practice, so any recovery-time advantage the proposed estimator shows cannot be attributed to an unfairly slow baseline.

**Steady-state hit ratio is essentially unchanged.** Averaged across all 36 groups, the mean steady-state hit-ratio difference (proposed minus baseline) is +0.0023 — indistinguishable from parity given that group-level values range from -0.061 to +0.072 depending on scenario. This satisfies the pre-registered regression check: the proposed estimator does not sacrifice steady-state accuracy to gain adaptivity, but it also does not improve it as a general matter.

**Recovery-time advantage is real but confined to one corner of the space.** [FIGURE:fig_heatmap] Figure 2 shows the recovery-time ratio (proposed over baseline; below 1.0 means the proposed estimator recovers faster) across all three skew levels and four drift scenarios at the smallest cache ratio (0.01). At \(\alpha=1.2\), the proposed estimator wins with a confidence interval excluding a null effect in three of the four drift scenarios: low-magnitude/low-frequency drift (ratio 0.735, 95% CI [0.625, 0.816]), high-magnitude/low-frequency drift (ratio 0.737, CI [0.704, 0.796]), and high-magnitude/high-frequency drift (ratio 0.780, CI [0.732, 0.857]) — a 22-27% reduction in the time needed to recover 90% of the way back to the pre-drift hit ratio, with a positive (not merely neutral) steady-state hit-ratio delta in the same three cells (+0.005, +0.004, +0.024 respectively). Every other combination of skew and drift scenario, at every cache ratio, either shows no significant difference or a recovery-time ratio above 1.0 (the proposed estimator recovering *more slowly*): at \(\alpha=0.8\) and the same smallest cache ratio, recovery ratios range from 1.05 to 1.84, i.e. up to 84% slower. Of the full 36-condition grid, exactly 3 groups (8.3%) meet the pre-registered win criterion, and all 3 sit at the smallest cache-to-key-space ratio combined with the highest skew tested — the operating point where the true key population is most concentrated relative to available capacity, so correctly distinguishing a handful of enduring heavy hitters from short-lived noise carries the most weight. At the two larger cache ratios (0.05 and 0.10), no condition meets the win criterion in either direction; several instead show the proposed estimator recovering measurably slower, e.g. a ratio of 1.229 at ratio=0.05, \(\alpha=1.2\), low-magnitude/high-frequency drift.

**Memory cost.** [FIGURE:fig_memory] Figure 3 compares total estimator memory at the three cache ratios (values shown for \(\alpha=1.0\); other skew levels are within 1% of these at ratios 0.01 and 0.05, and vary by at most 12% at 0.10 due to a smaller doorkeeper-suppressed fraction). At ratio 0.01, the baseline uses 88,542 bytes against the proposed estimator's 454,808 bytes, a 5.14x overhead; at ratio 0.05, 439,345 bytes against 2,270,759 bytes (5.17x); at ratio 0.10, 858,577 bytes against 4,525,577 bytes (5.27x), rising to 5.68x at the highest-skew, highest-ratio cell specifically. This overhead comes from carrying three independently-sized Count-Min sketches (one per volatility tier, each sized to the full cache capacity) plus the per-key shadow metadata needed to compute each key's coefficient of variation, against the baseline's single sketch. The overhead is stable across the operating range we tested and is not a one-off effect of the winning corner: the memory cost is paid identically whether or not the recovery-time benefit materializes.

# Discussion

The central finding is not that per-key decay fails, but that it succeeds in exactly one place and nowhere else we tested, and that place is identifiable in advance: the smallest cache-to-key-space ratio (a cache holding 1% of the key population) combined with the sharpest skew (\(\alpha=1.2\)). This is the regime in which the Zipf head is narrowest relative to available capacity, so the admission test is making its highest-stakes decisions on the fewest, most consequential keys, and a wrong forgetting rate for even a few of them measurably delays recovery. At larger cache ratios the same key population is a smaller fraction of capacity, the admission test has more room to be forgiving, and the extra discrimination the per-key mechanism buys stops mattering — consistent with the near-zero or reversed recovery-time ratios observed at ratios 0.05 and 0.10.

This reframes the hypothesis's original success criterion. We had asked whether per-key decay beats a *tuned* global-reset baseline across a broad operating range; it does not, and the honest reading of the 36-condition grid is that the tuned single reset period already captures most of the achievable adaptivity outside the narrow high-contention corner, which is itself one of the two disconfirming outcomes we pre-registered. What survives is a narrower, still useful claim: in the specific regime where a fixed-size cache must serve a small, sharply concentrated set of hot keys under drift, giving those keys individually appropriate memory does produce a real, CI-significant, non-cherry-picked improvement, and an operator who knows they are running in that regime — a small edge cache behind a CDN serving a long-tail catalog, for instance — has a documented case to consider it.

The cost side of that case is unfavorable outside the win corner. A consistent 5.1-5.7x memory multiplier is a substantial price for an admission filter that is deliberately supposed to be compact, and our results give no basis for paying it except in the one regime identified above. This also means the disconfirmation criterion about overhead is only partially met: the mechanism does not double baseline state, it more than quintuples it, which is a stronger negative signal than the pre-registered threshold anticipated.

**Limitations.** All drift-recovery results come from synthetic traces with injected, labeled drift; the planned real-world validation against Twitter's production cache traces was not run because the public release requires multi-gigabyte binary-format downloads with no lightweight decoded alternative available within budget, so we cannot yet confirm that real popularity drift has the same shape as our injected rank-reshuffle and burst events. The coefficient-of-variation classifier uses two fixed thresholds (0.5 and 1.5) and three tiers chosen without a separate tuning sweep of their own; it is possible a differently tuned tiering scheme performs better, though the win corner we did find is not sensitive to being near a threshold boundary at either extreme. Finally, our sweep covers three discrete cache ratios; the transition between the winning and non-winning regime could sit anywhere between ratio 0.01 and 0.05 and this grid cannot localize it more precisely.

# Conclusion

We tested whether giving each key its own frequency-decay rate, inferred from arrival volatility already visible in TinyLFU's shadow queue, can replace a single tuned global reset schedule. Across 36 conditions spanning cache-to-key-space ratio, Zipf skew, and drift type, it mostly cannot: steady-state hit ratio is unchanged and drift-recovery time is not reliably improved in 33 of 36 conditions, at a consistent 5.1-5.7x memory cost. It does produce a genuine, statistically supported 22-27% recovery-time improvement, but only at the smallest cache ratio and sharpest skew we tested, which is also the regime where a wrong forgetting rate is most expensive to get wrong. The practical conclusion is scoped rather than general: per-key decay is worth its overhead specifically for small caches serving extremely concentrated, drifting popularity, and is not a drop-in improvement to TinyLFU elsewhere. Future work should localize the transition between the two regimes more precisely by sweeping intermediate cache ratios between 0.01 and 0.05, and should validate the injected-drift results against real production traces once a lightweight decoded release of a labeled real-world trace becomes available.

# References

[1] Einziger, G. and Friedman, R. TinyLFU: A Highly Efficient Cache Admission Policy. Euromicro PDP 2014.

[2] Megiddo, N. and Modha, D. ARC: A Self-Tuning, Low Overhead Replacement Cache. USENIX FAST 2003.

[3] Yang, J., Zhang, Y., Qiu, Z., Yue, Y., and Vinayak, R. FIFO Queues are All You Need for Cache Eviction. ACM SOSP 2023.

[4] Yang, J., Yue, Y., and Vinayak, R. Segcache: A Memory-Efficient and Scalable In-Memory Key-Value Cache for Small Objects. USENIX NSDI 2021.

[5] Jacobson, V. Congestion Avoidance and Control. ACM SIGCOMM 1988.

[6] Berg, B., Berger, D. S., McAllister, S., Grosof, I., Gunasekar, S., Lu, J., Uhlar, M., Carrig, J., Beckmann, N., Harchol-Balter, M., and Ganger, G. R. The CacheLib Caching Engine: Design and Experiences at Scale. USENIX OSDI 2020.

[7] O'Neil, E., O'Neil, P., and Weikum, G. The LRU-K Page Replacement Algorithm for Database Disk Buffering. ACM SIGMOD 1993.

[8] Johnson, T. and Shasha, D. 2Q: A Low Overhead High Performance Buffer Management Replacement Algorithm. VLDB 1994.

[9] Rodriguez, L. V., Yusuf, F., Lyons, S., Paz, E., Rangaswami, R., Liu, J., Zhao, M., and Narasimhan, G. Learning Cache Replacement with Cacheus. USENIX FAST 2021.

[10] Ye, J., Liu, J., and Luo, S. AdCache: Adaptive Cache Management with Admission Control. EDBT 2026.
</current_paper>

<reviewer_feedback>
Paper reviewer feedback from the previous iteration. Your strategy MUST address these critiques.
Prioritize major issues — these are the most impactful improvements to make.

- [MAJOR] (evidence) The paper's central positive claim (3 of 36 groups significant, all in one corner) is reported without any multiple-comparisons correction. Under 36 independent 95%-CI tests, roughly 1.8 false positives are expected by chance alone; finding exactly 3, clustered in adjacent cells that share the same skew and cache-ratio (which are not independent draws, since seeds and traces overlap in structure across drift scenarios), is consistent with either a real effect or a milder multiple-testing/correlated-test artifact. The paper does not address this at all.
  Action: Report a Benjamini-Hochberg (or similar) FDR-adjusted significance threshold applied across the 36 groups, and state explicitly how many groups remain significant after adjustment. If the 3 winning groups survive correction, this substantially strengthens the paper's core claim; if they do not, the paper needs to be reframed as inconclusive rather than as demonstrating a real, identifiable win regime.
- [MAJOR] (methodology) There is no real-world trace evaluation. The Twitter/Twemcache trace arm was planned (and is referenced in the artifact as dataset 1) but was explicitly not executed for the drift-recovery experiments because of format/download constraints, so all reported recovery-time results rest entirely on synthetic, self-injected drift events whose statistical structure (Zipf skew, periodic rank-reshuffle every fixed 150,000 requests, 8 cold-key bursts) was chosen by the authors themselves. This is a substantial evidentiary gap for a systems/caching contribution, where realistic traffic drift shapes are known to differ significantly from clean synthetic injections (e.g., drift in real CDN/social traffic is typically non-periodic, heavy-tailed in burst magnitude, and correlated across keys).
  Action: At minimum, run the already-downloaded 80,000-request Twitter cluster026 sample (present in the dataset artifact as real_twitter_cache_trace) through the steady-state hit-ratio comparison even without labeled drift events, to show the estimator behaves sensibly on real traffic; ideally, identify or construct even coarse drift labels (e.g., via a changepoint detector on real per-key request rates) to get at least one real-trace recovery-time data point. Absent any real-trace evidence, soften every claim in the abstract/intro/conclusion that generalizes beyond 'synthetic, injected drift.'
- [MAJOR] (novelty) The mechanism is a fairly direct transplant of a well-known idea (per-entity adaptive smoothing based on the entity's own observed variance, as in TCP RTT estimation, cited by the paper itself) onto cache admission frequency sketches. The paper does not identify or benchmark against the most obvious simpler alternative that targets the same intuition — e.g., a two-tier (not three-tier, not classifier-driven) sketch keyed on a much cheaper per-key signal such as recency-of-last-reset-survival, or simply a shorter global reset period restricted to the specific small-cache/high-skew regime the paper identifies as the win corner. Without that comparison, it's unclear whether the specific machinery proposed (CoV-based 3-tier classification with EWMA moment tracking) is necessary to get the observed 22-27% recovery-time gain, or whether a much simpler and cheaper change (e.g., shortening the global reset period further in this specific regime) would achieve the same thing at a fraction of the memory cost.
  Action: Add an ablation where the baseline's reset-schedule sweep in the win-corner cells is extended to include much shorter multipliers than currently swept (the paper only sweeps {4,8,16,32}x cache capacity), to check whether a more aggressively short global reset alone recovers the same speed advantage without any per-key machinery. If a single well-tuned shorter reset matches the proposed method's recovery time in the win corner, the paper's contribution reduces to 'the standard baseline was under-swept,' which would need to be reported honestly; if the gap persists, this is strong, needed evidence that per-key tiering specifically (not just more aggressive aging) is what matters.
- [MINOR] (scope) The memory-cost figure is stated inconsistently: the paper's contributions list and the discussion both use '5.1-5.7x,' while the underlying experiment artifact's own summary describes the overhead as 'roughly 3-5x.' This is a small but noticeable inconsistency between the paper text and its own supporting artifact.
  Action: Update all mentions to the precise, later-computed figures (5.14x/5.17x/5.27x rising to 5.68x/5.68x at the highest-skew highest-ratio cell) and ensure the artifact summary or downstream description is regenerated to match, so a reader cross-checking claims against artifacts does not find a discrepancy.
- [MINOR] (rigor) The CoV classifier's two thresholds (0.5 and 1.5) and the three tiers' halving periods (2x/8x/32x cache capacity) are stated as chosen without a dedicated tuning sweep, and the paper's own limitations section acknowledges this but does not quantify sensitivity. Given that these hyperparameters directly determine which keys get long vs. short memory, the reported win could plausibly be fragile to these specific choices, or conversely could be a lower bound if better-tuned thresholds exist.
  Action: Run at minimum a 2x2 or 3x3 grid over the two CoV thresholds (holding tier halving periods fixed) restricted to the identified win-corner cell (ratio=0.01, alpha=1.2), and report whether the recovery-time advantage is stable, improves, or disappears — this is a cheap, targeted experiment relative to re-running the full 36-condition grid and would directly close the paper's stated limitation.
- [MINOR] (clarity) The paper never states the wall-clock/CPU cost of computing per-key CoV online (EWMA updates on gap and squared gap per shadow-queue entry, tier reclassification logic) relative to the baseline's O(1) counter increment plus periodic halving. For a system whose entire value proposition is 'cheap, tested in a shadow queue before any real cache state changes,' added per-request compute cost is as relevant as memory, and it is left completely unaddressed.
  Action: Report a simple throughput/latency microbenchmark (requests/sec or ns/request) comparing the two estimators in the simulator, or at minimum state the additional per-request operation count analytically (e.g., 2 EWMA updates + 1 conditional reclassification vs. 1 counter increment), so a practitioner can weigh compute overhead alongside the already-reported memory overhead.
- [MINOR] (evidence) The three tiers' fixed halving periods (2x/8x/32x cache capacity) are not compared against the corresponding sweep range used to tune the baseline (4x/8x/16x/32x), so it's unclear if the 'default' tier is a fair apples-to-apples match to the best-tuned single-sketch baseline in each cell, or whether the proposed method implicitly benefits from also covering the 2x point that the baseline sweep never tried.
  Action: Either extend the baseline's own multiplier sweep to include 2x (matching the volatile tier's period) so the single-sketch baseline has access to the same aging granularity, or explicitly justify why the tier periods were chosen independently of the baseline's sweep range.
</reviewer_feedback>

<task>
Generate 1 research strategy for THIS iteration.

**ARTIFACT LIMIT: Each strategy may contain AT MOST 3 artifact directions.** Focus on the highest-impact artifacts. Quality over quantity.

Each strategy should:
1. Define a clear OBJECTIVE - what novel contribution we're building toward
2. Plan artifacts to execute NOW - specify type, objective, approach, and depends_on for each
3. Account for parallel execution - all strategies and all planned artifacts run simultaneously, their artifacts are combined into one shared pool

**BROADER IS NOT THE SAME AS DEEPER.** Adding models, datasets, or settings to
an experiment that already ran makes the table bigger; it does not make the
contribution stronger, and it is the default a strategy generator drifts into
when it has nothing sharper to propose. Spend an artifact on scale only when
the SPREAD itself is the finding (a scaling trend, a regime boundary, a
generalisation claim the paper actually makes). Otherwise spend it on
something that could change the conclusion: the mechanism behind an observed
effect, the condition under which it disappears, the confound that would
explain it away, or the baseline whose absence a reviewer would name first.


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
    "ArtifactDep": {
      "description": "A single dependency on an existing artifact, with a short type label.\n\n``id`` and ``label`` are LLM-generated at strategy time. ``label`` is free-text but\nshort \u2014 a word or two naming the type of dependency, not a sentence.\n\n``relation_type`` and ``relation_rationale`` are populated later, in upd_hypo,\nusing the MultiCite citation-function typology (Lauscher et al., NAACL 2022).\nThey are absent at strategy time and may stay absent for legacy runs.",
      "properties": {
        "id": {
          "description": "ID of an existing artifact this artifact depends on",
          "title": "Id",
          "type": "string"
        },
        "label": {
          "description": "Short free-text label naming the type of this dependency (a word or two, not a sentence)",
          "title": "Label",
          "type": "string"
        }
      },
      "required": [
        "id",
        "label"
      ],
      "title": "ArtifactDep",
      "type": "object"
    },
    "ArtifactDirection": {
      "description": "High-level direction for an artifact to execute this iteration.\n\nID is code-assigned (LLMPrompt only \u2014 visible in prompts, not LLM-generated).",
      "properties": {
        "type": {
          "description": "Type of artifact to create",
          "enum": [
            "experiment",
            "research",
            "proof",
            "evaluation",
            "dataset"
          ],
          "title": "Type",
          "type": "string"
        },
        "objective": {
          "description": "What we want to achieve with this artifact",
          "title": "Objective",
          "type": "string"
        },
        "approach": {
          "description": "High-level direction/method",
          "title": "Approach",
          "type": "string"
        },
        "depends_on": {
          "description": "Existing artifacts this depends on, each with a short type label",
          "items": {
            "$ref": "#/$defs/ArtifactDep"
          },
          "title": "Depends On",
          "type": "array"
        }
      },
      "required": [
        "type",
        "objective",
        "approach"
      ],
      "title": "ArtifactDirection",
      "type": "object"
    },
    "Strategy": {
      "description": "A research strategy.\n\nContent fields have LLMPrompt + LLMStructOut markers.\n``id`` is code-assigned (LLMPrompt only \u2014 visible in prompts, not LLM-generated).\n\nID format: gen_strat_idx{N}",
      "properties": {
        "title": {
          "description": "Strategy name in plain, everyday language \u2014 short and jargon-free so a non-expert grasps it at a glance and it fits the run visualizations. Aim for about 4-8 words (~40 characters).",
          "title": "Title",
          "type": "string"
        },
        "objective": {
          "description": "The novel contribution we're building toward",
          "title": "Objective",
          "type": "string"
        },
        "rationale": {
          "description": "Why this strategy is promising",
          "title": "Rationale",
          "type": "string"
        },
        "artifact_directions": {
          "description": "Artifacts to execute THIS iteration",
          "items": {
            "$ref": "#/$defs/ArtifactDirection"
          },
          "title": "Artifact Directions",
          "type": "array"
        },
        "expected_outcome": {
          "description": "What we'll have after this iteration's artifacts complete",
          "title": "Expected Outcome",
          "type": "string"
        },
        "summary": {
          "default": "",
          "description": "Brief summary of the strategy and its expected contribution",
          "title": "Summary",
          "type": "string"
        }
      },
      "required": [
        "title",
        "objective",
        "rationale",
        "artifact_directions",
        "expected_outcome"
      ],
      "title": "Strategy",
      "type": "object"
    }
  },
  "description": "Top-level wrapper for LLM strategy generation output.",
  "properties": {
    "strategies": {
      "description": "List of generated strategies",
      "items": {
        "$ref": "#/$defs/Strategy"
      },
      "title": "Strategies",
      "type": "array"
    }
  },
  "required": [
    "strategies"
  ],
  "title": "Strategies",
  "type": "object"
}
```

IMPORTANT: this task is NOT complete until `./.terminal_claude_agent_struct_out.json` exists and contains JSON matching the schema above.
````

### [2] HUMAN-USER prompt · 2026-08-26 21:16:02 UTC

```
Cache admission policies for skewed key popularity in read-heavy key-value stores
```

### [3] SYSTEM-USER prompt · 2026-08-26 21:16:46 UTC

```
<verification_results>
Your previous response had issues that need fixing:

DEPENDENCY ERRORS (depends_on can ONLY reference IDs from <existing_artifacts>):
  - Strategy 1: Artifact 'experiment_iter2_dir1' (experiment): dependency 'art_gQEGVMwa8ZKC' has type 'experiment' which is not allowed (allowed: {'research', 'dataset'})

</verification_results>

<task>
Fix ALL issues above and regenerate your strategies:

1. Fix dependency errors:
   - depends_on is a list of {id, label} objects — every entry MUST have a non-empty short label
   - id can ONLY reference IDs from <existing_artifacts>
   - You CANNOT reference artifacts you are proposing in this strategy as dependencies (they all run in parallel)
   - Follow the dependency type rules (e.g., experiments require datasets)
   - If no suitable existing artifacts exist, use depends_on: []

Output the corrected JSON with the fixed strategies.
</task>
```
