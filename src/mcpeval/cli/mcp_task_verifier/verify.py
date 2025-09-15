#!/usr/bin/env python3
"""
Task Verifier CLI Tool

This module provides functionality for verifying tasks against an MCP server.
"""
import asyncio
import json
import os
import logging
import time
from pathlib import Path

from mcpeval.client.openai_client import OpenAIMCPClient
from mcpeval.synthesis.task_verifier import LLMTaskVerifier
from mcpeval.models.llms import OpenAIWrapper
from mcpeval.synthesis.utils import load_tasks_from_jsonl
from mcpeval.synthesis.task_generator import TaskGenerator
from mcpeval.synthesis.tools import ToolLibrary
from mcpeval.utils.cli import (
    load_prompt_from_file,
    print_task,
    print_tool_calls,
    handle_existing_file,
    generate_output_filename,
    save_tasks_to_jsonl,
    setup_colored_logging,
)
from mcpeval.utils.response_process import (
    process_conversation,
    process_final_response,
    process_tool_call_results,
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging using centralized setup
setup_colored_logging(level=logging.INFO)
logger = logging.getLogger(__name__)


async def verify_task(
    task,
    server_paths,
    server_args_list,
    server_envs=None,
    model="gpt-4o",
    model_config=None,
    api_key=None,
    system_message=None,
    max_turns=10,
):
    """Verify a task execution with LLMTaskVerifier.

    Args:
        task: The task to verify
        server_paths: List of server paths
        server_args_list: List of server arguments
        server_envs: List of environment variables for each server
        model: Model name to use
        api_key: OpenAI API key
        system_message: System message for the task
        max_turns: Maximum number of turns for task verification

    Returns:
        tuple: (success, task) where task is the updated Task object with verification results
    """
    logger.info(f"Starting verification for task: {task.name}")

    # Use model_config if provided, otherwise create default config
    if model_config is None:
        model_config = {
            "model": model,
            "temperature": 0.01,
            "max_tokens": 16384
        }
    
    # Initialize OpenAI LLM for the evaluator using the same pattern as TaskGenerator
    llm = OpenAIWrapper(
        api_key=api_key,
        model_config=model_config
    )

    # Initialize evaluator
    evaluator = LLMTaskVerifier(llm)

    # Initialize OpenAI MCP client using the model from config
    final_model = model_config.get("model", model)
    client = OpenAIMCPClient(model=final_model, api_key=api_key)
    logger.info("OpenAI MCP client created")

    try:
        # Connect to servers (always multi-server mode)
        logger.info(f"Connecting to {len(server_paths)} MCP server(s) for verification")

        # Connect to multiple servers
        await client.connect_to_multiple_servers(
            server_paths, server_args_list, server_envs
        )

        # Get aggregated tools from all servers
        all_tools = await client.get_all_tools()
        tools_data = all_tools
        logger.info(
            f"Retrieved {len(tools_data)} tools from {len(server_paths)} MCP server(s)"
        )

        # Build tool_name_to_session mapping
        tool_name_to_session = client.tool_name_to_session

        if not tools_data:
            logger.error("No valid tools found. Cannot verify task.")
            return False, None

        # Initialize task generator with the tools from the server using the same pattern
        task_generator = TaskGenerator(
            tool_library=ToolLibrary(tools=tools_data),
            model_config=model_config,
            api_key=api_key,
        )

        # Update the task tools with the actual tools from the server
        task.tools = tools_data

        # Print task information
        print_task(task)

        # Run the evaluation (multi-turn)
        logger.info("Running multi-turn evaluation...")

        # Set debug logging for task_verifier if DEBUG is true
        if os.getenv("DEBUG", "false").lower() == "true":
            logging.getLogger("mcpeval.synthesis.task_verifier").setLevel(logging.DEBUG)

        success, result = await evaluator.task_verification(
            task=task,
            tools=tools_data,
            tool_name_to_session=tool_name_to_session,
            max_turns=max_turns,  # Configurable max turns for complex tasks
            system_message=system_message,
        )

        # Check if the task verification was successful
        if not success:
            # Result is a reason for clarification
            logger.info(f"LLM requested clarification: {result}")
            updated_task = task_generator.updating_task_from_feedback(task, result)
            return False, updated_task
        else:
            # Result now contains tool_calls, final_response, and conversation
            try:
                # Get all the tool calls from the result
                tool_calls = result.get("tool_calls", [])
                logger.info(f"Got {len(tool_calls)} total tool calls across all turns")

                # Update the task's tool_calls with the actual tool calls from the result
                task.tool_calls = [
                    tc[0] if isinstance(tc, tuple) else tc for tc in tool_calls
                ]

                # Print detailed information about tool calls
                print_tool_calls(tool_calls)

                # Get final response directly from the result
                final_response = result.get("final_response", "")

                # Process final_response to ensure it's a string
                processed_final_response = process_final_response(final_response)

                if processed_final_response:
                    print(f"\n{'='*20} FINAL RESPONSE {'='*20}")
                    print(processed_final_response)
                    print(f"{'='*50}")

                # Process conversation to ensure content is a string and create proper Message objects
                conversation = process_conversation(result.get("conversation", []))

                # Process tool_call_results to ensure proper format
                processed_tool_call_results = process_tool_call_results(
                    result.get("tool_call_results")
                )

                # Update the task with the results
                task.final_response = processed_final_response
                task.conversation = conversation
                task.tool_call_results = processed_tool_call_results

                return True, task

            except Exception as e:
                logger.error(f"Error processing result: {e}")
                logger.info(f"Raw result: {result}")
                return False, None

    except Exception as e:
        logger.error(f"Error during execution: {e}", exc_info=True)
        return False, None
    finally:
        logger.info("Cleaning up resources")
        await client.cleanup()


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


async def verify_tasks(args):
    """Verify tasks from a JSONL file and save results."""
    # Model configuration - load this first
    model_config = {}

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
    
    # Load tasks from file
    all_tasks = load_tasks_from_jsonl(args.tasks_file)

    # Setup output files
    output_file = generate_output_filename(
        args.tasks_file, args.output, prefix="verified"
    )
    non_interactive = getattr(args, "non_interactive", False)
    output_file, _ = handle_existing_file(output_file, non_interactive=non_interactive)

    # Load already verified task IDs to skip duplicates
    verified_task_ids = set()
    if os.path.exists(output_file):
        try:
            existing_verified_tasks = load_tasks_from_jsonl(output_file)
            verified_task_ids = {
                task.id
                for task in existing_verified_tasks
                if hasattr(task, "id") and task.id
            }
        except Exception:
            pass

    # Filter out already verified tasks and limit number if requested
    tasks = [
        task
        for task in all_tasks
        if not (hasattr(task, "id") and task.id and task.id in verified_task_ids)
    ]

    # Log how many tasks were skipped
    skipped_count = len(all_tasks) - len(tasks)
    if skipped_count > 0:
        logger.info(f"Skipping {skipped_count} already verified tasks")

    num_tasks = getattr(args, "num_tasks", -1)
    if num_tasks > 0:
        tasks = tasks[:num_tasks]

    if not tasks:
        logger.info("No tasks to verify")
        return

    # Ensure output directory exists
    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)

    # Track results
    verified_count = 0
    unverified_count = 0
    error_count = 0

    # Create unverified tasks file
    base_name, ext = os.path.splitext(output_file)
    unverified_file = f"{base_name}_unverified{ext}"
    unverified_file, _ = handle_existing_file(
        unverified_file, non_interactive=non_interactive
    )

    # Get server parameters and system message
    system_message = load_prompt_from_file(getattr(args, "prompt_file", None))

    # Convert single server to multi-server format if needed
    if hasattr(args, "server_paths") and args.server_paths:
        # Already in multi-server format
        server_paths = args.server_paths
        server_args_list = args.server_args_list
        server_envs = getattr(args, "server_env_list", None)
    else:
        # Convert single server to multi-server format
        server_paths = [args.server]
        server_args_list = [getattr(args, "server_args", [])]
        server_envs = [getattr(args, "server_env", None)]

    logger.info(f"Starting verification of {len(tasks)} tasks")

    # Process tasks
    for i, task in enumerate(tasks):
        task_number = i + 1
        try:
            # Log start of verification
            logger.info(f"Starting verification for task {task_number}/{len(tasks)}")
            start_time = time.time()

            # Always use multi-server approach
            success, verified_task = await verify_task(
                task=task,
                server_paths=server_paths,
                server_args_list=server_args_list,
                server_envs=server_envs,
                model=final_model_name,
                model_config=model_config,
                api_key=getattr(args, "api_key", None),
                system_message=system_message,
                max_turns=getattr(args, "max_turns", 10),
            )

            # Log completion
            elapsed = time.time() - start_time
            logger.info(f"Task verification completed in {elapsed:.2f} seconds")

            if success and verified_task:
                save_tasks_to_jsonl(verified_task, output_file, append=True)
                verified_count += 1
                logger.info(
                    f"Successfully verified task {task_number}/{len(tasks)}: {task.name}"
                )
            else:
                if verified_task:
                    save_tasks_to_jsonl(verified_task, unverified_file, append=True)
                    unverified_count += 1
                    logger.info(
                        f"Task {task_number}/{len(tasks)} failed verification: {task.name}"
                    )
                else:
                    error_count += 1
                    logger.error(f"Task {task_number}/{len(tasks)} error: {task.name}")

            await asyncio.sleep(1)  # Rate limiting

        except Exception as e:
            error_count += 1
            elapsed = time.time() - start_time
            logger.error(
                f"Error processing task {task_number}/{len(tasks)} after {elapsed:.2f} seconds: {str(e)}",
                exc_info=True,
            )
            continue

    # Summary
    logger.info(
        f"Task verification complete. Successfully verified: {verified_count}, Failed verification: {unverified_count}, Errors: {error_count}"
    )
    logger.info(f"Verified tasks saved to {output_file}")
    if unverified_count > 0:
        logger.info(f"Unverified tasks saved to {unverified_file}")


def main(args):
    """Main entry point for the CLI."""
    asyncio.run(verify_tasks(args))


def main_revalidate(args):
    """Main entry point for the revalidation CLI."""
    asyncio.run(revalidate_tasks(args))


if __name__ == "__main__":
    # When run directly, this should not happen as the main CLI handles argument parsing
    print("Please use the main CLI: python -m mcpeval.cli.main verify-tasks --help")
    import sys

    sys.exit(1)
