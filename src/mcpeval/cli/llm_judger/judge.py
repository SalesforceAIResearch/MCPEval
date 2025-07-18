#!/usr/bin/env python3
"""
LLM Judger CLI for evaluating execution results with LLM judges.

This module provides command-line interface for using LLM judges to evaluate
AI agent execution trajectories from JSON evaluation files.
"""

import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

from mcpeval.metrics.llm_multi_aspect_eval import (
    MultiAspectLLMJudger,
)
from mcpeval.utils.cli import (
    Colors,
    colored_print,
    setup_colored_logging,
    load_jsonl,
    load_json,
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
setup_colored_logging(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_evaluation_data(file_path: str) -> List[Dict[str, Any]]:
    """Load evaluation results from JSON/JSONL file."""
    try:
        if file_path.endswith(".jsonl"):
            return load_jsonl(file_path)
        else:
            return load_json(file_path)

    except Exception as e:
        colored_print(
            f"❌ Error loading evaluation data from {file_path}: {e}", Colors.RED
        )
        sys.exit(1)


def load_ground_truth_data(file_path: str) -> Dict[str, Dict[str, Any]]:
    """Load ground truth data from JSON/JSONL file and return as dict keyed by task_id."""
    try:
        if file_path.endswith(".jsonl"):
            data = load_jsonl(file_path)
        else:
            data = load_json(file_path)

        # Create a mapping from task_id to ground truth data
        ground_truth_map = {}
        for item in data:
            task_id = item.get("id")
            if task_id:
                ground_truth_map[task_id] = item

        return ground_truth_map

    except Exception as e:
        colored_print(
            f"❌ Error loading ground truth data from {file_path}: {e}", Colors.RED
        )
        sys.exit(1)


def extract_final_response(execution_trajectory: List[Dict[str, Any]]) -> str:
    """Extract the final response from the execution trajectory."""
    for msg in reversed(execution_trajectory):
        if (
            msg.get("role") == "assistant"
            and not msg.get("tool_calls")
            and msg.get("content")
        ):
            return msg.get("content", "")
    return ""


def save_result_to_jsonl(result: Dict[str, Any], output_file: str) -> None:
    """Save a single result to JSONL file."""
    try:
        # Ensure output directory exists
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Append result to JSONL file
        with open(output_file, "a", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False)
            f.write("\n")

    except Exception as e:
        colored_print(f"⚠️ Warning: Could not save result: {e}", Colors.YELLOW)


def get_output_files(
    output_dir: Optional[str],
    input_file: str,
    final_model_name: str,
    trajectory_only: bool = False,
    completion_only: bool = False,
) -> Dict[str, Optional[str]]:
    """Generate output file paths for different result types based on output directory and input file name."""
    if not output_dir:
        return {"combined": None, "trajectory": None, "completion": None}

    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Generate file names based on input file name and model name
    input_path = Path(input_file)
    base_name = input_path.stem

    # Clean model name for file naming (replace problematic characters)
    clean_model_name = (
        final_model_name.replace("/", "_").replace(":", "_").replace(" ", "_")
    )

    # Create file names with base name first
    combined_file = str(
        output_path / f"{base_name}_with_{clean_model_name}_judge_results.jsonl"
    )
    trajectory_file = str(
        output_path / f"{base_name}_with_{clean_model_name}_trajectory.jsonl"
    )
    completion_file = str(
        output_path / f"{base_name}_with_{clean_model_name}_completion.jsonl"
    )

    return {
        "combined": combined_file,
        "trajectory": trajectory_file,
        "completion": completion_file,
    }


def load_existing_results(output_file: str) -> List[Dict[str, Any]]:
    """Load existing results from JSONL output file."""
    if not output_file or not os.path.exists(output_file):
        return []

    try:
        return load_jsonl(output_file)
    except Exception:
        return []


def format_scores_summary(results: List[Dict[str, Any]]) -> None:
    """Print a summary of evaluation scores."""
    if not results:
        return

    # Calculate averages
    trajectory_scores = []
    completion_scores = []

    for result in results:
        if "trajectory_score" in result:
            trajectory_scores.append(result["trajectory_score"])
        if "completion_score" in result:
            completion_scores.append(result["completion_score"])

    colored_print("\n📊 Evaluation Summary:", Colors.BRIGHT_CYAN, bold=True)
    colored_print("=" * 50, Colors.CYAN)

    if trajectory_scores:
        avg_trajectory = sum(trajectory_scores) / len(trajectory_scores)
        colored_print(f"Average Trajectory Score: {avg_trajectory:.3f}", Colors.YELLOW)

    if completion_scores:
        avg_completion = sum(completion_scores) / len(completion_scores)
        colored_print(f"Average Completion Score: {avg_completion:.3f}", Colors.YELLOW)

    colored_print(f"Total Evaluations: {len(results)}", Colors.WHITE)

    # Score distribution
    if trajectory_scores:
        high_trajectory = sum(1 for s in trajectory_scores if s >= 0.8)
        medium_trajectory = sum(1 for s in trajectory_scores if 0.5 <= s < 0.8)
        low_trajectory = sum(1 for s in trajectory_scores if s < 0.5)

        colored_print(f"\nTrajectory Score Distribution:", Colors.CYAN)
        colored_print(f"  High (≥0.8): {high_trajectory}", Colors.GREEN)
        colored_print(f"  Medium (0.5-0.8): {medium_trajectory}", Colors.YELLOW)
        colored_print(f"  Low (<0.5): {low_trajectory}", Colors.RED)


def load_custom_prompts(prompt_file: str) -> Dict[str, str]:
    """Load custom prompts from JSON file."""
    try:
        with open(prompt_file, "r", encoding="utf-8") as f:
            prompts = json.load(f)

        if not isinstance(prompts, dict):
            raise ValueError("Prompt file must contain a JSON object")

        return prompts

    except Exception as e:
        colored_print(f"❌ Error loading prompts from {prompt_file}: {e}", Colors.RED)
        sys.exit(1)


def load_model_config(model_config_file: str) -> Dict[str, Any]:
    """Load model configuration from JSON file."""
    try:
        config_path = Path(model_config_file)
        if not config_path.exists():
            colored_print(
                f"❌ Model config file not found: {model_config_file}", Colors.RED
            )
            sys.exit(1)

        with open(config_path, "r", encoding="utf-8") as f:
            model_config = json.load(f)

        if not isinstance(model_config, dict):
            raise ValueError("Model config file must contain a JSON object")

        colored_print(
            f"✅ Loaded model configuration from {model_config_file}", Colors.GREEN
        )
        return model_config

    except Exception as e:
        colored_print(
            f"❌ Error loading model config from {model_config_file}: {e}", Colors.RED
        )
        sys.exit(1)


def judge_evaluation_file(args) -> None:
    """
    Judge an evaluation file using LLM judges.

    Args:
        args: Parsed command line arguments
    """
    input_file = args.input_file
    output_dir = getattr(args, "output_dir", None)
    ground_truth_file = getattr(args, "ground_truth", None)
    model = getattr(args, "model", "gpt-4o")
    model_config_file = getattr(args, "model_config", None)
    max_samples = getattr(args, "max_samples", None)
    trajectory_only = getattr(args, "trajectory_only", False)
    completion_only = getattr(args, "completion_only", False)
    verbose = getattr(args, "verbose", False)
    quiet = getattr(args, "quiet", False)
    prompt_file = getattr(args, "prompt_file", None)
    resume = getattr(args, "resume", False)

    # Set up logging based on verbosity
    if quiet:
        setup_colored_logging(level=logging.WARNING)
    elif verbose:
        setup_colored_logging(level=logging.DEBUG)
    else:
        setup_colored_logging(level=logging.INFO)

    colored_print(f"🔍 Loading evaluation data from {input_file}...", Colors.CYAN)

    # Load evaluation data
    evaluation_data = load_evaluation_data(input_file)
    total_records = len(evaluation_data)

    # Load ground truth data if provided
    ground_truth_map = {}
    if ground_truth_file:
        colored_print(
            f"📖 Loading ground truth data from {ground_truth_file}...", Colors.CYAN
        )
        ground_truth_map = load_ground_truth_data(ground_truth_file)
        colored_print(
            f"📖 Loaded {len(ground_truth_map)} ground truth records", Colors.CYAN
        )

    # Limit samples if requested
    if max_samples and max_samples < total_records:
        evaluation_data = evaluation_data[:max_samples]
        colored_print(
            f"📝 Evaluating {max_samples} out of {total_records} records", Colors.YELLOW
        )
    else:
        colored_print(f"📝 Evaluating {total_records} records", Colors.CYAN)

    # Load model configuration if provided
    model_config = {}
    final_model_name = model

    if model_config_file:
        colored_print(
            f"⚙️ Loading model configuration from {model_config_file}...", Colors.CYAN
        )
        model_config = load_model_config(model_config_file)

        # Determine final model name - prioritize model_config, then fall back to CLI arg
        final_model_name = model_config.get("model") or model

        if verbose:
            colored_print(f"   Model config: {model_config}", Colors.DIM)
            colored_print(
                f"   Using model: {final_model_name} (from {'config file' if model_config.get('model') else 'CLI argument'})",
                Colors.DIM,
            )

    # Load custom prompts if provided
    custom_prompts = {}
    if prompt_file:
        colored_print(f"📝 Loading custom prompts from {prompt_file}...", Colors.CYAN)
        custom_prompts = load_custom_prompts(prompt_file)

        # Validate prompt keys
        valid_keys = {"trajectory", "completion"}
        provided_keys = set(custom_prompts.keys())
        invalid_keys = provided_keys - valid_keys

        if invalid_keys:
            colored_print(
                f"⚠️ Warning: Unknown prompt keys ignored: {invalid_keys}", Colors.YELLOW
            )
            colored_print(f"   Valid keys are: {valid_keys}", Colors.DIM)

        if "trajectory" in custom_prompts:
            colored_print("   ✓ Custom trajectory prompt loaded", Colors.GREEN)
        if "completion" in custom_prompts:
            colored_print("   ✓ Custom completion prompt loaded", Colors.GREEN)

    # Initialize LLM judger
    colored_print(
        f"🤖 Initializing LLM judger with model: {final_model_name}", Colors.CYAN
    )

    if custom_prompts:
        judger = MultiAspectLLMJudger.with_custom_prompts(
            trajectory_prompt=custom_prompts.get("trajectory"),
            task_completion_prompt=custom_prompts.get("completion"),
            model=final_model_name,
            model_config=model_config if model_config else None,
        )
    else:
        judger = MultiAspectLLMJudger(
            model=final_model_name, model_config=model_config if model_config else None
        )

    # Determine output files
    output_files = get_output_files(
        output_dir, input_file, final_model_name, trajectory_only, completion_only
    )

    if output_dir:
        colored_print(f"📁 Output files:", Colors.CYAN)
        colored_print(f"   Combined: {output_files['combined']}", Colors.DIM)
        colored_print(f"   Trajectory: {output_files['trajectory']}", Colors.DIM)
        colored_print(f"   Completion: {output_files['completion']}", Colors.DIM)

    # Load existing results and filter out already processed tasks
    existing_results = []
    processed_task_ids = set()

    if resume and output_files["combined"]:
        colored_print(f"🔄 Checking for existing results...", Colors.CYAN)
        existing_results = load_existing_results(output_files["combined"])
        processed_task_ids = {
            r.get("task_id") for r in existing_results if r.get("task_id")
        }

        if processed_task_ids:
            colored_print(
                f"📋 Found {len(processed_task_ids)} already processed tasks",
                Colors.GREEN,
            )
            if verbose:
                colored_print(
                    f"   Processed task IDs: {list(processed_task_ids)[:5]}{'...' if len(processed_task_ids) > 5 else ''}",
                    Colors.DIM,
                )

    # Filter out already processed tasks upfront
    original_count = len(evaluation_data)
    if processed_task_ids:
        filtered_data = []
        for i, record in enumerate(evaluation_data):
            task_id = record.get("task_id", f"sample_{i + 1}")
            if task_id not in processed_task_ids:
                filtered_data.append(record)
        evaluation_data = filtered_data
        skipped_count = original_count - len(evaluation_data)
        if skipped_count > 0:
            colored_print(
                f"⏭️  Skipping {skipped_count} already processed tasks", Colors.YELLOW
            )

    # Process evaluations
    results = existing_results.copy()  # Start with existing results
    trajectory_results = []
    completion_results = []

    # Separate existing results by type for separate files
    for result in existing_results:
        if "trajectory_score" in result:
            trajectory_results.append(
                {
                    k: v
                    for k, v in result.items()
                    if not k.startswith("completion_")
                    or k in ["task_id", "task_name", "original_success"]
                }
            )
        if "completion_score" in result:
            completion_results.append(
                {
                    k: v
                    for k, v in result.items()
                    if not k.startswith("trajectory_")
                    or k in ["task_id", "task_name", "original_success"]
                }
            )

    logger.info(f"Starting evaluation of {len(evaluation_data)} records")

    for i, record in enumerate(evaluation_data, 1):
        task_id = record.get("task_id", f"sample_{i}")

        # Log start of evaluation
        logger.info(f"Starting evaluation for record {i}/{len(evaluation_data)}")
        start_time = time.time()

        task = record.get("task", {})
        execution_trajectory = record.get("conversation", [])
        final_response = record.get("final_response", "")

        # If final_response is empty, try to extract it from conversation
        if not final_response and execution_trajectory:
            final_response = extract_final_response(execution_trajectory)

        colored_print(
            f"\n🔄 [{i}/{len(evaluation_data)}] Evaluating: {task_id}", Colors.WHITE
        )

        if verbose:
            task_name = task.get("name", "Unknown Task")
            colored_print(f"   Task: {task_name}", Colors.DIM)
            colored_print(f"   Success: {record.get('success', 'Unknown')}", Colors.DIM)
            colored_print(
                f"   Tool calls: {len(record.get('tool_calls', []))}", Colors.DIM
            )

        result = {
            "task_id": task_id,
            "task_name": task.get("name", ""),
            "original_success": record.get("success", None),
        }

        # Get ground truth data if available
        ground_truth_data = ground_truth_map.get(task_id)
        ground_truth_response = None
        ground_truth_conversation = None

        if ground_truth_data:
            ground_truth_response = ground_truth_data.get("final_response", "")
            ground_truth_conversation = ground_truth_data.get("conversation", [])

            if verbose:
                colored_print(f"   ✓ Ground truth data found", Colors.GREEN)

        try:
            # Evaluate trajectory if requested
            if not completion_only:
                # Use ground truth conversation if available, otherwise use prediction conversation
                trajectory_to_evaluate = (
                    ground_truth_conversation
                    if ground_truth_conversation
                    else execution_trajectory
                )

                trajectory_result = judger.evaluate_trajectory(
                    task=task, execution_trajectory=trajectory_to_evaluate
                )

                result.update(
                    {
                        "trajectory_score": trajectory_result.overall_score,
                        "trajectory_scores": trajectory_result.scores.model_dump(),
                        "trajectory_comments": trajectory_result.comments,
                        "used_ground_truth_trajectory": bool(ground_truth_conversation),
                    }
                )

                if verbose:
                    colored_print(
                        f"   Trajectory Score: {trajectory_result.overall_score:.3f}",
                        Colors.GREEN,
                    )

            # Evaluate task completion if requested
            if not trajectory_only:
                # Use ground truth response if available, otherwise use prediction response
                response_to_evaluate = (
                    ground_truth_response if ground_truth_response else final_response
                )
                trajectory_for_context = (
                    ground_truth_conversation
                    if ground_truth_conversation
                    else execution_trajectory
                )

                completion_result = judger.evaluate_task_completion(
                    task=task,
                    final_response=response_to_evaluate,
                    execution_trajectory=trajectory_for_context,
                    ground_truth_answer=(
                        ground_truth_response
                        if ground_truth_response
                        and not ground_truth_response == response_to_evaluate
                        else None
                    ),
                )

                result.update(
                    {
                        "completion_score": completion_result.overall_score,
                        "completion_scores": completion_result.scores.model_dump(),
                        "completion_comments": completion_result.comments,
                        "used_ground_truth_response": bool(ground_truth_response),
                    }
                )

                if verbose:
                    colored_print(
                        f"   Completion Score: {completion_result.overall_score:.3f}",
                        Colors.BLUE,
                    )

            results.append(result)

            # Log completion with timing
            elapsed = time.time() - start_time
            logger.info(f"Record evaluation completed in {elapsed:.2f} seconds")
            logger.info(
                f"Successfully evaluated record {i}/{len(evaluation_data)}: {task_id}"
            )

            # Save to combined file
            if output_files["combined"]:
                save_result_to_jsonl(result, output_files["combined"])

            # Save to separate files
            if "trajectory_score" in result and output_files["trajectory"]:
                trajectory_result = {
                    k: v
                    for k, v in result.items()
                    if not k.startswith("completion_")
                    or k in ["task_id", "task_name", "original_success"]
                }
                trajectory_results.append(trajectory_result)
                save_result_to_jsonl(trajectory_result, output_files["trajectory"])

            if "completion_score" in result and output_files["completion"]:
                completion_result = {
                    k: v
                    for k, v in result.items()
                    if not k.startswith("trajectory_")
                    or k in ["task_id", "task_name", "original_success"]
                }
                completion_results.append(completion_result)
                save_result_to_jsonl(completion_result, output_files["completion"])

        except Exception as e:
            elapsed = time.time() - start_time
            colored_print(f"   ❌ Error evaluating {task_id}: {e}", Colors.RED)
            logger.error(
                f"Error evaluating record {i}/{len(evaluation_data)} after {elapsed:.2f} seconds: {str(e)}",
                exc_info=True,
            )
            result.update(
                {
                    "error": str(e),
                    "trajectory_score": 0.0 if not completion_only else None,
                    "completion_score": 0.0 if not trajectory_only else None,
                }
            )
            results.append(result)

            # Save error result
            if output_files["combined"]:
                save_result_to_jsonl(result, output_files["combined"])

            # Save error to separate files
            if output_files["trajectory"]:
                trajectory_results.append(result)
                save_result_to_jsonl(result, output_files["trajectory"])

            if output_files["completion"]:
                completion_results.append(result)
                save_result_to_jsonl(result, output_files["completion"])

    # Calculate summary statistics
    successful_evaluations = sum(1 for r in results if not r.get("error"))
    failed_evaluations = len(results) - successful_evaluations

    # Log completion summary
    logger.info(
        f"Evaluation complete. Successfully evaluated: {successful_evaluations}, Failed: {failed_evaluations}"
    )
    if output_files["combined"]:
        logger.info(f"Results saved to {output_files['combined']}")
        logger.info(f"Trajectory results saved to {output_files['trajectory']}")
        logger.info(f"Completion results saved to {output_files['completion']}")

    # Print summary
    format_scores_summary(results)

    # Print results summary if output files specified
    if output_files["combined"]:
        colored_print(f"\n📊 Results Summary:", Colors.CYAN)
        colored_print(f"   Combined results: {len(results)} records", Colors.WHITE)
        colored_print(
            f"   Trajectory results: {len(trajectory_results)} records", Colors.WHITE
        )
        colored_print(
            f"   Completion results: {len(completion_results)} records", Colors.WHITE
        )

        colored_print(f"✅ Results saved to {output_files['combined']}", Colors.GREEN)
        colored_print(
            f"✅ Trajectory results saved to {output_files['trajectory']}", Colors.GREEN
        )
        colored_print(
            f"✅ Completion results saved to {output_files['completion']}", Colors.GREEN
        )

    elif not verbose:
        colored_print(
            "\n💡 Use --output-dir to save detailed results to files", Colors.DIM
        )


def main(args):
    """Main entry point for the CLI."""
    # Set API key in environment if provided directly
    if hasattr(args, "api_key") and args.api_key:
        os.environ["OPENAI_API_KEY"] = args.api_key
        colored_print("✓ API key set from command line", Colors.GREEN)

    # Validate arguments
    if getattr(args, "trajectory_only", False) and getattr(
        args, "completion_only", False
    ):
        colored_print(
            "❌ Cannot specify both --trajectory-only and --completion-only", Colors.RED
        )
        sys.exit(1)

    if not os.path.exists(args.input_file):
        colored_print(f"❌ Input file not found: {args.input_file}", Colors.RED)
        sys.exit(1)

    # Validate ground truth file if provided
    if (
        hasattr(args, "ground_truth")
        and args.ground_truth
        and not os.path.exists(args.ground_truth)
    ):
        colored_print(
            f"❌ Ground truth file not found: {args.ground_truth}", Colors.RED
        )
        sys.exit(1)

    # Validate model config file if provided
    if (
        hasattr(args, "model_config")
        and args.model_config
        and not os.path.exists(args.model_config)
    ):
        colored_print(
            f"❌ Model config file not found: {args.model_config}", Colors.RED
        )
        sys.exit(1)

    # Print banner
    if not getattr(args, "quiet", False):
        colored_print(
            "🧠 LLM Judger - AI Agent Execution Evaluator",
            Colors.BRIGHT_CYAN,
            bold=True,
        )
        colored_print("=" * 50, Colors.CYAN)

    # Validate prompt file if provided
    if (
        hasattr(args, "prompt_file")
        and args.prompt_file
        and not os.path.exists(args.prompt_file)
    ):
        colored_print(f"❌ Prompt file not found: {args.prompt_file}", Colors.RED)
        sys.exit(1)

    # Run evaluation
    try:
        judge_evaluation_file(args)

        if not getattr(args, "quiet", False):
            colored_print(
                "\n✅ LLM judgment completed successfully!",
                Colors.BRIGHT_GREEN,
                bold=True,
            )

    except KeyboardInterrupt:
        colored_print("\n⚠️ Evaluation interrupted by user", Colors.YELLOW)
        sys.exit(1)
    except Exception as e:
        colored_print(f"\n❌ Evaluation failed: {e}", Colors.RED)
        if getattr(args, "verbose", False):
            logger.exception("Detailed error information:")
        sys.exit(1)


if __name__ == "__main__":
    # When run directly, this should not happen as the main CLI handles argument parsing
    print("Please use the main CLI: python -m mcpeval.cli.main llm-judge --help")
    sys.exit(1)
