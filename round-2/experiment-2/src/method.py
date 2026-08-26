#!/usr/bin/env python3
"""Diagnostic: is inter-arrival-CV's near-chance burst/stable precision a fixable
window-size / threshold-placement artifact, or a fundamental limit of the statistic?

No cache-admission simulation here -- this is a pure labeling/classification study.
For each synthetic cache-trace, we build per-key inter-arrival-gap histories, compute
rolling CV (and MAD/mean) at several window lengths, classify keys into
burst / stable / neutral under several threshold strategies (fixed, percentile-fit,
oracle grid-search), and score against derived ground-truth key labels.
"""

import argparse
import gc
import itertools
import json
import resource
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from loguru import logger

WORKDIR = Path(__file__).resolve().parent
DATA_DIR = WORKDIR / "data"
RESULTS_DIR = WORKDIR / "results"
RESULTS_DIR.mkdir(exist_ok=True)

logger.remove()
logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss}|{level:<7}|{message}")
logger.add(WORKDIR / "logs" / "run.log", rotation="30 MB", level="DEBUG")

# ----------------------------- resource limits ------------------------------
RAM_BUDGET_BYTES = 8 * 1024**3  # 8GB is generous for <1M rows of ints
resource.setrlimit(resource.RLIMIT_AS, (RAM_BUDGET_BYTES * 3, RAM_BUDGET_BYTES * 3))

WINDOW_LENGTHS = [4, 8, 16, 32]
PRIMARY_TRACES = [  # traces that actually contain injected bursts (ground truth exists)
    "synthetic_alpha0.8_cold_burst",
    "synthetic_alpha1.0_cold_burst",
    "synthetic_alpha0.8_combined",
    "synthetic_alpha1.0_combined",
    "synthetic_alpha1.2_combined",
]
AUX_TRACES = [  # no burst events by construction -- stable-label sanity check only
    "synthetic_alpha0.8_rank_shuffle",
    "synthetic_alpha1.0_rank_shuffle",
    "synthetic_alpha0.8_slow_drift",
    "synthetic_alpha1.0_slow_drift",
]
STABLE_TOP_K = 200  # top-K by frequency, never touched by any drift event -> "stable"
RNG_SEED = 0
N_BOOTSTRAP = 1000
PERCENTILE_PAIRS = [(25, 75), (33, 67), (40, 60)]


# --------------------------------- loading -----------------------------------
def load_traces(data_dir: Path, trace_names: list[str], mini: bool = False) -> dict[str, dict]:
    """Load only the requested trace names from the (possibly multi-part) full_data_out.

    Returns {trace_id: {"t": np.array, "k": np.array, "burst_key_ids": set[int]}}.
    """
    if mini:
        files = [data_dir / "mini_data_out.json"]
    else:
        part_dir = data_dir / "full_data_out"
        files = sorted(part_dir.glob("full_data_out_*.json"))
        if not files:
            files = [data_dir / "full_data_out.json"]

    wanted = set(trace_names)
    out: dict[str, dict] = {}
    for f in files:
        if not wanted:
            break
        logger.info(f"Scanning {f.name} for {sorted(wanted)}")
        raw = json.loads(f.read_text())
        for ds in raw["datasets"]:
            name = ds["dataset"]
            if name not in wanted:
                continue
            ts = np.empty(len(ds["examples"]), dtype=np.int64)
            ks = np.empty(len(ds["examples"]), dtype=np.int64)
            burst_key_ids: set[int] = set()
            for i, ex in enumerate(ds["examples"]):
                row = json.loads(ex["input"])
                ts[i] = row["t"]
                ks[i] = row["k"]
                for ev in ex.get("metadata_drift_event", []) or []:
                    if ev.get("type") == "cold_burst" and "burst_key_id" in ev:
                        burst_key_ids.add(int(ev["burst_key_id"]))
            out[name] = {"t": ts, "k": ks, "burst_key_ids": burst_key_ids}
            logger.info(f"  loaded {name}: {len(ts)} rows, {len(burst_key_ids)} burst keys")
            wanted.discard(name)
        del raw
        gc.collect()
    if wanted:
        logger.warning(f"Traces not found in data files: {wanted}")
    return out


# --------------------------- labels + inter-arrivals --------------------------
def derive_labels(trace: dict) -> dict[int, str]:
    """burst = keys named as a cold_burst event's burst_key_id.
    stable = top-STABLE_TOP_K keys by total frequency that were NEVER a burst key.
    everything else = neutral (excluded from the 2-way burst/stable eval)."""
    keys, counts = np.unique(trace["k"], return_counts=True)
    order = np.argsort(-counts)
    labels: dict[int, str] = {}
    burst_ids = trace["burst_key_ids"]
    for kid in burst_ids:
        labels[int(kid)] = "burst"
    n_stable = 0
    for idx in order:
        kid = int(keys[idx])
        if kid in labels:
            continue
        labels[kid] = "stable"
        n_stable += 1
        if n_stable >= STABLE_TOP_K:
            break
    return labels


def build_inter_arrivals(trace: dict) -> dict[int, np.ndarray]:
    """Per key: sorted-by-t inter-arrival gaps (diffs between consecutive requests)."""
    order = np.argsort(trace["t"], kind="stable")
    t_sorted = trace["t"][order]
    k_sorted = trace["k"][order]
    df = pd.DataFrame({"t": t_sorted, "k": k_sorted})
    gaps: dict[int, np.ndarray] = {}
    for kid, grp in df.groupby("k", sort=False)["t"]:
        arr = grp.to_numpy()
        if len(arr) < 2:
            continue
        gaps[int(kid)] = np.diff(arr).astype(np.float64)
    return gaps


def decision_point_stat(gap_window: np.ndarray, statistic: str) -> float:
    mean = gap_window.mean()
    if mean == 0:
        return np.nan
    if statistic == "cv":
        if len(gap_window) < 2:
            return np.nan
        return gap_window.std(ddof=1) / mean
    if statistic == "mad_mean":
        med = np.median(gap_window)
        return np.median(np.abs(gap_window - med)) / mean
    raise ValueError(statistic)


def compute_stats_for_window(
    gaps: dict[int, np.ndarray], labels: dict[int, str], window: int, statistic: str
) -> pd.DataFrame:
    """One decision-point statistic value per key that has >= window gaps, using the
    LAST `window` gaps observed (mimics a live shadow-queue classifier: only past data
    is available at decision time). Also records the full within-key rolling
    distribution's std (to separate window LENGTH from SAMPLE COUNT effects)."""
    rows = []
    for kid, g in gaps.items():
        if len(g) < window:
            continue
        label = labels.get(kid, "neutral")
        decision_window = g[-window:]
        stat = decision_point_stat(decision_window, statistic)
        # full rolling distribution across this key's history at this window length --
        # capped to at most MAX_ROLL_POSITIONS evenly-spaced positions (a very hot key
        # can have thousands of gaps; an uncapped python loop there dominates runtime
        # while adding no precision to a std-of-CV summary statistic).
        n_positions = len(g) - window + 1
        if n_positions > 1:
            MAX_ROLL_POSITIONS = 50
            if n_positions > MAX_ROLL_POSITIONS:
                sample_starts = np.linspace(0, n_positions - 1, MAX_ROLL_POSITIONS).astype(int)
            else:
                sample_starts = np.arange(n_positions)
            roll_vals = np.array(
                [decision_point_stat(g[i : i + window], statistic) for i in sample_starts]
            )
            roll_std = float(np.nanstd(roll_vals))
        else:
            roll_std = np.nan
        rows.append(
            {"key": kid, "label": label, "stat": stat, "n_gaps": len(g), "roll_std": roll_std}
        )
    return pd.DataFrame(rows)


# ------------------------------- classification --------------------------------
# All hot-path classification/metric/bootstrap code below operates on plain numpy
# arrays, NOT pandas Series. The original implementation built a fresh pd.Series
# (with its index-alignment machinery) on every one of the ~1000 bootstrap
# iterations x ~800 (combo, class) pairs -- that per-iteration pandas overhead is
# what made the previous run hang past the container's time budget without ever
# reaching a class imbalanced enough (1 burst key per 80k-row trace) to be worth
# that cost. Numpy string-array comparisons are ~2 orders of magnitude cheaper here.
def classify_fixed_np(stat: np.ndarray, low: float, high: float) -> np.ndarray:
    """low CV -> stable (steady inter-arrival), high CV -> burst (bursty/irregular)."""
    out = np.full(stat.shape, "neutral", dtype=object)
    out[stat <= low] = "stable"
    out[stat >= high] = "burst"
    return out


def macro_f1_np(pred: np.ndarray, label: np.ndarray, classes=("burst", "stable")) -> float:
    mask = np.isin(label, classes)
    if mask.sum() == 0:
        return np.nan
    p, l = pred[mask], label[mask]
    f1s = []
    for c in classes:
        n_true = (l == c).sum()
        if n_true == 0:
            continue
        tp = ((p == c) & (l == c)).sum()
        fp = ((p == c) & (l != c)).sum()
        fn = ((p != c) & (l == c)).sum()
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1s.append(2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0)
    return float(np.mean(f1s)) if f1s else np.nan


def oracle_thresholds(stat: np.ndarray, label: np.ndarray) -> tuple[float, float, float]:
    """In-sample grid search over threshold pairs maximizing macro-F1 (burst/stable
    only) -- an explicit upper-bound ceiling, not a generalization estimate."""
    valid = stat[~np.isnan(stat)]
    if valid.size == 0:
        return np.nan, np.nan, np.nan
    candidates = np.unique(np.percentile(valid, np.linspace(1, 99, 15)))
    best = (-1.0, np.nan, np.nan)
    for low, high in itertools.product(candidates, candidates):
        if low >= high:
            continue
        f1 = macro_f1_np(classify_fixed_np(stat, low, high), label, classes=("burst", "stable"))
        if f1 > best[0]:
            best = (f1, low, high)
    return best[1], best[2], best[0]


def class_metrics_np(pred: np.ndarray, label: np.ndarray, cls: str) -> tuple[float, float, float]:
    tp = ((pred == cls) & (label == cls)).sum()
    fp = ((pred == cls) & (label != cls)).sum()
    fn = ((pred != cls) & (label == cls)).sum()
    prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
    return prec, rec, f1


def bootstrap_ci_np(
    pred: np.ndarray, label: np.ndarray, cls: str, metric: str, n_boot: int, rng: np.random.Generator
) -> tuple[float, float]:
    """Fully vectorized bootstrap: draw ALL n_boot resamples of indices at once,
    gather predicted/true labels for every resample in one shot, then compute
    per-resample TP/FP/FN with array ops (no per-iteration pandas/Python objects)."""
    n = len(pred)
    if n == 0:
        return np.nan, np.nan
    samp = rng.integers(0, n, size=(n_boot, n))  # (n_boot, n) resampled indices
    p = pred[samp]
    l = label[samp]
    is_p = p == cls
    is_l = l == cls
    tp = (is_p & is_l).sum(axis=1).astype(np.float64)
    fp = (is_p & ~is_l).sum(axis=1).astype(np.float64)
    fn = (~is_p & is_l).sum(axis=1).astype(np.float64)
    with np.errstate(invalid="ignore", divide="ignore"):
        prec = np.where(tp + fp > 0, tp / (tp + fp), 0.0)
        rec = np.where(tp + fn > 0, tp / (tp + fn), 0.0)
        f1 = np.where(prec + rec > 0, 2 * prec * rec / (prec + rec), 0.0)
    vals = {"precision": prec, "recall": rec, "f1": f1}[metric]
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def chance_baseline_np(label: np.ndarray, classes=("burst", "stable")) -> float:
    """Macro-F1 of a random classifier that predicts each class with its true prior
    (expected precision == prevalence, expected recall == prevalence -> expected F1 ==
    prevalence), matched to the ACTUAL class balance rather than assuming 1/3."""
    mask = np.isin(label, classes)
    n = mask.sum()
    if n == 0:
        return np.nan
    f1s = [float((label[mask] == c).sum()) / n for c in classes]
    return float(np.mean(f1s))


# ------------------------------- evaluation loop --------------------------------
def evaluate_combo(
    df: pd.DataFrame, threshold_kind: str, threshold_params: dict, rng: np.random.Generator
) -> dict | None:
    if df.empty or "stat" not in df.columns:
        return None
    df2 = df.dropna(subset=["stat"])
    df2 = df2[df2["label"].isin(["burst", "stable"])]
    if df2.empty or df2["label"].nunique() < 1:
        return None
    stat = df2["stat"].to_numpy(dtype=np.float64)
    label = df2["label"].to_numpy(dtype=object)

    if threshold_kind == "fixed":
        pred = classify_fixed_np(stat, threshold_params["low"], threshold_params["high"])
        low, high = threshold_params["low"], threshold_params["high"]
    elif threshold_kind == "percentile":
        low = float(np.percentile(stat, threshold_params["lo_pct"]))
        high = float(np.percentile(stat, threshold_params["hi_pct"]))
        pred = classify_fixed_np(stat, low, high)
    elif threshold_kind == "oracle":
        low, high, _ = oracle_thresholds(stat, label)
        pred = classify_fixed_np(stat, low, high) if not np.isnan(low) else np.full(stat.shape, "neutral", dtype=object)
    else:
        raise ValueError(threshold_kind)

    macro = macro_f1_np(pred, label, classes=("burst", "stable"))
    b_prec, b_rec, b_f1 = class_metrics_np(pred, label, "burst")
    s_prec, s_rec, s_f1 = class_metrics_np(pred, label, "stable")
    chance = chance_baseline_np(label)
    b_ci = bootstrap_ci_np(pred, label, "burst", "precision", N_BOOTSTRAP, rng)
    s_ci = bootstrap_ci_np(pred, label, "stable", "precision", N_BOOTSTRAP, rng)
    accuracy = float((pred == label).mean())
    return {
        "threshold_kind": threshold_kind,
        "threshold_low": low,
        "threshold_high": high,
        "n_keys_evaluated": int(len(df2)),
        "accuracy": accuracy,
        "macro_f1": macro,
        "chance_baseline_macro_f1": chance,
        "clears_2x_chance": bool(macro >= 2 * chance) if not np.isnan(chance) and chance > 0 else False,
        "burst_precision": float(b_prec),
        "burst_recall": float(b_rec),
        "burst_f1": float(b_f1),
        "burst_precision_ci_low": b_ci[0],
        "burst_precision_ci_high": b_ci[1],
        "stable_precision": float(s_prec),
        "stable_recall": float(s_rec),
        "stable_f1": float(s_f1),
        "stable_precision_ci_low": s_ci[0],
        "stable_precision_ci_high": s_ci[1],
    }


def run_sweep(all_dfs: dict[tuple[str, int, str], pd.DataFrame], rng: np.random.Generator) -> list[dict]:
    results = []
    fixed_thresholds = {"low": 0.5, "high": 1.5}  # reconstructed approximation (see caveat below)
    for (trace_name, window, statistic), df in all_dfs.items():
        threshold_variants = [("fixed_reconstructed", "fixed", fixed_thresholds)]
        for lo, hi in PERCENTILE_PAIRS:
            threshold_variants.append(
                (f"percentile_{lo}_{hi}", "percentile", {"lo_pct": lo, "hi_pct": hi})
            )
        threshold_variants.append(("oracle", "oracle", {}))

        for variant_name, kind, params in threshold_variants:
            res = evaluate_combo(df, kind, params, rng)
            if res is None:
                continue
            res.update(
                {
                    "trace": trace_name,
                    "window": window,
                    "statistic": statistic,
                    "threshold_variant": variant_name,
                }
            )
            results.append(res)
    return results


# ------------------------------------ main --------------------------------------
def build_all_dfs(
    traces: dict[str, dict], windows: list[int], statistics: list[str]
) -> dict[tuple[str, int, str], pd.DataFrame]:
    all_dfs: dict[tuple[str, int, str], pd.DataFrame] = {}
    for trace_name, trace in traces.items():
        labels = derive_labels(trace)
        n_burst = sum(1 for v in labels.values() if v == "burst")
        n_stable = sum(1 for v in labels.values() if v == "stable")
        logger.info(f"[{trace_name}] derived labels: burst={n_burst} stable={n_stable}")
        gaps = build_inter_arrivals(trace)
        logger.info(f"[{trace_name}] keys with >=2 arrivals: {len(gaps)}")
        for window in windows:
            n_usable = sum(1 for g in gaps.values() if len(g) >= window)
            logger.info(f"[{trace_name}] window={window}: {n_usable} keys have enough history")
            for statistic in statistics:
                df = compute_stats_for_window(gaps, labels, window, statistic)
                all_dfs[(trace_name, window, statistic)] = df
        del gaps
        gc.collect()

    # pool burst keys across ALL primary traces into one larger set for the headline
    # verdict (fallback plan point 4) -- per-trace burst counts are tiny (1 burst event
    # per 80k-row trace) so per-trace bootstrap CIs would be uninformatively wide.
    for window in windows:
        for statistic in statistics:
            parts = [
                all_dfs[(t, window, statistic)]
                for t in PRIMARY_TRACES
                if (t, window, statistic) in all_dfs and not all_dfs[(t, window, statistic)].empty
            ]
            if parts:
                all_dfs[("pooled_primary", window, statistic)] = pd.concat(parts, ignore_index=True)
    return all_dfs


def summarize_verdict(results: list[dict]) -> dict:
    primary = [r for r in results if r["trace"] == "pooled_primary"]
    if not primary:
        primary = [r for r in results if r["trace"] in PRIMARY_TRACES]
    if not primary:
        return {
            "verdict": "inconclusive",
            "reason": "no primary-trace results",
            "n_primary_combos_evaluated": 0,
            "n_non_oracle_combos_clearing_2x_chance": 0,
            "n_oracle_combos_clearing_2x_chance": 0,
            "best_overall_combo": {
                "trace": None, "window": None, "statistic": None, "threshold_variant": None,
                "macro_f1": float("nan"), "chance_baseline_macro_f1": float("nan"),
                "burst_precision": float("nan"), "burst_recall": float("nan"),
                "stable_precision": float("nan"), "stable_recall": float("nan"),
                "burst_precision_ci_low": float("nan"), "burst_precision_ci_high": float("nan"),
            },
            "cv_oracle_macro_f1_by_window_pooled_primary": {},
            "cv_macro_f1_monotonically_improves_with_window": None,
        }

    def bar_clearers(rows):
        return [r for r in rows if r.get("clears_2x_chance")]

    non_oracle = [r for r in primary if r["threshold_variant"] != "oracle"]
    oracle = [r for r in primary if r["threshold_variant"] == "oracle"]
    non_oracle_clear = bar_clearers(non_oracle)
    oracle_clear = bar_clearers(oracle)

    best_overall = max(primary, key=lambda r: r["macro_f1"] if not np.isnan(r["macro_f1"]) else -1)

    # monotonic-with-window check (CV, oracle thresholds, pooled across primary traces)
    window_perf = defaultdict(list)
    for r in primary:
        if r["threshold_variant"] == "oracle" and r["statistic"] == "cv":
            window_perf[r["window"]].append(r["macro_f1"])
    window_means = {w: float(np.mean(v)) for w, v in window_perf.items() if v}
    windows_sorted = sorted(window_means)
    monotonic_improves = all(
        window_means[windows_sorted[i + 1]] >= window_means[windows_sorted[i]] - 1e-9
        for i in range(len(windows_sorted) - 1)
    ) if len(windows_sorted) > 1 else None

    if not oracle_clear:
        verdict = "fundamental_limit"
        reason = (
            "Even oracle (in-sample, upper-bound) thresholds fail to clear macro-F1 >= "
            "2x the matched chance baseline at any window/statistic on the primary "
            "burst-labeled traces -- CV and MAD/mean carry too little burst/stable "
            "signal for tuning to rescue, independent of window length or threshold "
            "placement."
        )
    elif not non_oracle_clear:
        verdict = "artifact_partially_fixable_only_with_oracle_tuning"
        reason = (
            "Oracle thresholds clear the bar but no realistic (fixed or percentile-fit, "
            "non-oracle) threshold does -- the ceiling exists but is not reachable "
            "without label leakage, so in a deployed classifier the near-chance result "
            "is effectively a fundamental limit, not a window/threshold artifact fixable "
            "in practice."
        )
    else:
        verdict = "window_threshold_artifact"
        reason = (
            "At least one realistic (non-oracle) window/threshold combination clears "
            "macro-F1 >= 2x the matched chance baseline on primary burst-labeled traces "
            "-- the prior near-chance result is consistent with a fixable window-size "
            "or threshold-placement artifact rather than CV being fundamentally "
            "uninformative."
        )

    return {
        "verdict": verdict,
        "reason": reason,
        "n_primary_combos_evaluated": len(primary),
        "n_non_oracle_combos_clearing_2x_chance": len(non_oracle_clear),
        "n_oracle_combos_clearing_2x_chance": len(oracle_clear),
        "best_overall_combo": {
            k: best_overall[k]
            for k in [
                "trace",
                "window",
                "statistic",
                "threshold_variant",
                "macro_f1",
                "chance_baseline_macro_f1",
                "burst_precision",
                "burst_recall",
                "stable_precision",
                "stable_recall",
                "burst_precision_ci_low",
                "burst_precision_ci_high",
            ]
        },
        "cv_oracle_macro_f1_by_window_pooled_primary": window_means,
        "cv_macro_f1_monotonically_improves_with_window": monotonic_improves,
    }


def per_key_examples(all_dfs: dict[tuple[str, int, str], pd.DataFrame]) -> list[dict]:
    """Emit per-key rows (input/output + eval_ fields) for the exp_eval_sol_out schema,
    at the single best-diagnostic (window=8, cv) slice per trace, keeping payload small."""
    examples = []
    for (trace_name, window, statistic), df in all_dfs.items():
        if window != 8 or statistic != "cv":
            continue
        for _, row in df.iterrows():
            examples.append(
                {
                    "input": json.dumps({"trace": trace_name, "key": int(row["key"])}),
                    "output": row["label"],
                    "metadata_window": window,
                    "metadata_statistic": statistic,
                    "metadata_n_gaps": int(row["n_gaps"]),
                    "predict_true_label": row["label"],
                    "eval_cv_decision_stat": float(row["stat"]) if not pd.isna(row["stat"]) else -1.0,
                }
            )
    if not examples:
        examples.append(
            {
                "input": json.dumps({"trace": "none", "key": -1}),
                "output": "neutral",
                "predict_true_label": "neutral",
                "eval_cv_decision_stat": -1.0,
            }
        )
    return examples


def main(mini: bool = False) -> None:
    logger.info(f"Starting run (mini={mini})")
    trace_names = PRIMARY_TRACES + AUX_TRACES
    traces = load_traces(DATA_DIR, trace_names, mini=mini)
    if not traces:
        raise RuntimeError("No traces loaded -- check trace names against dataset schema")

    statistics = ["cv", "mad_mean"]
    all_dfs = build_all_dfs(traces, WINDOW_LENGTHS, statistics)
    del traces
    gc.collect()

    rng = np.random.default_rng(RNG_SEED)
    results = run_sweep(all_dfs, rng)
    logger.info(f"Evaluated {len(results)} (trace, window, statistic, threshold) combos")

    verdict = summarize_verdict(results)
    logger.info(f"VERDICT: {verdict['verdict']} -- {verdict['reason']}")

    metrics_agg = {
        "n_combos_evaluated": len(results),
        "n_traces": len(all_dfs and {k[0] for k in all_dfs}),
        "n_windows": len(WINDOW_LENGTHS),
        "n_primary_non_oracle_clearing_2x_chance": verdict["n_non_oracle_combos_clearing_2x_chance"],
        "n_primary_oracle_clearing_2x_chance": verdict["n_oracle_combos_clearing_2x_chance"],
        "best_macro_f1": verdict["best_overall_combo"]["macro_f1"],
        "best_chance_baseline": verdict["best_overall_combo"]["chance_baseline_macro_f1"],
        "verdict_is_window_threshold_artifact": float(verdict["verdict"] == "window_threshold_artifact"),
        "verdict_is_fundamental_limit": float(verdict["verdict"] == "fundamental_limit"),
    }

    caveats = [
        "Ground-truth burst/stable labels are DERIVED, not an authoritative pre-existing "
        "field: burst = keys named as burst_key_id in a cold_burst drift event; stable = "
        f"top-{STABLE_TOP_K} keys by total request frequency never touched by any drift "
        "event. Neutral/other keys are excluded from the burst/stable evaluation.",
        "The 'fixed_reconstructed' threshold variant (CV<0.5=stable, CV>1.5=burst) is a "
        "RECONSTRUCTED approximation -- the prior experiment's exact original thresholds "
        "and window-alignment convention could not be located in this run's artifact "
        "history, so this is NOT an exact reproduction/control of the prior 0.10-precision "
        "result (fallback plan point 2).",
        "The decision-point CV/MAD-mean statistic uses the LAST `window` inter-arrival "
        "gaps per key (mimicking a live shadow-queue classifier with only past data "
        "available at decision time).",
        "Oracle thresholds are grid-searched IN-SAMPLE on the same evaluation data -- they "
        "report an upper-bound ceiling on achievable performance with this statistic "
        "family, not a fair generalization estimate.",
        "AUX_TRACES (rank_shuffle, slow_drift) contain no injected burst events by "
        "construction; they contribute stable-label sanity checks only and are excluded "
        "from the primary verdict, which is computed on cold_burst/combined traces only.",
        "Keys are NOT subsampled to a common set across window lengths; each window length "
        "is evaluated on the largest valid key subset for that window, so n_keys_evaluated "
        "varies by window and a shrinking subset at larger W is itself part of the finding.",
        "Chance baseline is recomputed per combo from the ACTUAL class balance present "
        "(prevalence-weighted macro-F1 of a random/majority-matched classifier), not "
        "assumed to be 1/3.",
    ]

    out = {
        "metadata": {
            "evaluation_name": "cv_volatility_window_threshold_artifact_diagnostic",
            "description": (
                "Sweeps rolling-window length (4/8/16/32) and threshold placement "
                "(fixed-reconstructed / percentile-fit / oracle) for inter-arrival CV "
                "(and MAD/mean) as a burst/stable key classifier on synthetic drift "
                "traces, to determine whether a prior near-chance precision result is a "
                "fixable window/threshold artifact or a fundamental limit of the statistic."
            ),
            "window_lengths": WINDOW_LENGTHS,
            "statistics": statistics,
            "primary_traces": PRIMARY_TRACES,
            "aux_traces": AUX_TRACES,
            "percentile_pairs": PERCENTILE_PAIRS,
            "n_bootstrap": N_BOOTSTRAP,
            "verdict": verdict,
            "caveats": caveats,
            "full_results_table": results,
        },
        "metrics_agg": metrics_agg,
        "datasets": [
            {"dataset": "cv_window_threshold_sweep", "examples": per_key_examples(all_dfs)}
        ],
    }

    out_path = WORKDIR / "method_out.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    logger.info(f"Saved {out_path} ({out_path.stat().st_size / 1e6:.2f} MB)")

    results_table_path = RESULTS_DIR / "full_results_table.json"
    results_table_path.write_text(json.dumps(results, indent=2, default=str))
    logger.info(f"Saved detailed results table to {results_table_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mini", action="store_true", help="Run on mini_data_out.json for smoke test")
    args = parser.parse_args()
    logger.catch(reraise=True)(main)(mini=args.mini)
