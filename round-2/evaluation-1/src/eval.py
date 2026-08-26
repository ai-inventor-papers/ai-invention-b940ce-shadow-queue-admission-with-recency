#!/usr/bin/env python3
"""Causal-attribution evaluation for the per-key-decay cache admission experiment.

Consumes art_0aR0TOK6EOBa's method_out.json. Does NOT re-run any simulation.
Inventories which of the ablation/window-sweep/RetailRocket/second-accounting
data the artifact plan calls for actually exist, performs the strongest
analysis the *actually present* data supports, and is explicit wherever the
requested causal decomposition cannot be done.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from itertools import product
from pathlib import Path
from typing import Any

import numpy as np
from loguru import logger
from scipy import stats

logger.remove()
logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss}|{level:<7}|{message}")
Path("logs").mkdir(exist_ok=True)
logger.add("logs/run.log", rotation="30 MB", level="DEBUG")

WORKSPACE = Path(__file__).parent
EXPERIMENT_DIR = Path(
    "/ai-inventor/aii_data/runs/run_txuMz_zeCwr8/3_invention_loop/iter_1/gen_art/gen_art_experiment_1"
)
DATASET_DIR = Path(
    "/ai-inventor/aii_data/runs/run_txuMz_zeCwr8/3_invention_loop/iter_1/gen_art/gen_art_dataset_1"
)

N_BOOT = 2000
RNG_SEED = 0


def bootstrap_ci(values: np.ndarray, statistic=np.mean, n_boot: int = N_BOOT, seed: int = RNG_SEED) -> dict:
    """Percentile bootstrap CI. `values` resampled with replacement."""
    rng = np.random.default_rng(seed)
    values = np.asarray(values, dtype=float)
    n = len(values)
    if n == 0:
        return {"point": float("nan"), "ci_low": float("nan"), "ci_high": float("nan"), "n": 0}
    if n == 1:
        point = float(statistic(values))
        return {"point": point, "ci_low": point, "ci_high": point, "n": 1}
    boot_stats = np.empty(n_boot)
    for i in range(n_boot):
        sample = values[rng.integers(0, n, size=n)]
        boot_stats[i] = statistic(sample)
    return {
        "point": float(statistic(values)),
        "ci_low": float(np.percentile(boot_stats, 2.5)),
        "ci_high": float(np.percentile(boot_stats, 97.5)),
        "n": int(n),
    }


def bootstrap_diff_ci(a: np.ndarray, b: np.ndarray, n_boot: int = N_BOOT, seed: int = RNG_SEED) -> dict:
    """Bootstrap CI on mean(a) - mean(b), independent resampling of each (unequal n allowed)."""
    rng = np.random.default_rng(seed)
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    na, nb = len(a), len(b)
    if na == 0 or nb == 0:
        return {"point": float("nan"), "ci_low": float("nan"), "ci_high": float("nan"), "n_a": na, "n_b": nb}
    diffs = np.empty(n_boot)
    for i in range(n_boot):
        sa = a[rng.integers(0, na, size=na)]
        sb = b[rng.integers(0, nb, size=nb)]
        diffs[i] = sa.mean() - sb.mean()
    return {
        "point": float(a.mean() - b.mean()),
        "ci_low": float(np.percentile(diffs, 2.5)),
        "ci_high": float(np.percentile(diffs, 97.5)),
        "n_a": int(na),
        "n_b": int(nb),
    }


def holm_bonferroni(pvals: list[float]) -> list[float]:
    """Return Holm-Bonferroni adjusted p-values, same order as input."""
    m = len(pvals)
    order = np.argsort(pvals)
    adjusted = np.empty(m)
    running_max = 0.0
    for rank, idx in enumerate(order):
        val = (m - rank) * pvals[idx]
        running_max = max(running_max, val)
        adjusted[idx] = min(running_max, 1.0)
    return adjusted.tolist()


def ci_excludes_zero(ci_low: float, ci_high: float) -> bool:
    return (ci_low > 0) or (ci_high < 0)


# ---------------------------------------------------------------------------
# STEP 0: inventory what actually exists
# ---------------------------------------------------------------------------

@logger.catch(reraise=True)
def step0_inventory(full: dict) -> dict:
    logger.info("STEP 0: inventorying available fields in method_out.json")
    meta = full["metadata"]
    examples = full["datasets"][0]["examples"]
    configs = [ex["metadata_config"] for ex in examples]

    top_keys = set(meta.keys())
    cfg_keys: set[str] = set()
    for c in configs[:50]:
        cfg_keys.update(c.keys())
    systems = sorted({c["system"] for c in configs})

    def has_any(keys: set[str], needles: list[str]) -> bool:
        return any(any(n in k.lower() for n in needles) for k in keys)

    ablation_present = ("oracle" in systems) or has_any(cfg_keys | top_keys, ["oracle", "classifier_mode", "storage_mode", "unhashed"])
    window_sweep_present = has_any(top_keys, ["window_sweep", "threshold_sweep"]) or has_any(cfg_keys, ["window_length"])
    retailrocket_present = any(c.get("trace_source", "") == "real_retailrocket_events" for c in configs)
    per_config_collision_present = "decay_slot_collision_rate" in cfg_keys
    per_config_classifier_precision_present = has_any(cfg_keys, ["classifier_precision"])
    second_accounting_convention_present = isinstance(meta.get("memory_summary"), dict) and (
        "priced_per_key" in meta["memory_summary"] or "priced_shared_with_sketch" in meta["memory_summary"]
    )

    availability = {
        "sub_claim_a_window_threshold_sweep": "ABSENT",
        "sub_claim_b_three_arm_ablation": "ABSENT" if not ablation_present else "PRESENT",
        "sub_claim_b_correlational_substitute_fields": {
            "per_config_decay_slot_collision_rate": "PRESENT" if per_config_collision_present else "ABSENT",
            "per_config_classifier_precision": "PRESENT" if per_config_classifier_precision_present else "ABSENT",
        },
        "sub_claim_c_second_memory_accounting_convention": "PRESENT" if second_accounting_convention_present else "ABSENT",
        "retailrocket_real_trace_rows_in_method_out": "PRESENT" if retailrocket_present else "ABSENT",
        "systems_present": systems,
        "n_configs_run": meta.get("n_configs_run"),
        "top_level_metadata_keys": sorted(top_keys),
        "per_config_metadata_keys": sorted(cfg_keys),
        "notes": (
            "Confirmed by direct schema/key inspection of full_method_out.json: only 'baseline' and 'decay' "
            "systems exist (no oracle-labels or hashed/unhashed storage-mode ablation arms); no standalone "
            "window-length/threshold-placement labeling sweep exists; no real_retailrocket_events rows exist "
            "in this method_out.json (the experiment ran synthetic-only per its own documented scope reduction); "
            "metadata.memory_summary exposes exactly one pricing convention (the matched-memory 0.003%% figure), "
            "not two, so the 16.9x figure referenced in the hypothesis cannot be reconciled from this artifact's "
            "data -- it originates from a different, non-dependency simulator. Per-config decay_slot_collision_rate "
            "IS present (per decay-system example), enabling a correlational (not causal) substitute analysis for "
            "sub-claim (b); per-config classifier precision is NOT logged."
        ),
    }
    Path(WORKSPACE / "data_availability.json").write_text(json.dumps(availability, indent=2))
    logger.info(f"Data availability written: ablation={availability['sub_claim_b_three_arm_ablation']}, "
                f"window_sweep=ABSENT, retailrocket={availability['retailrocket_real_trace_rows_in_method_out']}, "
                f"second_accounting={availability['sub_claim_c_second_memory_accounting_convention']}")
    return availability


# ---------------------------------------------------------------------------
# STEP 1 (degraded branch): correlational deficit analysis + cell-level deficits
# ---------------------------------------------------------------------------

@logger.catch(reraise=True)
def step1_deficit_and_correlation(full: dict) -> dict:
    logger.info("STEP 1: cell-level deficits (baseline-best vs decay) + collision-rate correlational substitute")
    examples = full["datasets"][0]["examples"]
    configs = [ex["metadata_config"] for ex in examples]

    baseline = [c for c in configs if c["system"] == "baseline"]
    decay = [c for c in configs if c["system"] == "decay"]

    # group baseline by (alpha, cache_ratio, drift_scenario, seed) -> best over W_multiplier
    by_seed_cell: dict[tuple, list[dict]] = defaultdict(list)
    for c in baseline:
        key = (c["alpha"], c["cache_ratio"], c["drift_scenario"], c["seed"])
        by_seed_cell[key].append(c)

    baseline_best_per_seed_cell: dict[tuple, dict] = {}
    for key, rows in by_seed_cell.items():
        best = max(rows, key=lambda r: r["steady_state_hit_ratio"])
        baseline_best_per_seed_cell[key] = best

    decay_by_seed_cell: dict[tuple, dict] = {}
    for c in decay:
        key = (c["alpha"], c["cache_ratio"], c["drift_scenario"], c["seed"])
        decay_by_seed_cell[key] = c

    cells = sorted({(a, r, d) for (a, r, d, s) in by_seed_cell.keys()})
    cell_results = []
    hitratio_pvals = []
    recovery_pvals = []
    for (alpha, cache_ratio, drift) in cells:
        seeds = sorted({s for (a, r, d, s) in by_seed_cell if (a, r, d) == (alpha, cache_ratio, drift)})
        base_hr, decay_hr, base_rec, decay_rec = [], [], [], []
        for s in seeds:
            bkey = (alpha, cache_ratio, drift, s)
            if bkey in baseline_best_per_seed_cell and bkey in decay_by_seed_cell:
                b = baseline_best_per_seed_cell[bkey]
                dd = decay_by_seed_cell[bkey]
                base_hr.append(b["steady_state_hit_ratio"])
                decay_hr.append(dd["steady_state_hit_ratio"])
                base_rec.append(b["recovery_time_requests"])
                decay_rec.append(dd["recovery_time_requests"])
        if not base_hr:
            continue
        base_hr, decay_hr = np.array(base_hr), np.array(decay_hr)
        base_rec, decay_rec = np.array(base_rec), np.array(decay_rec)

        hr_diff = bootstrap_diff_ci(base_hr, decay_hr)
        rec_diff = bootstrap_diff_ci(decay_rec, base_rec)  # decay recovery - baseline recovery (positive = decay slower)

        # paired t-test as nominal p-value input to Holm-Bonferroni (n is tiny; flagged explicitly)
        if len(base_hr) > 1 and np.std(base_hr - decay_hr) > 0:
            _, p_hr = stats.ttest_rel(base_hr, decay_hr)
        else:
            p_hr = 1.0
        if len(base_rec) > 1 and np.std(base_rec - decay_rec) > 0:
            _, p_rec = stats.ttest_rel(decay_rec, base_rec)
        else:
            p_rec = 1.0
        hitratio_pvals.append(p_hr)
        recovery_pvals.append(p_rec)

        cell_results.append({
            "alpha": alpha, "cache_ratio": cache_ratio, "drift_scenario": drift,
            "n_seeds": len(base_hr),
            "hit_ratio_deficit_baseline_minus_decay": hr_diff,
            "recovery_time_excess_decay_minus_baseline": rec_diff,
            "hit_ratio_paired_t_pvalue_raw": float(p_hr),
            "recovery_time_paired_t_pvalue_raw": float(p_rec),
        })

    hr_padj = holm_bonferroni(hitratio_pvals) if hitratio_pvals else []
    rec_padj = holm_bonferroni(recovery_pvals) if recovery_pvals else []
    for cell, ph, pr in zip(cell_results, hr_padj, rec_padj):
        cell["hit_ratio_paired_t_pvalue_holm_adjusted"] = float(ph)
        cell["recovery_time_paired_t_pvalue_holm_adjusted"] = float(pr)
        cell["hit_ratio_deficit_significant_after_holm"] = bool(
            ph < 0.05 and ci_excludes_zero(cell["hit_ratio_deficit_baseline_minus_decay"]["ci_low"],
                                            cell["hit_ratio_deficit_baseline_minus_decay"]["ci_high"])
        )

    # pooled fixed-effect (inverse-variance) meta-analysis across cells for hit-ratio deficit
    pooled = {}
    pts = np.array([c["hit_ratio_deficit_baseline_minus_decay"]["point"] for c in cell_results])
    los = np.array([c["hit_ratio_deficit_baseline_minus_decay"]["ci_low"] for c in cell_results])
    his = np.array([c["hit_ratio_deficit_baseline_minus_decay"]["ci_high"] for c in cell_results])
    se = np.maximum((his - los) / (2 * 1.96), 1e-6)
    w = 1.0 / (se ** 2)
    pooled_est = float(np.sum(w * pts) / np.sum(w))
    pooled_se = float(np.sqrt(1.0 / np.sum(w)))
    pooled = {
        "pooled_hit_ratio_deficit_point": pooled_est,
        "pooled_hit_ratio_deficit_ci95": [pooled_est - 1.96 * pooled_se, pooled_est + 1.96 * pooled_se],
        "per_cell_range": [float(pts.min()), float(pts.max())],
        "n_cells_pooled": len(cell_results),
        "heterogeneity_note": (
            "Per-cell hit-ratio deficits range from "
            f"{pts.min():.4f} to {pts.max():.4f}; the pooled CI should not be read as representative of every "
            "cell individually -- see per-cell table for heterogeneity."
        ),
        "small_n_caveat": (
            f"n_seeds per cell is only {sorted({c['n_seeds'] for c in cell_results})} (the grid_spec sweep used "
            "3 seeds, NOT the 5 the artifact plan assumed). Bootstrap CIs and paired-t p-values from n<=3 seeds "
            "are inherently unstable; treat any single-cell 'significant after Holm' flag as suggestive, not proof."
        ),
    }

    # correlational substitute for sub-claim (b): decay_slot_collision_rate vs per-config deficit
    per_config_rows = []
    for c in decay:
        key = (c["alpha"], c["cache_ratio"], c["drift_scenario"], c["seed"])
        base_rows = by_seed_cell.get(key, [])
        if not base_rows:
            continue
        best_base = max(base_rows, key=lambda r: r["steady_state_hit_ratio"])
        deficit = best_base["steady_state_hit_ratio"] - c["steady_state_hit_ratio"]
        rec_excess = c["recovery_time_requests"] - best_base["recovery_time_requests"]
        per_config_rows.append({
            "collision_rate": c["decay_slot_collision_rate"],
            "hit_ratio_deficit": deficit,
            "recovery_time_excess": rec_excess,
        })

    corr_result: dict[str, Any] = {"n_configs": len(per_config_rows)}
    if len(per_config_rows) >= 3:
        coll = np.array([r["collision_rate"] for r in per_config_rows])
        hdef = np.array([r["hit_ratio_deficit"] for r in per_config_rows])
        rexc = np.array([r["recovery_time_excess"] for r in per_config_rows])

        def _spearman_boot(x, y):
            rho, p = stats.spearmanr(x, y)
            rng = np.random.default_rng(RNG_SEED)
            n = len(x)
            boots = np.empty(N_BOOT)
            for i in range(N_BOOT):
                idx = rng.integers(0, n, size=n)
                bx, by = x[idx], y[idx]
                if np.std(bx) == 0 or np.std(by) == 0:
                    boots[i] = 0.0
                else:
                    boots[i] = stats.spearmanr(bx, by)[0]
            return {
                "spearman_rho": float(rho), "p_value_raw": float(p),
                "ci_low": float(np.percentile(boots, 2.5)), "ci_high": float(np.percentile(boots, 97.5)),
                "n": int(n),
            }

        corr_result["collision_rate_vs_hit_ratio_deficit"] = _spearman_boot(coll, hdef)
        corr_result["collision_rate_vs_recovery_time_excess"] = _spearman_boot(coll, rexc)
        slope, intercept, r, p, se_slope = stats.linregress(coll, hdef)
        corr_result["ols_hit_ratio_deficit_on_collision_rate"] = {
            "slope": float(slope), "intercept": float(intercept), "r2": float(r ** 2), "p_value": float(p),
        }
    corr_result["label"] = "CORRELATIONAL_SUBSTITUTE_NOT_CAUSAL"
    corr_result["caveat"] = (
        "This is a cross-config correlation between the decay variant's own hashed-slot collision rate and its "
        "performance deficit relative to the best-tuned baseline. It is NOT the 3-arm oracle/hashing ablation the "
        "hypothesis's sub-claim (b) requires, cannot separate classifier-labeling error from hashing collision "
        "(no per-config classifier_precision is logged), and cannot establish causation -- both collision rate and "
        "deficit could be driven by a common third factor (e.g. cache_ratio, alpha)."
    )

    return {
        "per_cell_deficits": cell_results,
        "pooled_meta_analysis": pooled,
        "collision_rate_correlational_substitute": corr_result,
    }


# ---------------------------------------------------------------------------
# STEP 2: classifier window/threshold sweep -- ABSENT
# ---------------------------------------------------------------------------

def step2_window_sweep() -> dict:
    logger.info("STEP 2: window/threshold sweep -- confirmed ABSENT from method_out.json")
    return {
        "status": "UNTESTABLE-DATA-MISSING",
        "missing_fields": ["a standalone labeling-task sweep over window_length in {4,8,16,32} x threshold, "
                            "scored against ground-truth burst/stable labels with precision/recall/F1/AUROC"],
        "missing_artifact": "No sibling artifact or field in art_0aR0TOK6EOBa's method_out.json contains this. "
                             "Would require a follow-up EXPERIMENT artifact that runs the ShadowQueue/CV "
                             "classifier as a standalone labeling task against ground-truth volatility labels.",
        "note": "The only classifier-adjacent field present is metadata.mean_decay_slot_collision_rate (a single "
                "scalar, 0.0684, aggregated over the whole sweep) and per-config decay_bucket_assignment_stats "
                "(fractions of keys labeled stable/medium/bursty) -- neither is a precision/recall/F1 table "
                "against ground truth, so sub-claim (a) cannot be tested even weakly from this data.",
    }


# ---------------------------------------------------------------------------
# STEP 3: memory accounting reconciliation
# ---------------------------------------------------------------------------

def step3_memory_reconciliation(full: dict) -> dict:
    logger.info("STEP 3: memory accounting reconciliation")
    mem = full["metadata"]["memory_summary"]
    return {
        "convention_present_in_this_artifact": {
            "description": "Matched-memory tolerance check: admission-filter memory (sketch counters + doorkeeper "
                            "bits + shadow-queue slots) for baseline vs decay variant, solved to be within a "
                            "stated +/-15% tolerance.",
            "baseline_mean_bytes": mem["baseline_mean_bytes"],
            "decay_mean_bytes": mem["decay_mean_bytes"],
            "pct_diff": mem["pct_diff"],
            "within_15pct_tolerance": mem["within_15pct_tolerance"],
        },
        "second_convention_16_9x_figure": {
            "status": "CANNOT_BE_RECONCILED_FROM_THIS_ARTIFACT",
            "reason": "The hypothesis's 16.9x overhead figure is attributed to a second, independent simulator "
                      "that is not a dependency of this evaluation (not art_0aR0TOK6EOBa). method_out.json's "
                      "metadata.memory_summary exposes exactly one pricing convention (a single "
                      "baseline_mean_bytes/decay_mean_bytes pair), not a shared-with-sketch vs per-key split, so "
                      "there is nothing to recompute the second figure from without that other simulator's code.",
        },
        "recommended_convention_for_future_matched_comparisons": {
            "recommendation": "per-key pricing of the inter-arrival-history buffer",
            "justification": (
                "Pricing the shadow-queue / inter-arrival-history buffer as 'shared with the sketch' undercounts "
                "the decay variant's true marginal memory cost, since that buffer would not exist at all under "
                "the TinyLFU baseline -- it exists purely to support the decay mechanism's per-key CV "
                "classification. A fair memory-matched ablation should price it per-key (its actual marginal "
                "footprint), which is the more conservative and more honest convention for attributing any "
                "hit-ratio advantage to the decay mechanism rather than to uncounted memory."
            ),
        },
        "note": "Because only one convention exists in this artifact's data, this evaluation reports it as-is "
                "(0.003%%, well within tolerance) and does not attempt to synthesize a second number.",
    }


# ---------------------------------------------------------------------------
# STEP 4: real trace vs synthetic
# ---------------------------------------------------------------------------

def step4_real_vs_synthetic(full: dict) -> dict:
    logger.info("STEP 4: real-trace-vs-synthetic comparison")
    configs = [ex["metadata_config"] for ex in full["datasets"][0]["examples"]]
    retail_rows = [c for c in configs if c.get("trace_source") == "real_retailrocket_events"]
    if retail_rows:
        return {"status": "PRESENT", "note": "unexpected -- present despite experiment summary stating synthetic-only"}
    return {
        "status": "UNTESTABLE-DATA-MISSING",
        "finding": "Confirmed: no real_retailrocket_events rows exist in art_0aR0TOK6EOBa's method_out.json. "
                   "The experiment ran synthetic-only, as its own metadata.notes states, because its data "
                   "dependency (gen_art_dataset_1) was empty at the time it ran.",
        "recommendation": (
            "art_ypvfJGcyJJsE (delivered in the CURRENT iteration, after art_0aR0TOK6EOBa ran) now provides "
            "real_retailrocket_events (229,676 rows). This evaluation artifact cannot generate new experiment "
            "runs, so the real-vs-synthetic comparison remains an open item for a follow-up EXPERIMENT artifact "
            "that re-runs method.py against the now-available RetailRocket trace."
        ),
    }


# ---------------------------------------------------------------------------
# STEP 5: verdict table
# ---------------------------------------------------------------------------

def step5_verdicts(availability: dict, step1: dict, step2: dict, step3: dict, step4: dict) -> dict:
    logger.info("STEP 5: assembling per-sub-claim verdict table")
    pooled = step1["pooled_meta_analysis"]
    verdicts = [
        {
            "sub_claim": "(a) classifier window-length choice (W=8) is near-optimal for burst/stable labeling",
            "data_status": "UNTESTABLE-DATA-MISSING",
            "verdict": "N-A",
            "quantitative_summary": None,
            "caveats": step2["missing_fields"],
        },
        {
            "sub_claim": "(b) once classifier and hashing confounds are removed (oracle labels + unhashed storage), "
                         "the per-key-decay mechanism closes most of its deficit vs. tuned TinyLFU",
            "data_status": "UNTESTABLE-DATA-MISSING (causal ablation); PARTIALLY-TESTED (correlational substitute)",
            "verdict": "N-A",
            "quantitative_summary": {
                "pooled_hit_ratio_deficit_of_full_decay_variant_vs_tuned_baseline": pooled,
                "collision_rate_correlational_substitute": step1["collision_rate_correlational_substitute"],
            },
            "caveats": [
                "No oracle-labels/unhashed-storage ablation arms exist in the dependency's output; the 3-arm "
                "ablation this sub-claim requires was never run.",
                "The correlational substitute (collision rate vs. deficit) cannot separate classifier-labeling "
                "error from hashing collision, and correlation is not causation.",
            ],
        },
        {
            "sub_claim": "(c) the two prior simulators' memory-overhead figures (0.003%% vs 16.9x) can be "
                         "reconciled under one consistent accounting convention",
            "data_status": "PARTIALLY-TESTED",
            "verdict": "MIXED",
            "quantitative_summary": step3["convention_present_in_this_artifact"],
            "caveats": [
                "Only one convention is present in this artifact's data; the 16.9x figure originates from a "
                "second simulator not available as a dependency, so full reconciliation is not executable here.",
            ],
        },
    ]
    ceiling_question = {
        "question": "Does the oracle-labels+unhashed-storage 'ceiling' arm's drift-recovery time beat the "
                     "tuned baseline's best-W recovery time (the pre-registered >=20%% reduction, CI excluding "
                     "zero, bar)?",
        "status": "UNTESTED",
        "reason": "The oracle+unhashed ceiling arm does not exist in art_0aR0TOK6EOBa's output.",
        "priority": "This is flagged as the single highest-priority follow-up experiment: without it, the "
                    "hypothesis cannot be distinguished from 'the idea is architecturally fine but the "
                    "implementation (classifier + hashing) was bad' versus 'the idea itself is inferior to a "
                    "global reset even under ideal conditions'.",
    }
    return {"per_sub_claim_verdicts": verdicts, "ceiling_vs_baseline_headline_question": ceiling_question}


# ---------------------------------------------------------------------------
# Assemble exp_eval_sol_out.json
# ---------------------------------------------------------------------------

@logger.catch(reraise=True)
def main():
    logger.info("Loading full_method_out.json from dependency experiment")
    full = json.loads((EXPERIMENT_DIR / "full_method_out.json").read_text())

    availability = step0_inventory(full)
    step1 = step1_deficit_and_correlation(full)
    step2 = step2_window_sweep()
    step3 = step3_memory_reconciliation(full)
    step4 = step4_real_vs_synthetic(full)
    step5 = step5_verdicts(availability, step1, step2, step3, step4)

    pooled = step1["pooled_meta_analysis"]
    corr = step1["collision_rate_correlational_substitute"]

    metrics_agg = {
        "n_cells_analyzed": float(len(step1["per_cell_deficits"])),
        "n_seeds_per_cell": float(step1["per_cell_deficits"][0]["n_seeds"]) if step1["per_cell_deficits"] else 0.0,
        "pooled_hit_ratio_deficit_baseline_minus_decay": pooled["pooled_hit_ratio_deficit_point"],
        "pooled_hit_ratio_deficit_ci_low": pooled["pooled_hit_ratio_deficit_ci95"][0],
        "pooled_hit_ratio_deficit_ci_high": pooled["pooled_hit_ratio_deficit_ci95"][1],
        "n_cells_significant_after_holm": float(sum(c["hit_ratio_deficit_significant_after_holm"] for c in step1["per_cell_deficits"])),
        "collision_rate_vs_hit_ratio_deficit_spearman_rho": corr.get("collision_rate_vs_hit_ratio_deficit", {}).get("spearman_rho", float("nan")),
        "memory_overhead_pct_diff_matched_convention": full["metadata"]["memory_summary"]["pct_diff"],
        "mean_decay_slot_collision_rate": full["metadata"]["mean_decay_slot_collision_rate"],
        "n_subclaims_untestable_data_missing": float(sum(
            1 for v in step5["per_sub_claim_verdicts"] if "UNTESTABLE-DATA-MISSING" in v["data_status"]
        )),
        "ceiling_vs_baseline_tested": 0.0,
    }

    examples = []
    for cell in step1["per_cell_deficits"]:
        examples.append({
            "input": f"alpha={cell['alpha']} cache_ratio={cell['cache_ratio']} drift_scenario={cell['drift_scenario']}",
            "output": (
                f"hit_ratio_deficit_baseline_minus_decay={cell['hit_ratio_deficit_baseline_minus_decay']['point']:.5f} "
                f"[{cell['hit_ratio_deficit_baseline_minus_decay']['ci_low']:.5f}, "
                f"{cell['hit_ratio_deficit_baseline_minus_decay']['ci_high']:.5f}] "
                f"recovery_time_excess_decay_minus_baseline={cell['recovery_time_excess_decay_minus_baseline']['point']:.2f}"
            ),
            "metadata_cell_stats": cell,
            "eval_hit_ratio_deficit_point": cell["hit_ratio_deficit_baseline_minus_decay"]["point"],
            "eval_recovery_time_excess_point": cell["recovery_time_excess_decay_minus_baseline"]["point"],
            "eval_hit_ratio_deficit_significant_after_holm": float(cell["hit_ratio_deficit_significant_after_holm"]),
        })

    eval_out = {
        "metadata": {
            "evaluation_name": "cache_decay_failure_causal_attribution",
            "data_availability": availability,
            "deficit_attribution": step1,
            "classifier_window_threshold_sweep": step2,
            "memory_accounting_reconciliation": step3,
            "real_trace_vs_synthetic_comparison": step4,
            "verdicts": step5,
            "notes": [
                "This evaluation's dependency (art_0aR0TOK6EOBa) does NOT contain the 3-arm oracle/hashing "
                "ablation, the classifier window/threshold sweep, RetailRocket rows, or a second memory-pricing "
                "convention that the artifact plan's objective assumes exist. Every place this evaluation could "
                "not perform the requested analysis is marked UNTESTABLE-DATA-MISSING above, with the exact "
                "missing fields/artifact named, rather than fabricated or silently skipped.",
                "What COULD be done with the available data: (i) a full bootstrap/Holm-corrected re-analysis of "
                "the steady-state hit-ratio and drift-recovery deficits per (alpha, cache_ratio, drift_scenario) "
                "cell using the best-tuned baseline as the comparator, (ii) a correlational (explicitly non-causal) "
                "substitute linking the decay variant's own per-config hashed-slot collision rate to its "
                "performance deficit, (iii) a reconciled single-convention memory-overhead table with an explicit "
                "recommendation for which convention is more defensible going forward, all with bootstrap 95%% CIs "
                "and Holm-Bonferroni-corrected significance calls.",
                "Follow-up EXPERIMENT artifact requirements to make sub-claims (a)/(b)/(c) fully testable: "
                "(a) a standalone classifier labeling-task sweep over window_length in {4,8,16,32} x threshold, "
                "scored with precision/recall/F1/AUROC against ground-truth burst/stable labels; "
                "(b) re-run method.py's grid with two additional systems, e.g. system in {'oracle_hashed', "
                "'real_unhashed', 'oracle_unhashed'} (classifier_mode in {real, oracle} crossed with storage_mode "
                "in {hashed, unhashed}), logging per-config classifier_precision alongside the existing "
                "decay_slot_collision_rate; "
                "(c) either obtain the second simulator's code/config as a dependency, or log both a "
                "'history_buffer_priced_shared_with_sketch' and 'history_buffer_priced_per_key' byte count in "
                "metadata.memory_summary from a single simulator; "
                "(d) re-run method.py with art_ypvfJGcyJJsE's real_retailrocket_events trace now that it is "
                "available as a dependency, to enable the real-vs-synthetic comparison.",
                f"n_seeds actually available per cell was {metrics_agg['n_seeds_per_cell']:.0f} (grid_spec.seeds), "
                "NOT the 5 seeds the artifact plan's objective assumed -- flagged per the small-n caveat in "
                "deficit_attribution.pooled_meta_analysis.",
            ],
        },
        "metrics_agg": metrics_agg,
        "datasets": [
            {"dataset": "cache_decay_causal_attribution_per_cell", "examples": examples}
        ],
    }

    out_path = WORKSPACE / "eval_out.json"
    out_path.write_text(json.dumps(eval_out, indent=2))
    logger.info(f"Wrote {out_path} ({out_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
