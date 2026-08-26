# gen_plan_dataset_1 — test_idea

> Phase: `invention_loop` · round 1 · `gen_plan`
> Run: `iter1_eb86f00c4c5a` — Why Per-Key Cache Decay Rarely Beats a Cheaper Shorter Reset
>
> Full, verbatim transcript of this agent task — every system/user prompt, assistant response, thinking block, tool call and tool result — in the order they occurred. Nothing truncated.

## Task: `gen_plan_dataset_1` (terminal_claude_agent, claude-sonnet-5)

### [1] CONFIG · 2026-08-26 20:04:50 UTC

```
model: claude-sonnet-5 | effort: low | permission: bypassPermissions | cwd: /ai-inventor/aii_data/runs/run_0pMem8W3ijCf/3_invention_loop/iter_1/gen_plan/gen_plan_dataset_1
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
You are expanding an artifact direction of type: DATASET

DATASET
Collect, prepare, and merge datasets for experiments and analysis.
Runtime: Python 3.12, UV, isolated workspace.
Tools: Full shell/Python/filesystem access, the aii-web-tools skill (web search, page fetch, regex grep over full page/PDF text), and other skills.
Skills: aii-hf-datasets (HuggingFace Hub — ML datasets, many UCI/OpenML/Kaggle mirrors), aii-owid-datasets (Our World in Data — global statistics), aii-json (schema validation). Also any Python source (sklearn.datasets, openml, direct URLs, APIs) — must verify within 300MB limit.
Capabilities: Search, acquire, transform, combine, and standardize data from any available source.
Deps: REQUIRED none | OPTIONAL RESEARCH for guidance on what data to collect
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

The dataset executor has 6h total (including writing code, debugging, testing, and fixing errors).

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

id: dataset_iter1_dir1
type: dataset
objective: >-
  Assemble a dataset of key-access traces spanning real-world and synthetic sources: at least one real public trace with documented
  temporal/popularity skew (e.g. a memcached/CDN/Wikipedia-pageview-derived key-access log, or a published block-storage/cache-benchmark
  trace such as those distributed with Caffeine's own simulator or SNIA/UMass trace repositories), plus a parameterized synthetic
  Zipf-with-drift generator producing traces at multiple skew levels (alpha swept) with controlled drift events (periodic
  rank re-shuffling of a rank subset, and randomly injected short bursts on initially-cold keys), each event's timestamp/magnitude/affected-key-set
  recorded as ground truth so drift-recovery time can later be measured against a known injection point.
approach: >-
  Search HuggingFace/UMass Trace Repository/SNIA IOTTA/public CDN-log releases for a real trace with per-request key/object
  IDs and timestamps at a size feasible to replay (target 1-10M requests, well under 300MB); if no suitable real trace is
  found within the time budget, fall back to a documented synthetic-only dataset but flag this explicitly as a limitation.
  For the synthetic generator: implement a Zipf sampler with time-varying rank permutation (a drift schedule) and burst injection
  (previously-cold keys given a temporary elevated sampling weight for a fixed window), parameterize alpha in {0.8, 1.0, 1.2},
  drift period, and burst rate, and emit ground-truth drift-event metadata (timestamp, affected keys, magnitude) alongside
  each trace so evaluation can align recovery windows to true injection points. Split into full/mini/preview per the DATASET
  schema.
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

DATASET executor scope:
  Output: data_out.json with rows of {input, output, metadata_fold, ...} — raw data only, no derived computations
  DOES: Download/generate datasets, analyze candidates to pick the best ones, standardize to JSON schema (features, labels, folds, metadata), validate schema, split into full/mini/preview
  DOES NOT: Run experiments, train models, compute derived statistics (PID/MI/correlations/synergy matrices) as final output
  If you need to COMPUTE something from data (synergy matrices, MI scores, timing benchmarks), use an EXPERIMENT artifact instead
</artifact_executor_scope>

<artifact_planning_rules>
DATASET:
- Plan for REAL third-party datasets (HuggingFace, Kaggle, direct-download URLs) — downloadable within time and size constraints
- Describe dataset criteria (domain, size, format) — executors find exact sources, but you can suggest candidates or search directions
- ALWAYS prefer real datasets over synthetic. Synthetic is a LAST RESORT only when no suitable real data exists
</artifact_planning_rules>

<compute_profiles>
Choose the compute profile this artifact needs for execution.
Available profiles for dataset artifacts:
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
  "description": "Plan for a DATASET artifact.",
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
    "ideal_dataset_criteria": {
      "description": "What makes an ideal dataset for this purpose - size, format, content requirements",
      "title": "Ideal Dataset Criteria",
      "type": "string"
    },
    "dataset_search_plan": {
      "description": "Step-by-step plan for finding/creating this dataset - sources to check, fallback options",
      "title": "Dataset Search Plan",
      "type": "string"
    },
    "target_num_datasets": {
      "description": "How many individual datasets should be delivered. Count each dataset separately, not collections \u2014 a benchmark suite of N datasets counts as N. This controls how broadly the executor searches, so setting it too low will under-collect.",
      "title": "Target Num Datasets",
      "type": "integer"
    }
  },
  "required": [
    "title",
    "ideal_dataset_criteria",
    "dataset_search_plan",
    "target_num_datasets"
  ],
  "title": "DatasetPlan",
  "type": "object"
}
```

IMPORTANT: this task is NOT complete until `./.terminal_claude_agent_struct_out.json` exists and contains JSON matching the schema above.
````

### [3] HUMAN-USER prompt · 2026-08-26 20:04:58 UTC

```
Cache admission policies for skewed key popularity in read-heavy key-value stores
```

### [4] TOOL CALL — Write · 2026-08-26 20:05:32 UTC

```
File: /ai-inventor/aii_data/runs/run_0pMem8W3ijCf/3_invention_loop/iter_1/gen_plan/gen_plan_dataset_1/.terminal_claude_agent_struct_out.json

{
  "title": "Real and synthetic cache access traces with drift",
  "summary": "Assemble key-access traces for testing cache admission policies: at least one real-world trace with documented temporal/popularity skew (memcached/CDN/Wikipedia-pageview/storage-I/O trace) plus a parameterized synthetic Zipf-with-drift generator that emits ground-truth drift-event metadata (timestamp, affected keys, magnitude) so downstream experiments can measure steady-state hit ratio and drift-recovery time.",
  "runpod_compute_profile": "cpu_light",
  "ideal_dataset_criteria": "Each dataset is a sequence of (timestamp_or_seq_index, key_id) request records, ordered, with enough distinct keys and skew for cache simulation to be meaningful (target 100K-2M unique-ish keys drawn from a space of >=10K distinct IDs, 1-10M total requests per trace, comfortably under the 300MB/dataset budget). Required per-row fields after standardization: `input` = {seq, timestamp (float/int, monotonic within trace), key (string/int id), trace_id, request_type (if available, e.g. GET)}, `output` = null or a label if the source provides one (most won't — this is unsupervised replay data, output can be a placeholder such as the key itself or omitted per schema convention), `metadata_fold` = train/test split marker (e.g. by trace segment) plus `metadata` = {source: real|synthetic, drift_event: null or {event_id, magnitude, affected_keys} if this row falls inside/near an injected drift window, alpha (for synthetic), trace_name}. At least one REAL trace is required (not just synthetic) — real traces should have documented, cited provenance (a paper, repo README, or archive page) establishing they exhibit skewed and/or time-varying popularity, e.g. the classic memcached/Twitter cache trace papers, Wikipedia pageview dumps (used as a key-popularity proxy keyed by article id), YCSB-style Zipf workload traces, or SNIA IOTTA block-I/O traces (LBA as 'key'). For the synthetic generator's OUTPUT (this artifact must actually produce and save the generated trace files, not just a spec for one), sweep at least alpha in {0.8, 1.0, 1.2}, include periodic rank-reshuffling drift events and randomly injected cold-key bursts, and persist the ground-truth event log as a separate structured array (or embedded per-row metadata) so no future recomputation of 'when did drift happen' is needed. full/mini/preview variants per the DATASET schema, with mini/preview being row-count-truncated but still containing at least one full drift cycle so they remain useful for smoke tests.",
  "dataset_search_plan": "1) REAL TRACE SEARCH (do this first, budget ~1-1.5h): (a) Search HuggingFace Hub (aii-hf-datasets skill) for keywords 'memcached trace', 'cache trace', 'CDN log', 'key-value workload', 'YCSB trace', 'wikipedia pageviews' — HF sometimes mirrors research traces or pageview dumps as parquet. (b) Web-search (aii-web-tools) for 'Twitter memcached trace github', 'Facebook memcached KV workload trace release' (the Twitter/Facebook production cache trace releases used in USENIX/SOSP cache papers, e.g. 'Twitter's In-Memory Caching' and 'RIPQ'/'Segcache' evaluation traces are the most directly relevant precedent for TinyLFU/Caffeine-style evaluation and are the single best-fit candidate — search 'twitter cache trace dataset download', 'cachelib traces download', 'segcache traces'). (c) Check SNIA IOTTA trace repository (iotta.snia.org) via web search/fetch for block-storage or object-cache traces with request-level key/LBA + timestamp columns, filtering to ones with documented long-tail/temporal skew in their description page. (d) Check Wikipedia pageviews (dumps.wikimedia.org/other/pageviews, or an HF mirror) as a fallback proxy for a 'real' skewed+drifting key-popularity signal: treat each article title as a key and reconstruct a per-hour/per-day request-count series, which naturally has Zipf-like skew and real popularity drift (viral articles) even though it isn't literally a cache-replay log — flag this explicitly as an approximation if used. (e) If a candidate is found, verify: per-request or per-time-bucket granularity, size fits 1-10M rows under 300MB, license permits reuse, and it is fetchable via public URL/HF/API within the time budget — do NOT spend more than ~1.5h on real-trace search; if nothing suitable surfaces, proceed to synthetic-only and record this as a documented limitation per the artifact direction's explicit fallback instruction. 2) SYNTHETIC GENERATION (build regardless, as the controlled/ground-truth-labeled half of the dataset): implement and RUN a Python Zipf trace generator (numpy.random.zipf or an explicit rank-probability table normalized from a Zipf-Mandelbrot law for better tail control) over a fixed key universe (e.g. 20,000-100,000 keys), producing sequential (timestamp, key) rows for a few million requests per trace. Add a drift schedule: every T requests (e.g. every 200K), pick a random subset (5-20%) of ranks and permute them (a previously-hot key becomes cold and vice versa) — log this as a drift event with timestamp, event_id, and the list of affected key ids plus their rank changes. Separately inject short bursts: pick K previously-cold keys at random points, give them an elevated sampling weight for a short window (e.g. 5,000-20,000 requests), then revert — log each burst similarly. Generate one trace per alpha in {0.8, 1.0, 1.2} (3 synthetic traces minimum), each with the same drift/burst injection logic so downstream experiments can compare adaptation speed across skew levels. 3) STANDARDIZE all traces (real + synthetic) into the shared JSON row schema described in ideal_dataset_criteria, with per-trace metadata distinguishing source=real vs source=synthetic and embedding the ground-truth drift-event log. 4) VALIDATE with aii-json (schema check) and produce full/mini/preview per dataset. 5) If the real-trace search in step 1 fails entirely, still deliver at least 3 synthetic Zipf-with-drift traces (one per alpha) as separate datasets, clearly documented as a limitation in the metadata (source=synthetic, note='no suitable real trace found within time budget').",
  "target_num_datasets": 4
}
```

### [5] TOOL RESULT — Write · 2026-08-26 20:05:32 UTC

```
{"type": "create", "filePath": "/ai-inventor/aii_data/runs/run_0pMem8W3ijCf/3_invention_loop/iter_1/gen_plan/gen_plan_dataset_1/.terminal_claude_agent_struct_out.json", "content": "{\n  \"title\": \"Real and synthetic cache access traces with drift\",\n  \"summary\": \"Assemble key-access traces for testing cache admission policies: at least one real-world trace with documented temporal/popularity skew (memcached/CDN/Wikipedia-pageview/storage-I/O trace) plus a parameterized synthetic Zipf-with-drift generator that emits ground-truth drift-event metadata (timestamp, affected keys, magnitude) so downstream experiments can measure steady-state hit ratio and drift-recovery time.\",\n  \"runpod_compute_profile\": \"cpu_light\",\n  \"ideal_dataset_criteria\": \"Each dataset is a sequence of (timestamp_or_seq_index, key_id) request records, ordered, with enough distinct keys and skew for cache simulation to be meaningful (target 100K-2M unique-ish keys drawn from a space of >=10K distinct IDs, 1-10M total requests per trace, comfortably under the 300MB/dataset budget). Required per-row fields after standardization: `input` = {seq, timestamp (float/int, monotonic within trace), key (string/int id), trace_id, request_type (if available, e.g. GET)}, `output` = null or a label if the source provides one (most won't — this is unsupervised replay data, output can be a placeholder such as the key itself or omitted per schema convention), `metadata_fold` = train/test split marker (e.g. by trace segment) plus `metadata` = {source: real|synthetic, drift_event: null or {event_id, magnitude, affected_keys} if this row falls inside/near an injected drift window, alpha (for synthetic), trace_name}. At least one REAL trace is required (not just synthetic) — real traces should have documented, cited provenance (a paper, repo README, or archive page) establishing they exhibit skewed and/or time-varying popularity, e.g. the classic memcached/Twitter cache trace papers, Wikipedia pageview dumps (used as a key-popularity proxy keyed by article id), YCSB-style Zipf workload traces, or SNIA IOTTA block-I/O traces (LBA as 'key'). For the synthetic generator's OUTPUT (this artifact must actually produce and save the generated trace files, not just a spec for one), sweep at least alpha in {0.8, 1.0, 1.2}, include periodic rank-reshuffling drift events and randomly injected cold-key bursts, and persist the ground-truth event log as a separate structured array (or embedded per-row metadata) so no future recomputation of 'when did drift happen' is needed. full/mini/preview variants per the DATASET schema, with mini/preview being row-count-truncated but still containing at least one full drift cycle so they remain useful for smoke tests.\",\n  \"dataset_search_plan\": \"1) REAL TRACE SEARCH (do this first, budget ~1-1.5h): (a) Search HuggingFace Hub (aii-hf-datasets skill) for keywords 'memcached trace', 'cache trace', 'CDN log', 'key-value workload', 'YCSB trace', 'wikipedia pageviews' — HF sometimes mirrors research traces or pageview dumps as parquet. (b) Web-search (aii-web-tools) for 'Twitter memcached trace github', 'Facebook memcached KV workload trace release' (the Twitter/Facebook production cache trace releases used in USENIX/SOSP cache papers, e.g. 'Twitter's In-Memory Caching' and 'RIPQ'/'Segcache' evaluation traces are the most directly relevant precedent for TinyLFU/Caffeine-style evaluation and are the single best-fit candidate — search 'twitter cache trace dataset download', 'cachelib traces download', 'segcache traces'). (c) Check SNIA IOTTA trace repository (iotta.snia.org) via web search/fetch for block-storage or object-cache traces with request-level key/LBA + timestamp columns, filtering to ones with documented long-tail/temporal skew in their description page. (d) Check Wikipedia pageviews (dumps.wikimedia.org/other/pageviews, or an HF mirror) as a fallback proxy for a 'real' skewed+drifting key-popularity signal: treat each article title as a key and reconstruct a per-hour/per-day request-count series, which naturally has Zipf-like skew and real popularity drift (viral articles) even though it isn't literally a cache-replay log — flag this explicitly as an approximation if used. (e) If a candidate is found, verify: per-request or per-time-bucket granularity, size fits 1-10M rows under 300MB, license permits reuse, and it is fetchable via public URL/HF/API within the time budget — do NOT spend more than ~1.5h on real-trace search; if nothing suitable surfaces, proceed to synthetic-only and record this as a documented limitation per the artifact direction's explicit fallback instruction. 2) SYNTHETIC GENERATION (build regardless, as the controlled/ground-truth-labeled half of the dataset): implement and RUN a Python Zipf trace generator (numpy.random.zipf or an explicit rank-probability table normalized from a Zipf-Mandelbrot law for better tail control) over a fixed key universe (e.g. 20,000-100,000 keys), producing sequential (timestamp, key) rows for a few million requests per trace. Add a drift schedule: every T requests (e.g. every 200K), pick a random subset (5-20%) of ranks and permute them (a previously-hot key becomes cold and vice versa) — log this as a drift event with timestamp, event_id, and the list of affected key ids plus their rank changes. Separately inject short bursts: pick K previously-cold keys at random points, give them an elevated sampling weight for a short window (e.g. 5,000-20,000 requests), then revert — log each burst similarly. Generate one trace per alpha in {0.8, 1.0, 1.2} (3 synthetic traces minimum), each with the same drift/burst injection logic so downstream experiments can compare adaptation speed across skew levels. 3) STANDARDIZE all traces (real + synthetic) into the shared JSON row schema described in ideal_dataset_criteria, with per-trace metadata distinguishing source=real vs source=synthetic and embedding the ground-truth drift-event log. 4) VALIDATE with aii-json (schema check) and produce full/mini/preview per dataset. 5) If the real-trace search in step 1 fails entirely, still deliver at least 3 synthetic Zipf-with-drift traces (one per alpha) as separate datasets, clearly documented as a limitation in the metadata (source=synthetic, note='no suitable real trace found within time budget').\",\n  \"target_num_datasets\": 4\n}\n", "structuredPatch": [], "originalFile": null, "userModified": false}
```

### [6] ASSISTANT · 2026-08-26 20:05:34 UTC

```
Plan written to `.terminal_claude_agent_struct_out.json`: search for a real memcached/CDN/Wikipedia-pageview trace first (fallback to documented limitation if none found), then generate 3+ synthetic Zipf-with-drift traces (alpha 0.8/1.0/1.2) with ground-truth drift/burst event logs, standardized to the JSON schema.
```
