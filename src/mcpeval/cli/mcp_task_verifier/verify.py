#!/usr/bin/env python3
"""
Task Verifier CLI Tool

This module provides functionality for verifying tasks against an MCP server.
"""
import asyncio
import os
import logging
import time

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

    # Initialize OpenAI LLM for the evaluator
    llm = OpenAIWrapper(model=model, api_key=api_key)

    # Initialize evaluator
    evaluator = LLMTaskVerifier(llm)

    # Initialize OpenAI MCP client
    client = OpenAIMCPClient(model=model, api_key=api_key)
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

        # Initialize task generator with the tools from the server
        task_generator = TaskGenerator(
            tool_library=ToolLibrary(tools=tools_data),
            model_provider="openai",
            model_name=model,
            max_tokens=4000,
            model_temperature=0.2,
            top_p=0.95,
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
            temperature=0.2,
            max_tokens=1000,
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


async def verify_tasks(args):
    """Verify tasks from a JSONL file and save results."""
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
                model=args.model,
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


if __name__ == "__main__":
    # When run directly, this should not happen as the main CLI handles argument parsing
    print("Please use the main CLI: python -m mcpeval.cli.main verify-tasks --help")
    import sys

    sys.exit(1)
