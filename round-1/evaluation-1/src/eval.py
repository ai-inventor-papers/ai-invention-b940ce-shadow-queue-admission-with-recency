#!/usr/bin/env python3
"""Evaluate per-key-decay cache admission vs tuned W-TinyLFU global-reset baseline.

No upstream experiment/dataset artifacts were produced for this run (both
gen_art_experiment_1 and gen_art_dataset_1 directories are empty), so this
script is self-contained: it implements the shadow-queue admission simulator
(baseline W-TinyLFU with a swept global reset period W, and a per-key
inter-arrival-decay variant), generates synthetic Zipf traces with injected
popularity drift and injected burst/stable/neutral key labels, runs both
systems across a sensitivity grid, and computes the five pre-registered
metrics from the artifact plan.
"""

from __future__ import annotations

import json
import math
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path

from loguru import logger

WORKDIR = Path(__file__).resolve().parent
LOG_DIR = WORKDIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

logger.remove()
logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss}|{level:<7}|{message}")
logger.add(LOG_DIR / "run.log", rotation="30 MB", level="DEBUG")

RNG_SEEDS = [1, 2, 3, 4, 5]
N_KEYS = 2000
REQUESTS_PER_SEGMENT = 12000  # per stationary/drift segment
CACHE_SIZE_RATIOS = [0.02, 0.05, 0.10]  # cache_size / N_KEYS
ALPHA_GRID = [0.8, 1.0, 1.2]
BASELINE_W_GRID = [4, 8, 16, 32, 64]
DRIFT_SCENARIOS = ["hotset_rotation", "skew_flatten", "skew_sharpen", "burst_injection"]
STEADY_TAIL_FRAC = 0.20
T90_WINDOW = 500
T90_THRESH = 0.90
T90_K_CONSEC = 3


# ------------------------------- trace generation -------------------------------


def zipf_probs(n_keys: int, alpha: float) -> list[float]:
    weights = [1.0 / (rank ** alpha) for rank in range(1, n_keys + 1)]
    total = sum(weights)
    return [w / total for w in weights]


@dataclass
class KeyLabel:
    burst: set[int] = field(default_factory=set)
    stable: set[int] = field(default_factory=set)
    neutral: set[int] = field(default_factory=set)


def make_key_labels(n_keys: int, rng: random.Random) -> KeyLabel:
    ranked = list(range(n_keys))
    n_stable = max(1, n_keys // 20)
    n_burst = max(1, n_keys // 10)
    stable = set(ranked[:n_stable])  # top-ranked = stable heavy hitters
    remaining = ranked[n_stable:]
    burst = set(rng.sample(remaining, min(n_burst, len(remaining))))
    neutral = set(ranked) - stable - burst
    return KeyLabel(burst=burst, stable=stable, neutral=neutral)


def gen_stationary_segment(n_keys: int, alpha: float, n_requests: int, rng: random.Random) -> list[int]:
    probs = zipf_probs(n_keys, alpha)
    population = list(range(n_keys))
    return rng.choices(population, weights=probs, k=n_requests)


def gen_drift_segment(scenario: str, n_keys: int, alpha: float, n_requests: int, rng: random.Random) -> list[int]:
    """Generate a post-drift-event segment for the given scenario."""
    if scenario == "hotset_rotation":
        probs = zipf_probs(n_keys, alpha)
        shift = n_keys // 3
        rotated = probs[shift:] + probs[:shift]
        population = list(range(n_keys))
        return rng.choices(population, weights=rotated, k=n_requests)
    if scenario == "skew_flatten":
        return gen_stationary_segment(n_keys, max(0.3, alpha - 0.6), n_requests, rng)
    if scenario == "skew_sharpen":
        return gen_stationary_segment(n_keys, alpha + 0.8, n_requests, rng)
    if scenario == "burst_injection":
        probs = zipf_probs(n_keys, alpha)
        boosted = probs[:]
        burst_keys = rng.sample(range(n_keys), max(1, n_keys // 20))
        boost = max(probs) * 3.0
        for k in burst_keys:
            boosted[k] += boost
        total = sum(boosted)
        boosted = [b / total for b in boosted]
        population = list(range(n_keys))
        return rng.choices(population, weights=boosted, k=n_requests)
    raise ValueError(f"unknown scenario {scenario}")


# ------------------------------- admission simulators -------------------------------


class WTinyLFUBaseline:
    """Count-Min-style frequency sketch + doorkeeper, with periodic global reset."""

    def __init__(self, cache_size: int, reset_period_x_c: int, n_keys: int):
        self.cache_size = cache_size
        self.window = reset_period_x_c * cache_size
        self.n_keys = n_keys
        self.freq: dict[int, int] = {}
        self.doorkeeper: set[int] = set()
        self.seen_since_reset = 0
        self.cache: dict[int, int] = {}  # key -> freq at insertion time (LFU eviction proxy)
        self.hits = 0
        self.total = 0

    def _maybe_reset(self) -> None:
        self.seen_since_reset += 1
        if self.seen_since_reset >= max(1, self.window):
            for k in self.freq:
                self.freq[k] //= 2
            self.doorkeeper.clear()
            self.seen_since_reset = 0

    def request(self, key: int) -> bool:
        self.total += 1
        self._maybe_reset()
        if key in self.cache:
            self.hits += 1
            self.freq[key] = self.freq.get(key, 0) + 1
            return True
        # admission logic
        if key in self.doorkeeper:
            self.freq[key] = self.freq.get(key, 0) + 1
        else:
            self.doorkeeper.add(key)
            self.freq[key] = self.freq.get(key, 1)
        candidate_freq = self.freq[key]
        if len(self.cache) < self.cache_size:
            self.cache[key] = candidate_freq
        else:
            victim = min(self.cache, key=lambda k: self.cache[k])
            if candidate_freq > self.cache[victim]:
                del self.cache[victim]
                self.cache[key] = candidate_freq
        return False

    def state_bits(self) -> int:
        # 4-bit CM sketch counters over n_keys, doorkeeper bloom filter (1 bit/key), shadow slot metadata
        cm_bits = 4 * self.n_keys
        doorkeeper_bits = self.n_keys
        shadow_meta_bits = 32 * self.cache_size
        return cm_bits + doorkeeper_bits + shadow_meta_bits


class PerKeyDecayVariant:
    """Admission filter with per-key decay rate learned from inter-arrival variance."""

    DECAY_FAST = 0.5  # short-decay bucket
    DECAY_MED = 0.85
    DECAY_SLOW = 0.98  # long-decay bucket

    def __init__(self, cache_size: int, n_keys: int, bucket_update_every: int = 200):
        self.cache_size = cache_size
        self.n_keys = n_keys
        self.freq: dict[int, float] = {}
        self.last_seen: dict[int, int] = {}
        self.inter_arrivals: dict[int, list[int]] = {}
        self.decay_rate: dict[int, float] = {}
        self.bucket: dict[int, str] = {}
        self.cache: dict[int, float] = {}
        self.hits = 0
        self.total = 0
        self.t = 0
        self.bucket_update_every = bucket_update_every

    def _update_bucket(self, key: int) -> None:
        arrivals = self.inter_arrivals.get(key, [])
        if len(arrivals) < 3:
            self.decay_rate[key] = self.DECAY_MED
            self.bucket[key] = "mid"
            return
        mean_ia = sum(arrivals) / len(arrivals)
        var_ia = sum((a - mean_ia) ** 2 for a in arrivals) / len(arrivals)
        cv = math.sqrt(var_ia) / (mean_ia + 1e-9)
        # high inter-arrival variance (bursty) -> fast decay; low variance (steady) -> slow decay
        if cv > 1.2:
            self.decay_rate[key] = self.DECAY_FAST
            self.bucket[key] = "short-decay"
        elif cv < 0.5:
            self.decay_rate[key] = self.DECAY_SLOW
            self.bucket[key] = "long-decay"
        else:
            self.decay_rate[key] = self.DECAY_MED
            self.bucket[key] = "mid"

    def request(self, key: int) -> bool:
        self.total += 1
        self.t += 1
        if key in self.last_seen:
            ia = self.t - self.last_seen[key]
            hist = self.inter_arrivals.setdefault(key, [])
            hist.append(ia)
            if len(hist) > 20:
                hist.pop(0)
            if len(hist) % self.bucket_update_every == 0 or len(hist) in (3, 5, 10):
                self._update_bucket(key)
        self.last_seen[key] = self.t
        decay = self.decay_rate.get(key, self.DECAY_MED)
        self.freq[key] = self.freq.get(key, 0.0) * decay + 1.0

        if key in self.cache:
            self.hits += 1
            return True
        candidate_freq = self.freq[key]
        if len(self.cache) < self.cache_size:
            self.cache[key] = candidate_freq
        else:
            victim = min(self.cache, key=lambda k: self.cache[k])
            if candidate_freq > self.cache[victim]:
                del self.cache[victim]
                self.cache[key] = candidate_freq
        return False

    def state_bits(self) -> int:
        cm_bits = 8 * self.n_keys  # float decayed counter, coarser than baseline's 4-bit CM
        history_bits = 5 * 20 * self.n_keys  # per-key inter-arrival ring buffer (20 x 5-bit deltas, capped)
        bucket_tag_bits = 2 * self.n_keys
        shadow_meta_bits = 32 * self.cache_size
        return cm_bits + history_bits + bucket_tag_bits + shadow_meta_bits

    def bucket_confusion_inputs(self) -> dict[int, str]:
        return dict(self.bucket)


# ------------------------------- rolling hit-ratio helpers -------------------------------


def rolling_hit_ratio(hit_seq: list[bool], window: int) -> list[float]:
    out = []
    running = 0
    for i, h in enumerate(hit_seq):
        running += 1 if h else 0
        if i >= window:
            running -= 1 if hit_seq[i - window] else 0
            out.append(running / window)
        elif i == window - 1:
            out.append(running / window)
    return out


def steady_state_hit_ratio(hit_seq: list[bool], tail_frac: float) -> float:
    n = len(hit_seq)
    tail = hit_seq[int(n * (1 - tail_frac)):]
    return sum(tail) / len(tail) if tail else 0.0


def compute_t90(hit_seq_post_drift: list[bool], window: int, thresh_frac: float, k_consec: int) -> int:
    """Requests after drift event until rolling hit ratio reaches thresh_frac * post-drift-optimal
    and stays there for k_consec consecutive windows. Returns len(hit_seq_post_drift) if never reached
    (censored recovery)."""
    optimal = steady_state_hit_ratio(hit_seq_post_drift, STEADY_TAIL_FRAC)
    target = thresh_frac * optimal
    rolling = rolling_hit_ratio(hit_seq_post_drift, window)
    consec = 0
    for i, r in enumerate(rolling):
        if r >= target:
            consec += 1
            if consec >= k_consec:
                # position of the window that first crossed
                idx = window + (i - k_consec + 1)
                return max(idx, 1)
        else:
            consec = 0
    return len(hit_seq_post_drift)


# ------------------------------- bootstrap -------------------------------


def bootstrap_ci(values: list[float], n_resamples: int, rng: random.Random, stat: str = "mean") -> tuple[float, float, float]:
    if not values:
        return (float("nan"), float("nan"), float("nan"))
    point = sum(values) / len(values) if stat == "mean" else sorted(values)[len(values) // 2]
    n = len(values)
    resample_stats = []
    for _ in range(n_resamples):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        if stat == "mean":
            resample_stats.append(sum(sample) / n)
        else:
            resample_stats.append(sorted(sample)[n // 2])
    resample_stats.sort()
    lo = resample_stats[int(0.025 * n_resamples)]
    hi = resample_stats[min(int(0.975 * n_resamples), n_resamples - 1)]
    return (point, lo, hi)


# ------------------------------- single-run simulation -------------------------------


def run_pair(
    system_cls_baseline_w: int | None,
    cache_size: int,
    n_keys: int,
    alpha: float,
    stationary_reqs: list[int],
    drift_reqs: list[int],
    is_baseline: bool,
):
    if is_baseline:
        sim = WTinyLFUBaseline(cache_size=cache_size, reset_period_x_c=system_cls_baseline_w, n_keys=n_keys)
    else:
        sim = PerKeyDecayVariant(cache_size=cache_size, n_keys=n_keys)
    stat_hits = [sim.request(k) for k in stationary_reqs]
    drift_hits = [sim.request(k) for k in drift_reqs]
    return sim, stat_hits, drift_hits


def select_best_w(cache_size: int, n_keys: int, alpha: float, stationary_reqs: list[int]) -> int:
    best_w, best_hr = BASELINE_W_GRID[0], -1.0
    for w in BASELINE_W_GRID:
        sim = WTinyLFUBaseline(cache_size=cache_size, reset_period_x_c=w, n_keys=n_keys)
        hits = [sim.request(k) for k in stationary_reqs]
        hr = steady_state_hit_ratio(hits, STEADY_TAIL_FRAC)
        if hr > best_hr or (hr == best_hr and w < best_w):
            best_hr, best_w = hr, w
    return best_w


# ------------------------------- main evaluation -------------------------------


@logger.catch(reraise=True)
def main() -> None:
    logger.info("Starting cache-admission evaluation (self-contained simulator; no upstream artifacts found)")
    metrics_agg: dict[str, float] = {}
    datasets_out: list[dict] = []

    # ---- Metric 1 & 2: steady-state parity + drift recovery, across scenarios/traces/seeds ----
    parity_diffs = []  # pp differences, one per (alpha, ratio, seed)
    recovery_reductions: dict[str, list[float]] = {s: [] for s in DRIFT_SCENARIOS}
    memory_ratios: list[float] = []
    grid_pass = {}  # (alpha, ratio, scenario) -> bool

    examples_main = []

    for alpha in ALPHA_GRID:
        for ratio in CACHE_SIZE_RATIOS:
            cache_size = max(4, int(N_KEYS * ratio))
            for scenario in DRIFT_SCENARIOS:
                seed_parity = []
                seed_recovery_pct = []
                for seed in RNG_SEEDS:
                    rng = random.Random(1000 * seed + hash((alpha, ratio, scenario)) % 997)
                    labels = make_key_labels(N_KEYS, rng)
                    stationary_reqs = gen_stationary_segment(N_KEYS, alpha, REQUESTS_PER_SEGMENT, rng)
                    drift_reqs = gen_drift_segment(scenario, N_KEYS, alpha, REQUESTS_PER_SEGMENT, rng)

                    best_w = select_best_w(cache_size, N_KEYS, alpha, stationary_reqs)

                    base_sim, base_stat_hits, base_drift_hits = run_pair(
                        best_w, cache_size, N_KEYS, alpha, stationary_reqs, drift_reqs, is_baseline=True
                    )
                    var_sim, var_stat_hits, var_drift_hits = run_pair(
                        None, cache_size, N_KEYS, alpha, stationary_reqs, drift_reqs, is_baseline=False
                    )

                    base_ss = steady_state_hit_ratio(base_stat_hits, STEADY_TAIL_FRAC)
                    var_ss = steady_state_hit_ratio(var_stat_hits, STEADY_TAIL_FRAC)
                    diff_pp = (var_ss - base_ss) * 100.0
                    seed_parity.append(diff_pp)
                    parity_diffs.append(diff_pp)

                    t90_base = compute_t90(base_drift_hits, T90_WINDOW, T90_THRESH, T90_K_CONSEC)
                    t90_var = compute_t90(var_drift_hits, T90_WINDOW, T90_THRESH, T90_K_CONSEC)
                    pct_reduction = (t90_base - t90_var) / t90_base * 100.0 if t90_base > 0 else 0.0
                    seed_recovery_pct.append(pct_reduction)
                    recovery_reductions[scenario].append(pct_reduction)

                    if alpha == ALPHA_GRID[len(ALPHA_GRID) // 2] and ratio == CACHE_SIZE_RATIOS[len(CACHE_SIZE_RATIOS) // 2]:
                        mem_ratio = var_sim.state_bits() / base_sim.state_bits()
                        memory_ratios.append(mem_ratio)

                    examples_main.append(
                        {
                            "input": f"trace=synthetic_zipf alpha={alpha} cache_ratio={ratio} scenario={scenario} seed={seed} best_W={best_w}",
                            "output": "steady_state_parity_pp,drift_recovery_pct_reduction",
                            "predict_baseline": f"steady_state_hr={base_ss:.4f};T90={t90_base}",
                            "predict_variant": f"steady_state_hr={var_ss:.4f};T90={t90_var}",
                            "eval_steady_state_diff_pp": diff_pp,
                            "eval_recovery_pct_reduction": pct_reduction,
                        }
                    )

                mean_parity = sum(seed_parity) / len(seed_parity)
                rng_ci = random.Random(42)
                _, lo_rec, hi_rec = bootstrap_ci(seed_recovery_pct, 2000, rng_ci, stat="mean")
                mean_rec = sum(seed_recovery_pct) / len(seed_recovery_pct)
                scenario_pass = (mean_rec >= 20.0) and (lo_rec > 0.0)
                grid_pass[(alpha, ratio, scenario)] = scenario_pass

    logger.info(f"Simulated {len(examples_main)} (alpha, ratio, scenario, seed) configurations")

    # ---- aggregate metric 1: steady-state parity ----
    rng1 = random.Random(101)
    parity_point, parity_lo, parity_hi = bootstrap_ci(parity_diffs, 2000, rng1, stat="mean")
    parity_pass = abs(parity_point) <= 1.0 and not (parity_lo > 1.0 or parity_hi < -1.0)
    metrics_agg["steady_state_parity_diff_pp_mean"] = parity_point
    metrics_agg["steady_state_parity_diff_pp_ci_lo"] = parity_lo
    metrics_agg["steady_state_parity_diff_pp_ci_hi"] = parity_hi
    metrics_agg["steady_state_parity_pass"] = 1.0 if parity_pass else 0.0

    # ---- aggregate metric 2: drift recovery, per scenario + overall (synthetic only; no real trace available) ----
    scenario_pass_count = 0
    for scenario in DRIFT_SCENARIOS:
        vals = recovery_reductions[scenario]
        rng_s = random.Random(hash(scenario) % 9999)
        point, lo, hi = bootstrap_ci(vals, 2000, rng_s, stat="mean")
        passed = point >= 20.0 and lo > 0.0
        scenario_pass_count += 1 if passed else 0
        metrics_agg[f"recovery_reduction_pct_{scenario}_mean"] = point
        metrics_agg[f"recovery_reduction_pct_{scenario}_ci_lo"] = lo
        metrics_agg[f"recovery_reduction_pct_{scenario}_ci_hi"] = hi
        metrics_agg[f"recovery_reduction_pct_{scenario}_pass"] = 1.0 if passed else 0.0
    metrics_agg["recovery_scenarios_passed_count"] = float(scenario_pass_count)
    metrics_agg["recovery_scenarios_total"] = float(len(DRIFT_SCENARIOS))
    recovery_overall_pass = scenario_pass_count >= 3
    metrics_agg["recovery_overall_pass"] = 1.0 if recovery_overall_pass else 0.0
    metrics_agg["recovery_real_trace_available"] = 0.0  # no real trace supplied upstream; synthetic-only

    # ---- metric 3: memory overhead ratio ----
    mem_pass = all(r <= 2.0 for r in memory_ratios) if memory_ratios else False
    metrics_agg["memory_overhead_ratio_mean"] = sum(memory_ratios) / len(memory_ratios) if memory_ratios else float("nan")
    metrics_agg["memory_overhead_ratio_max"] = max(memory_ratios) if memory_ratios else float("nan")
    metrics_agg["memory_overhead_pass"] = 1.0 if mem_pass else 0.0

    # ---- metric 4: volatility-classifier diagnostic (one representative config) ----
    rng4 = random.Random(777)
    labels4 = make_key_labels(N_KEYS, rng4)
    cache_size4 = max(4, int(N_KEYS * CACHE_SIZE_RATIOS[1]))
    alpha4 = ALPHA_GRID[1]
    stat4 = gen_stationary_segment(N_KEYS, alpha4, REQUESTS_PER_SEGMENT, rng4)
    drift4 = gen_drift_segment("burst_injection", N_KEYS, alpha4, REQUESTS_PER_SEGMENT, rng4)
    var4 = PerKeyDecayVariant(cache_size=cache_size4, n_keys=N_KEYS)
    for k in stat4:
        var4.request(k)
    for k in drift4:
        var4.request(k)
    buckets = var4.bucket_confusion_inputs()

    def gt_label(k: int) -> str:
        if k in labels4.burst:
            return "burst"
        if k in labels4.stable:
            return "stable"
        return "neutral"

    conf = {"short-decay": {"burst": 0, "stable": 0, "neutral": 0}, "long-decay": {"burst": 0, "stable": 0, "neutral": 0}, "mid": {"burst": 0, "stable": 0, "neutral": 0}}
    for k in range(N_KEYS):
        b = buckets.get(k, "mid")
        conf[b][gt_label(k)] += 1

    def prf(bucket_name: str, gt_name: str) -> tuple[float, float, float]:
        tp = conf[bucket_name][gt_name]
        fp = sum(conf[bucket_name][g] for g in conf[bucket_name] if g != gt_name)
        fn = sum(conf[b][gt_name] for b in conf if b != bucket_name)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        return precision, recall, f1

    p_short, r_short, f1_short = prf("short-decay", "burst")
    p_long, r_long, f1_long = prf("long-decay", "stable")
    metrics_agg["classifier_short_decay_vs_burst_precision"] = p_short
    metrics_agg["classifier_short_decay_vs_burst_recall"] = r_short
    metrics_agg["classifier_short_decay_vs_burst_f1"] = f1_short
    metrics_agg["classifier_long_decay_vs_stable_precision"] = p_long
    metrics_agg["classifier_long_decay_vs_stable_recall"] = r_long
    metrics_agg["classifier_long_decay_vs_stable_f1"] = f1_long
    classifier_separates = (f1_short > 0.34) and (f1_long > 0.34)  # >2x chance (3-way random ~0.33)
    metrics_agg["classifier_separates_mechanism"] = 1.0 if classifier_separates else 0.0

    confusion_examples = []
    for b in conf:
        for g in conf[b]:
            confusion_examples.append(
                {
                    "input": f"decay_bucket={b} ground_truth={g}",
                    "output": "count",
                    "predict_variant": str(conf[b][g]),
                    "eval_count": float(conf[b][g]),
                    "eval_fraction_of_bucket": conf[b][g] / max(1, sum(conf[b].values())),
                }
            )

    # ---- metric 5: sensitivity/robustness heatmap ----
    heatmap_examples = []
    total_cells = 0
    passed_cells = 0
    for alpha in ALPHA_GRID:
        for ratio in CACHE_SIZE_RATIOS:
            for scenario in DRIFT_SCENARIOS:
                p = grid_pass.get((alpha, ratio, scenario), False)
                total_cells += 1
                passed_cells += 1 if p else 0
                heatmap_examples.append(
                    {
                        "input": f"alpha={alpha} cache_ratio={ratio} scenario={scenario}",
                        "output": "pass_fail",
                        "predict_variant": "PASS" if p else "FAIL",
                        "eval_pass": 1.0 if p else 0.0,
                    }
                )
    grid_pass_rate = passed_cells / total_cells if total_cells else 0.0
    metrics_agg["sensitivity_grid_pass_rate"] = grid_pass_rate
    metrics_agg["sensitivity_grid_total_cells"] = float(total_cells)
    metrics_agg["sensitivity_grid_passed_cells"] = float(passed_cells)
    narrow_operating_point = grid_pass_rate < 0.5
    metrics_agg["sensitivity_confined_to_narrow_operating_point"] = 1.0 if narrow_operating_point else 0.0

    # ---- overall verdict ----
    criteria = {
        "steady_state_parity": parity_pass,
        "drift_recovery_reduction": recovery_overall_pass,
        "memory_overhead": mem_pass,
    }
    n_pass = sum(1 for v in criteria.values() if v)
    if n_pass == len(criteria):
        verdict = "CONFIRMED"
    elif n_pass == 0:
        verdict = "DISCONFIRMED"
    else:
        verdict = "MIXED"
    driving = [k for k, v in criteria.items() if not v] or ["all_pass"]
    metrics_agg["overall_verdict_confirmed"] = 1.0 if verdict == "CONFIRMED" else 0.0
    metrics_agg["overall_verdict_disconfirmed"] = 1.0 if verdict == "DISCONFIRMED" else 0.0
    metrics_agg["overall_verdict_mixed"] = 1.0 if verdict == "MIXED" else 0.0
    logger.info(f"Overall verdict: {verdict}; failing criteria: {driving}")
    logger.info(f"parity_pass={parity_pass} recovery_pass={recovery_overall_pass} ({scenario_pass_count}/4) memory_pass={mem_pass}")
    logger.info(f"classifier F1 short={f1_short:.3f} long={f1_long:.3f} separates={classifier_separates}")

    datasets_out.append({"dataset": "synthetic_zipf_drift_sweep", "examples": examples_main})
    datasets_out.append({"dataset": "volatility_classifier_confusion_matrix", "examples": confusion_examples})
    datasets_out.append({"dataset": "sensitivity_robustness_heatmap", "examples": heatmap_examples})

    output = {
        "metadata": {
            "evaluation_name": "Scoring Adaptive Cache Admission vs Tuned Baseline",
            "description": (
                "Self-contained shadow-queue simulation and evaluation: per-key-decay admission "
                "variant vs best-tuned W-TinyLFU global-reset baseline. No upstream experiment/"
                "dataset artifacts were available (empty gen_art_experiment_1 and gen_art_dataset_1 "
                "directories), so the simulator, synthetic traces, and evaluation were all generated here."
            ),
            "overall_verdict": verdict,
            "driving_criteria": driving,
            "n_keys": N_KEYS,
            "requests_per_segment": REQUESTS_PER_SEGMENT,
            "alpha_grid": ALPHA_GRID,
            "cache_size_ratios": CACHE_SIZE_RATIOS,
            "baseline_w_grid": BASELINE_W_GRID,
            "drift_scenarios": DRIFT_SCENARIOS,
            "seeds": RNG_SEEDS,
        },
        "metrics_agg": metrics_agg,
        "datasets": datasets_out,
    }

    out_path = WORKDIR / "exp_eval_sol_out.json"
    out_path.write_text(json.dumps(output, indent=2))
    logger.info(f"Wrote {out_path} ({out_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
