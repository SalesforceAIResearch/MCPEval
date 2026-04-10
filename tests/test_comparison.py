"""Tests for the statistical comparison module."""

import json
import os
import tempfile

import numpy as np
import pytest

from mcpeval.stats.comparison import (
    bootstrap_ci,
    compare_results,
)


class TestBootstrapCI:
    def test_perfect_data(self):
        values = np.ones(100)
        point, lower, upper = bootstrap_ci(values)
        assert point == pytest.approx(1.0)
        assert lower == pytest.approx(1.0)
        assert upper == pytest.approx(1.0)

    def test_mixed_data(self):
        values = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1], dtype=float)
        point, lower, upper = bootstrap_ci(values)
        assert point == pytest.approx(0.5)
        assert lower < point
        assert upper > point
        assert lower >= 0.0
        assert upper <= 1.0

    def test_single_value(self):
        values = np.array([0.5])
        point, lower, upper = bootstrap_ci(values)
        assert point == pytest.approx(0.5)

    def test_confidence_level(self):
        rng = np.random.RandomState(42)
        values = rng.binomial(1, 0.7, size=200).astype(float)
        _, lo_90, hi_90 = bootstrap_ci(values, confidence=0.90)
        _, lo_99, hi_99 = bootstrap_ci(values, confidence=0.99)
        # 99% CI should be wider than 90% CI
        assert (hi_99 - lo_99) >= (hi_90 - lo_90)


class TestCompareResults:
    @pytest.fixture
    def create_jsonl(self, tmp_path):
        """Helper to create JSONL files with task results."""
        def _create(name, tasks):
            path = str(tmp_path / f"{name}.jsonl")
            with open(path, "w") as f:
                for t in tasks:
                    f.write(json.dumps(t) + "\n")
            return path
        return _create

    def test_identical_runs(self, create_jsonl):
        tasks = [{"task_id": f"t{i}", "success": True} for i in range(20)]
        path_a = create_jsonl("run_a", tasks)
        path_b = create_jsonl("run_b", tasks)

        report = compare_results([path_a, path_b])
        assert report["common_tasks"] == 20
        assert len(report["runs"]) == 2
        assert report["runs"][0]["success_rate"] == pytest.approx(1.0)
        assert report["pairwise"][0]["delta_success_rate"] == pytest.approx(0.0)

    def test_different_runs(self, create_jsonl):
        # Run A: all pass. Run B: half fail.
        tasks_a = [{"task_id": f"t{i}", "success": True} for i in range(20)]
        tasks_b = [{"task_id": f"t{i}", "success": i < 10} for i in range(20)]
        path_a = create_jsonl("run_a", tasks_a)
        path_b = create_jsonl("run_b", tasks_b)

        report = compare_results([path_a, path_b])
        assert report["runs"][0]["success_rate"] == pytest.approx(1.0)
        assert report["runs"][1]["success_rate"] == pytest.approx(0.5)
        assert report["pairwise"][0]["delta_success_rate"] == pytest.approx(0.5)

    def test_no_common_tasks(self, create_jsonl):
        tasks_a = [{"task_id": "a1", "success": True}]
        tasks_b = [{"task_id": "b1", "success": True}]
        path_a = create_jsonl("run_a", tasks_a)
        path_b = create_jsonl("run_b", tasks_b)

        report = compare_results([path_a, path_b])
        assert "error" in report

    def test_partial_overlap(self, create_jsonl):
        tasks_a = [{"task_id": f"t{i}", "success": True} for i in range(10)]
        tasks_b = [{"task_id": f"t{i}", "success": True} for i in range(5, 15)]
        path_a = create_jsonl("run_a", tasks_a)
        path_b = create_jsonl("run_b", tasks_b)

        report = compare_results([path_a, path_b])
        assert report["common_tasks"] == 5  # t5-t9

    def test_three_way_comparison(self, create_jsonl):
        tasks = [{"task_id": f"t{i}", "success": True} for i in range(10)]
        path_a = create_jsonl("a", tasks)
        path_b = create_jsonl("b", tasks)
        path_c = create_jsonl("c", tasks)

        report = compare_results([path_a, path_b, path_c])
        assert len(report["runs"]) == 3
        # C(3,2) = 3 pairwise comparisons
        assert len(report["pairwise"]) == 3

    def test_bootstrap_ci_in_report(self, create_jsonl):
        rng = np.random.RandomState(42)
        tasks = [
            {"task_id": f"t{i}", "success": bool(rng.binomial(1, 0.7))}
            for i in range(50)
        ]
        path = create_jsonl("run", tasks)
        report = compare_results([path, path])

        run_info = report["runs"][0]
        assert run_info["ci_lower"] <= run_info["success_rate"]
        assert run_info["ci_upper"] >= run_info["success_rate"]
