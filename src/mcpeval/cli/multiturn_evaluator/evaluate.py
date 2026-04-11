#!/usr/bin/env python3
"""
Multi-Turn Evaluator CLI Module

Evaluates multi-turn conversation results using an LLM judge,
scoring conversations across multiple quality dimensions.
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv

from mcpeval.eval.multiturn_evaluator import MultiTurnEvaluator
from mcpeval.models.llms import OpenAIWrapper
from mcpeval.utils.cli import setup_colored_logging

load_dotenv()
setup_colored_logging(level=logging.INFO)
logger = logging.getLogger(__name__)


def _load_conversation_results(file_path: str) -> List[Dict[str, Any]]:
    """Load conversation results from a JSONL file."""
    results = []
    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            # Skip error entries
            if "error" in data and "turns" not in data:
                logger.warning(
                    f"Skipping errored scenario: {data.get('scenario_name', 'unknown')}"
                )
                continue
            results.append(data)
    return results


def main(args):
    """Main entry point for multi-turn evaluation CLI."""
    try:
        # Load model config
        model_config = {}
        if hasattr(args, "model_config") and args.model_config:
            config_path = Path(args.model_config)
            if not config_path.exists():
                logger.error(f"Model config file not found: {args.model_config}")
                sys.exit(1)
            with open(config_path, "r") as f:
                model_config = json.load(f)

        # Create output directory
        output_dir = os.path.dirname(args.output)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Load conversation results
        results = _load_conversation_results(args.input)
        if not results:
            logger.error(f"No conversation results loaded from {args.input}")
            sys.exit(1)

        logger.info(f"Loaded {len(results)} conversation results from {args.input}")

        # Limit if specified
        if hasattr(args, "num_samples") and args.num_samples and args.num_samples > 0:
            results = results[: args.num_samples]
            logger.info(f"Limiting evaluation to {len(results)} samples")

        # Check for already evaluated scenarios (resume support)
        already_evaluated = set()
        if hasattr(args, "resume") and args.resume and os.path.exists(args.output):
            with open(args.output, "r") as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        already_evaluated.add(data.get("scenario_id"))
            logger.info(f"Found {len(already_evaluated)} already evaluated scenarios")
            results = [
                r for r in results if r.get("scenario_id") not in already_evaluated
            ]

        # Create judge LLM
        judge_llm = OpenAIWrapper(model_config=model_config)
        evaluator = MultiTurnEvaluator(llm=judge_llm)

        # Evaluate conversations
        logger.info(f"Starting evaluation of {len(results)} conversations")
        batch_result = evaluator.evaluate_batch(results)

        # Save individual evaluations to JSONL
        mode = "a" if (hasattr(args, "resume") and args.resume) else "w"
        with open(args.output, mode) as f:
            for eval_result in batch_result["evaluations"]:
                f.write(json.dumps(eval_result) + "\n")

        # Save summary
        summary_path = args.output.replace(".jsonl", "_summary.json")
        with open(summary_path, "w") as f:
            json.dump(batch_result["summary"], f, indent=2)

        # Print summary
        summary = batch_result["summary"]
        print(f"\n{'='*60}")
        print("Multi-Turn Evaluation Summary")
        print(f"{'='*60}")
        print(f"Total conversations: {summary.get('total_conversations', 0)}")
        print(f"Successful evaluations: {summary.get('successful_evaluations', 0)}")
        print(f"Failed evaluations: {summary.get('failed_evaluations', 0)}")

        if summary.get("successful_evaluations", 0) > 0:
            print(f"\nAverage Scores:")
            print(
                f"  Clarification Handling: {summary.get('avg_clarification_handling', 'N/A')}"
            )
            print(
                f"  Context Maintenance:    {summary.get('avg_context_maintenance', 'N/A')}"
            )
            print(
                f"  Tool Usage Efficiency:  {summary.get('avg_tool_usage_efficiency', 'N/A')}"
            )
            print(
                f"  Goal Achievement:       {summary.get('avg_goal_achievement', 'N/A')}"
            )
            print(
                f"  Response Quality:       {summary.get('avg_response_quality', 'N/A')}"
            )
            print(
                f"  Overall Score:          {summary.get('avg_overall_score', 'N/A')}"
            )

        print(f"\nResults saved to: {args.output}")
        print(f"Summary saved to: {summary_path}")

    except KeyboardInterrupt:
        logger.info("Evaluation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Multi-turn evaluation failed: {e}")
        sys.exit(1)
