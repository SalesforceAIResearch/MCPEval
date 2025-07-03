from typing import Dict, List, Any, Tuple, Optional, Set, Union, Literal
import json
from collections import Counter
import numpy as np
from pydantic import BaseModel, Field

from mcp_eval_llm.commons.types import ToolCall


class ToolEvalResult(BaseModel):
    """Results from evaluating tool calls for a task."""
    
    # Task-level information
    task_id: str = Field("unknown", description="Identifier of the task being evaluated")
    success: bool = Field(False, description="Whether all tools were called correctly")
    tool_count_match: bool = Field(False, description="Whether the number of tool calls matches")
    ground_truth_tool_count: int = Field(0, description="Number of tools in ground truth")
    prediction_tool_count: int = Field(0, description="Number of tools in prediction")
    
    # Tool matching information
    exact_matches: int = Field(0, description="Number of tools that match exactly (name and parameters)")
    name_only_matches: int = Field(0, description="Number of tools that match by name only")
    missing_tools: List[str] = Field(default_factory=list, description="Tool names in ground truth but not in prediction")
    extra_tools: List[str] = Field(default_factory=list, description="Tool names in prediction but not in ground truth")
    
    # Detailed parameter information
    param_matches: Dict[str, float] = Field(
        default_factory=dict, 
        description="Parameter match scores for each tool: {tool_name: score}"
    )
    
    param_mismatches: Dict[str, Dict[str, Tuple[Any, Any]]] = Field(
        default_factory=dict, 
        description="Mismatched parameters for each tool: {tool_name: {param: (gt_value, pred_value)}}"
    )
    
    # Scoring metrics
    tool_name_score: float = Field(0.0, description="Percentage of tool names that match")
    param_match_score: float = Field(0.0, description="Average parameter match score across all tools")
    order_score: float = Field(0.0, description="How well the order of tool calls matches (0-1)")
    overall_score: float = Field(0.0, description="Overall evaluation score (0-1)")
    
    # Match type
    match_type: str = Field("strict", description="Type of matching used (strict or flexible)")
    
    # Weights and thresholds used
    weights: Dict[str, float] = Field(
        default_factory=lambda: {"name": 0.4, "params": 0.4, "order": 0.2},
        description="Weights used for calculating overall score"
    )
    thresholds: Dict[str, float] = Field(
        default_factory=lambda: {"flexible_param": 0.6, "flexible_order": 0.5},
        description="Thresholds used for evaluation"
    )


class StaticToolEvaluator:
    """
    Evaluates tool call execution by comparing ground truth tool calls to model predictions.
    Supports both strict (exact) and flexible (soft) matching of tools and parameters.
    """
    
    @staticmethod
    def _normalize_value(value: Any) -> Any:
        """Normalize a value for comparison (e.g., handle different string formats, numeric types)."""
        if isinstance(value, str):
            return value.strip().lower()
        elif isinstance(value, (int, float)):
            # Convert numeric values to float for comparison
            return float(value)
        elif isinstance(value, list):
            return [StaticToolEvaluator._normalize_value(v) for v in value]
        elif isinstance(value, dict):
            return {
                StaticToolEvaluator._normalize_value(k): StaticToolEvaluator._normalize_value(v) 
                for k, v in value.items()
            }
        return value
    
    @staticmethod
    def _compare_values(val1: Any, val2: Any, flexible: bool = False) -> bool:
        """
        Compare two values, handling various types.
        
        Args:
            val1: First value to compare
            val2: Second value to compare
            flexible: If True, use more lenient comparison for numeric values
            
        Returns:
            True if values match according to the comparison rules
        """
        norm_val1 = StaticToolEvaluator._normalize_value(val1)
        norm_val2 = StaticToolEvaluator._normalize_value(val2)
        
        # Handle numeric comparisons
        if isinstance(norm_val1, float) and isinstance(norm_val2, float):
            if flexible:
                # More lenient comparison for flexible matching
                # If either value is very small, use absolute difference
                if abs(norm_val1) < 1.0 or abs(norm_val2) < 1.0:
                    return abs(norm_val1 - norm_val2) < 0.2  # Increased tolerance from 0.1 to 0.2
                # Otherwise use relative difference with increased tolerance
                return abs(norm_val1 - norm_val2) / max(abs(norm_val1), abs(norm_val2)) < 0.2  # Increased from 0.1 to 0.2
            else:
                # Strict comparison for exact matching (small tolerance for floating point)
                return abs(norm_val1 - norm_val2) < 1e-6
        
        # For string comparisons in flexible mode, check for substring or similarity
        if flexible and isinstance(norm_val1, str) and isinstance(norm_val2, str):
            # Consider it a match if one is a substring of the other
            norm_val1_lower = norm_val1.lower()
            norm_val2_lower = norm_val2.lower()
            if norm_val1_lower in norm_val2_lower or norm_val2_lower in norm_val1_lower:
                return True
        
        return norm_val1 == norm_val2
    
    @staticmethod
    def _compare_tool_parameters(
        ground_truth: Dict[str, Any], 
        prediction: Dict[str, Any],
        flexible: bool = False
    ) -> Tuple[float, Dict[str, Tuple[Any, Any]]]:
        """
        Compare parameters from a ground truth tool call to a prediction.
        
        Args:
            ground_truth: Parameters from ground truth tool call
            prediction: Parameters from prediction tool call
            flexible: If True, use flexible parameter matching
            
        Returns:
            Tuple of (match_score, mismatched_params)
        """
        gt_params = set(ground_truth.keys())
        pred_params = set(prediction.keys())
        
        # Find common parameters
        common_params = gt_params.intersection(pred_params)
        mismatched_params = {}
        
        # Count matched parameters
        matched_params = 0
        for param in common_params:
            gt_value = ground_truth[param]
            pred_value = prediction[param]
            
            if StaticToolEvaluator._compare_values(gt_value, pred_value, flexible):
                matched_params += 1
            else:
                mismatched_params[param] = (gt_value, pred_value)
        
        if flexible:
            # For flexible matching, only required parameters matter
            # Missing optional parameters don't affect the score
            important_params = set()
            for param in gt_params:
                # Consider a parameter important if it's not None and not an empty container
                value = ground_truth[param]
                if value is not None and (not isinstance(value, (list, dict, str)) or len(value) > 0):
                    important_params.add(param)
            
            # Calculate match score based on important parameters only
            # and give partial credit for parameters that exist but don't match perfectly
            partial_match_score = 0.0
            for param in important_params:
                if param in common_params:
                    # Parameter exists in both
                    if param not in mismatched_params:
                        # Perfect match
                        partial_match_score += 1.0
                    else:
                        # Exists but doesn't match perfectly - give partial credit (0.5)
                        partial_match_score += 0.5
                # Missing parameter - no credit
            
            match_score = partial_match_score / len(important_params) if important_params else 1.0
        else:
            # For strict matching, all parameters must match exactly
            match_score = matched_params / len(gt_params) if gt_params else 1.0
        
        return match_score, mismatched_params
    
    @staticmethod
    def longest_common_subsequence(seq1: List[str], seq2: List[str]) -> int:
        """
        Find the length of the longest common subsequence between two sequences.
        Used to measure tool call ordering similarity.
        """
        m, n = len(seq1), len(seq2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if seq1[i-1] == seq2[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
        
        return dp[m][n]
    
    @staticmethod
    def evaluate_task(
        ground_truth_calls: List[ToolCall],
        prediction_calls: List[ToolCall],
        task_id: Optional[str] = None,
        match_type: Literal["strict", "flexible"] = "strict",
        weights: Optional[Dict[str, float]] = None,
        thresholds: Optional[Dict[str, float]] = None
    ) -> ToolEvalResult:
        """
        Evaluate all tool calls for a task.
        
        Args:
            ground_truth_calls: List of expected tool calls
            prediction_calls: List of actual tool calls made by the model
            task_id: Optional identifier for the task
            match_type: Type of matching to use ("strict" for exact matching, "flexible" for soft matching)
            weights: Optional dictionary with custom weights for scoring components: 
                    {"name": float, "params": float, "order": float}
            thresholds: Optional dictionary with custom thresholds:
                    {"flexible_param": float, "flexible_order": float}
            
        Returns:
            ToolEvalResult with detailed evaluation metrics
        """
        # Determine if we're using flexible matching
        flexible = match_type == "flexible"
        
        # Set default weights and thresholds if not provided
        default_weights = {"name": 0.4, "params": 0.4, "order": 0.2}
        default_thresholds = {"flexible_param": 0.6, "flexible_order": 0.5}
        
        # Use provided weights/thresholds or defaults
        w = weights or default_weights
        t = thresholds or default_thresholds
        
        # Validate weights sum to 1.0
        weight_sum = w.get("name", 0.4) + w.get("params", 0.4) + w.get("order", 0.2)
        if abs(weight_sum - 1.0) > 0.001:
            w = default_weights
            print(f"Warning: Provided weights do not sum to 1.0. Using default weights: {default_weights}")
        
        # Initialize result with basic task information
        result = ToolEvalResult(
            task_id=task_id or "unknown",
            ground_truth_tool_count=len(ground_truth_calls),
            prediction_tool_count=len(prediction_calls),
            tool_count_match=len(ground_truth_calls) == len(prediction_calls),
            match_type=match_type
        )
        
        # Extract tool names for both ground truth and prediction
        gt_tool_names = [tool.tool_name for tool in ground_truth_calls]
        pred_tool_names = [tool.tool_name for tool in prediction_calls]
        
        # Create dictionaries for lookup by tool name
        gt_tools_dict = {tool.tool_name: tool for tool in ground_truth_calls}
        pred_tools_dict = {tool.tool_name: tool for tool in prediction_calls}
        
        # Find missing and extra tools
        result.missing_tools = [name for name in gt_tool_names if name not in pred_tool_names]
        result.extra_tools = [name for name in pred_tool_names if name not in gt_tool_names]
        
        # Count tools that match by name position-wise (handles duplicates correctly)
        name_only_matches = 0
        for gt_call, pred_call in zip(ground_truth_calls, prediction_calls):
            if gt_call.tool_name == pred_call.tool_name:
                name_only_matches += 1
        result.name_only_matches = name_only_matches
        
        # Calculate tool name score by comparing position-wise matches
        # This properly handles duplicate tool names
        if gt_tool_names:
            name_matches = sum(1 for gt_name, pred_name in zip(gt_tool_names, pred_tool_names) if gt_name == pred_name)
            result.tool_name_score = name_matches / len(gt_tool_names)
        else:
            # Perfect score when both GT and prediction have no tools
            result.tool_name_score = 1.0 if len(pred_tool_names) == 0 else 0.0
        
        # Evaluate parameters for each tool call position-wise (handles duplicates correctly)
        position_param_scores = []
        position_exact_matches = 0
        
        # Compare tool calls position by position
        for i, (gt_call, pred_call) in enumerate(zip(ground_truth_calls, prediction_calls)):
            if gt_call.tool_name == pred_call.tool_name:
                # Compare parameters for this specific position
                param_score, mismatches = StaticToolEvaluator._compare_tool_parameters(
                    gt_call.tool_parameters, pred_call.tool_parameters, flexible
                )
                
                position_param_scores.append(param_score)
                
                # Store parameter match score (using position index for unique keys when duplicates exist)
                key = f"{gt_call.tool_name}_{i}" if gt_call.tool_name in [call.tool_name for j, call in enumerate(ground_truth_calls) if j != i] else gt_call.tool_name
                result.param_matches[key] = param_score
                
                # Store mismatches if any
                if mismatches:
                    result.param_mismatches[key] = mismatches
                
                # Count exact matches (name and parameters match perfectly)
                if param_score == 1.0:
                    position_exact_matches += 1
        
        result.exact_matches = position_exact_matches
        
        # Calculate average parameter match score across all matching tools
        if position_param_scores:
            result.param_match_score = sum(position_param_scores) / len(position_param_scores)
        elif len(gt_tool_names) == 0 and len(pred_tool_names) == 0:
            # Perfect score when both GT and prediction have no tools
            result.param_match_score = 1.0
        else:
            # No matches
            result.param_match_score = 0.0
        
        # Calculate order score using longest common subsequence
        if len(gt_tool_names) == 0 and len(pred_tool_names) == 0:
            # Perfect order match when both have no tools
            result.order_score = 1.0
        else:
            lcs_length = StaticToolEvaluator.longest_common_subsequence(gt_tool_names, pred_tool_names)
            max_length = max(len(gt_tool_names), 1)  # Avoid division by zero
            result.order_score = lcs_length / max_length
        
        # Determine overall success based on match type
        if flexible:
            # For flexible matching, success is more lenient:
            # 1. All required tools must be present (matched by name)
            # 2. Required parameters must match with flexible comparison
            # 3. Order is less important
            param_threshold = t.get("flexible_param", 0.6)
            required_param_match = all(
                score >= param_threshold for score in result.param_matches.values()
            )
            # Be more lenient about order in flexible matching
            order_threshold = t.get("flexible_order", 0.5)
            order_ok = result.order_score >= order_threshold
            
            if len(ground_truth_calls) == 0 and len(prediction_calls) == 0:
                # Perfect match when both have no tools
                result.success = True
            else:
                # For flexible matching, count name-only matches (includes exact matches)
                # This handles duplicate tool names correctly
                result.success = (
                    result.name_only_matches == len(ground_truth_calls) and 
                    required_param_match and
                    order_ok
                )
        else:
            # For strict matching, success requires exact matching:
            # 1. All ground truth tools must be called with exact parameters
            # 2. No extra tools should be present
            # 3. Tools must be called in the same order
            if len(ground_truth_calls) == 0 and len(prediction_calls) == 0:
                # Perfect match when both have no tools
                result.success = True
            else:
                tools_match = (result.exact_matches == len(ground_truth_calls) and 
                              len(result.extra_tools) == 0)
                order_match = result.order_score == 1.0
                result.success = tools_match and order_match
        
        # Calculate overall score as weighted average of different metrics
        result.overall_score = (
            w.get("name", 0.4) * result.tool_name_score +
            w.get("params", 0.4) * result.param_match_score +
            w.get("order", 0.2) * result.order_score
        )
        
        # Store the weights used for reference
        result.weights = w
        result.thresholds = t
        
        return result
    
    @staticmethod
    def evaluate_with_both_match_types(
        ground_truth_calls: List[ToolCall],
        prediction_calls: List[ToolCall],
        task_id: Optional[str] = None,
        weights: Optional[Dict[str, float]] = None,
        thresholds: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate tool calls using both strict and flexible matching criteria,
        returning a dictionary with detailed scores for each metric.
        
        Args:
            ground_truth_calls: List of expected tool calls
            prediction_calls: List of actual tool calls made by the model
            task_id: Optional identifier for the task
            weights: Optional dictionary with custom weights
            thresholds: Optional dictionary with custom thresholds
            
        Returns:
            Dictionary containing both strict and flexible evaluation results and all individual scores
        """
        # Evaluate with both match types
        strict_result = StaticToolEvaluator.evaluate_exact(
            ground_truth_calls, prediction_calls, task_id, weights, thresholds
        )
        flexible_result = StaticToolEvaluator.evaluate_flexible(
            ground_truth_calls, prediction_calls, task_id, weights, thresholds
        )
        
        # Create score dictionary with all metrics
        score_dict = {
            "task_id": task_id or "unknown",
            "counts": {
                "ground_truth_tool_count": strict_result.ground_truth_tool_count,
                "prediction_tool_count": strict_result.prediction_tool_count,
                "tool_count_match": strict_result.tool_count_match,
                "name_only_matches": strict_result.name_only_matches,
                "exact_matches": strict_result.exact_matches,
            },
            "strict": {
                "success": strict_result.success,
                "overall_score": strict_result.overall_score,
                "tool_name_score": strict_result.tool_name_score,
                "param_match_score": strict_result.param_match_score,
                "order_score": strict_result.order_score,
            },
            "flexible": {
                "success": flexible_result.success,
                "overall_score": flexible_result.overall_score,
                "tool_name_score": flexible_result.tool_name_score,
                "param_match_score": flexible_result.param_match_score,
                "order_score": flexible_result.order_score,
            },
            "weights": strict_result.weights,
            "thresholds": strict_result.thresholds,
            "missing_tools": strict_result.missing_tools,
            "extra_tools": strict_result.extra_tools,
            "param_mismatches": strict_result.param_mismatches,
            "param_matches": strict_result.param_matches
        }
        
        return score_dict
    
    @staticmethod
    def evaluate_exact(
        ground_truth_calls: List[ToolCall],
        prediction_calls: List[ToolCall],
        task_id: Optional[str] = None,
        weights: Optional[Dict[str, float]] = None,
        thresholds: Optional[Dict[str, float]] = None
    ) -> ToolEvalResult:
        """
        Evaluate tool calls using strict/exact matching criteria.
        This is a convenience method that calls evaluate_task with match_type="strict".
        
        Args:
            ground_truth_calls: List of expected tool calls
            prediction_calls: List of actual tool calls made by the model
            task_id: Optional identifier for the task
            weights: Optional dictionary with custom weights
            thresholds: Optional dictionary with custom thresholds
            
        Returns:
            ToolEvalResult with strict evaluation metrics
        """
        return StaticToolEvaluator.evaluate_task(
            ground_truth_calls, prediction_calls, task_id, 
            match_type="strict", weights=weights, thresholds=thresholds
        )
    
    @staticmethod
    def evaluate_flexible(
        ground_truth_calls: List[ToolCall],
        prediction_calls: List[ToolCall],
        task_id: Optional[str] = None,
        weights: Optional[Dict[str, float]] = None,
        thresholds: Optional[Dict[str, float]] = None
    ) -> ToolEvalResult:
        """
        Evaluate tool calls using flexible/soft matching criteria.
        This is more lenient with parameter matching and is useful for
        evaluating cases where exact parameter values aren't critical.
        
        Args:
            ground_truth_calls: List of expected tool calls
            prediction_calls: List of actual tool calls made by the model
            task_id: Optional identifier for the task
            weights: Optional dictionary with custom weights
            thresholds: Optional dictionary with custom thresholds
            
        Returns:
            ToolEvalResult with flexible evaluation metrics
        """
        return StaticToolEvaluator.evaluate_task(
            ground_truth_calls, prediction_calls, task_id, 
            match_type="flexible", weights=weights, thresholds=thresholds
        )
    
    @staticmethod
    def evaluate_from_json(
        ground_truth_json: Dict[str, Any],
        prediction_json: Dict[str, Any],
        match_type: Literal["strict", "flexible"] = "strict"
    ) -> ToolEvalResult:
        """
        Evaluate tool calls from JSON data.
        
        Args:
            ground_truth_json: Dictionary containing ground truth data with tool_calls
            prediction_json: Dictionary containing prediction data with tool_calls
            match_type: Type of matching to use ("strict" for exact matching, "flexible" for soft matching)
            
        Returns:
            ToolEvalResult with detailed evaluation metrics
        """
        # Extract tool calls from JSON
        gt_tool_calls = [
            ToolCall(tool_name=tc["tool_name"], tool_parameters=tc["tool_parameters"])
            for tc in ground_truth_json.get("tool_calls", [])
        ]
        
        pred_tool_calls = [
            ToolCall(tool_name=tc["tool_name"], tool_parameters=tc["tool_parameters"])
            for tc in prediction_json.get("tool_calls", [])
        ]
        
        # Get task ID from either input
        task_id = (
            ground_truth_json.get("task_id") or 
            ground_truth_json.get("id") or 
            ground_truth_json.get("name") or
            prediction_json.get("task_id") or
            "unknown"
        )
        
        return StaticToolEvaluator.evaluate_task(gt_tool_calls, pred_tool_calls, task_id, match_type)
    
    @staticmethod
    def batch_evaluate_with_both_match_types(
        ground_truth_data: Union[str, List[Dict]],
        prediction_data: Union[str, List[Dict]],
        weights: Optional[Dict[str, float]] = None,
        thresholds: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate multiple tasks using both strict and flexible matching.
        
        Args:
            ground_truth_data: Either a JSON string or list of dictionaries with ground truth data
            prediction_data: Either a JSON string or list of dictionaries with prediction data
            weights: Optional dictionary with custom weights
            thresholds: Optional dictionary with custom thresholds
            
        Returns:
            Dictionary with overall statistics and individual task results for both match types
        """
        # Parse data if needed
        if isinstance(ground_truth_data, str):
            if ground_truth_data.strip().startswith('['):
                ground_truth_data = json.loads(ground_truth_data)
            else:
                # Handle JSONL format
                ground_truth_data = [json.loads(line) for line in ground_truth_data.strip().split('\n') if line.strip()]
        
        if isinstance(prediction_data, str):
            if prediction_data.strip().startswith('['):
                prediction_data = json.loads(prediction_data)
            else:
                # Handle JSONL format
                prediction_data = [json.loads(line) for line in prediction_data.strip().split('\n') if line.strip()]
        
        # Convert to dictionaries keyed by task_id
        gt_dict = {}
        for item in ground_truth_data:
            task_id = item.get("task_id") or item.get("id") or item.get("name")
            if task_id:
                gt_dict[task_id] = item
        
        pred_dict = {}
        for item in prediction_data:
            task_id = item.get("task_id") or item.get("id") or item.get("name")
            if task_id:
                pred_dict[task_id] = item
        
        # Evaluate each task with both match types
        results = {}
        for task_id in set(gt_dict.keys()).intersection(pred_dict.keys()):
            gt_tool_calls = [
                ToolCall(tool_name=tc["tool_name"], tool_parameters=tc["tool_parameters"])
                for tc in gt_dict[task_id].get("tool_calls", [])
            ]
            
            pred_tool_calls = [
                ToolCall(tool_name=tc["tool_name"], tool_parameters=tc["tool_parameters"])
                for tc in pred_dict[task_id].get("tool_calls", [])
            ]
            
            results[task_id] = StaticToolEvaluator.evaluate_with_both_match_types(
                gt_tool_calls, pred_tool_calls, task_id, weights, thresholds
            )
        
        # Calculate overall statistics for both match types
        strict_scores = [r["strict"]["overall_score"] for r in results.values()]
        flexible_scores = [r["flexible"]["overall_score"] for r in results.values()]
        
        strict_success = sum(1 for r in results.values() if r["strict"]["success"])
        flexible_success = sum(1 for r in results.values() if r["flexible"]["success"])
        
        # Compute averages for various metrics
        strict_name_scores = [r["strict"]["tool_name_score"] for r in results.values()]
        strict_param_scores = [r["strict"]["param_match_score"] for r in results.values()]
        strict_order_scores = [r["strict"]["order_score"] for r in results.values()]
        
        flexible_name_scores = [r["flexible"]["tool_name_score"] for r in results.values()]
        flexible_param_scores = [r["flexible"]["param_match_score"] for r in results.values()]
        flexible_order_scores = [r["flexible"]["order_score"] for r in results.values()]
        
        overall_stats = {
            "total_tasks": len(results),
            "strict": {
                "successful_tasks": strict_success,
                "success_rate": strict_success / len(results) if results else 0.0,
                "average_score": np.mean(strict_scores) if strict_scores else 0.0,
                "tool_name_accuracy": np.mean(strict_name_scores) if strict_name_scores else 0.0,
                "param_match_accuracy": np.mean(strict_param_scores) if strict_param_scores else 0.0,
                "order_score": np.mean(strict_order_scores) if strict_order_scores else 0.0,
            },
            "flexible": {
                "successful_tasks": flexible_success,
                "success_rate": flexible_success / len(results) if results else 0.0,
                "average_score": np.mean(flexible_scores) if flexible_scores else 0.0,
                "tool_name_accuracy": np.mean(flexible_name_scores) if flexible_name_scores else 0.0,
                "param_match_accuracy": np.mean(flexible_param_scores) if flexible_param_scores else 0.0,
                "order_score": np.mean(flexible_order_scores) if flexible_order_scores else 0.0,
            }
        }
        
        return {
            "overall_stats": overall_stats,
            "task_results": results
        }


# Example usage function
def evaluate_tool_calls_with_both_match_types(
    ground_truth_path: str,
    prediction_path: str,
    output_path: Optional[str] = None,
    weights: Optional[Dict[str, float]] = None,
    thresholds: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Evaluate tool calls by comparing ground truth to predictions using both match types.
    
    Args:
        ground_truth_path: Path to ground truth JSON or JSONL file
        prediction_path: Path to prediction JSON or JSONL file
        output_path: Optional path to write results
        weights: Optional dictionary with custom weights for scoring components:
                {"name": float, "params": float, "order": float}
        thresholds: Optional dictionary with custom thresholds:
                {"flexible_param": float, "flexible_order": float}
        
    Returns:
        Dictionary with evaluation results for both strict and flexible matching
    """
    # Load data
    with open(ground_truth_path, 'r') as f:
        ground_truth_data = f.read()
    
    with open(prediction_path, 'r') as f:
        prediction_data = f.read()
    
    # Run evaluation
    results = StaticToolEvaluator.batch_evaluate_with_both_match_types(
        ground_truth_data, prediction_data, weights=weights, thresholds=thresholds
    )
    
    # Write results if output path is provided
    if output_path:
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
    
    return results
