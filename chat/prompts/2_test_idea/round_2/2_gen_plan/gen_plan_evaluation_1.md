# gen_plan_evaluation_1 — test_idea

> Phase: `invention_loop` · round 2 · `gen_plan`
> Run: `iter1_eb86f00c4c5a` — Why Per-Key Cache Decay Rarely Beats a Cheaper Shorter Reset
>
> Full, verbatim record of every prompt the AI Inventor pipeline gave this agent — system-user, human-user and skill-input — in the order they landed. Nothing truncated.

## Task: `gen_plan_evaluation_1` (terminal_claude_agent)

### [1] SYSTEM-USER prompt · 2026-08-26 21:17:10 UTC

````
<ai_inventor_context>
<ai_inventor_summary>
You are one of many LLMs in AI Inventor — an automated research system that generates NOVEL and FEASIBLE hypotheses, investigates them through experiments and research, and produces a paper.

Your output feeds other LLMs downstream. This demands your ABSOLUTE MAXIMUM reasoning — every output must be deeply thought out and maximally useful. Surface-level responses waste downstream computation.
</ai_inventor_summary>

<your_role>
YOU ARE: A plan generator (Step 3.2: GEN_PLAN in the invention loop)

You received the hypothesis, an artifact direction to elaborate, and dependency artifacts relevant to the plan.
Your job: elaborate this direction into a detailed, actionable plan for the executor agent.

Specific, actionable plan → valuable artifact. Vague plan → wasted execution.
</your_role>
</ai_inventor_context>

<artifact_type_info>
You are expanding an artifact direction of type: EVALUATION

EVALUATION
Evaluate experiment results with metrics, statistical analysis, and validity checks.
Runtime: Python 3.12, UV (any evaluation library), isolated workspace, gradual scaling matching experiment.
Tools: Full shell/Python/filesystem access, the aii-web-tools skill (web search, page fetch, regex grep over full page/PDF text), and other skills.
Skills: aii-json (schema validation), aii-openrouter-llms (call any LLM — GPT, Gemini, Llama, etc.), domain-specific as needed.
Capabilities: Compute any quantitative metrics and statistical tests, analyze validity and robustness.
Deps: REQUIRED at least one EXPERIMENT | OPTIONAL DATASET if reference data needed
</artifact_type_info>

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

<time_budget>

The evaluation executor has 3h total (including writing code, debugging, testing, and fixing errors).

</time_budget>

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

<plan_guidelines>
You are expanding an artifact direction from the strategy into a detailed plan.
The artifact direction specifies what to do at a high level (type, objective, approach, dependencies).
Your job is to make it concrete and actionable as a detailed plan.
Use web research to look up technical details, verify feasibility, and find reference materials
that will make your plan more concrete and actionable for the executor.

GOOD PLANS:
- Make each component SPECIFIC and actionable (not vague platitudes)
- Consider both success AND failure scenarios
- Build on the approach in the artifact direction
- Add concrete details the executor needs

BAD PLANS:
- Vague hand-waving ("do research on X")
- Ignoring the approach in the artifact direction
- Missing critical details the executor needs
</plan_guidelines>

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
Domain handbooks below capture expert knowledge for a specific field — its landscape, prior work, dead ends, evaluation norms, and what counts as a genuinely novel contribution. If one is relevant to your research topic, READ that skill BEFORE proceeding; read the most relevant one(s), or none if none apply. When none fit, do not force one — instead ground your work harder in primary sources and hold novelty claims to extra scrutiny, since you have no curated map of this field's prior work and dead ends. Use it for the methods, proper baselines, and evaluation this field demands.

- **aii-handbook-auto-computational-linguistics** — Field handbook for computational linguistics as a SCIENCE of language — grammaticality and minimal pairs (BLiMP), surprisal versus reading times, linguistic structure in LMs, annotator disagreement an
- **aii-handbook-auto-mechanistic-interpretability** — Field handbook for mechanistic interpretability of neural networks — circuit discovery, activation and attribution patching, sparse autoencoders, transcoders, attribution graphs, steering vectors, pro
- **aii-handbook-auto-multi-agent-llm-systems** — Field handbook for multi-agent LLM systems (MAS) — orchestration topology, multi-agent debate, mixture-of-agents, verifier and critic agents, inter-agent protocols (MCP/A2A), failure attribution and s
- **aii-handbook-auto-neurosymbolic** — Field handbook for neuro-symbolic AI — text-to-logic autoformalization (NL to FOL), LLM-plus-solver and prover pipelines (Prolog, ASP, SMT), probabilistic-differentiable NeSy (DeepProbLog, Scallop), r
</available_domain_handbooks>

<artifact_direction>
Make this direction concrete and actionable. Keep the same type and respect dependencies.

id: evaluation_iter2_dir2
type: evaluation
objective: >-
  Apply a Benjamini-Hochberg FDR correction across the original 36-group significance tests and report how many groups survive;
  quantify sensitivity of the win-corner result to the CoV classifier's two thresholds via a small targeted grid restricted
  to that cell; report a per-request compute-cost comparison (operation counts and/or a microbenchmark) between the two estimators;
  and synthesize the new short-reset-ablation and real-trace results from the paired experiment artifact into a single, honest
  verdict on whether the paper's headline claim survives all four reviewer critiques.
approach: >-
  Re-load the existing 36-group bootstrap CI results from art_gQEGVMwa8ZKC's method_out.json, apply Benjamini-Hochberg correction
  (or equivalent FDR procedure) across the 36 recovery-time-ratio tests, and report the adjusted significance count alongside
  the original 3/36 raw count, explicitly stating whether the win-corner cells still clear the corrected threshold. Using
  the new experiment artifact's short-reset-ablation results, directly compare the best short-tuned single-sketch baseline's
  recovery time against the proposed estimator's in the same win-corner cells and state plainly whether the gap persists,
  narrows, or disappears. Using the new real-trace results, report real-trace steady-state hit ratio parity (or lack thereof)
  and, if changepoints were found, the real-trace recovery-time comparison, clearly labeled as coarse/exploratory evidence
  given the absence of ground-truth drift labels. Run a small 2x2 or 3x3 grid over the two CoV thresholds (0.5, 1.5) holding
  tier periods fixed, restricted to the ratio=0.01/alpha=1.2 cell, and report whether the recovery-time advantage is stable,
  improves, or disappears as thresholds vary. Compute or analytically derive per-request operation counts (EWMA updates +
  reclassification vs. single counter increment) for both estimators as a compute-cost table. Conclude with a single reconciled
  verdict — updating the 5.1-5.7x memory figure to be consistent throughout — on whether the per-key-decay mechanism's narrow
  win is a genuine, robust effect or should be reframed as inconclusive/an artifact of under-tuning and multiple testing.
depends_on:
- id: art_gQEGVMwa8ZKC
  label: results
  relation_type:
  relation_rationale:
- id: art_f48a8QRaZrIB
  label: dataset
  relation_type:
  relation_rationale:
</artifact_direction>

<dependencies>
Completed artifacts this artifact can use during execution.

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
</dependencies>

<instructions>
YOUR ROLE: Write a detailed PLAN for the artifact. A separate executor agent runs the actual artifact later.

You are a PLANNER, not an executor. Your output is a plan that tells the executor what to do and how.
Do NOT execute the artifact itself — a separate agent handles that. Your job is to plan it so well that the executor can follow your plan step by step.

You CAN and SHOULD: search the web, read papers, and explore library docs to make your plan concrete.
You CANNOT run shell commands or scripts — code execution is disabled. Research via web tools only.

Do NOT do the executor's job: don't download datasets, don't implement code, don't run experiments, don't write proofs, don't compute evaluations.

<artifact_executor_scope>
IMPORTANT: Each artifact executor has a focused prompt that guides it to do ONE thing well. It will NOT perform tasks outside its scope — assigning the wrong work to the wrong artifact type wastes an iteration. Match the task to the right executor.

EVALUATION executor scope:
  Output: eval_out.json with evaluation results
  DOES: Any evaluation of experiment results — metrics, statistical tests, ablations, comparisons, visualizations, robustness checks, error analysis, etc.
  DOES NOT: Implement new methods (use EXPERIMENT), collect data (use DATASET)
  This is for analyzing experiment outputs from any angle
</artifact_executor_scope>

<artifact_planning_rules>
EVALUATION: Must depend on at least one EXPERIMENT. Focus on statistical rigor and validity checks.
</artifact_planning_rules>

<compute_profiles>
Choose the compute profile this artifact needs for execution.
Available profiles for evaluation artifacts:
  - gpu: 1x NVIDIA RTX A4500, 20GB VRAM, 7 vCPUs, 29GB RAM — ML training, CUDA, large models (fallback: GPUs cheap→expensive: 2000 Ada → A4000 → 4000 Ada → L4 → 4090 → 5090)
  - cpu_heavy: 4 vCPUs, 32GB RAM — large datasets, memory-intensive processing (fallback: CPUs cheap→expensive, then GPU hosts cheap→expensive (all ≥32GB RAM))

Set runpod_compute_profile to one of these exact tier names.
</compute_profiles>
GOOD PLANS: specific, actionable, consider failure scenarios, build on the suggested approach.
BAD PLANS: vague hand-waving, ignoring the suggested approach, missing critical executor details.
</instructions><user_data>
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
  "description": "Plan for an EVALUATION artifact.",
  "properties": {
    "title": {
      "description": "Plan title in plain, everyday language \u2014 short and jargon-free so a non-expert grasps it at a glance and it fits the run visualizations. Aim for about 4-8 words (~40 characters).",
      "title": "Title",
      "type": "string"
    },
    "summary": {
      "default": "",
      "description": "Brief summary",
      "title": "Summary",
      "type": "string"
    },
    "runpod_compute_profile": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "default": "cpu_light",
      "description": "Compute tier for execution \u2014 pick from the available profiles list (e.g., 'gpu', 'cpu_heavy', 'cpu_light'). Only used in RunPod mode.",
      "title": "Runpod Compute Profile"
    },
    "metrics_descriptions": {
      "description": "What metrics will be computed and how they're defined",
      "title": "Metrics Descriptions",
      "type": "string"
    },
    "metrics_justification": {
      "description": "Why these metrics are the right ones - what do they tell us about the hypothesis",
      "title": "Metrics Justification",
      "type": "string"
    }
  },
  "required": [
    "title",
    "metrics_descriptions",
    "metrics_justification"
  ],
  "title": "EvaluationPlan",
  "type": "object"
}
```

IMPORTANT: this task is NOT complete until `./.terminal_claude_agent_struct_out.json` exists and contains JSON matching the schema above.
````

### [2] HUMAN-USER prompt · 2026-08-26 21:17:10 UTC

```
Cache admission policies for skewed key popularity in read-heavy key-value stores
```
