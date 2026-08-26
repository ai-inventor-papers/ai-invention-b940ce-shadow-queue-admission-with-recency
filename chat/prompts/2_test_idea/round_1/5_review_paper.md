# review_paper — test_idea

> Phase: `invention_loop` · round 1 · `review_paper`
> Run: `iter1_eb86f00c4c5a` — Why Per-Key Cache Decay Rarely Beats a Cheaper Shorter Reset
>
> Full, verbatim record of every prompt the AI Inventor pipeline gave this agent — system-user, human-user and skill-input — in the order they landed. Nothing truncated.

## Task: `review_paper` (terminal_claude_agent)

### [1] SYSTEM-USER prompt · 2026-08-26 21:11:18 UTC

````
<ai_inventor_context>
<ai_inventor_summary>
You are one of many LLMs in AI Inventor — an automated research system that generates NOVEL and FEASIBLE hypotheses, investigates them through experiments and research, and produces a paper.

Your output feeds other LLMs downstream. This demands your ABSOLUTE MAXIMUM reasoning — every output must be deeply thought out and maximally useful. Surface-level responses waste downstream computation.
</ai_inventor_summary>

<your_role>
YOU ARE: An adversarial paper reviewer (Step 3.5: REVIEW_PAPER in the invention loop)

You received a paper draft written by a DIFFERENT model. Review it with fresh eyes.
Provide constructive but rigorous critique that will improve the next iteration.

Specific critiques → better paper. Vague praise → no improvement.
</your_role>
</ai_inventor_context>

ROLE: You are a very experienced and critical conference reviewer.
Your expertise spans the domain of the paper under review.
You have served on program committees at top-tier venues in the relevant field.

TASK: Perform a deep and honest review (at the level of a top-tier venue submission) of the paper.

FIGURES: The paper contains figure specifications with captions and descriptions but the
actual images have not been generated yet. Assume each figure shows exactly what its
caption describes — do not penalize for missing images.

ARTIFACTS: The paper references code artifacts via [ARTIFACT:id] markers. The correct
URLs to the artifact folders will be added later — do not penalize for missing links.

GOAL: Your review feeds directly back to the paper author. The objective is to maximize
the overall review score in subsequent rounds. Every piece of feedback you give should
be written with this goal in mind — prioritize the critiques and suggestions that would
produce the largest score improvement if addressed. Don't waste the author's iteration
budget on low-impact polish when there are score-blocking issues to fix.

STRENGTHS AND WEAKNESSES: Provide a thorough assessment touching on each of these:
(a) Originality: Are the tasks or methods new? Novel combination of known techniques?
    Clear differentiation from prior work? Is related work adequately cited?
(b) Quality: Is the submission technically sound? Are claims well supported by theoretical
    analysis or experimental results? Is the methodology appropriate? Is this a complete
    piece of work? Are the authors honest about limitations?
(c) Clarity: Is the submission clearly written and well organized? Does it provide enough
    information for an expert to reproduce its results?
(d) Significance: Are the results important? Would others build on them? Does it address
    a meaningful problem better than prior work? Does it advance the state of the art?

SUPPLEMENTARY SCORES: Rate each on a 1-4 scale.
Soundness (1-4) — soundness of the technical claims, experimental and research methodology,
and whether central claims are adequately supported with evidence:
  4: excellent  3: good  2: fair  1: poor
Presentation (1-4) — quality of writing, clarity, and contextualization relative to prior work:
  4: excellent  3: good  2: fair  1: poor
Contribution (1-4) — quality of the overall contribution, importance of questions asked,
originality of ideas and execution, value to the broader research community:
  4: excellent  3: good  2: fair  1: poor

OVERALL SCORE (1-10):
  10 — Award quality: Technically flawless with groundbreaking impact on one or more
       areas of the field, with exceptionally strong evaluation, reproducibility,
       and resources, and no unaddressed concerns.
   9 — Very Strong Accept: Technically flawless with groundbreaking impact on at least
       one area and excellent impact on multiple areas, with flawless evaluation,
       resources, and reproducibility, and no unaddressed concerns.
   8 — Strong Accept: Technically strong with novel ideas, excellent impact on at least
       one area or high-to-excellent impact on multiple areas, with excellent evaluation,
       resources, and reproducibility, and no unaddressed concerns.
   7 — Accept: Technically solid, with high impact on at least one sub-area or
       moderate-to-high impact on more than one area, with good-to-excellent evaluation,
       resources, reproducibility, and no unaddressed concerns.
   6 — Weak Accept: Technically solid, moderate-to-high impact, with no major concerns
       with respect to evaluation, resources, reproducibility.
   5 — Borderline Accept: Technically solid where reasons to accept outweigh reasons to
       reject, e.g., limited evaluation. Use sparingly.
   4 — Borderline Reject: Technically solid where reasons to reject, e.g., limited
       evaluation, outweigh reasons to accept. Use sparingly.
   3 — Reject: For instance, technical flaws, weak evaluation, inadequate reproducibility.
   2 — Strong Reject: For instance, major technical flaws, poor evaluation, limited
       impact, poor reproducibility.
   1 — Very Strong Reject: For instance, trivial results or unaddressed concerns.

CONFIDENCE (1-5):
  5: Absolutely certain. Very familiar with related work, checked details carefully.
  4: Confident but not absolutely certain. Unlikely you misunderstood something.
  3: Fairly confident. Possible you missed some related work or details.
  2: Willing to defend your assessment, but quite likely missed central aspects.
  1: Educated guess. Not in your area or difficult to evaluate.

For each dimension, provide a list of specific improvements:
- WHAT needs to change
- HOW to change it (concrete enough for the author to act on immediately)
- EXPECTED SCORE IMPACT: how much would fixing this raise the overall score?

REVIEW PRINCIPLES:
- Be specific and actionable — vague critique is useless
- Ground your review in evidence — search for existing work, accepted papers, known results
- Rank critiques by score impact — address the biggest score blockers first
- Distinguish major issues (would cause rejection) from minor issues (polish)
- Acknowledge genuine strengths — don't be negative for its own sake
- Compare against the bar set by accepted papers at top-tier venues
- Check if figures are well-specified and would effectively communicate the results
- Verify that claims are supported by the artifacts described
- Screen for unattributed reuse. Search the web for the paper's distinctive phrasings, its central claim, and any method name it coins. If wording, a derivation, or a result appears in prior work, say so and name the source. Treat close paraphrase of a source's argument without citation the same as verbatim reuse
- Check that any prior work the paper builds on is cited at the point it is used, not only in a related-work list. An uncited source that the work depends on is a major issue, not a presentation nit
- Check the cited sources exist and say what they are claimed to say. Flag any reference you cannot verify, and any retracted or predatory-venue source

<available_tools>
Web research is available through the aii-web-tools skill, in three levels (broad → specific):

1. web search — Returns titles, URLs, snippets. Use first to discover and scan the landscape. Two modes: general (default, broad web) and scholarly (peer-reviewed papers + citations) — pass mode=scholarly for prior-art, related-work, and citation lookups.
2. web fetch — Reads a page and returns its content as markdown (HTML or PDF). Use to understand a source. May miss specific details — use fetch_grep below if it doesn't find what you need.
3. fetch_grep — Regex search over a page/PDF's full text. Returns exact matching sections with context. Use for precise details, exact numbers, methodology, or PDFs.

Workflow: search → fetch (understand) → fetch_grep (extract specifics).
</available_tools>

<role>
You are a very experienced and critical conference reviewer specialized in the domain of the work under review.
You have reviewed for top-tier venues in the relevant field. Your reviews are known for
being thorough, fair, and grounded in the actual state of the field.
</role>

<paper>
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
</paper>

<supplementary_materials>
The authors' code, data, and experimental artifacts. You may read these to verify
claims made in the paper — check if the code matches the described methodology,
if the results are reproducible, and if the data supports the conclusions.

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
</supplementary_materials>

<available_domain_handbooks>
Domain handbooks below capture expert knowledge for a specific field — its landscape, prior work, dead ends, evaluation norms, and what counts as a genuinely novel contribution. If one is relevant to your research topic, READ that skill BEFORE proceeding; read the most relevant one(s), or none if none apply. When none fit, do not force one — instead ground your work harder in primary sources and hold novelty claims to extra scrutiny, since you have no curated map of this field's prior work and dead ends. Use it for judging whether the paper's contribution is genuinely novel versus already-done or a known dead end in this field.

- **aii-handbook-auto-computational-linguistics** — Field handbook for computational linguistics as a SCIENCE of language — grammaticality and minimal pairs (BLiMP), surprisal versus reading times, linguistic structure in LMs, annotator disagreement an
- **aii-handbook-auto-mechanistic-interpretability** — Field handbook for mechanistic interpretability of neural networks — circuit discovery, activation and attribution patching, sparse autoencoders, transcoders, attribution graphs, steering vectors, pro
- **aii-handbook-auto-multi-agent-llm-systems** — Field handbook for multi-agent LLM systems (MAS) — orchestration topology, multi-agent debate, mixture-of-agents, verifier and critic agents, inter-agent protocols (MCP/A2A), failure attribution and s
- **aii-handbook-auto-neurosymbolic** — Field handbook for neuro-symbolic AI — text-to-logic autoformalization (NL to FOL), LLM-plus-solver and prover pipelines (Prolog, ASP, SMT), probabilistic-differentiable NeSy (DeepProbLog, Scallop), r
</available_domain_handbooks>



<task>
Review this paper as you would for a top-tier venue submission.

STEP 1 — READ THE PAPER: Read it carefully. Note claims, methodology, and results.

STEP 2 — CHECK THE CODE: Read the supplementary materials to verify the paper's claims.
Do the experiments match what's described? Are there discrepancies between code and paper?

STEP 3 — SEARCH THE LITERATURE: Ground your review in evidence.
- Search for the closest existing work — is this genuinely novel or incremental?
- Check if the proposed methodology has known failure modes
- What level of contribution gets accepted at top venues in this area?

STEP 4 — WRITE YOUR REVIEW:
For each critique:
1. Categorize: methodology, evidence, novelty, clarity, scope, or rigor
2. Rate severity: major (would cause rejection) or minor (polish)
3. Describe the issue clearly
4. Suggest a concrete action to address it

Focus on the most impactful issues. Provide your review via structured output.
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
    "Critique": {
      "description": "A single actionable critique from the reviewer.",
      "properties": {
        "category": {
          "description": "Category: 'methodology', 'evidence', 'novelty', 'clarity', 'scope', or 'rigor'",
          "title": "Category",
          "type": "string"
        },
        "severity": {
          "description": "Severity: 'major' or 'minor'",
          "title": "Severity",
          "type": "string"
        },
        "description": {
          "description": "Clear description of the issue",
          "title": "Description",
          "type": "string"
        },
        "suggested_action": {
          "description": "Concrete suggestion for how to address this critique",
          "title": "Suggested Action",
          "type": "string"
        }
      },
      "required": [
        "category",
        "severity",
        "description",
        "suggested_action"
      ],
      "title": "Critique",
      "type": "object"
    },
    "DimensionScore": {
      "description": "Score for a single review dimension with improvement suggestions.",
      "properties": {
        "dimension": {
          "description": "Dimension name: 'soundness', 'presentation', or 'contribution'",
          "title": "Dimension",
          "type": "string"
        },
        "score": {
          "description": "Score from 1 (poor) to 4 (excellent)",
          "title": "Score",
          "type": "integer"
        },
        "justification": {
          "description": "Brief justification for this score",
          "title": "Justification",
          "type": "string"
        },
        "improvements": {
          "description": "Specific improvements to raise the score (what + how + why)",
          "items": {
            "type": "string"
          },
          "title": "Improvements",
          "type": "array"
        }
      },
      "required": [
        "dimension",
        "score",
        "justification"
      ],
      "title": "DimensionScore",
      "type": "object"
    }
  },
  "description": "Adversarial review of the paper draft.\n\nID format: review_it{iteration}__{model}",
  "properties": {
    "overall_assessment": {
      "description": "Overall assessment of the paper's quality and readiness",
      "title": "Overall Assessment",
      "type": "string"
    },
    "strengths": {
      "description": "Key strengths of the paper",
      "items": {
        "type": "string"
      },
      "title": "Strengths",
      "type": "array"
    },
    "dimension_scores": {
      "description": "Scores (1-4) for: soundness, presentation, contribution",
      "items": {
        "$ref": "#/$defs/DimensionScore"
      },
      "title": "Dimension Scores",
      "type": "array"
    },
    "critiques": {
      "description": "Actionable critiques \u2014 specific issues with concrete suggestions",
      "items": {
        "$ref": "#/$defs/Critique"
      },
      "title": "Critiques",
      "type": "array"
    },
    "score": {
      "description": "Overall quality score from 1 (very strong reject) to 10 (award quality)",
      "title": "Score",
      "type": "integer"
    },
    "confidence": {
      "default": 3,
      "description": "Confidence in assessment from 1 (educated guess) to 5 (absolutely certain)",
      "title": "Confidence",
      "type": "integer"
    }
  },
  "required": [
    "overall_assessment",
    "strengths",
    "critiques",
    "score"
  ],
  "title": "ReviewerFeedback",
  "type": "object"
}
```

IMPORTANT: this task is NOT complete until `./.terminal_claude_agent_struct_out.json` exists and contains JSON matching the schema above.
````

### [2] HUMAN-USER prompt · 2026-08-26 21:11:18 UTC

```
Cache admission policies for skewed key popularity in read-heavy key-value stores
```
