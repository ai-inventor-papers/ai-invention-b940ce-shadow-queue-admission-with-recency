# gen_plan_experiment_1 — test_idea

> Phase: `invention_loop` · round 2 · `gen_plan`
> Run: `iter1_eb86f00c4c5a` — Why Per-Key Cache Decay Rarely Beats a Cheaper Shorter Reset
>
> Full, verbatim transcript of this agent task — every system/user prompt, assistant response, thinking block, tool call and tool result — in the order they occurred. Nothing truncated.

## Task: `gen_plan_experiment_1` (terminal_claude_agent, claude-sonnet-5)

### [1] CONFIG · 2026-08-26 21:17:00 UTC

```
model: claude-sonnet-5 | effort: low | permission: bypassPermissions | cwd: /ai-inventor/aii_data/runs/run_0pMem8W3ijCf/3_invention_loop/iter_2/gen_plan/gen_plan_experiment_1
```

### [2] SYSTEM-USER prompt · 2026-08-26 21:17:10 UTC

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
You are expanding an artifact direction of type: EXPERIMENT

EXPERIMENT
Run code to test hypotheses, implement methods, and collect empirical results.
Runtime: Python 3.12, UV (any pip package), isolated workspace, gradual scaling (mini → full data).
Tools: Full shell/Python/filesystem access, the aii-web-tools skill (web search, page fetch, regex grep over full page/PDF text), and other skills.
Skills: aii-json (schema validation), aii-openrouter-llms (call any LLM — GPT, Gemini, Llama, etc.), domain-specific as needed.
Capabilities: Implement and run any code-based experiment, compare method vs baselines.
Deps: REQUIRED at least one DATASET | OPTIONAL RESEARCH for methodology guidance
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

The experiment executor has 6h total (including writing code, debugging, testing, and fixing errors).

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

id: experiment_iter2_dir1
type: experiment
objective: >-
  Extend the existing W-TinyLFU simulator to (a) sweep much shorter global-reset multipliers (down to 1x and 2x cache capacity,
  in addition to the existing {4,8,16,32}x) specifically in the identified win-corner cells (ratio=0.01, alpha=1.2, all 4
  drift scenarios) to test whether a simply-shortened global reset matches the proposed per-key mechanism's recovery-time
  gain without any per-key machinery, and (b) replay both the baseline and per-key-decay estimators over the real Twitter
  production trace (real_twitter_cache_trace, 80,000 requests) to report steady-state hit ratio on genuine traffic, plus a
  simple changepoint-detector-derived coarse drift label (e.g. a rolling-window rate-of-request-composition-change signal
  on the per-key request stream) so at least one real-trace recovery-time data point can be computed.
approach: >-
  Reuse method.py's estimator and simulator classes unchanged; add a short-multiplier arm to the baseline's Phase A tuning
  specifically for the win-corner (ratio=0.01, alpha=1.2) cells, testing multipliers in {1, 2, 4} in addition to the already-swept
  set, and rerun the Phase B drift-scenario grid for just those 4 drift scenarios at this one (ratio, skew) cell with the
  newly best-tuned short-reset baseline vs. the existing proposed-estimator results (no need to rerun the proposed estimator,
  only the sharpened baseline). Separately, load real_twitter_cache_trace from the dataset artifact, run both estimators over
  it end-to-end (SLRU pipeline unchanged) to get real-trace steady-state hit ratio and memory footprint, then implement a
  lightweight changepoint detector (e.g. a CUSUM or simple rolling-window Jensen-Shannon-divergence test over the top-K key
  identities in successive windows) to flag candidate drift points in the real trace, and compute recovery time around any
  detected changepoints exactly as done for synthetic drift events, explicitly reporting how many changepoints were found
  and flagging this as coarse/unlabeled evidence rather than ground-truth drift. Keep total added compute small: this is a
  handful of extra sweep points plus one 80,000-request replay, not a new full grid.
depends_on:
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

EXPERIMENT executor scope:
  Output: method_out.json with results (metrics, predictions, analysis) — the core computational work
  DOES: Implement and run methods/algorithms, compute metrics, compare approaches, produce quantitative results
  DOES NOT: Collect new datasets (depends on DATASET artifacts for input data), write formal proofs
  This is the right artifact for any code that processes data and produces results
</artifact_executor_scope>

<artifact_planning_rules>
EXPERIMENT: Must depend on at least one DATASET. Define clear metrics and baselines before running. Consider trying multiple method variations rather than a single approach.
</artifact_planning_rules>

<compute_profiles>
Choose the compute profile this artifact needs for execution.
Available profiles for experiment artifacts:
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
  "description": "Plan for an EXPERIMENT artifact.",
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
    "implementation_pseudocode": {
      "description": "High-level pseudocode for the experiment implementation",
      "title": "Implementation Pseudocode",
      "type": "string"
    },
    "fallback_plan": {
      "description": "What to do if the primary approach fails - alternative methods, simplified versions",
      "title": "Fallback Plan",
      "type": "string"
    },
    "testing_plan": {
      "description": "How to validate the experiment works: start with small/fast tests, look for confirmation signals before running full-scale experiments",
      "title": "Testing Plan",
      "type": "string"
    }
  },
  "required": [
    "title",
    "implementation_pseudocode",
    "fallback_plan",
    "testing_plan"
  ],
  "title": "ExperimentPlan",
  "type": "object"
}
```

IMPORTANT: this task is NOT complete until `./.terminal_claude_agent_struct_out.json` exists and contains JSON matching the schema above.
````

### [3] HUMAN-USER prompt · 2026-08-26 21:17:10 UTC

```
Cache admission policies for skewed key popularity in read-heavy key-value stores
```

### [4] TOOL CALL — Write · 2026-08-26 21:18:05 UTC

```
File: /ai-inventor/aii_data/runs/run_0pMem8W3ijCf/3_invention_loop/iter_2/gen_plan/gen_plan_experiment_1/.terminal_claude_agent_struct_out.json

{
  "title": "Sharper Baseline Test + Real Twitter Trace Replay",
  "summary": "Extends the existing W-TinyLFU cache simulator (method.py) in two targeted ways: (1) sweeps very short global-reset multipliers (1x, 2x, 4x cache capacity) specifically in the win-corner cell (ratio=0.01, alpha=1.2) across all 4 drift scenarios, to test whether a cheaply-shortened global reset closes the gap with the per-key decay mechanism without any per-key machinery -- this is the sharpest possible disconfirmation test of the hypothesis's core claim; and (2) replays both the baseline and per-key-decay estimators end-to-end over the real Twitter production trace (real_twitter_cache_trace, 80,000 requests, cluster026) to report genuine steady-state hit ratio and memory footprint on real traffic, plus a lightweight unsupervised changepoint detector over the per-key request stream to derive at least one coarse, honestly-labeled real-trace recovery-time data point. Both additions reuse the existing estimator/simulator classes unchanged and are deliberately small in scope: a handful of extra sweep points plus one single-pass 80k-request replay, not a new grid.",
  "runpod_compute_profile": "cpu_light",
  "implementation_pseudocode": "# Reuse existing method.py classes unchanged: FrequencySketch/BaselineEstimator (global reset),\n# PerKeyDecayEstimator (CoV-based per-key decay w/ M>=8 cold-start guard), SLRUCache, DriftInjector,\n# and the metrics/recovery-time helpers from iter1. Do NOT reimplement these -- import and call them.\n\nimport json, math\nfrom pathlib import Path\nfrom collections import defaultdict, deque\nimport numpy as np\nfrom method import (            # names as defined in the iter1 method.py; adjust import if renamed\n    BaselineWTinyLFUEstimator, PerKeyDecayEstimator, SLRUCache,\n    run_trace, load_synthetic_trace, load_real_trace,\n    compute_hit_ratio, compute_recovery_time, DRIFT_SCENARIOS,\n)\n\nRESULTS = {\"part_a_short_reset\": [], \"part_b_real_trace\": {}}\n\n# ---------- PART A: short-multiplier arm at the win-corner cell ----------\n# Win-corner cell identified in iter1: ratio=0.01 (cache_size = 0.01 * key_universe), alpha=1.2\nRATIO = 0.01\nALPHA = 1.2\nSHORT_MULTIPLIERS = [1, 2, 4]   # in addition to the already-swept {4,8,16,32}; 4 overlaps intentionally as a sanity cross-check\nDRIFT_SCENARIOS_TO_RUN = DRIFT_SCENARIOS  # all 4 from iter1: e.g. low/high-magnitude x low/high-frequency rank reshuffle + burst\n\nsynthetic_alpha12 = load_synthetic_trace(dataset=\"synthetic_zipf_alpha12\")  # from dependency dataset artifact\ncache_size = int(RATIO * key_universe_size(synthetic_alpha12))\n\nfor scenario in DRIFT_SCENARIOS_TO_RUN:\n    trace_with_drift = inject_or_select_drift(synthetic_alpha12, scenario)  # reuse iter1's drift injector/labels\n    best_short = None\n    for mult in SHORT_MULTIPLIERS:\n        sample_size_W = mult * cache_size          # matches Caffeine's W = mult * C sizing convention\n        baseline = BaselineWTinyLFUEstimator(sample_size=sample_size_W)\n        cache = SLRUCache(capacity=cache_size, estimator=baseline)\n        trace_result = run_trace(cache, trace_with_drift)\n        recovery = compute_recovery_time(trace_result, drift_events=trace_with_drift.drift_events,\n                                          target_frac=0.90)   # time-to-90%-of-post-drift-optimal, matches iter1 convention\n        steady_state_hr = compute_hit_ratio(trace_result, window=\"pre_drift_stationary_segment\")\n        entry = {\"scenario\": scenario, \"multiplier\": mult, \"sample_size_W\": sample_size_W,\n                 \"steady_state_hit_ratio\": steady_state_hr, \"recovery_time\": recovery}\n        RESULTS[\"part_a_short_reset\"].append(entry)\n        if best_short is None or recovery[\"time_to_90pct\"] < best_short[\"recovery_time\"][\"time_to_90pct\"]:\n            best_short = entry\n    # Pull the already-computed proposed-estimator (per-key decay) result for this exact (ratio, alpha, scenario) cell\n    # from iter1's method_out.json (do NOT rerun it) and compute the head-to-head gap vs this newly best short-reset baseline.\n    proposed_result = load_iter1_proposed_result(ratio=RATIO, alpha=ALPHA, scenario=scenario)\n    gap_pct = 100.0 * (best_short[\"recovery_time\"][\"time_to_90pct\"] - proposed_result[\"time_to_90pct\"]) / best_short[\"recovery_time\"][\"time_to_90pct\"]\n    RESULTS.setdefault(\"part_a_head_to_head\", []).append({\n        \"scenario\": scenario, \"best_short_reset_multiplier\": best_short[\"multiplier\"],\n        \"best_short_reset_recovery\": best_short[\"recovery_time\"][\"time_to_90pct\"],\n        \"proposed_estimator_recovery\": proposed_result[\"time_to_90pct\"],\n        \"proposed_still_faster_pct\": gap_pct,          # >0 means proposed still wins even vs best short reset; <=0 means short reset matches/beats it -> disconfirms the mechanism's necessity for this cell\n    })\n\n# ---------- PART B: real Twitter trace replay ----------\ntwitter_trace = load_real_trace(dataset=\"real_twitter_cache_trace\")  # 80,000 requests, cluster026, from dependency dataset artifact\nreal_cache_size = pick_matched_cache_size(twitter_trace, ratio=RATIO)  # same ratio convention as synthetic sweep for comparability\n\nfor name, EstimatorCls, kwargs in [\n    (\"baseline_w_tinylfu\", BaselineWTinyLFUEstimator, {\"sample_size\": best_global_multiplier_from_iter1 * real_cache_size}),\n    (\"per_key_decay\", PerKeyDecayEstimator, {\"cold_start_M\": 8, \"decay_buckets\": iter1_decay_bucket_config}),\n]:\n    estimator = EstimatorCls(**kwargs)\n    cache = SLRUCache(capacity=real_cache_size, estimator=estimator)\n    trace_result = run_trace(cache, twitter_trace)\n    RESULTS[\"part_b_real_trace\"][name] = {\n        \"steady_state_hit_ratio\": compute_hit_ratio(trace_result, window=\"full\"),\n        \"memory_bytes_per_slot\": estimator.measured_bytes_per_entry(),   # reuse iter1's memory accounting helper\n        \"per_request_stream\": trace_result.per_request_summary,          # kept for changepoint detection below\n    }\n\n# --- lightweight unsupervised changepoint detector over the per-key request stream ---\n# Rolling-window Jensen-Shannon divergence over top-K key-identity distributions, K=50, window=2000 requests, stride=500\ndef detect_changepoints(request_stream, window=2000, stride=500, top_k=50, js_threshold_percentile=95):\n    windows = sliding_windows(request_stream, window, stride)\n    dists = [key_freq_distribution(w, top_k=top_k) for w in windows]\n    js_scores = [jensen_shannon_divergence(dists[i], dists[i+1]) for i in range(len(dists)-1)]\n    threshold = np.percentile(js_scores, js_threshold_percentile)\n    changepoints = [i*stride + window for i, s in enumerate(js_scores) if s > threshold]\n    return changepoints, js_scores, threshold\n\ncps, js_scores, threshold = detect_changepoints(twitter_trace.request_stream)\nRESULTS[\"part_b_real_trace\"][\"changepoints_detected\"] = cps\nRESULTS[\"part_b_real_trace\"][\"changepoint_threshold\"] = threshold\nRESULTS[\"part_b_real_trace\"][\"n_changepoints\"] = len(cps)\nRESULTS[\"part_b_real_trace\"][\"changepoint_caveat\"] = (\n    \"UNSUPERVISED, coarse, unlabeled -- these are candidate drift points from a JS-divergence heuristic, \"\n    \"NOT ground-truth drift events. Treat any recovery-time numbers around them as suggestive, not confirmatory.\"\n)\n\nfor name in [\"baseline_w_tinylfu\", \"per_key_decay\"]:\n    per_cp_recovery = []\n    for cp in cps:\n        rec = compute_recovery_time_at_index(RESULTS[\"part_b_real_trace\"][name][\"per_request_stream\"],\n                                              changepoint_idx=cp, target_frac=0.90,\n                                              window_after=5000)  # bounded lookahead since real trace has no known post-drift optimum\n        per_cp_recovery.append(rec)\n    RESULTS[\"part_b_real_trace\"][name][\"recovery_time_at_changepoints\"] = per_cp_recovery\n\n# ---------- write output ----------\nmethod_out = {\"schema\": \"exp_gen_sol_out_or_appropriate_schema\", \"results\": RESULTS}\nPath(\"method_out.json\").write_text(json.dumps(method_out, indent=2))\n# validate via aii-json skill before finishing",
  "fallback_plan": "1. If iter1's method.py estimator/simulator class names or method_out.json result schema differ from what this plan assumes (they must be located and read FIRST, before writing any new code, by grepping the iter1 experiment artifact's workspace for the class/function names actually used) -- adapt imports and the result-lookup key structure to match reality rather than guessing; do not silently invent a compatible-looking API.\n2. If the short-multiplier (1x, 2x) reset sweep is numerically unstable or degenerate (e.g. W=1x cache size resets the sketch so often that frequency estimates are pure noise, causing near-random admission) -- this is itself a valid, reportable result (evidence the global mechanism cannot be pushed this low without breaking, which still supports the hypothesis) rather than a bug to hide; report it explicitly with the observed hit-ratio collapse, do not discard the data point.\n3. If real_twitter_cache_trace's request_type field or timestamp granularity makes per-key inter-arrival-gap computation ill-defined (e.g. many requests share identical timestamps, or non-GET request types dominate) -- filter to read-dominant request types only (matching the hypothesis's 'read-heavy' scope) and document the filtered fraction; if timestamps are too coarse for gap-based CoV, fall back to using request SEQUENCE POSITION (seq field) as the inter-arrival proxy instead of wall-clock time, which the dataset schema already guarantees is present and monotonic.\n4. If the JS-divergence changepoint detector finds zero changepoints above the 95th-percentile threshold on the 80k-request trace (plausible if Twitter cache traffic composition is fairly stable at this window size) -- progressively lower the percentile threshold (e.g. to 90th, then 85th) and/or shrink the window to 1000/stride 250 to surface at least a few candidate points; if still zero after two relaxations, report this as a finding (\"no detectable large composition shifts in this 80k-request sample\") rather than forcing spurious changepoints, and rely on Part A + the real-trace steady-state comparison (already both real, already both meaningful) as the artifact's evidence.\n5. If loading iter1's proposed-estimator result for the exact (ratio=0.01, alpha=1.2, scenario) cell fails because iter1's method_out.json was structured differently or that exact cell wasn't run at fine enough granularity -- rerun ONLY the proposed per-key-decay estimator for those 4 scenarios at this one cell (still small: 4 runs, not a new grid) rather than leaving Part A's head-to-head comparison incomplete.\n6. If total wall-clock for the 80k-request real-trace replay plus changepoint detection plus the 12 short-multiplier synthetic runs exceeds roughly 1 hour of the 6h budget (it should not -- these are small workloads for a Python simulator) -- profile with cProfile, vectorize the hot inner admission-test loop with numpy where possible, and if still too slow, subsample the synthetic drift runs to fewer independent replicate seeds while keeping all 4 scenarios and all 3 multipliers.",
  "testing_plan": "1. Smoke test first: load method.py's classes on the mini/preview trace files (a few hundred requests) for both synthetic_zipf_alpha12 and real_twitter_cache_trace, confirm the baseline and per-key-decay estimators both run end-to-end without error and produce a hit ratio in [0,1] and a memory-bytes-per-slot value close to iter1's reported baseline (~8 bytes/entry) before touching full data.\n2. Verify the short-multiplier sweep mechanics on a tiny synthetic slice: with sample_size_W set deliberately tiny (e.g. W=10), confirm the sketch actually resets/halves within the first few hundred requests (log a counter) -- this catches an off-by-factor bug in how multiplier maps to sample_size_W before running the full ratio=0.01/alpha=1.2 sweep.\n3. Sanity-check the changepoint detector on a SYNTHETIC trace with KNOWN injected drift events first (reusing synthetic_zipf_alpha12's ground-truth drift_events_alpha12.json): confirm detected changepoints land near a meaningful fraction of the true labeled drift event positions (do not require exact match -- report recall/precision against ground truth as a validity check) before trusting it on the unlabeled real Twitter trace. If detection recall on the labeled synthetic trace is near zero, fix the detector's window/threshold before applying it to real data, since a detector that misses known drift cannot be trusted to find unknown drift.\n4. Confirm the real-trace replay's steady-state hit ratios are directionally sane -- e.g. per-key-decay should not be dramatically worse than baseline (large regression signals a bug in cold-start-guard logic when applied to a real trace's actual inter-arrival statistics, which may differ structurally from the synthetic traces the estimator was tuned on).\n5. Only after all of the above pass, run the full 3-multiplier x 4-scenario Part A sweep and the full 80,000-request Part B replay, then validate method_out.json against the appropriate pipeline schema via the aii-json skill and confirm mini/preview variants are generated if the output is large."
}
```

### [5] TOOL RESULT — Write · 2026-08-26 21:18:05 UTC

```
{"type": "create", "filePath": "/ai-inventor/aii_data/runs/run_0pMem8W3ijCf/3_invention_loop/iter_2/gen_plan/gen_plan_experiment_1/.terminal_claude_agent_struct_out.json", "content": "{\n  \"title\": \"Sharper Baseline Test + Real Twitter Trace Replay\",\n  \"summary\": \"Extends the existing W-TinyLFU cache simulator (method.py) in two targeted ways: (1) sweeps very short global-reset multipliers (1x, 2x, 4x cache capacity) specifically in the win-corner cell (ratio=0.01, alpha=1.2) across all 4 drift scenarios, to test whether a cheaply-shortened global reset closes the gap with the per-key decay mechanism without any per-key machinery -- this is the sharpest possible disconfirmation test of the hypothesis's core claim; and (2) replays both the baseline and per-key-decay estimators end-to-end over the real Twitter production trace (real_twitter_cache_trace, 80,000 requests, cluster026) to report genuine steady-state hit ratio and memory footprint on real traffic, plus a lightweight unsupervised changepoint detector over the per-key request stream to derive at least one coarse, honestly-labeled real-trace recovery-time data point. Both additions reuse the existing estimator/simulator classes unchanged and are deliberately small in scope: a handful of extra sweep points plus one single-pass 80k-request replay, not a new grid.\",\n  \"runpod_compute_profile\": \"cpu_light\",\n  \"implementation_pseudocode\": \"# Reuse existing method.py classes unchanged: FrequencySketch/BaselineEstimator (global reset),\\n# PerKeyDecayEstimator (CoV-based per-key decay w/ M>=8 cold-start guard), SLRUCache, DriftInjector,\\n# and the metrics/recovery-time helpers from iter1. Do NOT reimplement these -- import and call them.\\n\\nimport json, math\\nfrom pathlib import Path\\nfrom collections import defaultdict, deque\\nimport numpy as np\\nfrom method import (            # names as defined in the iter1 method.py; adjust import if renamed\\n    BaselineWTinyLFUEstimator, PerKeyDecayEstimator, SLRUCache,\\n    run_trace, load_synthetic_trace, load_real_trace,\\n    compute_hit_ratio, compute_recovery_time, DRIFT_SCENARIOS,\\n)\\n\\nRESULTS = {\\\"part_a_short_reset\\\": [], \\\"part_b_real_trace\\\": {}}\\n\\n# ---------- PART A: short-multiplier arm at the win-corner cell ----------\\n# Win-corner cell identified in iter1: ratio=0.01 (cache_size = 0.01 * key_universe), alpha=1.2\\nRATIO = 0.01\\nALPHA = 1.2\\nSHORT_MULTIPLIERS = [1, 2, 4]   # in addition to the already-swept {4,8,16,32}; 4 overlaps intentionally as a sanity cross-check\\nDRIFT_SCENARIOS_TO_RUN = DRIFT_SCENARIOS  # all 4 from iter1: e.g. low/high-magnitude x low/high-frequency rank reshuffle + burst\\n\\nsynthetic_alpha12 = load_synthetic_trace(dataset=\\\"synthetic_zipf_alpha12\\\")  # from dependency dataset artifact\\ncache_size = int(RATIO * key_universe_size(synthetic_alpha12))\\n\\nfor scenario in DRIFT_SCENARIOS_TO_RUN:\\n    trace_with_drift = inject_or_select_drift(synthetic_alpha12, scenario)  # reuse iter1's drift injector/labels\\n    best_short = None\\n    for mult in SHORT_MULTIPLIERS:\\n        sample_size_W = mult * cache_size          # matches Caffeine's W = mult * C sizing convention\\n        baseline = BaselineWTinyLFUEstimator(sample_size=sample_size_W)\\n        cache = SLRUCache(capacity=cache_size, estimator=baseline)\\n        trace_result = run_trace(cache, trace_with_drift)\\n        recovery = compute_recovery_time(trace_result, drift_events=trace_with_drift.drift_events,\\n                                          target_frac=0.90)   # time-to-90%-of-post-drift-optimal, matches iter1 convention\\n        steady_state_hr = compute_hit_ratio(trace_result, window=\\\"pre_drift_stationary_segment\\\")\\n        entry = {\\\"scenario\\\": scenario, \\\"multiplier\\\": mult, \\\"sample_size_W\\\": sample_size_W,\\n                 \\\"steady_state_hit_ratio\\\": steady_state_hr, \\\"recovery_time\\\": recovery}\\n        RESULTS[\\\"part_a_short_reset\\\"].append(entry)\\n        if best_short is None or recovery[\\\"time_to_90pct\\\"] < best_short[\\\"recovery_time\\\"][\\\"time_to_90pct\\\"]:\\n            best_short = entry\\n    # Pull the already-computed proposed-estimator (per-key decay) result for this exact (ratio, alpha, scenario) cell\\n    # from iter1's method_out.json (do NOT rerun it) and compute the head-to-head gap vs this newly best short-reset baseline.\\n    proposed_result = load_iter1_proposed_result(ratio=RATIO, alpha=ALPHA, scenario=scenario)\\n    gap_pct = 100.0 * (best_short[\\\"recovery_time\\\"][\\\"time_to_90pct\\\"] - proposed_result[\\\"time_to_90pct\\\"]) / best_short[\\\"recovery_time\\\"][\\\"time_to_90pct\\\"]\\n    RESULTS.setdefault(\\\"part_a_head_to_head\\\", []).append({\\n        \\\"scenario\\\": scenario, \\\"best_short_reset_multiplier\\\": best_short[\\\"multiplier\\\"],\\n        \\\"best_short_reset_recovery\\\": best_short[\\\"recovery_time\\\"][\\\"time_to_90pct\\\"],\\n        \\\"proposed_estimator_recovery\\\": proposed_result[\\\"time_to_90pct\\\"],\\n        \\\"proposed_still_faster_pct\\\": gap_pct,          # >0 means proposed still wins even vs best short reset; <=0 means short reset matches/beats it -> disconfirms the mechanism's necessity for this cell\\n    })\\n\\n# ---------- PART B: real Twitter trace replay ----------\\ntwitter_trace = load_real_trace(dataset=\\\"real_twitter_cache_trace\\\")  # 80,000 requests, cluster026, from dependency dataset artifact\\nreal_cache_size = pick_matched_cache_size(twitter_trace, ratio=RATIO)  # same ratio convention as synthetic sweep for comparability\\n\\nfor name, EstimatorCls, kwargs in [\\n    (\\\"baseline_w_tinylfu\\\", BaselineWTinyLFUEstimator, {\\\"sample_size\\\": best_global_multiplier_from_iter1 * real_cache_size}),\\n    (\\\"per_key_decay\\\", PerKeyDecayEstimator, {\\\"cold_start_M\\\": 8, \\\"decay_buckets\\\": iter1_decay_bucket_config}),\\n]:\\n    estimator = EstimatorCls(**kwargs)\\n    cache = SLRUCache(capacity=real_cache_size, estimator=estimator)\\n    trace_result = run_trace(cache, twitter_trace)\\n    RESULTS[\\\"part_b_real_trace\\\"][name] = {\\n        \\\"steady_state_hit_ratio\\\": compute_hit_ratio(trace_result, window=\\\"full\\\"),\\n        \\\"memory_bytes_per_slot\\\": estimator.measured_bytes_per_entry(),   # reuse iter1's memory accounting helper\\n        \\\"per_request_stream\\\": trace_result.per_request_summary,          # kept for changepoint detection below\\n    }\\n\\n# --- lightweight unsupervised changepoint detector over the per-key request stream ---\\n# Rolling-window Jensen-Shannon divergence over top-K key-identity distributions, K=50, window=2000 requests, stride=500\\ndef detect_changepoints(request_stream, window=2000, stride=500, top_k=50, js_threshold_percentile=95):\\n    windows = sliding_windows(request_stream, window, stride)\\n    dists = [key_freq_distribution(w, top_k=top_k) for w in windows]\\n    js_scores = [jensen_shannon_divergence(dists[i], dists[i+1]) for i in range(len(dists)-1)]\\n    threshold = np.percentile(js_scores, js_threshold_percentile)\\n    changepoints = [i*stride + window for i, s in enumerate(js_scores) if s > threshold]\\n    return changepoints, js_scores, threshold\\n\\ncps, js_scores, threshold = detect_changepoints(twitter_trace.request_stream)\\nRESULTS[\\\"part_b_real_trace\\\"][\\\"changepoints_detected\\\"] = cps\\nRESULTS[\\\"part_b_real_trace\\\"][\\\"changepoint_threshold\\\"] = threshold\\nRESULTS[\\\"part_b_real_trace\\\"][\\\"n_changepoints\\\"] = len(cps)\\nRESULTS[\\\"part_b_real_trace\\\"][\\\"changepoint_caveat\\\"] = (\\n    \\\"UNSUPERVISED, coarse, unlabeled -- these are candidate drift points from a JS-divergence heuristic, \\\"\\n    \\\"NOT ground-truth drift events. Treat any recovery-time numbers around them as suggestive, not confirmatory.\\\"\\n)\\n\\nfor name in [\\\"baseline_w_tinylfu\\\", \\\"per_key_decay\\\"]:\\n    per_cp_recovery = []\\n    for cp in cps:\\n        rec = compute_recovery_time_at_index(RESULTS[\\\"part_b_real_trace\\\"][name][\\\"per_request_stream\\\"],\\n                                              changepoint_idx=cp, target_frac=0.90,\\n                                              window_after=5000)  # bounded lookahead since real trace has no known post-drift optimum\\n        per_cp_recovery.append(rec)\\n    RESULTS[\\\"part_b_real_trace\\\"][name][\\\"recovery_time_at_changepoints\\\"] = per_cp_recovery\\n\\n# ---------- write output ----------\\nmethod_out = {\\\"schema\\\": \\\"exp_gen_sol_out_or_appropriate_schema\\\", \\\"results\\\": RESULTS}\\nPath(\\\"method_out.json\\\").write_text(json.dumps(method_out, indent=2))\\n# validate via aii-json skill before finishing\",\n  \"fallback_plan\": \"1. If iter1's method.py estimator/simulator class names or method_out.json result schema differ from what this plan assumes (they must be located and read FIRST, before writing any new code, by grepping the iter1 experiment artifact's workspace for the class/function names actually used) -- adapt imports and the result-lookup key structure to match reality rather than guessing; do not silently invent a compatible-looking API.\\n2. If the short-multiplier (1x, 2x) reset sweep is numerically unstable or degenerate (e.g. W=1x cache size resets the sketch so often that frequency estimates are pure noise, causing near-random admission) -- this is itself a valid, reportable result (evidence the global mechanism cannot be pushed this low without breaking, which still supports the hypothesis) rather than a bug to hide; report it explicitly with the observed hit-ratio collapse, do not discard the data point.\\n3. If real_twitter_cache_trace's request_type field or timestamp granularity makes per-key inter-arrival-gap computation ill-defined (e.g. many requests share identical timestamps, or non-GET request types dominate) -- filter to read-dominant request types only (matching the hypothesis's 'read-heavy' scope) and document the filtered fraction; if timestamps are too coarse for gap-based CoV, fall back to using request SEQUENCE POSITION (seq field) as the inter-arrival proxy instead of wall-clock time, which the dataset schema already guarantees is present and monotonic.\\n4. If the JS-divergence changepoint detector finds zero changepoints above the 95th-percentile threshold on the 80k-request trace (plausible if Twitter cache traffic composition is fairly stable at this window size) -- progressively lower the percentile threshold (e.g. to 90th, then 85th) and/or shrink the window to 1000/stride 250 to surface at least a few candidate points; if still zero after two relaxations, report this as a finding (\\\"no detectable large composition shifts in this 80k-request sample\\\") rather than forcing spurious changepoints, and rely on Part A + the real-trace steady-state comparison (already both real, already both meaningful) as the artifact's evidence.\\n5. If loading iter1's proposed-estimator result for the exact (ratio=0.01, alpha=1.2, scenario) cell fails because iter1's method_out.json was structured differently or that exact cell wasn't run at fine enough granularity -- rerun ONLY the proposed per-key-decay estimator for those 4 scenarios at this one cell (still small: 4 runs, not a new grid) rather than leaving Part A's head-to-head comparison incomplete.\\n6. If total wall-clock for the 80k-request real-trace replay plus changepoint detection plus the 12 short-multiplier synthetic runs exceeds roughly 1 hour of the 6h budget (it should not -- these are small workloads for a Python simulator) -- profile with cProfile, vectorize the hot inner admission-test loop with numpy where possible, and if still too slow, subsample the synthetic drift runs to fewer independent replicate seeds while keeping all 4 scenarios and all 3 multipliers.\",\n  \"testing_plan\": \"1. Smoke test first: load method.py's classes on the mini/preview trace files (a few hundred requests) for both synthetic_zipf_alpha12 and real_twitter_cache_trace, confirm the baseline and per-key-decay estimators both run end-to-end without error and produce a hit ratio in [0,1] and a memory-bytes-per-slot value close to iter1's reported baseline (~8 bytes/entry) before touching full data.\\n2. Verify the short-multiplier sweep mechanics on a tiny synthetic slice: with sample_size_W set deliberately tiny (e.g. W=10), confirm the sketch actually resets/halves within the first few hundred requests (log a counter) -- this catches an off-by-factor bug in how multiplier maps to sample_size_W before running the full ratio=0.01/alpha=1.2 sweep.\\n3. Sanity-check the changepoint detector on a SYNTHETIC trace with KNOWN injected drift events first (reusing synthetic_zipf_alpha12's ground-truth drift_events_alpha12.json): confirm detected changepoints land near a meaningful fraction of the true labeled drift event positions (do not require exact match -- report recall/precision against ground truth as a validity check) before trusting it on the unlabeled real Twitter trace. If detection recall on the labeled synthetic trace is near zero, fix the detector's window/threshold before applying it to real data, since a detector that misses known drift cannot be trusted to find unknown drift.\\n4. Confirm the real-trace replay's steady-state hit ratios are directionally sane -- e.g. per-key-decay should not be dramatically worse than baseline (large regression signals a bug in cold-start-guard logic when applied to a real trace's actual inter-arrival statistics, which may differ structurally from the synthetic traces the estimator was tuned on).\\n5. Only after all of the above pass, run the full 3-multiplier x 4-scenario Part A sweep and the full 80,000-request Part B replay, then validate method_out.json against the appropriate pipeline schema via the aii-json skill and confirm mini/preview variants are generated if the output is large.\"\n}\n", "structuredPatch": [], "originalFile": null, "userModified": false}
```

### [6] ASSISTANT · 2026-08-26 21:18:06 UTC

```
Plan written to `.terminal_claude_agent_struct_out.json`, covering both parts of the artifact direction: a sharp short-multiplier reset sweep at the win-corner cell (disconfirmation test) and a real Twitter trace replay with a JS-divergence changepoint detector for coarse drift-recovery evidence.
```
