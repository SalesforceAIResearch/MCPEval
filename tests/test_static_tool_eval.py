"""Tests for StaticToolEvaluator — the core metrics engine."""

import pytest

from mcpeval.commons.types import ToolCall
from mcpeval.metrics.static_tool_eval import StaticToolEvaluator, ToolEvalResult


class TestEvaluateTaskStrict:
    """Test strict (exact) matching."""

    def test_perfect_match(self, sample_tool_calls):
        """Identical ground truth and predictions score 1.0."""
        result = StaticToolEvaluator.evaluate_exact(
            sample_tool_calls, sample_tool_calls, task_id="t1"
        )
        assert result.success is True
        assert result.overall_score == pytest.approx(1.0)
        assert result.tool_name_score == pytest.approx(1.0)
        assert result.param_match_score == pytest.approx(1.0)
        assert result.order_score == pytest.approx(1.0)
        assert result.exact_matches == 2
        assert result.missing_tools == []
        assert result.extra_tools == []

    def test_wrong_param_value_strict(self, sample_tool_calls, sample_prediction_calls):
        """Strict matching fails when param casing differs."""
        result = StaticToolEvaluator.evaluate_exact(
            sample_tool_calls, sample_prediction_calls, task_id="t2"
        )
        # Second tool has "Engineering" vs "engineering" - strict compare normalizes to lowercase
        # so this should still match after normalization
        assert result.tool_name_score == pytest.approx(1.0)

    def test_missing_tool(self, sample_tool_calls):
        """Prediction is missing a tool call."""
        pred = [sample_tool_calls[0]]
        result = StaticToolEvaluator.evaluate_exact(
            sample_tool_calls, pred, task_id="t3"
        )
        assert result.success is False
        assert result.tool_name_score == pytest.approx(0.5)  # 1 of 2 matched
        assert "get_department" in result.missing_tools

    def test_extra_tool(self, sample_tool_calls):
        """Prediction has an extra tool call."""
        pred = sample_tool_calls + [
            ToolCall(tool_name="extra_tool", tool_parameters={"x": 1})
        ]
        result = StaticToolEvaluator.evaluate_exact(
            sample_tool_calls, pred, task_id="t4"
        )
        assert result.success is False
        assert "extra_tool" in result.extra_tools

    def test_wrong_order(self):
        """Tools called in wrong order should have order_score < 1.0."""
        gt = [
            ToolCall(tool_name="tool_a", tool_parameters={}),
            ToolCall(tool_name="tool_b", tool_parameters={}),
        ]
        pred = [
            ToolCall(tool_name="tool_b", tool_parameters={}),
            ToolCall(tool_name="tool_a", tool_parameters={}),
        ]
        result = StaticToolEvaluator.evaluate_exact(gt, pred, task_id="t5")
        assert result.order_score < 1.0
        assert result.tool_name_score == pytest.approx(0.0)  # position-wise mismatch

    def test_empty_calls(self):
        """Both empty should be a perfect match."""
        result = StaticToolEvaluator.evaluate_exact([], [], task_id="t6")
        assert result.success is True
        assert result.overall_score == pytest.approx(1.0)

    def test_gt_empty_pred_nonempty(self):
        """Empty ground truth but nonempty prediction."""
        pred = [ToolCall(tool_name="tool_a", tool_parameters={})]
        result = StaticToolEvaluator.evaluate_exact([], pred, task_id="t7")
        assert result.success is False
        assert result.tool_name_score == pytest.approx(0.0)


class TestEvaluateTaskFlexible:
    """Test flexible (soft) matching."""

    def test_case_insensitive_params(self, sample_tool_calls, sample_prediction_calls):
        """Flexible matching should handle case differences in string params."""
        result = StaticToolEvaluator.evaluate_flexible(
            sample_tool_calls, sample_prediction_calls, task_id="t10"
        )
        # Both should match flexibly since normalization lowercases strings
        assert result.param_match_score >= 0.8

    def test_numeric_tolerance(self):
        """Flexible matching should tolerate small numeric differences."""
        gt = [ToolCall(tool_name="set_price", tool_parameters={"price": 10.0})]
        pred = [ToolCall(tool_name="set_price", tool_parameters={"price": 10.5})]
        result = StaticToolEvaluator.evaluate_flexible(gt, pred, task_id="t11")
        # 10.0 vs 10.5 - relative diff is 0.05, within 0.2 tolerance
        assert result.param_match_score > 0.0

    def test_substring_match(self):
        """Flexible matching should match substrings."""
        gt = [
            ToolCall(
                tool_name="search", tool_parameters={"query": "python programming"}
            )
        ]
        pred = [ToolCall(tool_name="search", tool_parameters={"query": "python"})]
        result = StaticToolEvaluator.evaluate_flexible(gt, pred, task_id="t12")
        assert result.param_match_score > 0.0


class TestCustomWeights:
    """Test custom weight configurations."""

    def test_custom_weights(self, sample_tool_calls):
        """Custom weights should affect overall score calculation."""
        weights = {"name": 0.8, "params": 0.1, "order": 0.1}
        result = StaticToolEvaluator.evaluate_exact(
            sample_tool_calls,
            sample_tool_calls,
            task_id="t20",
            weights=weights,
        )
        assert result.overall_score == pytest.approx(1.0)
        assert result.weights == weights

    def test_invalid_weights_fallback(self, sample_tool_calls):
        """Weights not summing to 1.0 should fall back to defaults."""
        weights = {"name": 0.5, "params": 0.5, "order": 0.5}
        result = StaticToolEvaluator.evaluate_exact(
            sample_tool_calls,
            sample_tool_calls,
            task_id="t21",
            weights=weights,
        )
        # Should use default weights since sum is 1.5
        assert result.weights == {"name": 0.4, "params": 0.4, "order": 0.2}


class TestLCS:
    """Test longest common subsequence calculation."""

    def test_identical_sequences(self):
        assert (
            StaticToolEvaluator.longest_common_subsequence(
                ["a", "b", "c"], ["a", "b", "c"]
            )
            == 3
        )

    def test_reversed_sequences(self):
        assert (
            StaticToolEvaluator.longest_common_subsequence(
                ["a", "b", "c"], ["c", "b", "a"]
            )
            == 1
        )

    def test_empty_sequences(self):
        assert StaticToolEvaluator.longest_common_subsequence([], []) == 0

    def test_partial_overlap(self):
        assert (
            StaticToolEvaluator.longest_common_subsequence(["a", "b", "c"], ["a", "c"])
            == 2
        )


class TestEvaluateFromJson:
    """Test JSON-based evaluation."""

    def test_basic_json_eval(self):
        gt = {
            "task_id": "test1",
            "tool_calls": [
                {
                    "tool_name": "fetch",
                    "tool_parameters": {"url": "https://example.com"},
                }
            ],
        }
        pred = {
            "task_id": "test1",
            "tool_calls": [
                {
                    "tool_name": "fetch",
                    "tool_parameters": {"url": "https://example.com"},
                }
            ],
        }
        result = StaticToolEvaluator.evaluate_from_json(gt, pred, match_type="strict")
        assert result.success is True
        assert result.overall_score == pytest.approx(1.0)

    def test_json_with_empty_tool_calls(self):
        gt = {"task_id": "test2", "tool_calls": []}
        pred = {"task_id": "test2", "tool_calls": []}
        result = StaticToolEvaluator.evaluate_from_json(gt, pred)
        assert result.success is True


class TestBothMatchTypes:
    """Test evaluate_with_both_match_types."""

    def test_returns_both(self, sample_tool_calls):
        result = StaticToolEvaluator.evaluate_with_both_match_types(
            sample_tool_calls, sample_tool_calls, task_id="t30"
        )
        assert "strict" in result
        assert "flexible" in result
        assert result["strict"]["success"] is True
        assert result["flexible"]["success"] is True
        assert result["task_id"] == "t30"
