#!/usr/bin/env python3
"""
Model Evaluator Module

This module provides functionality for evaluating LLM models on MCP tasks.
It enables connecting to an MCP server, executing tasks, and reporting results.
"""
import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import time

from mcpeval.eval.task_executor import LLMTaskExecutor
from mcpeval.commons.types import Task
from mcpeval.synthesis.utils import load_tasks_from_jsonl
from mcpeval.client.openai_client import OpenAIMCPClient
from mcpeval.utils.cli import load_prompt_from_file, load_jsonl, setup_colored_logging
from mcpeval.models.llms import OpenAIWrapper
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging using centralized setup
setup_colored_logging(level=logging.INFO)
logger = logging.getLogger(__name__)


def save_evaluation_results_to_jsonl(
    results: List[Dict[str, Any]], output_file: str, append: bool = False
) -> None:
    """Save evaluation results to a JSONL file.

    Args:
        results: List of evaluation result dictionaries
        output_file: Path to output JSONL file
        append: Whether to append to the file (True) or overwrite (False)
    """
    mode = "a" if append else "w"

    # Convert to list if single result
    result_list = results if isinstance(results, list) else [results]

    with open(output_file, mode) as f:
        for result in result_list:
            # Write as a single line JSON
            f.write(json.dumps(result) + "\n")

    logger.info(f"Saved {len(result_list)} evaluation results to {output_file}")


def load_evaluation_results_from_jsonl(file_path: str) -> List[Dict[str, Any]]:
    """Load evaluation results from a JSONL file.

    Args:
        file_path: Path to the JSONL file

    Returns:
        List of evaluation result dictionaries
    """
    try:
        return load_jsonl(file_path)
    except Exception as e:
        logger.warning(f"Could not load existing results from {file_path}: {e}")
        return []


async def evaluate_performance(
    tasks: List[Task],
    model_name: str,
    model_config: Dict[str, Any],
    server_paths: List[str],
    server_args_list: List[List[str]],
    server_envs: Optional[List[Optional[Dict[str, str]]]] = None,
    output_file: Optional[str] = None,
    max_turns: int = 30,
    prompt_file: Optional[str] = None,
):
    """
    Evaluate model performance on tasks using OpenAI client with multiple servers.

    Args:
        tasks: List of Task objects
        model_name: Name of the model being evaluated
        model_config: Model configuration
        server_paths: List of server paths
        server_args_list: List of server arguments
        server_envs: List of environment variables for each server
        output_file: Path to output file
        max_turns: Maximum number of turns for task execution
        prompt_file: Optional path to JSON file containing system message
    """
    try:
        # Load system message from prompt file if provided
        loaded_system_message = (
            load_prompt_from_file(prompt_file) if prompt_file else None
        )

        if loaded_system_message:
            final_system_message = loaded_system_message
            logger.info(f"Using system message from prompt file: {prompt_file}")
        else:
            final_system_message = (
                "You are a helpful assistant completing tasks using tools."
            )
            logger.info("Using default system message")

        # First, check if output file exists and load already tested task IDs
        already_tested_task_ids = set()
        existing_results = []
        if output_file and os.path.exists(output_file):
            existing_results = load_evaluation_results_from_jsonl(output_file)
            already_tested_task_ids = {
                result.get("task_id")
                for result in existing_results
                if result.get("task_id")
            }
            logger.info(
                f"Found {len(already_tested_task_ids)} already tested tasks in {output_file}"
            )

        # Create OpenAI client
        logger.info(
            f"Initializing OpenAI client for model: {model_name} with config: {model_config}"
        )

        api_key = model_config.get("api_key") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key is required")

        base_url = model_config.get("base_url")
        client_kwargs = {
            "model": model_config.get("model") or model_name,
            "system_prompt": final_system_message,
            "api_key": api_key,
        }
        if base_url:
            client_kwargs["base_url"] = base_url
        client = OpenAIMCPClient(**client_kwargs)
        logger.info("OpenAI MCP client created")

        # Connect to server(s)
        await client.connect_to_multiple_servers(
            server_paths, server_args_list, server_envs or []
        )
        logger.info(f"Connected to {len(server_paths)} MCP servers")

        results = existing_results.copy() if existing_results else []

        logger.info(f"Starting evaluation of {len(tasks)} tasks")

        for i, task in enumerate(tasks):
            task_number = i + 1
            # Skip tasks that have already been tested
            if task.id in already_tested_task_ids:
                logger.info(
                    f"Skipping task {task_number}/{len(tasks)}: {task.id} (already tested)"
                )
                continue

            # Log start of evaluation
            logger.info(f"Starting evaluation for task {task_number}/{len(tasks)}")
            start_time = time.time()

            try:
                # Use the existing OpenAIWrapper from llms.py with same config as client
                wrapped_llm = OpenAIWrapper(model=model_name, model_config=model_config)
                executor = LLMTaskExecutor(wrapped_llm)

                # Create tool_name_to_session mapping
                tool_name_to_session = client.tool_name_to_session

                success, result = await executor.execute_task(
                    task=task,
                    tool_name_to_session=tool_name_to_session,
                    max_turns=max_turns,
                    system_message=final_system_message,
                )

                # Convert ToolCall objects to dictionaries for JSON serialization
                tool_calls = []
                for tc in result.get("tool_calls", []):
                    if hasattr(tc, "model_dump"):
                        tool_calls.append(tc.model_dump())
                    elif hasattr(tc, "to_dict"):
                        tool_calls.append(tc.to_dict())
                    elif hasattr(tc, "__dict__"):
                        tool_calls.append(tc.__dict__)
                    else:
                        try:
                            tool_call_dict = {}
                            if hasattr(tc, "tool_name"):
                                tool_call_dict["tool_name"] = tc.tool_name
                            if hasattr(tc, "tool_parameters"):
                                tool_call_dict["tool_parameters"] = tc.tool_parameters
                            tool_calls.append(tool_call_dict)
                        except Exception as e:
                            logger.warning(f"Could not convert tool call to dict: {e}")
                            tool_calls.append({"str_representation": str(tc)})

                conversation = []
                for msg in result.get("conversation", []):
                    if isinstance(msg, dict):
                        conversation.append(dict(msg))
                    elif hasattr(msg, "model_dump"):
                        conversation.append(msg.model_dump())
                    elif hasattr(msg, "to_dict"):
                        conversation.append(msg.to_dict())
                    elif hasattr(msg, "__dict__"):
                        conversation.append(msg.__dict__)
                    else:
                        conversation.append({"str_representation": str(msg)})

                # Create result object
                evaluation_result = {
                    "task_id": task.id,
                    "success": success,
                    "tool_calls": tool_calls,
                    "final_response": result.get("final_response", ""),
                    "conversation": conversation,
                    "task": {
                        "id": task.id,
                        "name": task.name,
                        "description": task.description,
                        "goal": task.goal,
                    },
                    "model": model_name,
                    "client_type": "openai",
                }

                results.append(evaluation_result)

                # Log completion with timing
                elapsed = time.time() - start_time
                logger.info(f"Task evaluation completed in {elapsed:.2f} seconds")

                # Append result to file
                if output_file:
                    try:
                        save_evaluation_results_to_jsonl(
                            [evaluation_result], output_file, append=True
                        )
                    except Exception as save_error:
                        logger.error(f"Error saving result: {save_error}")

                logger.info(
                    f"Successfully completed task {task_number}/{len(tasks)}: {task.name}"
                )
            except Exception as task_error:
                elapsed = time.time() - start_time
                logger.error(
                    f"Error executing task {task_number}/{len(tasks)} after {elapsed:.2f} seconds: {str(task_error)}",
                    exc_info=True,
                )

                # Check if this is an API key related error
                error_message = str(task_error)
                if "OPENAI_API_KEY" in error_message or "api" in error_message.lower():
                    logger.error(
                        "This appears to be an API key related error. Please ensure your OpenAI API key is properly set (OPENAI_API_KEY)."
                    )

                # Try to capture any partial execution data if the executor was created
                partial_tool_calls = []
                partial_conversation = []
                try:
                    if "executor" in locals():
                        # Try to get any partial results from the executor
                        # This is best effort - if it fails, we'll just use empty lists
                        pass
                except:
                    pass

                error_result = {
                    "task_id": task.id,
                    "success": False,
                    "error": str(task_error),
                    "tool_calls": partial_tool_calls,  # Include any partial tool calls
                    "final_response": f"Error occurred during task execution: {task_error}",
                    "conversation": partial_conversation,  # Include any partial conversation
                    "task": {
                        "id": task.id,
                        "name": task.name,
                        "description": task.description,
                        "goal": task.goal,
                    },
                    "model": model_name,
                    "client_type": "openai",
                }
                results.append(error_result)

                # Append error result to file
                if output_file:
                    try:
                        save_evaluation_results_to_jsonl(
                            [error_result], output_file, append=True
                        )
                    except Exception as save_error:
                        logger.error(f"Error saving result: {save_error}")

        # Compute overall statistics
        successful_tasks = sum(1 for r in results if r.get("success", False))
        failed_tasks = len(results) - successful_tasks
        logger.info(
            f"Task evaluation complete. Successfully completed: {successful_tasks}, Failed: {failed_tasks}"
        )
        logger.info(
            f"Overall success rate: {successful_tasks}/{len(results)} ({successful_tasks/len(results)*100:.2f}%)"
        )
        if output_file:
            logger.info(f"Results saved to {output_file}")

        # Cleanup
        await client.cleanup()
        logger.info("Client resources cleaned up")

        return results
    except Exception as e:
        logger.exception(f"Error in evaluate_performance: {e}")
        raise


async def run_evaluation(args):
    """
    Run the evaluation process.

    Args:
        args: Command line arguments
    """
    try:
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(args.output)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Model configuration
        model_config = {}

        # Load model configuration from file if provided
        if hasattr(args, "model_config") and args.model_config:
            try:
                config_path = Path(args.model_config)
                if not config_path.exists():
                    logger.error(f"Model config file not found: {args.model_config}")
                    return False

                with open(config_path, "r") as f:
                    model_config = json.load(f)

                logger.info(f"Loaded model configuration from {args.model_config}")
            except Exception as e:
                logger.error(
                    f"Error loading model config file {args.model_config}: {e}"
                )
                return False

        logger.info(f"Model config: {model_config}")

        # Determine final model name - prioritize model_config, then fall back to CLI arg
        final_model_name = model_config.get("model") or args.model
        logger.info(
            f"Using model: {final_model_name} (from {'config file' if model_config.get('model') else 'CLI argument'})"
        )

        # Check for required OpenAI API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            error_msg = (
                "❌ OpenAI API key environment variable is required but not set.\n"
                "Please set your OpenAI API key using:\n"
                "  export OPENAI_API_KEY='your-api-key-here'"
            )
            logger.error(error_msg)
            print(error_msg)
            # Exit early - do not proceed with evaluation
            return False

        # Load tasks
        tasks = load_tasks_from_jsonl(args.tasks_file)
        logger.info(f"Loaded {len(tasks)} tasks from {args.tasks_file}")

        if not tasks:
            logger.error(f"No tasks loaded from {args.tasks_file}")
            return False

        # Limit number of tasks if specified
        if args.num_tasks > 0:
            tasks = tasks[: args.num_tasks]
            logger.info(f"Limiting evaluation to first {args.num_tasks} tasks")

        # If force_rerun is specified, rename the existing output file as a backup
        if (
            hasattr(args, "force_rerun")
            and args.force_rerun
            and os.path.exists(args.output)
        ):
            backup_file = f"{args.output}.bak.{int(time.time())}"
            os.rename(args.output, backup_file)
            logger.info(
                f"Renamed existing output file to {backup_file} for force rerun"
            )

        # Evaluate performance
        # Convert single server to multi-server format if needed
        if hasattr(args, "server_paths") and args.server_paths:
            # Already in multi-server format
            server_paths = args.server_paths
            server_args_list = args.server_args_list
            server_envs = getattr(args, "server_envs", None)
        else:
            # Convert single server to multi-server format
            server_paths = [args.server]
            server_args_list = [getattr(args, "server_args", [])]
            server_envs = [getattr(args, "server_env", None)]

        results = await evaluate_performance(
            tasks=tasks,
            model_name=final_model_name,
            model_config=model_config,
            server_paths=server_paths,
            server_args_list=server_args_list,
            server_envs=server_envs,
            output_file=args.output,
            max_turns=args.max_turns if hasattr(args, "max_turns") else 3,
            prompt_file=(
                args.prompt_file
                if hasattr(args, "prompt_file") and args.prompt_file
                else None
            ),
        )

        logger.info(f"Evaluation complete. Results saved to {args.output}")

        # Print summary statistics
        successful_tasks = sum(1 for r in results if r.get("success", False))
        total_tasks = len(results)
        success_rate = successful_tasks / total_tasks * 100 if total_tasks > 0 else 0

        # Color utilities (simple inline version)
        GREEN = "\033[92m"
        BLUE = "\033[94m"
        YELLOW = "\033[93m"
        CYAN = "\033[96m"
        BOLD = "\033[1m"
        RESET = "\033[0m"

        if sys.stdout.isatty():
            print(f"\n{CYAN}{BOLD}📊 Evaluation Summary:{RESET}")
            print(f"{CYAN}{'─' * 50}{RESET}")
            print(f"{BLUE}Model:{RESET} {BOLD}{final_model_name}{RESET}")
            print(f"{BLUE}Client Type:{RESET} {BOLD}openai{RESET}")
            print(f"{BLUE}Tasks evaluated:{RESET} {BOLD}{total_tasks}{RESET}")
            print(
                f"{GREEN}Tasks completed successfully:{RESET} {BOLD}{successful_tasks}{RESET}"
            )

            # Color-code success rate
            if success_rate >= 80:
                rate_color = GREEN
            elif success_rate >= 60:
                rate_color = YELLOW
            else:
                rate_color = "\033[91m"  # Red

            print(
                f"{BLUE}Success rate:{RESET} {rate_color}{BOLD}{success_rate:.2f}%{RESET}"
            )
            print(f"{BLUE}Results saved to:{RESET} {BOLD}{args.output}{RESET}")
        else:
            print(f"\nEvaluation Summary:")
            print(f"-------------------")
            print(f"Model: {final_model_name}")
            print(f"Client Type: openai")
            print(f"Tasks evaluated: {total_tasks}")
            print(f"Tasks completed successfully: {successful_tasks}")
            print(f"Success rate: {success_rate:.2f}%")
            print(f"Results saved to: {args.output}")

        return True

    except Exception as e:
        logger.exception(f"Error in run_evaluation: {e}")
        if sys.stdout.isatty():
            RED = "\033[91m"
            BOLD = "\033[1m"
            RESET = "\033[0m"
            print(f"{RED}{BOLD}❌ Evaluation failed: {e}{RESET}")
        else:
            print(f"Evaluation failed: {e}")
        return False


def main(args):
    """
    Main entry point for the model evaluator.

    Args:
        args: Command line arguments
    """
    try:
        # Run the evaluation asynchronously
        success = asyncio.run(run_evaluation(args))

        # Only show success message if evaluation actually completed
        if not success:
            # run_evaluation already printed the appropriate error message
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Evaluation interrupted by user")
        if sys.stdout.isatty():
            YELLOW = "\033[93m"
            BOLD = "\033[1m"
            RESET = "\033[0m"
            print(f"\n{YELLOW}{BOLD}⚠️  Evaluation interrupted by user{RESET}")
        else:
            print("Evaluation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Error in model evaluator main: {e}")
        if sys.stdout.isatty():
            RED = "\033[91m"
            BOLD = "\033[1m"
            RESET = "\033[0m"
            print(f"{RED}{BOLD}❌ Evaluation failed: {e}{RESET}")
        else:
            print(f"Evaluation failed: {e}")
        sys.exit(1)
