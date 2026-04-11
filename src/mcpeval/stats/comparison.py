"""Statistical comparison of evaluation runs.

Provides bootstrap confidence intervals, paired significance tests
(McNemar for pass/fail, Wilcoxon for continuous scores), and a
CLI-friendly report.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Bootstrap confidence intervals
# ---------------------------------------------------------------------------


def bootstrap_ci(
    values: np.ndarray,
    stat_fn=np.mean,
    n_bootstrap: int = 10_000,
    confidence: float = 0.95,
    seed: int = 42,
) -> Tuple[float, float, float]:
    """Compute bootstrap confidence interval for a statistic.

    Returns:
        (point_estimate, lower_bound, upper_bound)
    """
    rng = np.random.RandomState(seed)
    point = float(stat_fn(values))
    if len(values) < 2:
        return point, point, point

    boot_stats = np.empty(n_bootstrap)
    n = len(values)
    for i in range(n_bootstrap):
        sample = values[rng.randint(0, n, size=n)]
        boot_stats[i] = stat_fn(sample)

    alpha = 1 - confidence
    lower = float(np.percentile(boot_stats, 100 * alpha / 2))
    upper = float(np.percentile(boot_stats, 100 * (1 - alpha / 2)))
    return point, lower, upper


# ---------------------------------------------------------------------------
# Paired significance tests
# ---------------------------------------------------------------------------


def mcnemar_test(successes_a: np.ndarray, successes_b: np.ndarray) -> Dict[str, Any]:
    """McNemar's test for paired binary outcomes (pass/fail).

    successes_a, successes_b: boolean arrays of same length.
    Returns dict with statistic, p_value, and interpretation.
    """
    assert len(successes_a) == len(successes_b)

    # Count discordant pairs
    b = int(np.sum(successes_a & ~successes_b))  # A pass, B fail
    c = int(np.sum(~successes_a & successes_b))  # A fail, B pass

    # McNemar test with continuity correction
    if b + c == 0:
        return {"statistic": 0.0, "p_value": 1.0, "significant": False, "b": b, "c": c}

    from scipy.stats import binomtest  # type: ignore

    # Use exact binomial test (small-sample safe)
    try:
        p_value = float(binomtest(b, b + c, 0.5).pvalue)
    except Exception:
        # Fallback chi-squared approximation
        stat = (abs(b - c) - 1) ** 2 / (b + c) if b + c > 0 else 0
        from scipy.stats import chi2  # type: ignore

        p_value = float(1 - chi2.cdf(stat, df=1))

    return {
        "statistic": float(b - c),
        "p_value": p_value,
        "significant": p_value < 0.05,
        "b_wins_exclusive": b,
        "c_wins_exclusive": c,
    }


def wilcoxon_test(scores_a: np.ndarray, scores_b: np.ndarray) -> Dict[str, Any]:
    """Wilcoxon signed-rank test for paired continuous scores.

    Returns dict with statistic, p_value, effect_size (r = Z/sqrt(N)).
    """
    diffs = scores_a - scores_b
    nonzero = diffs[diffs != 0]

    if len(nonzero) < 2:
        return {
            "statistic": 0.0,
            "p_value": 1.0,
            "significant": False,
            "effect_size": 0.0,
        }

    from scipy.stats import wilcoxon as _wilcoxon  # type: ignore

    stat, p_value = _wilcoxon(nonzero)
    # Effect size r = Z / sqrt(N)
    n = len(nonzero)
    z = float(stat)
    effect_size = z / np.sqrt(n) if n > 0 else 0.0

    return {
        "statistic": float(stat),
        "p_value": float(p_value),
        "significant": p_value < 0.05,
        "effect_size": effect_size,
    }


# ---------------------------------------------------------------------------
# Load and align evaluation results
# ---------------------------------------------------------------------------


def _load_jsonl(path: str) -> List[Dict]:
    results = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                results.append(json.loads(line))
    return results


def _align_by_task_id(
    runs: List[List[Dict]],
) -> Tuple[List[str], List[np.ndarray]]:
    """Align runs by task_id, returning only tasks present in ALL runs.

    Returns:
        (task_ids, list of boolean arrays — one per run)
    """
    # Build task_id -> success mapping per run
    run_maps = []
    for run in runs:
        mapping = {}
        for r in run:
            tid = r.get("task_id")
            if tid:
                mapping[tid] = r.get("success", False)
        run_maps.append(mapping)

    # Intersect task IDs
    common_ids = set(run_maps[0].keys())
    for rm in run_maps[1:]:
        common_ids &= set(rm.keys())

    task_ids = sorted(common_ids)
    success_arrays = [
        np.array([rm[tid] for tid in task_ids], dtype=bool) for rm in run_maps
    ]
    return task_ids, success_arrays


# ---------------------------------------------------------------------------
# Main comparison logic
# ---------------------------------------------------------------------------


def compare_results(
    run_paths: List[str],
    confidence: float = 0.95,
) -> Dict[str, Any]:
    """Compare two or more evaluation runs statistically.

    Args:
        run_paths: list of JSONL file paths
        confidence: confidence level for bootstrap CIs

    Returns:
        Comparison report dict
    """
    runs = [_load_jsonl(p) for p in run_paths]
    labels = [Path(p).stem for p in run_paths]

    task_ids, success_arrays = _align_by_task_id(runs)

    if not task_ids:
        return {"error": "No common task IDs found across runs", "labels": labels}

    report: Dict[str, Any] = {
        "labels": labels,
        "common_tasks": len(task_ids),
        "confidence_level": confidence,
        "runs": [],
        "pairwise": [],
    }

    # Per-run stats with bootstrap CI
    for i, (label, succ) in enumerate(zip(labels, success_arrays)):
        rate = float(np.mean(succ))
        _, lower, upper = bootstrap_ci(succ.astype(float), confidence=confidence)
        report["runs"].append(
            {
                "label": label,
                "success_rate": round(rate, 4),
                "ci_lower": round(lower, 4),
                "ci_upper": round(upper, 4),
                "n_tasks": len(succ),
                "n_pass": int(np.sum(succ)),
                "n_fail": int(np.sum(~succ)),
            }
        )

    # Pairwise comparisons
    has_scipy = True
    try:
        import scipy  # noqa: F401
    except ImportError:
        has_scipy = False
        logger.warning("scipy not installed — skipping significance tests")

    for i in range(len(runs)):
        for j in range(i + 1, len(runs)):
            pair = {
                "a": labels[i],
                "b": labels[j],
                "delta_success_rate": round(
                    float(np.mean(success_arrays[i]) - np.mean(success_arrays[j])), 4
                ),
            }
            if has_scipy:
                pair["mcnemar"] = mcnemar_test(success_arrays[i], success_arrays[j])
            report["pairwise"].append(pair)

    return report


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def run_comparison(args):
    """Run comparison from CLI args and print results."""
    run_paths = args.runs
    confidence = getattr(args, "confidence", 0.95)
    output = getattr(args, "output", None)

    report = compare_results(run_paths, confidence=confidence)

    if "error" in report:
        print(f"Error: {report['error']}")
        sys.exit(1)

    # Print human-readable summary
    _print_report(report)

    # Save JSON if requested
    if output:
        with open(output, "w") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\nDetailed results saved to: {output}")


def _print_report(report: Dict[str, Any]):
    """Print a human-readable comparison report."""
    GREEN = "\033[92m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    RESET = "\033[0m"
    CYAN = "\033[96m"

    use_color = sys.stdout.isatty()
    if not use_color:
        GREEN = RED = BOLD = RESET = CYAN = ""

    print(f"\n{CYAN}{BOLD}Statistical Comparison Report{RESET}")
    print(f"{CYAN}{'=' * 60}{RESET}")
    print(f"Common tasks: {report['common_tasks']}")
    print(f"Confidence level: {report['confidence_level']:.0%}\n")

    # Per-run table
    print(f"{BOLD}{'Run':<35} {'Rate':>8} {'CI':>20} {'Pass':>6} {'Fail':>6}{RESET}")
    print("-" * 80)
    for r in report["runs"]:
        ci_str = f"[{r['ci_lower']:.3f}, {r['ci_upper']:.3f}]"
        print(
            f"{r['label']:<35} {r['success_rate']:>7.3f}  {ci_str:>20} {r['n_pass']:>6} {r['n_fail']:>6}"
        )

    # Pairwise
    if report["pairwise"]:
        print(f"\n{BOLD}Pairwise Comparisons{RESET}")
        print("-" * 80)
        for p in report["pairwise"]:
            delta = p["delta_success_rate"]
            delta_color = GREEN if delta > 0 else RED if delta < 0 else ""
            delta_str = f"{delta_color}{delta:+.4f}{RESET}"

            sig_str = ""
            if "mcnemar" in p:
                mc = p["mcnemar"]
                if mc["significant"]:
                    sig_str = f" {RED}** p={mc['p_value']:.4f}{RESET}"
                else:
                    sig_str = f" p={mc['p_value']:.4f}"

            print(f"  {p['a']} vs {p['b']}: delta={delta_str}{sig_str}")
