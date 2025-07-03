#!/usr/bin/env python
"""
Analysis module for comparing evaluation results against ground truth.
This module combines scoring and detailed analysis functionality.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Tuple
from collections import Counter, defaultdict
import sys

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from mcp_eval_llm.metrics.static_tool_eval import StaticToolEvaluator
from mcp_eval_llm.commons.types import ToolCall
from mcp_eval_llm.utils.cli import (
    load_jsonl, 
    load_json, 
    extract_tool_calls_from_prediction, 
    extract_tool_calls_from_ground_truth
)

# Import OpenAI for report generation
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv is optional, continue without it
    pass


def analyze_parameter_mismatches(results: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze parameter mismatches across all tasks."""
    parameter_mismatches = defaultdict(lambda: defaultdict(int))
    
    for task_result in results["task_results"]:
        eval_result = task_result["evaluation"]
        
        # Check each tool's parameter mismatches
        for tool_name, mismatches in eval_result.get("param_mismatches", {}).items():
            for param_name in mismatches.keys():
                parameter_mismatches[tool_name][param_name] += 1
    
    # Convert to regular dict for JSON serialization
    return {
        tool: dict(params) for tool, params in parameter_mismatches.items()
    }


def analyze_tool_usage(results: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze tool usage patterns in ground truth and predictions."""
    gt_tools = Counter()
    pred_tools = Counter()
    missing_tools = Counter()
    extra_tools = Counter()
    
    for task_result in results["task_results"]:
        ground_truth_calls = task_result["ground_truth_calls"]
        prediction_calls = task_result["prediction_calls"]
        
        # Count tools in ground truth
        for call in ground_truth_calls:
            gt_tools[call["tool_name"]] += 1
        
        # Count tools in predictions
        for call in prediction_calls:
            pred_tools[call["tool_name"]] += 1
        
        # Count missing and extra tools
        eval_result = task_result["evaluation"]
        for tool in eval_result.get("missing_tools", []):
            missing_tools[tool] += 1
        
        for tool in eval_result.get("extra_tools", []):
            extra_tools[tool] += 1
    
    return {
        "ground_truth_tools": dict(gt_tools),
        "prediction_tools": dict(pred_tools),
        "missing_tools": dict(missing_tools),
        "extra_tools": dict(extra_tools)
    }


def analyze_success_patterns(results: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze patterns in successful vs failed evaluations."""
    # Categorize by number of tools in the task
    tools_count_analysis = {
        "strict": {"success": {}, "failure": {}},
        "flexible": {"success": {}, "failure": {}}
    }
    
    # Track success/failure for specific tool combinations
    tool_combo_analysis = {
        "strict": {"success": {}, "failure": {}},
        "flexible": {"success": {}, "failure": {}}
    }
    
    # Track per-tool success rates
    tool_counts = defaultdict(lambda: {"success": 0, "failure": 0})
    
    # Process tasks
    for task_result in results["task_results"]:
        gt_calls = task_result["ground_truth_calls"]
        gt_call_count = len(gt_calls)
        
        # Extract tool names and create a descriptive key
        gt_tools = [call["tool_name"] for call in gt_calls]
        tool_counts_by_type = Counter(gt_tools)
        
        # Create a readable representation of the tool combination
        tools_description = ", ".join([f"{count}x {tool}" for tool, count in tool_counts_by_type.items()])
        
        # Check strict matching success
        strict_success = task_result["evaluation"]["strict"]["success"]
        
        # Track by tool count
        if gt_call_count not in tools_count_analysis["strict"]["success"]:
            tools_count_analysis["strict"]["success"][gt_call_count] = 0
            tools_count_analysis["strict"]["failure"][gt_call_count] = 0
        
        if strict_success:
            tools_count_analysis["strict"]["success"][gt_call_count] += 1
            tool_combo_analysis["strict"]["success"][tools_description] = tool_combo_analysis["strict"]["success"].get(tools_description, 0) + 1
            
            # Count success per tool
            for tool in gt_tools:
                tool_counts[tool]["success"] += 1
        else:
            tools_count_analysis["strict"]["failure"][gt_call_count] += 1
            tool_combo_analysis["strict"]["failure"][tools_description] = tool_combo_analysis["strict"]["failure"].get(tools_description, 0) + 1
            
            # Count failure per tool
            for tool in gt_tools:
                tool_counts[tool]["failure"] += 1
        
        # Check flexible matching success
        flexible_success = task_result["evaluation"]["flexible"]["success"]
        
        # Track by tool count
        if gt_call_count not in tools_count_analysis["flexible"]["success"]:
            tools_count_analysis["flexible"]["success"][gt_call_count] = 0
            tools_count_analysis["flexible"]["failure"][gt_call_count] = 0
            
        if flexible_success:
            tools_count_analysis["flexible"]["success"][gt_call_count] += 1
            tool_combo_analysis["flexible"]["success"][tools_description] = tool_combo_analysis["flexible"]["success"].get(tools_description, 0) + 1
        else:
            tools_count_analysis["flexible"]["failure"][gt_call_count] += 1
            tool_combo_analysis["flexible"]["failure"][tools_description] = tool_combo_analysis["flexible"]["failure"].get(tools_description, 0) + 1
    
    # Calculate tool-specific success rates
    tool_success_rates = {}
    for tool, counts in tool_counts.items():
        total = counts["success"] + counts["failure"]
        if total > 0:
            success_rate = counts["success"] / total
            tool_success_rates[tool] = {
                "success_rate": success_rate,
                "total_tasks": total,
                "successful_tasks": counts["success"]
            }
    
    # Organize by group size
    for match_type in ["strict", "flexible"]:
        for result_type in ["success", "failure"]:
            tools_count_analysis[match_type][result_type] = dict(sorted(
                tools_count_analysis[match_type][result_type].items()
            ))
            tool_combo_analysis[match_type][result_type] = dict(sorted(
                tool_combo_analysis[match_type][result_type].items(),
                key=lambda x: x[1],
                reverse=True
            ))
    
    return {
        "by_tool_count": tools_count_analysis,
        "by_tool_combination": tool_combo_analysis,
        "by_tool": tool_success_rates
    }


def perform_evaluation(prediction_data: List[Dict[str, Any]], 
                      ground_truth_data: List[Dict[str, Any]], 
                      weights: Dict[str, float], 
                      thresholds: Dict[str, float]) -> Dict[str, Any]:
    """Perform the evaluation comparing predictions against ground truth."""
    
    # Create mappings of task_id -> tool_calls
    predictions_map = {}
    for task in prediction_data:
        task_id, tool_calls = extract_tool_calls_from_prediction(task)
        if task_id:
            predictions_map[task_id] = tool_calls
    
    ground_truth_map = {}
    for task in ground_truth_data:
        task_id, tool_calls = extract_tool_calls_from_ground_truth(task)
        if task_id:
            ground_truth_map[task_id] = tool_calls
    
    # Perform evaluation for each task
    results = {
        "task_results": [],
        "summary_metrics": {
            "total_tasks": 0,
            "tasks_with_matching_tools": 0,
            "exact_match": {
                "tasks_with_complete_success": 0,
                "average_name_match_score": 0.0,
                "average_param_match_score": 0.0,
                "average_order_match_score": 0.0,
                "average_overall_score": 0.0
            },
            "flexible_match": {
                "tasks_with_complete_success": 0,
                "average_name_match_score": 0.0,
                "average_param_match_score": 0.0,
                "average_order_match_score": 0.0,
                "average_overall_score": 0.0
            },
            "weights": weights,
            "thresholds": thresholds
        }
    }
    
    # Keep track of metrics for summary
    total_tasks = 0
    tasks_with_matching_tool_ids = 0
    
    exact_successful_tasks = 0
    exact_name_scores = []
    exact_param_scores = []
    exact_order_scores = []
    exact_overall_scores = []
    
    flexible_successful_tasks = 0
    flexible_name_scores = []
    flexible_param_scores = []
    flexible_order_scores = []
    flexible_overall_scores = []
    
    # Evaluate each task
    for task_id, ground_truth_calls in ground_truth_map.items():
        if task_id not in predictions_map:
            print(f"Warning: Task ID {task_id} not found in predictions")
            continue
        
        prediction_calls = predictions_map[task_id]
        total_tasks += 1
        
        # Evaluate with both match types
        eval_result = StaticToolEvaluator.evaluate_with_both_match_types(
            ground_truth_calls=ground_truth_calls,
            prediction_calls=prediction_calls,
            task_id=task_id,
            weights=weights,
            thresholds=thresholds
        )
        
        # Extract metrics
        if len(eval_result["missing_tools"]) < len(ground_truth_calls):
            tasks_with_matching_tool_ids += 1
        
        # Exact match metrics
        exact_result = eval_result["strict"]
        if exact_result["success"]:
            exact_successful_tasks += 1
        exact_name_scores.append(exact_result["tool_name_score"])
        exact_param_scores.append(exact_result["param_match_score"])
        exact_order_scores.append(exact_result["order_score"])
        exact_overall_scores.append(exact_result["overall_score"])
        
        # Flexible match metrics
        flexible_result = eval_result["flexible"]
        if flexible_result["success"]:
            flexible_successful_tasks += 1
        flexible_name_scores.append(flexible_result["tool_name_score"])
        flexible_param_scores.append(flexible_result["param_match_score"])
        flexible_order_scores.append(flexible_result["order_score"])
        flexible_overall_scores.append(flexible_result["overall_score"])
        
        # Add task result to output
        results["task_results"].append({
            "task_id": task_id,
            "ground_truth_calls": [call.__dict__ for call in ground_truth_calls],
            "prediction_calls": [call.__dict__ for call in prediction_calls],
            "evaluation": eval_result
        })
    
    # Calculate summary metrics
    results["summary_metrics"]["total_tasks"] = total_tasks
    results["summary_metrics"]["tasks_with_matching_tools"] = tasks_with_matching_tool_ids
    
    # Exact match summary
    results["summary_metrics"]["exact_match"]["tasks_with_complete_success"] = exact_successful_tasks
    results["summary_metrics"]["exact_match"]["average_name_match_score"] = sum(exact_name_scores) / total_tasks if total_tasks > 0 else 0
    results["summary_metrics"]["exact_match"]["average_param_match_score"] = sum(exact_param_scores) / total_tasks if total_tasks > 0 else 0
    results["summary_metrics"]["exact_match"]["average_order_match_score"] = sum(exact_order_scores) / total_tasks if total_tasks > 0 else 0
    results["summary_metrics"]["exact_match"]["average_overall_score"] = sum(exact_overall_scores) / total_tasks if total_tasks > 0 else 0
    
    # Flexible match summary
    results["summary_metrics"]["flexible_match"]["tasks_with_complete_success"] = flexible_successful_tasks
    results["summary_metrics"]["flexible_match"]["average_name_match_score"] = sum(flexible_name_scores) / total_tasks if total_tasks > 0 else 0
    results["summary_metrics"]["flexible_match"]["average_param_match_score"] = sum(flexible_param_scores) / total_tasks if total_tasks > 0 else 0
    results["summary_metrics"]["flexible_match"]["average_order_match_score"] = sum(flexible_order_scores) / total_tasks if total_tasks > 0 else 0
    results["summary_metrics"]["flexible_match"]["average_overall_score"] = sum(flexible_overall_scores) / total_tasks if total_tasks > 0 else 0
    
    return results


def print_summary(results: Dict[str, Any], analysis: Dict[str, Any]):
    """Print a comprehensive summary of the evaluation and analysis."""
    print("\n" + "="*80)
    print("EVALUATION SUMMARY")
    print("="*80)
    
    total_tasks = results["summary_metrics"]["total_tasks"]
    tasks_with_matching = results["summary_metrics"]["tasks_with_matching_tools"]
    weights = results["summary_metrics"]["weights"]
    thresholds = results["summary_metrics"]["thresholds"]
    
    print(f"📊 Total tasks evaluated: {total_tasks}")
    print(f"🎯 Tasks with matching tool names: {tasks_with_matching}")
    print(f"⚖️  Weights used: name={weights['name']:.2f}, params={weights['params']:.2f}, order={weights['order']:.2f}")
    print(f"🎚️  Thresholds used: param={thresholds['flexible_param']:.2f}, order={thresholds['flexible_order']:.2f}")
    
    print(f"\n📈 EXACT MATCH METRICS:")
    exact = results["summary_metrics"]["exact_match"]
    exact_success_rate = exact['tasks_with_complete_success'] / total_tasks * 100 if total_tasks > 0 else 0
    print(f"  ✅ Tasks with complete success: {exact['tasks_with_complete_success']} ({exact_success_rate:.1f}%)")
    print(f"  🏷️  Average name match score: {exact['average_name_match_score']:.3f}")
    print(f"  🔧 Average parameter match score: {exact['average_param_match_score']:.3f}")
    print(f"  📋 Average order match score: {exact['average_order_match_score']:.3f}")
    print(f"  🎯 Average overall score: {exact['average_overall_score']:.3f}")
    
    print(f"\n📈 FLEXIBLE MATCH METRICS:")
    flexible = results["summary_metrics"]["flexible_match"]
    flexible_success_rate = flexible['tasks_with_complete_success'] / total_tasks * 100 if total_tasks > 0 else 0
    print(f"  ✅ Tasks with complete success: {flexible['tasks_with_complete_success']} ({flexible_success_rate:.1f}%)")
    print(f"  🏷️  Average name match score: {flexible['average_name_match_score']:.3f}")
    print(f"  🔧 Average parameter match score: {flexible['average_param_match_score']:.3f}")
    print(f"  📋 Average order match score: {flexible['average_order_match_score']:.3f}")
    print(f"  🎯 Average overall score: {flexible['average_overall_score']:.3f}")
    
    print(f"\n🔍 DETAILED ANALYSIS:")
    
    # Most common parameter mismatches
    print(f"\n❌ TOP PARAMETER MISMATCHES:")
    for tool_name, params in analysis["parameter_mismatches"].items():
        top_mismatches = sorted(params.items(), key=lambda x: x[1], reverse=True)[:3]
        if top_mismatches:
            print(f"  🔧 Tool '{tool_name}':")
            for param, count in top_mismatches:
                print(f"    - '{param}': {count} mismatches")
    
    # Success rates by tool
    print(f"\n🏆 TOOL SUCCESS RATES (Strict Matching):")
    tool_rates = sorted(
        analysis["success_patterns"]["by_tool"].items(),
        key=lambda x: x[1]["success_rate"],
        reverse=True
    )
    
    for tool, stats in tool_rates:
        print(f"  - {tool}: {stats['success_rate']*100:.1f}% ({stats['successful_tasks']}/{stats['total_tasks']} tasks)")
    
    # Success rates by tool count (strict)
    print(f"\n📊 SUCCESS RATE BY TOOL COUNT (Strict Matching):")
    strict_counts = analysis["success_patterns"]["by_tool_count"]["strict"]
    for count in sorted(set(strict_counts["success"].keys()) | set(strict_counts["failure"].keys())):
        success = strict_counts["success"].get(count, 0)
        failure = strict_counts["failure"].get(count, 0)
        total = success + failure
        rate = success / total if total else 0
        print(f"  - {count} tool(s): {rate*100:.1f}% ({success}/{total} tasks)")
    
    # Top successful tool combinations
    print(f"\n🎭 TOP TOOL COMBINATIONS (Success Rate with Strict Matching):")
    tool_combos = analysis["success_patterns"]["by_tool_combination"]["strict"]
    all_combos = set(tool_combos["success"].keys()) | set(tool_combos["failure"].keys())
    combo_rates = []
    
    for combo in all_combos:
        success = tool_combos["success"].get(combo, 0)
        failure = tool_combos["failure"].get(combo, 0)
        total = success + failure
        if total >= 5:  # Only show combinations with at least 5 occurrences
            rate = success / total if total else 0
            combo_rates.append((combo, rate, success, total))
    
    # Sort by success rate
    for combo, rate, success, total in sorted(combo_rates, key=lambda x: x[1], reverse=True)[:5]:
        print(f"  - {combo}: {rate*100:.1f}% ({success}/{total} tasks)")
    
    # Most common missing tools
    print(f"\n❓ MOST COMMONLY MISSING TOOLS:")
    for tool, count in sorted(analysis["tool_usage"]["missing_tools"].items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  - {tool}: missing in {count} tasks")
    
    # Most common extra tools
    print(f"\n➕ MOST COMMONLY EXTRA TOOLS:")
    for tool, count in sorted(analysis["tool_usage"]["extra_tools"].items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  - {tool}: extra in {count} tasks")


def load_metrics_content() -> str:
    """Load the metrics.md content from the analyzer directory."""
    metrics_path = Path(__file__).parent / "metrics.md"
    try:
        with open(metrics_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Metrics documentation not available."


def generate_ai_report(analysis: Dict[str, Any], model: str = "gpt-4o") -> str:
    """Generate an AI-powered performance report using OpenAI models."""
    if not OPENAI_AVAILABLE:
        raise ImportError("OpenAI package is not installed. Install it with: pip install openai")
    
    # Load metrics content
    metrics_content = load_metrics_content()
    
    # Create OpenAI client
    client = OpenAI()
    
    # System prompt with metrics content
    system_prompt = f"""Given the metric documentation content:

{metrics_content}

Generate a comprehensive model performance report based on the provided analysis data. 

Your report should:
1. Provide an executive summary of the model's performance
2. Include structured tables for key metrics and performance breakdowns
3. Highlight key strengths and weaknesses 
4. Identify specific areas for improvement
5. Explain the significance of the metrics in plain language
6. Provide actionable recommendations
7. Use the metric definitions from the documentation to give context

IMPORTANT: Include well-formatted tables for:
- Performance by Task Complexity (number of tools vs success rate)
- Tool-Specific Performance (individual tool success rates)
- Top Tool Combinations (with success rates)
- Parameter Mismatches (most common parameter errors)

Use markdown table format like this example:
| Tool | Success Rate | Successful Tasks | Total Tasks |
|------|--------------|------------------|-------------|
| tool_name | 85.0% | 17/20 | 20 |

Format the report in clear markdown with appropriate sections, emphasis, and well-structured tables."""

    # User prompt with analysis results
    user_prompt = f"""Please analyze this model evaluation data and generate a performance report:

{json.dumps(analysis, indent=2)}"""

    try:
        # Generate the report
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=4000
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        raise Exception(f"Failed to generate AI report: {str(e)}")


def generate_report_from_summary(summary_file: str, model: str = "gpt-4o", output_file: str = None) -> str:
    """Generate an AI report directly from a summary analysis JSON file."""
    if not OPENAI_AVAILABLE:
        raise ImportError("OpenAI package is not installed. Install it with: pip install openai")
    
    # Load the summary analysis file
    try:
        with open(summary_file, 'r', encoding='utf-8') as f:
            analysis = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Summary file not found: {summary_file}")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON format in summary file: {summary_file}")
    
    # Prepare output file path
    if output_file is None:
        base_name = os.path.splitext(summary_file)[0]
        if base_name.endswith('_summary_analysis'):
            base_name = base_name[:-16]  # Remove '_summary_analysis' suffix
        output_file = f"{base_name}_ai_report.md"
    
    # Create directory if it doesn't exist (before API call)
    output_dir = os.path.dirname(output_file)
    if output_dir:  # Only create directory if it's not empty
        os.makedirs(output_dir, exist_ok=True)
    
    # Generate the report
    report_content = generate_ai_report(analysis, model)
    
    # Save the report
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    return output_file


def main(args):
    """Main analysis function."""
    
    # Check if we're generating a report from an existing summary file
    if hasattr(args, 'from_summary') and args.from_summary:
        print(f"🤖 Generating AI report from summary file: {args.from_summary}")
        try:
            output_file = generate_report_from_summary(
                args.from_summary, 
                args.report_model,
                args.report_output
            )
            print(f"📄 AI performance report saved to: {output_file}")
            print(f"\n✅ Report generation completed successfully!")
            return
        except Exception as e:
            print(f"❌ Failed to generate report from summary: {str(e)}")
            return
    
    # Continue with normal analysis workflow if not generating from summary
    # Construct weights and thresholds dictionaries
    weights = {
        "name": args.name_weight,
        "params": args.params_weight,
        "order": args.order_weight
    }
    
    thresholds = {
        "flexible_param": args.param_threshold,
        "flexible_order": args.order_threshold
    }
    
    # Validate weights sum to approximately 1.0
    weight_sum = sum(weights.values())
    if abs(weight_sum - 1.0) > 0.001:
        print(f"Warning: Provided weights sum to {weight_sum}, not 1.0.")
        print("Normalizing weights to ensure they sum to 1.0.")
        factor = 1.0 / weight_sum
        weights = {k: v * factor for k, v in weights.items()}
        print(f"Normalized weights: {weights}")

    # Load data
    print(f"📂 Loading prediction data from: {args.predictions}")
    if args.predictions.endswith('.jsonl'):
        prediction_data = load_jsonl(args.predictions)
    else:
        prediction_data = load_json(args.predictions)
    
    print(f"📂 Loading ground truth data from: {args.ground_truth}")
    if args.ground_truth.endswith('.jsonl'):
        ground_truth_data = load_jsonl(args.ground_truth)
    else:
        ground_truth_data = load_json(args.ground_truth)
    
    print(f"🔍 Found {len(prediction_data)} prediction tasks and {len(ground_truth_data)} ground truth tasks")
    
    # Perform evaluation
    print(f"⚖️  Performing evaluation...")
    results = perform_evaluation(prediction_data, ground_truth_data, weights, thresholds)
    
    # Perform detailed analysis
    print(f"📊 Performing detailed analysis...")
    analysis = {
        "summary": results["summary_metrics"],
        "parameter_mismatches": analyze_parameter_mismatches(results),
        "tool_usage": analyze_tool_usage(results),
        "success_patterns": analyze_success_patterns(results)
    }
    
    # Determine output directory and base filename
    if args.report_output:
        output_dir = os.path.dirname(args.report_output)
        base_name = os.path.splitext(os.path.basename(args.predictions))[0]
    else:
        output_dir = os.path.dirname(args.predictions)
        base_name = os.path.splitext(os.path.basename(args.predictions))[0]
    
    # Create output directory if it doesn't exist
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Save evaluation results only if explicitly requested
    if args.evaluation_output:
        evaluation_output = args.evaluation_output
        with open(evaluation_output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        print(f"💾 Task-level metrics saved to: {evaluation_output}")
    
    # Save analysis results
    if args.analysis_output:
        analysis_output = args.analysis_output
    else:
        analysis_filename = f"{base_name}_summary_analysis.json"
        analysis_output = os.path.join(output_dir, analysis_filename) if output_dir else analysis_filename
    
    with open(analysis_output, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2)
    
    print(f"💾 Summary analysis saved to: {analysis_output}")
    
    # Generate AI report if requested
    if args.generate_report:
        print(f"🤖 Generating AI performance report using {args.report_model}...")
        try:
            # Prepare output path (directory already created above)
            if args.report_output:
                report_output = args.report_output
            else:
                report_filename = f"{base_name}_ai_report.md"
                report_output = os.path.join(output_dir, report_filename) if output_dir else report_filename
            
            # Generate the report
            report_content = generate_ai_report(analysis, args.report_model)
            
            # Save report
            with open(report_output, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            print(f"📄 AI performance report saved to: {report_output}")
            
        except Exception as e:
            print(f"❌ Failed to generate AI report: {str(e)}")
            print("💡 Make sure you have the OpenAI API key set and the openai package installed")
    
    # Print comprehensive summary
    print_summary(results, analysis)
    
    print(f"\n✅ Analysis completed successfully!")


if __name__ == "__main__":
    # When run directly, this should not happen as the main CLI handles argument parsing
    print("Please use the main CLI: python -m mcp_eval_llm.cli.main analyze --help")
    import sys
    sys.exit(1) 