# gen_plan_experiment_1 — test_idea

> Phase: `invention_loop` · round 1 · `gen_plan`
> Run: `iter1_eb86f00c4c5a` — Why Per-Key Cache Decay Rarely Beats a Cheaper Shorter Reset
>
> Full, verbatim transcript of this agent task — every system/user prompt, assistant response, thinking block, tool call and tool result — in the order they occurred. Nothing truncated.

## Task: `gen_plan_experiment_1` (terminal_claude_agent, claude-sonnet-5)

### [1] CONFIG · 2026-08-26 20:04:50 UTC

```
model: claude-sonnet-5 | effort: low | permission: bypassPermissions | cwd: /ai-inventor/aii_data/runs/run_0pMem8W3ijCf/3_invention_loop/iter_1/gen_plan/gen_plan_experiment_1
```

### [2] SYSTEM-USER prompt · 2026-08-26 20:04:58 UTC

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
  Shadow-Queue Admission with Recency-Decayed Frequency Sketches for Skewed Read-Heavy Key-Value Caches
hypothesis: >-
  In a read-heavy key-value store with Zipf-skewed key popularity and a bursty, non-stationary component (popularity ranks
  that drift or spike over time), an admission policy that combines (a) a compact shadow-queue ghost-cache simulating the
  marginal hit-rate gain of admitting the current miss (as in TinyLFU/W-TinyLFU) with (b) a frequency estimate that exponentially
  decays old counts at a per-key-class-tuned half-life (rather than TinyLFU's periodic global halving of the whole Count-Min
  sketch) will achieve a higher steady-state hit ratio AND a faster adaptation time to popularity drift than admission based
  on static/global-decay frequency estimation alone, at comparable memory overhead. The mechanism: global periodic halving
  forgets all keys at the same rate, so it is forced to trade off between remembering long-lived popular keys (long window)
  and reacting to newly-trending keys (short window); a per-key-class decay rate — inferred cheaply from each key's own inter-arrival
  variance in the shadow queue — lets stable heavy hitters keep long memory while volatile/bursty keys get a short one, without
  needing two separately-sized sketches or an oracle labeling of which keys are which.
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

id: experiment_iter1_dir2
type: experiment
objective: >-
  Implement a cache admission simulator with two competing frequency-decay mechanisms sharing identical scaffolding (doorkeeper,
  shadow-queue admission test, SLRU eviction, matched sketch width), and run both over every trace in the dataset at swept
  cache-size-to-key-space ratios, recording hit-ratio time series and per-mechanism memory footprint.
approach: >-
  Implement (1) the W-TinyLFU baseline exactly per Caffeine's FrequencySketch semantics: 4-bit Count-Min-style counters, a
  shared size counter incrementing on every access, global `table[i] = (table[i] >>> 1) & mask` halving of the ENTIRE sketch
  once size reaches sampleSize (sweep sampleSize/W as a tunable baseline, since success_criteria requires comparing against
  the *best* tuned global-reset period), plus doorkeeper Bloom filter and SLRU (protected/probationary) eviction; and (2)
  the proposed variant, identical except each shadow-queue entry additionally tracks a short rolling window of inter-arrival
  gaps, computes a coefficient-of-variation-based volatility score, buckets it into a small number of decay-rate tiers, and
  applies that key's own decay rate to its frequency counter instead of the global reset (implemented as per-key floating-point
  EMA counters or per-bucket independent Count-Min sketches with different halving periods, whichever keeps memory within
  ~2x of baseline). Run both mechanisms over every dataset trace at 2-3 cache-size-to-key-space ratios and 3+ skew levels,
  log hit/miss per request and admission-test decisions, and record total bytes used by each mechanism's state (sketch + doorkeeper
  + shadow queue + any added per-key decay state) for the memory-overhead check.
depends_on: []
</artifact_direction>



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

### [3] HUMAN-USER prompt · 2026-08-26 20:04:58 UTC

```
Cache admission policies for skewed key popularity in read-heavy key-value stores
```

### [4] TOOL CALL — Write · 2026-08-26 20:06:08 UTC

```
File: /ai-inventor/aii_data/runs/run_0pMem8W3ijCf/3_invention_loop/iter_1/gen_plan/gen_plan_experiment_1/.terminal_claude_agent_struct_out.json

{
  "title": "Per-Key Decay vs Global TinyLFU Reset",
  "summary": "Build a cache-admission simulator implementing W-TinyLFU (Caffeine-faithful global sketch halving) and a per-key inter-arrival-volatility-decayed variant, sharing identical doorkeeper/shadow-queue/SLRU scaffolding, and compare steady-state hit ratio, memory footprint, and drift-recovery speed across synthetic Zipf(+drift) traces and a real trace at swept cache ratios and skew levels.",
  "runpod_compute_profile": "cpu_heavy",
  "implementation_pseudocode": "# ============================================================\n# FILE LAYOUT\n#   sketch.py        - CountMin4Bit sketch, doorkeeper, both decay mechanisms\n#   cache_sim.py      - SLRU eviction + admission-test driven simulator loop\n#   traces.py         - synthetic Zipf+drift generator, real trace loader/adapter\n#   run_experiment.py - sweep driver, logging, method_out.json writer\n#   aii_python + aii_parallel_computing skills: use loguru, pathlib, ProcessPoolExecutor\n# ============================================================\n\n# ---- 1. CountMin4Bit sketch (shared building block) ----\nclass CountMin4Bit:\n    # width = 4 * cache_capacity (per TinyLFU sizing guidance W/C=8 -> total counters ~ 4x slots x 4 hashes... )\n    # depth = 4 hash functions (standard TinyLFU choice), 4-bit counters packed into a byte array (2 counters/byte)\n    def __init__(self, num_counters, depth=4, seed_list):\n        self.table = bytearray(num_counters // 2)   # 4-bit packed\n        self.hashes = [make_hash(seed) for seed in seed_list]\n    def increment(self, key): ...        # cap at 15 (4-bit max), min-increment across depth rows (conservative update)\n    def estimate(self, key) -> int: ...  # min across depth rows\n    def halve_all(self):                 # GLOBAL baseline mechanism\n        for i in range(len(self.table)):\n            self.table[i] = ((self.table[i] >> 1) & 0x77)  # halve both nibbles, mask high bits (Caffeine RESET_MASK equiv)\n\nclass Doorkeeper:\n    # 1-bit Bloom filter, cleared alongside sketch reset (matches Caffeine: doorkeeper reset on same schedule)\n    def __init__(self, num_bits, num_hashes=1): ...\n    def maybe_add(self, key) -> bool: ...  # returns True if key was NOT already present (first-touch protection)\n    def contains(self, key) -> bool: ...\n    def clear(self): ...\n\n# ---- 2. BASELINE: W-TinyLFU admission filter, Caffeine-faithful ----\nclass GlobalResetFrequencyEstimator:\n    def __init__(self, cache_capacity, sample_size_multiplier):  # sweep multiplier in {4, 8, 16, 32} as 'tuned' grid\n        self.sketch = CountMin4Bit(num_counters=4 * cache_capacity)\n        self.doorkeeper = Doorkeeper(num_bits=cache_capacity * 8)\n        self.sample_size = sample_size_multiplier * cache_capacity  # W = multiplier * C, per TinyLFU sizing formula\n        self.size = 0\n    def record_access(self, key):\n        if self.doorkeeper.maybe_add(key):\n            pass  # first touch: doorkeeper absorbs it, sketch not incremented (matches Caffeine's addAndSample)\n        else:\n            self.sketch.increment(key)\n        self.size += 1\n        if self.size >= self.sample_size:\n            self.sketch.halve_all()\n            self.doorkeeper.clear()\n            self.size = 0\n    def frequency(self, key):\n        base = self.sketch.estimate(key)\n        return base + (15 if self.doorkeeper.contains(key) else 0)  # Caffeine adds doorkeeper bit as +1 tier; use consistent tie-break, document exact formula used\n\n# ---- 3. PROPOSED: per-key decay via inter-arrival volatility ----\nclass PerKeyDecayFrequencyEstimator:\n    # Implementation choice (memory-bounded to ~2x baseline): K independently-halved Count-Min sketches ('tiers'),\n    # each with its OWN sample_size (decay half-life), plus a small per-shadow-queue-entry hash map tracking:\n    #   last_timestamp, ewma_gap, ewma_gap_sq (for CoV), assigned_tier\n    # Only keys currently resident in the shadow queue (bounded size, e.g. 2x cache_capacity) get per-key tracking;\n    # keys that fall out of the shadow queue revert to tier-0 (default/short) on re-entry -> bounds memory.\n    TIERS = [ (2, 'volatile'), (8, 'default'), (32, 'stable') ]  # (sample_size_multiplier, label); pick 3 tiers\n    def __init__(self, cache_capacity, shadow_queue_capacity):\n        self.tier_sketches = [CountMin4Bit(4*cache_capacity) for _ in self.TIERS]\n        self.tier_samplesize = [m * cache_capacity for m,_ in self.TIERS]\n        self.tier_size = [0]*len(self.TIERS)\n        self.doorkeeper = Doorkeeper(cache_capacity * 8)\n        self.shadow_meta = LRUDict(capacity=shadow_queue_capacity)  # key -> (last_ts, ewma_gap, ewma_gap_sq, tier_idx, n_obs)\n        self.global_clock = 0\n    def _classify(self, ewma_gap, ewma_gap_sq, n_obs):\n        if n_obs < 3: return 1  # not enough signal -> default tier\n        var = max(ewma_gap_sq - ewma_gap**2, 0.0)\n        cov = (var**0.5) / max(ewma_gap, 1e-6)\n        if cov > COV_HIGH_THRESH: return 0   # bursty/volatile -> short half-life\n        if cov < COV_LOW_THRESH:  return 2   # regular/steady -> long half-life\n        return 1\n    def record_access(self, key):\n        self.global_clock += 1\n        meta = self.shadow_meta.get(key)\n        if meta is None:\n            tier = 1  # unseen key starts at default tier\n            self.shadow_meta.put(key, (self.global_clock, 0.0, 0.0, tier, 1))\n        else:\n            last_ts, ewma_gap, ewma_gap_sq, tier, n_obs = meta\n            gap = self.global_clock - last_ts\n            alpha = 0.3  # EWMA smoothing constant for the gap statistics themselves (fixed, document choice)\n            ewma_gap = alpha*gap + (1-alpha)*ewma_gap if n_obs>0 else gap\n            ewma_gap_sq = alpha*(gap**2) + (1-alpha)*ewma_gap_sq if n_obs>0 else gap**2\n            n_obs += 1\n            tier = self._classify(ewma_gap, ewma_gap_sq, n_obs)\n            self.shadow_meta.put(key, (self.global_clock, ewma_gap, ewma_gap_sq, tier, n_obs))\n        if self.doorkeeper.maybe_add(key):\n            pass\n        else:\n            self.tier_sketches[tier].increment(key)\n            self.tier_size[tier] += 1\n            if self.tier_size[tier] >= self.tier_samplesize[tier]:\n                self.tier_sketches[tier].halve_all()\n                self.tier_size[tier] = 0\n    def frequency(self, key):\n        meta = self.shadow_meta.get(key)\n        tier = meta[3] if meta else 1\n        base = self.tier_sketches[tier].estimate(key)\n        return base + (15 if self.doorkeeper.contains(key) else 0)\n\n# ---- 4. SLRU eviction (identical for both systems) ----\nclass SLRUCache:\n    # protected_capacity = 0.8 * capacity, probationary_capacity = 0.2 * capacity (standard Caffeine ratio)\n    def get(self, key): ...      # promote to MRU of protected on hit, else miss\n    def admit_candidate(self, key): ...  # inserts into probationary MRU; evicts probationary LRU if full\n    def victim_for_admission_test(self) -> key: ...  # probationary LRU is the comparison victim\n\n# ---- 5. Simulator loop (shared driver, mechanism is pluggable) ----\ndef run_trace(trace, cache_capacity, estimator, window_admission_frac=0.01):\n    slru = SLRUCache(capacity=cache_capacity)\n    window_admitter = LRUWindow(capacity=int(window_admission_frac*cache_capacity))  # W-TinyLFU small admission window\n    hits, total = 0, 0\n    hit_series = []  # (request_idx, rolling_hit_ratio) sampled every N requests, for recovery-curve analysis\n    for i, key in enumerate(trace):\n        total += 1\n        estimator.record_access(key)\n        if slru.get(key) is not None:\n            hits += 1\n        else:\n            if window_admitter.contains(key):\n                hits += 1  # counts as hit path per W-TinyLFU semantics only if actually cached; else treat as admission via window\n            candidate_freq = estimator.frequency(key)\n            victim = slru.victim_for_admission_test()\n            if victim is None or candidate_freq > estimator.frequency(victim):\n                slru.admit_candidate(key)\n            else:\n                window_admitter.admit(key)\n        if i % 1000 == 0:\n            hit_series.append((i, hits/total))\n    return {'hit_series': hit_series, 'final_hit_ratio': hits/total,\n            'memory_bytes': estimator_memory_bytes(estimator) + slru_memory_bytes(slru)}\n\n# ---- 6. Trace generation ----\ndef make_zipf_drift_trace(n_requests, key_space, alpha, n_drift_events, drift_magnitude, burst_prob, seed):\n    # base: sample from Zipf(alpha) rank->key mapping over key_space\n    # every n_requests/(n_drift_events+1) steps: reshuffle drift_magnitude fraction of top ranks to new random keys\n    # additionally: with burst_prob, pick a previously-cold key and inject a short burst window (e.g. 200 consecutive/near-consecutive requests)\n    # RECORD drift event indices explicitly -> needed for recovery-time metric\n    ...\n\ndef load_real_trace():\n    # search for a public trace via aii-hf-datasets / aii-web-tools first: e.g. a published CDN/memcached/Twitter-cache\n    # trace commonly used in caching papers (search terms: \"memcached trace dataset\", \"Twitter cache trace github twitter/cache-trace\",\n    # \"CDN access log trace research\", \"Wikipedia page view trace cache simulator\"). If a suitable one is found and fetchable\n    # within budget, download and adapt to (timestamp, key) request stream. If NOT found/fetchable in time, SKIP the real-trace\n    # arm entirely and note this explicitly in method_out.json -- do not fabricate a 'real' trace.\n    ...\n\n# ---- 7. Sweep driver ----\nCACHE_RATIOS = [0.001, 0.01, 0.1]       # cache_capacity / key_space\nSKEW_LEVELS = [0.8, 1.0, 1.2, 1.5]      # Zipf alpha\nSAMPLE_MULTIPLIERS = [4, 8, 16, 32]     # baseline W/C sweep -> pick best per (ratio, skew) on stationary portion\nDRIFT_SCENARIOS = [ (low_mag, low_freq), (low_mag, high_freq), (high_mag, low_freq), (high_mag, high_freq) ]\n\nfor ratio in CACHE_RATIOS:\n  for alpha in SKEW_LEVELS:\n    key_space = 200_000  # fixed; cache_capacity = ratio * key_space\n    # Phase A: stationary-only trace, sweep SAMPLE_MULTIPLIERS for baseline -> pick best (lowest cache misses) as 'tuned baseline'\n    # Phase B: for the tuned baseline AND the per-key variant, run each of DRIFT_SCENARIOS x [synthetic seeds x3]\n    #   record hit_series, drift-event indices, memory_bytes\n    # Phase C (if real trace available): run tuned baseline + variant once each, same metrics\n    for drift_scenario in DRIFT_SCENARIOS:\n      for seed in [1,2,3]:\n        trace, drift_indices = make_zipf_drift_trace(..., seed=seed)\n        result_baseline = run_trace(trace, cache_capacity, GlobalResetFrequencyEstimator(cache_capacity, best_multiplier))\n        result_proposed = run_trace(trace, cache_capacity, PerKeyDecayFrequencyEstimator(cache_capacity, shadow_queue_capacity=2*cache_capacity))\n        # recovery time: for each drift_indices[j], find first index after it where rolling hit ratio >= 0.9 * post-drift-optimal\n        #   (post-drift-optimal estimated as the hit ratio plateau reached by whichever of the two mechanisms converges highest\n        #    over the next K requests, OR precomputed from the trace's true post-drift Zipf entropy -- document exact definition used)\n        log_result(ratio, alpha, drift_scenario, seed, result_baseline, result_proposed)\n\n# ---- 8. Statistics & output ----\n# Bootstrap CIs (1000 resamples over seeds) for: steady-state hit-ratio delta, recovery-time ratio (proposed/baseline)\n# Aggregate: fraction of (ratio x alpha x drift_scenario) cells where proposed wins by >=20% faster recovery with CI excl. 0\n# Write method_out.json: {config_grid_results: [...], summary_stats: {...}, memory_footprint_table: {...}, real_trace_results: {...} or null}\n",
  "fallback_plan": "If no suitable public real-world cache-access trace can be found/downloaded within the time budget (search HuggingFace datasets, GitHub repos for memcached/Twitter/CDN traces, and academic caching-paper artifact pages via aii-web-tools/aii-hf-datasets before giving up), proceed with synthetic traces only (Zipf + drift + bursts) across a wider sweep of alpha and drift parameters to compensate for losing trace diversity, and explicitly report in method_out.json that the real-trace arm of success_criteria was not evaluable and why. If the coefficient-of-variation-based per-key classification produces degenerate results (e.g., nearly all keys land in one tier, or classification is too noisy with few observations), fall back to a simpler 2-tier scheme (volatile vs stable, dropping the middle 'default' tier) and/or increase the EWMA smoothing window before declaring the mechanism itself a failure — report both the 3-tier and 2-tier results if time permits. If the K-sketch-tier implementation exceeds the ~2x memory budget at the swept cache ratios, switch the proposed variant's frequency storage to per-key floating-point EMA counters stored directly in the shadow-queue hash map (bounded by shadow_queue_capacity) instead of K parallel Count-Min sketches — this trades some hashing collision-robustness for a hard memory cap and should be implemented as an alternate PerKeyDecayFrequencyEstimator subclass so both variants can be compared if time allows. If runtime is too slow in pure Python for the full sweep (key_space=200k x n_requests likely in the millions), first try numpy-vectorizing the sketch counter updates and reduce N_REQUESTS/seeds per cell (e.g., 2 seeds instead of 3, or drop the largest cache_ratio) before cutting scenarios entirely — log explicitly which cells were skipped and why, never silently truncate the grid.",
  "testing_plan": "1) Unit-test CountMin4Bit and Doorkeeper alone: increment a handful of known keys different numbers of times, verify estimate() returns correct sketch-theoretic bounds (never underestimates true count on stationary synthetic input of ~1000 requests over 20 keys) and halve_all() actually roughly halves observed estimates. 2) Unit-test SLRU: feed a short deterministic sequence (e.g. hand-constructed 20-key access pattern) and manually verify hit/miss and eviction order match expected LRU/SLRU behavior. 3) Sanity-check GlobalResetFrequencyEstimator against a tiny (key_space=1000, n_requests=50000) stationary Zipf(alpha=1.0) trace at cache_ratio=0.05 — confirm hit ratio is in a plausible range (roughly 40-70% for these params, compare qualitatively against published Caffeine simulator hit-ratio curves for similar Zipf/ratio settings if found via web search) before trusting the full pipeline. 4) Confirm PerKeyDecayFrequencyEstimator recovers the SAME order-of-magnitude hit ratio as the baseline on a purely stationary trace (this is the success_criteria's own regression check, e.g. within ~1-2 percentage points) BEFORE testing drift scenarios — if steady-state already diverges wildly, debug the tiering/classification logic first rather than proceeding to drift experiments. 5) Sanity-check the drift-injection trace generator by plotting/inspecting the empirical top-20 key frequency before and after a drift event on a small trace (e.g. n_requests=20000) to confirm ranks actually reshuffle as intended and bursts are visible as request-count spikes for the targeted cold key. 6) Run one full drift scenario (one seed, one ratio, one alpha) end-to-end for both mechanisms and manually inspect the hit_series plot / recovery-time computation on that single run to confirm the recovery-time metric behaves sensibly (post-drift dip visible, recovery point falls after the dip, not before) before launching the full sweep across all ratios/alphas/scenarios/seeds. 7) Only after all of the above pass, launch the full grid sweep using the aii-long-running-tasks staged-scaling pattern (start with 1 seed x reduced grid, extrapolate time, then scale to full 3-seed x full grid) to stay within the 6-hour executor budget, checking elapsed time after each stage before committing to the next."
}
```

### [5] TOOL RESULT — Write · 2026-08-26 20:06:08 UTC

```
{"type": "create", "filePath": "/ai-inventor/aii_data/runs/run_0pMem8W3ijCf/3_invention_loop/iter_1/gen_plan/gen_plan_experiment_1/.terminal_claude_agent_struct_out.json", "content": "{\n  \"title\": \"Per-Key Decay vs Global TinyLFU Reset\",\n  \"summary\": \"Build a cache-admission simulator implementing W-TinyLFU (Caffeine-faithful global sketch halving) and a per-key inter-arrival-volatility-decayed variant, sharing identical doorkeeper/shadow-queue/SLRU scaffolding, and compare steady-state hit ratio, memory footprint, and drift-recovery speed across synthetic Zipf(+drift) traces and a real trace at swept cache ratios and skew levels.\",\n  \"runpod_compute_profile\": \"cpu_heavy\",\n  \"implementation_pseudocode\": \"# ============================================================\\n# FILE LAYOUT\\n#   sketch.py        - CountMin4Bit sketch, doorkeeper, both decay mechanisms\\n#   cache_sim.py      - SLRU eviction + admission-test driven simulator loop\\n#   traces.py         - synthetic Zipf+drift generator, real trace loader/adapter\\n#   run_experiment.py - sweep driver, logging, method_out.json writer\\n#   aii_python + aii_parallel_computing skills: use loguru, pathlib, ProcessPoolExecutor\\n# ============================================================\\n\\n# ---- 1. CountMin4Bit sketch (shared building block) ----\\nclass CountMin4Bit:\\n    # width = 4 * cache_capacity (per TinyLFU sizing guidance W/C=8 -> total counters ~ 4x slots x 4 hashes... )\\n    # depth = 4 hash functions (standard TinyLFU choice), 4-bit counters packed into a byte array (2 counters/byte)\\n    def __init__(self, num_counters, depth=4, seed_list):\\n        self.table = bytearray(num_counters // 2)   # 4-bit packed\\n        self.hashes = [make_hash(seed) for seed in seed_list]\\n    def increment(self, key): ...        # cap at 15 (4-bit max), min-increment across depth rows (conservative update)\\n    def estimate(self, key) -> int: ...  # min across depth rows\\n    def halve_all(self):                 # GLOBAL baseline mechanism\\n        for i in range(len(self.table)):\\n            self.table[i] = ((self.table[i] >> 1) & 0x77)  # halve both nibbles, mask high bits (Caffeine RESET_MASK equiv)\\n\\nclass Doorkeeper:\\n    # 1-bit Bloom filter, cleared alongside sketch reset (matches Caffeine: doorkeeper reset on same schedule)\\n    def __init__(self, num_bits, num_hashes=1): ...\\n    def maybe_add(self, key) -> bool: ...  # returns True if key was NOT already present (first-touch protection)\\n    def contains(self, key) -> bool: ...\\n    def clear(self): ...\\n\\n# ---- 2. BASELINE: W-TinyLFU admission filter, Caffeine-faithful ----\\nclass GlobalResetFrequencyEstimator:\\n    def __init__(self, cache_capacity, sample_size_multiplier):  # sweep multiplier in {4, 8, 16, 32} as 'tuned' grid\\n        self.sketch = CountMin4Bit(num_counters=4 * cache_capacity)\\n        self.doorkeeper = Doorkeeper(num_bits=cache_capacity * 8)\\n        self.sample_size = sample_size_multiplier * cache_capacity  # W = multiplier * C, per TinyLFU sizing formula\\n        self.size = 0\\n    def record_access(self, key):\\n        if self.doorkeeper.maybe_add(key):\\n            pass  # first touch: doorkeeper absorbs it, sketch not incremented (matches Caffeine's addAndSample)\\n        else:\\n            self.sketch.increment(key)\\n        self.size += 1\\n        if self.size >= self.sample_size:\\n            self.sketch.halve_all()\\n            self.doorkeeper.clear()\\n            self.size = 0\\n    def frequency(self, key):\\n        base = self.sketch.estimate(key)\\n        return base + (15 if self.doorkeeper.contains(key) else 0)  # Caffeine adds doorkeeper bit as +1 tier; use consistent tie-break, document exact formula used\\n\\n# ---- 3. PROPOSED: per-key decay via inter-arrival volatility ----\\nclass PerKeyDecayFrequencyEstimator:\\n    # Implementation choice (memory-bounded to ~2x baseline): K independently-halved Count-Min sketches ('tiers'),\\n    # each with its OWN sample_size (decay half-life), plus a small per-shadow-queue-entry hash map tracking:\\n    #   last_timestamp, ewma_gap, ewma_gap_sq (for CoV), assigned_tier\\n    # Only keys currently resident in the shadow queue (bounded size, e.g. 2x cache_capacity) get per-key tracking;\\n    # keys that fall out of the shadow queue revert to tier-0 (default/short) on re-entry -> bounds memory.\\n    TIERS = [ (2, 'volatile'), (8, 'default'), (32, 'stable') ]  # (sample_size_multiplier, label); pick 3 tiers\\n    def __init__(self, cache_capacity, shadow_queue_capacity):\\n        self.tier_sketches = [CountMin4Bit(4*cache_capacity) for _ in self.TIERS]\\n        self.tier_samplesize = [m * cache_capacity for m,_ in self.TIERS]\\n        self.tier_size = [0]*len(self.TIERS)\\n        self.doorkeeper = Doorkeeper(cache_capacity * 8)\\n        self.shadow_meta = LRUDict(capacity=shadow_queue_capacity)  # key -> (last_ts, ewma_gap, ewma_gap_sq, tier_idx, n_obs)\\n        self.global_clock = 0\\n    def _classify(self, ewma_gap, ewma_gap_sq, n_obs):\\n        if n_obs < 3: return 1  # not enough signal -> default tier\\n        var = max(ewma_gap_sq - ewma_gap**2, 0.0)\\n        cov = (var**0.5) / max(ewma_gap, 1e-6)\\n        if cov > COV_HIGH_THRESH: return 0   # bursty/volatile -> short half-life\\n        if cov < COV_LOW_THRESH:  return 2   # regular/steady -> long half-life\\n        return 1\\n    def record_access(self, key):\\n        self.global_clock += 1\\n        meta = self.shadow_meta.get(key)\\n        if meta is None:\\n            tier = 1  # unseen key starts at default tier\\n            self.shadow_meta.put(key, (self.global_clock, 0.0, 0.0, tier, 1))\\n        else:\\n            last_ts, ewma_gap, ewma_gap_sq, tier, n_obs = meta\\n            gap = self.global_clock - last_ts\\n            alpha = 0.3  # EWMA smoothing constant for the gap statistics themselves (fixed, document choice)\\n            ewma_gap = alpha*gap + (1-alpha)*ewma_gap if n_obs>0 else gap\\n            ewma_gap_sq = alpha*(gap**2) + (1-alpha)*ewma_gap_sq if n_obs>0 else gap**2\\n            n_obs += 1\\n            tier = self._classify(ewma_gap, ewma_gap_sq, n_obs)\\n            self.shadow_meta.put(key, (self.global_clock, ewma_gap, ewma_gap_sq, tier, n_obs))\\n        if self.doorkeeper.maybe_add(key):\\n            pass\\n        else:\\n            self.tier_sketches[tier].increment(key)\\n            self.tier_size[tier] += 1\\n            if self.tier_size[tier] >= self.tier_samplesize[tier]:\\n                self.tier_sketches[tier].halve_all()\\n                self.tier_size[tier] = 0\\n    def frequency(self, key):\\n        meta = self.shadow_meta.get(key)\\n        tier = meta[3] if meta else 1\\n        base = self.tier_sketches[tier].estimate(key)\\n        return base + (15 if self.doorkeeper.contains(key) else 0)\\n\\n# ---- 4. SLRU eviction (identical for both systems) ----\\nclass SLRUCache:\\n    # protected_capacity = 0.8 * capacity, probationary_capacity = 0.2 * capacity (standard Caffeine ratio)\\n    def get(self, key): ...      # promote to MRU of protected on hit, else miss\\n    def admit_candidate(self, key): ...  # inserts into probationary MRU; evicts probationary LRU if full\\n    def victim_for_admission_test(self) -> key: ...  # probationary LRU is the comparison victim\\n\\n# ---- 5. Simulator loop (shared driver, mechanism is pluggable) ----\\ndef run_trace(trace, cache_capacity, estimator, window_admission_frac=0.01):\\n    slru = SLRUCache(capacity=cache_capacity)\\n    window_admitter = LRUWindow(capacity=int(window_admission_frac*cache_capacity))  # W-TinyLFU small admission window\\n    hits, total = 0, 0\\n    hit_series = []  # (request_idx, rolling_hit_ratio) sampled every N requests, for recovery-curve analysis\\n    for i, key in enumerate(trace):\\n        total += 1\\n        estimator.record_access(key)\\n        if slru.get(key) is not None:\\n            hits += 1\\n        else:\\n            if window_admitter.contains(key):\\n                hits += 1  # counts as hit path per W-TinyLFU semantics only if actually cached; else treat as admission via window\\n            candidate_freq = estimator.frequency(key)\\n            victim = slru.victim_for_admission_test()\\n            if victim is None or candidate_freq > estimator.frequency(victim):\\n                slru.admit_candidate(key)\\n            else:\\n                window_admitter.admit(key)\\n        if i % 1000 == 0:\\n            hit_series.append((i, hits/total))\\n    return {'hit_series': hit_series, 'final_hit_ratio': hits/total,\\n            'memory_bytes': estimator_memory_bytes(estimator) + slru_memory_bytes(slru)}\\n\\n# ---- 6. Trace generation ----\\ndef make_zipf_drift_trace(n_requests, key_space, alpha, n_drift_events, drift_magnitude, burst_prob, seed):\\n    # base: sample from Zipf(alpha) rank->key mapping over key_space\\n    # every n_requests/(n_drift_events+1) steps: reshuffle drift_magnitude fraction of top ranks to new random keys\\n    # additionally: with burst_prob, pick a previously-cold key and inject a short burst window (e.g. 200 consecutive/near-consecutive requests)\\n    # RECORD drift event indices explicitly -> needed for recovery-time metric\\n    ...\\n\\ndef load_real_trace():\\n    # search for a public trace via aii-hf-datasets / aii-web-tools first: e.g. a published CDN/memcached/Twitter-cache\\n    # trace commonly used in caching papers (search terms: \\\"memcached trace dataset\\\", \\\"Twitter cache trace github twitter/cache-trace\\\",\\n    # \\\"CDN access log trace research\\\", \\\"Wikipedia page view trace cache simulator\\\"). If a suitable one is found and fetchable\\n    # within budget, download and adapt to (timestamp, key) request stream. If NOT found/fetchable in time, SKIP the real-trace\\n    # arm entirely and note this explicitly in method_out.json -- do not fabricate a 'real' trace.\\n    ...\\n\\n# ---- 7. Sweep driver ----\\nCACHE_RATIOS = [0.001, 0.01, 0.1]       # cache_capacity / key_space\\nSKEW_LEVELS = [0.8, 1.0, 1.2, 1.5]      # Zipf alpha\\nSAMPLE_MULTIPLIERS = [4, 8, 16, 32]     # baseline W/C sweep -> pick best per (ratio, skew) on stationary portion\\nDRIFT_SCENARIOS = [ (low_mag, low_freq), (low_mag, high_freq), (high_mag, low_freq), (high_mag, high_freq) ]\\n\\nfor ratio in CACHE_RATIOS:\\n  for alpha in SKEW_LEVELS:\\n    key_space = 200_000  # fixed; cache_capacity = ratio * key_space\\n    # Phase A: stationary-only trace, sweep SAMPLE_MULTIPLIERS for baseline -> pick best (lowest cache misses) as 'tuned baseline'\\n    # Phase B: for the tuned baseline AND the per-key variant, run each of DRIFT_SCENARIOS x [synthetic seeds x3]\\n    #   record hit_series, drift-event indices, memory_bytes\\n    # Phase C (if real trace available): run tuned baseline + variant once each, same metrics\\n    for drift_scenario in DRIFT_SCENARIOS:\\n      for seed in [1,2,3]:\\n        trace, drift_indices = make_zipf_drift_trace(..., seed=seed)\\n        result_baseline = run_trace(trace, cache_capacity, GlobalResetFrequencyEstimator(cache_capacity, best_multiplier))\\n        result_proposed = run_trace(trace, cache_capacity, PerKeyDecayFrequencyEstimator(cache_capacity, shadow_queue_capacity=2*cache_capacity))\\n        # recovery time: for each drift_indices[j], find first index after it where rolling hit ratio >= 0.9 * post-drift-optimal\\n        #   (post-drift-optimal estimated as the hit ratio plateau reached by whichever of the two mechanisms converges highest\\n        #    over the next K requests, OR precomputed from the trace's true post-drift Zipf entropy -- document exact definition used)\\n        log_result(ratio, alpha, drift_scenario, seed, result_baseline, result_proposed)\\n\\n# ---- 8. Statistics & output ----\\n# Bootstrap CIs (1000 resamples over seeds) for: steady-state hit-ratio delta, recovery-time ratio (proposed/baseline)\\n# Aggregate: fraction of (ratio x alpha x drift_scenario) cells where proposed wins by >=20% faster recovery with CI excl. 0\\n# Write method_out.json: {config_grid_results: [...], summary_stats: {...}, memory_footprint_table: {...}, real_trace_results: {...} or null}\\n\",\n  \"fallback_plan\": \"If no suitable public real-world cache-access trace can be found/downloaded within the time budget (search HuggingFace datasets, GitHub repos for memcached/Twitter/CDN traces, and academic caching-paper artifact pages via aii-web-tools/aii-hf-datasets before giving up), proceed with synthetic traces only (Zipf + drift + bursts) across a wider sweep of alpha and drift parameters to compensate for losing trace diversity, and explicitly report in method_out.json that the real-trace arm of success_criteria was not evaluable and why. If the coefficient-of-variation-based per-key classification produces degenerate results (e.g., nearly all keys land in one tier, or classification is too noisy with few observations), fall back to a simpler 2-tier scheme (volatile vs stable, dropping the middle 'default' tier) and/or increase the EWMA smoothing window before declaring the mechanism itself a failure — report both the 3-tier and 2-tier results if time permits. If the K-sketch-tier implementation exceeds the ~2x memory budget at the swept cache ratios, switch the proposed variant's frequency storage to per-key floating-point EMA counters stored directly in the shadow-queue hash map (bounded by shadow_queue_capacity) instead of K parallel Count-Min sketches — this trades some hashing collision-robustness for a hard memory cap and should be implemented as an alternate PerKeyDecayFrequencyEstimator subclass so both variants can be compared if time allows. If runtime is too slow in pure Python for the full sweep (key_space=200k x n_requests likely in the millions), first try numpy-vectorizing the sketch counter updates and reduce N_REQUESTS/seeds per cell (e.g., 2 seeds instead of 3, or drop the largest cache_ratio) before cutting scenarios entirely — log explicitly which cells were skipped and why, never silently truncate the grid.\",\n  \"testing_plan\": \"1) Unit-test CountMin4Bit and Doorkeeper alone: increment a handful of known keys different numbers of times, verify estimate() returns correct sketch-theoretic bounds (never underestimates true count on stationary synthetic input of ~1000 requests over 20 keys) and halve_all() actually roughly halves observed estimates. 2) Unit-test SLRU: feed a short deterministic sequence (e.g. hand-constructed 20-key access pattern) and manually verify hit/miss and eviction order match expected LRU/SLRU behavior. 3) Sanity-check GlobalResetFrequencyEstimator against a tiny (key_space=1000, n_requests=50000) stationary Zipf(alpha=1.0) trace at cache_ratio=0.05 — confirm hit ratio is in a plausible range (roughly 40-70% for these params, compare qualitatively against published Caffeine simulator hit-ratio curves for similar Zipf/ratio settings if found via web search) before trusting the full pipeline. 4) Confirm PerKeyDecayFrequencyEstimator recovers the SAME order-of-magnitude hit ratio as the baseline on a purely stationary trace (this is the success_criteria's own regression check, e.g. within ~1-2 percentage points) BEFORE testing drift scenarios — if steady-state already diverges wildly, debug the tiering/classification logic first rather than proceeding to drift experiments. 5) Sanity-check the drift-injection trace generator by plotting/inspecting the empirical top-20 key frequency before and after a drift event on a small trace (e.g. n_requests=20000) to confirm ranks actually reshuffle as intended and bursts are visible as request-count spikes for the targeted cold key. 6) Run one full drift scenario (one seed, one ratio, one alpha) end-to-end for both mechanisms and manually inspect the hit_series plot / recovery-time computation on that single run to confirm the recovery-time metric behaves sensibly (post-drift dip visible, recovery point falls after the dip, not before) before launching the full sweep across all ratios/alphas/scenarios/seeds. 7) Only after all of the above pass, launch the full grid sweep using the aii-long-running-tasks staged-scaling pattern (start with 1 seed x reduced grid, extrapolate time, then scale to full 3-seed x full grid) to stay within the 6-hour executor budget, checking elapsed time after each stage before committing to the next.\"\n}\n", "structuredPatch": [], "originalFile": null, "userModified": false}
```

### [6] ASSISTANT · 2026-08-26 20:06:09 UTC

```
Plan written to `.terminal_claude_agent_struct_out.json`: a Caffeine-faithful W-TinyLFU baseline vs. a per-key inter-arrival-volatility-decayed variant, sharing sketch/doorkeeper/SLRU scaffolding, swept over synthetic Zipf+drift traces (and a real trace if found) with concrete pseudocode, fallbacks, and a staged testing plan.
```
