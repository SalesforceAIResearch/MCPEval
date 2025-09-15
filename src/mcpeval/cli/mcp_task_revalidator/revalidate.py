#!/usr/bin/env python3
"""
Task Revalidator CLI Tool

This module provides functionality for revalidating task descriptions based on actual tool conversations.
It takes verified tasks with conversation history and updates their descriptions to better reflect
what actually happened during task execution.
"""
import asyncio
import json
import os
import logging
import time
from pathlib import Path

from mcpeval.synthesis.task_verifier import LLMTaskVerifier
from mcpeval.models.llms import OpenAIWrapper
from mcpeval.synthesis.utils import load_tasks_from_jsonl
from mcpeval.utils.cli import (
    handle_existing_file,
    generate_output_filename,
    save_tasks_to_jsonl,
    setup_colored_logging,
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging using centralized setup
setup_colored_logging(level=logging.INFO)
logger = logging.getLogger(__name__)


async def revalidate_tasks(args):
    """Revalidate task descriptions based on their actual tool conversations."""
    # Model configuration - load this first
    model_config = {}
    
    # Load custom prompt if provided
    custom_prompts = None
    if hasattr(args, "prompt_file") and args.prompt_file:
        try:
            prompt_path = Path(args.prompt_file)
            if not prompt_path.exists():
                logger.error(f"Prompt file not found: {args.prompt_file}")
                return
            
            with open(prompt_path, "r") as f:
                custom_prompts = json.load(f)
            
            logger.info(f"Loaded custom prompts from {args.prompt_file}")
        except Exception as e:
            logger.error(f"Error loading prompt file: {e}")
            return

    # Load model configuration from file if provided
    if hasattr(args, "model_config") and args.model_config:
        try:
            config_path = Path(args.model_config)
            if not config_path.exists():
                logger.error(f"Model config file not found: {args.model_config}")
                return

            with open(config_path, "r") as f:
                model_config = json.load(f)

            logger.info(f"Loaded model configuration from {args.model_config}")
        except Exception as e:
            logger.error(f"Error loading model config file {args.model_config}: {e}")
            return
    
    # Determine final model name - prioritize model_config, then fall back to CLI arg
    final_model_name = model_config.get("model") if model_config else args.model
    logger.info(
        f"Using model: {final_model_name} (from {'config file' if model_config.get('model') else 'CLI argument'})"
    )
    
    # Load tasks from verified file
    all_tasks = load_tasks_from_jsonl(args.verified_tasks_file)

    # Filter tasks that have conversation/tool_calls data
    tasks_with_conversations = [
        task for task in all_tasks 
        if hasattr(task, 'conversation') and task.conversation and 
           hasattr(task, 'tool_calls') and task.tool_calls
    ]

    if not tasks_with_conversations:
        logger.error("No tasks with conversation and tool_calls data found. Cannot revalidate.")
        return

    logger.info(f"Found {len(tasks_with_conversations)} tasks with conversation data out of {len(all_tasks)} total tasks")

    # Setup output files
    output_file = generate_output_filename(
        args.verified_tasks_file, args.output, prefix="revalidated"
    )
    non_interactive = getattr(args, "non_interactive", False)
    # Determine default action from CLI if provided
    default_action = getattr(args, "on_existing_file", "timestamp")
    output_file, append_mode = handle_existing_file(
        output_file,
        non_interactive=non_interactive,
        default_action=default_action,
    )

    # Limit number if requested
    num_tasks = getattr(args, "num_tasks", -1)
    if num_tasks > 0:
        tasks_with_conversations = tasks_with_conversations[:num_tasks]

    # Ensure output directory exists
    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)

    # Initialize LLM for revalidation
    if model_config is None:
        model_config = {
            "model": final_model_name,
            "temperature": 0.01,
            "max_tokens": 16384
        }
    
    llm = OpenAIWrapper(
        api_key=getattr(args, "api_key", None),
        model_config=model_config
    )

    # Initialize evaluator
    evaluator = LLMTaskVerifier(llm)

    # Track results
    revalidated_count = 0
    error_count = 0

    # If appending, load existing IDs to avoid duplicates
    existing_ids = set()
    if append_mode and os.path.exists(output_file):
        try:
            existing_tasks = load_tasks_from_jsonl(output_file)
            existing_ids = {t.id for t in existing_tasks if hasattr(t, "id") and t.id}
            logger.info(f"Found {len(existing_ids)} existing revalidated tasks to skip")
        except Exception:
            existing_ids = set()

    # Filter out already revalidated tasks when appending
    if append_mode and existing_ids:
        original_count = len(tasks_with_conversations)
        tasks_with_conversations = [
            task for task in tasks_with_conversations 
            if not (hasattr(task, "id") and task.id and task.id in existing_ids)
        ]
        skipped_count = original_count - len(tasks_with_conversations)
        if skipped_count > 0:
            logger.info(f"Skipping {skipped_count} already revalidated tasks")

    if not tasks_with_conversations:
        logger.info("No tasks to revalidate (all tasks already processed)")
        return

    logger.info(f"Starting revalidation of {len(tasks_with_conversations)} tasks")

    # Process tasks
    for i, task in enumerate(tasks_with_conversations):
        task_number = i + 1
        try:
            # Log start of revalidation
            logger.info(f"Starting revalidation for task {task_number}/{len(tasks_with_conversations)}: {task.name}")
            start_time = time.time()

            # Revalidate the task using LLMTaskVerifier
            revalidated_task = evaluator.revalidate_task_description(
                task=task,
                tools=task.tools,
                conversation=task.conversation,
                tool_calls=task.tool_calls,
                tool_call_results=task.tool_call_results,
                custom_prompts=custom_prompts,
            )

            # Log completion
            elapsed = time.time() - start_time
            logger.info(f"Task revalidation completed in {elapsed:.2f} seconds")

            # Log differences if any
            if revalidated_task.description != task.description:
                logger.info(f"Updated description for '{task.name}':")
                logger.info(f"  OLD DESCRIPTION: {task.description}")
                logger.info(f"  NEW DESCRIPTION: {revalidated_task.description}")

            if revalidated_task.goal != task.goal:
                logger.info(f"Updated goal for '{task.name}':")
                logger.info(f"  OLD GOAL: {task.goal}")
                logger.info(f"  NEW GOAL: {revalidated_task.goal}")

            # Save the revalidated task
            save_tasks_to_jsonl(revalidated_task, output_file, append=True)
            revalidated_count += 1
            logger.info(f"Successfully revalidated task {task_number}/{len(tasks_with_conversations)}: {task.name}")

            await asyncio.sleep(0.5)  # Rate limiting

        except Exception as e:
            error_count += 1
            elapsed = time.time() - start_time
            logger.error(
                f"Error revalidating task {task_number}/{len(tasks_with_conversations)} after {elapsed:.2f} seconds: {str(e)}",
                exc_info=True,
            )
            continue

    # Summary
    logger.info(
        f"Task revalidation complete. Successfully revalidated: {revalidated_count}, Errors: {error_count}"
    )
    logger.info(f"Revalidated tasks saved to {output_file}")


def main(args):
    """Main entry point for the CLI."""
    asyncio.run(revalidate_tasks(args))


if __name__ == "__main__":
    # When run directly, this should not happen as the main CLI handles argument parsing
    print("Please use the main CLI: python -m mcpeval.cli.main revalidate-tasks --help")
    import sys

    sys.exit(1)
