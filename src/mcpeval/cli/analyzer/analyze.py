#!/usr/bin/env python
"""
Analysis module for comparing evaluation results against ground truth.
This module combines scoring and detailed analysis functionality.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from mcpeval.utils.cli import (
    extract_tool_calls_from_ground_truth,
    extract_tool_calls_from_prediction,
    load_json,
    load_jsonl,
)

# Import report generation functions
from .report_generator import generate_ai_report

# Import core analysis functions
from .tool_analysis import (
    analyze_parameter_mismatches,
    analyze_success_patterns,
    analyze_tool_usage,
    load_metrics_content,
    perform_evaluation,
    print_summary,
)


def main(args):
    """Main analysis function."""

    # Validate required arguments
    if not args.predictions or not args.ground_truth:
        print("❌ Error: Both --predictions and --ground-truth arguments are required")
        return

    # Construct weights and thresholds dictionaries
    weights = {
        "name": args.name_weight,
        "params": args.params_weight,
        "order": args.order_weight,
    }

    thresholds = {
        "flexible_param": args.param_threshold,
        "flexible_order": args.order_threshold,
    }

    # Validate weights sum to approximately 1.0
    weight_sum = sum(weights.values())
    if abs(weight_sum - 1.0) > 0.001:
        print(f"⚠️  Warning: Provided weights sum to {weight_sum}, not 1.0.")
        print("Normalizing weights to ensure they sum to 1.0.")
        factor = 1.0 / weight_sum
        weights = {k: v * factor for k, v in weights.items()}
        print(f"✅ Normalized weights: {weights}")

    # Load data
    print(f"📂 Loading prediction data from: {args.predictions}")
    try:
        if args.predictions.endswith(".jsonl"):
            prediction_data = load_jsonl(args.predictions)
        else:
            prediction_data = load_json(args.predictions)
    except Exception as e:
        print(f"❌ Error loading prediction data: {str(e)}")
        return

    print(f"📂 Loading ground truth data from: {args.ground_truth}")
    try:
        if args.ground_truth.endswith(".jsonl"):
            ground_truth_data = load_jsonl(args.ground_truth)
        else:
            ground_truth_data = load_json(args.ground_truth)
    except Exception as e:
        print(f"❌ Error loading ground truth data: {str(e)}")
        return

    print(
        f"🔍 Found {len(prediction_data)} prediction tasks and {len(ground_truth_data)} ground truth tasks"
    )

    # Perform evaluation
    print(f"⚖️  Performing evaluation with custom weights and thresholds...")
    results = perform_evaluation(
        prediction_data, ground_truth_data, weights, thresholds
    )

    # Perform detailed analysis
    print(f"📊 Performing detailed analysis...")
    analysis = {
        "summary": results["summary_metrics"],
        "parameter_mismatches": analyze_parameter_mismatches(results),
        "tool_usage": analyze_tool_usage(results),
        "success_patterns": analyze_success_patterns(results),
        "evaluation_config": {"weights": weights, "thresholds": thresholds},
    }

    # Determine output directory and base filename
    predictions_path = Path(args.predictions)
    output_dir = predictions_path.parent
    base_name = predictions_path.stem

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save evaluation results if explicitly requested
    if args.evaluation_output:
        evaluation_output = Path(args.evaluation_output)
        with open(evaluation_output, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"💾 Task-level metrics saved to: {evaluation_output}")

    # Save analysis results
    if args.analysis_output:
        analysis_output = Path(args.analysis_output)
    else:
        analysis_filename = f"{base_name}_summary_analysis.json"
        analysis_output = output_dir / analysis_filename

    with open(analysis_output, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2)

    print(f"💾 Summary analysis saved to: {analysis_output}")

    # Generate AI report if requested
    if args.generate_report:
        print(f"🤖 Generating AI performance report using {args.report_model}...")
        try:
            # Prepare output path
            if args.report_output:
                report_output = Path(args.report_output)
            else:
                report_filename = f"{base_name}_ai_report.md"
                report_output = output_dir / report_filename

            # Generate the report
            report_content = generate_ai_report(analysis, args.report_model)

            # Save report
            with open(report_output, "w", encoding="utf-8") as f:
                f.write(report_content)

            print(f"📄 AI performance report saved to: {report_output}")

        except Exception as e:
            print(f"❌ Failed to generate AI report: {str(e)}")

    # Print comprehensive summary
    print_summary(results, analysis)

    print(f"\n✅ Analysis completed successfully!")

    # Calculate match rates from the available data
    total_tasks = analysis["summary"]["total_tasks"]
    exact_match_rate = (
        analysis["summary"]["exact_match"]["tasks_with_complete_success"] / total_tasks
        if total_tasks > 0
        else 0
    )
    flexible_match_rate = (
        analysis["summary"]["flexible_match"]["tasks_with_complete_success"]
        / total_tasks
        if total_tasks > 0
        else 0
    )

    print(
        f"📊 Summary: {exact_match_rate:.1%} exact match rate, "
        f"{flexible_match_rate:.1%} flexible match rate"
    )


if __name__ == "__main__":
    # When run directly, this should not happen as the main CLI handles argument parsing
    print("Please use the main CLI: python -m mcpeval.cli.main analyze --help")
    import sys

    sys.exit(1)
