#!/usr/bin/env python3
"""
Task Generator CLI Tool

This module provides functionality for connecting to MCP servers and generating tasks.
"""
import asyncio
import os
import sys
import logging
import time
import json
from pathlib import Path

from mcpeval.client.openai_client import OpenAIMCPClient
from mcpeval.synthesis.task_generator import TaskGenerator
from mcpeval.commons.types import ToolLibrary
from mcpeval.utils.cli import print_task, setup_colored_logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging using centralized setup
setup_colored_logging(level=logging.INFO)
logger = logging.getLogger(__name__)


async def generate_tasks(args):
    """Generate tasks from MCP server(s)."""
    # Get API key if provided
    api_key = getattr(args, "api_key", None)

    # Load custom prompt messages if provided
    system_message = None
    user_message = None
    if hasattr(args, "prompt_file") and args.prompt_file:
        try:
            with open(args.prompt_file, "r", encoding="utf-8") as f:
                prompt_data = json.load(f)
            system_message = prompt_data.get("system")
            user_message = prompt_data.get("user")
            logger.info(f"Loaded custom prompts from {args.prompt_file}")
            if system_message:
                logger.info(f"System message: {system_message[:100]}...")
            if user_message:
                logger.info(f"User message: {user_message[:100]}...")
        except FileNotFoundError:
            logger.error(f"Prompt file not found: {args.prompt_file}")
            return
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in prompt file {args.prompt_file}: {e}")
            return
        except Exception as e:
            logger.error(f"Error reading prompt file {args.prompt_file}: {e}")
            return

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
    else:
        # Fallback to CLI arguments if no config file provided
        model_config = {
            "model": args.model,
            "temperature": args.temperature,
            "max_tokens": args.max_tokens,
            "top_p": args.top_p,
        }

    logger.info(f"Model config: {model_config}")

    # Determine final model name - prioritize model_config, then fall back to CLI arg
    final_model_name = model_config.get("model") or args.model
    logger.info(
        f"Using model: {final_model_name} (from {'config file' if model_config.get('model') else 'CLI argument'})"
    )

    # Create MCP client with final model name
    client = OpenAIMCPClient(model=final_model_name, api_key=api_key)
    logger.info(f"OpenAI MCP client created with model {final_model_name}")

    try:
        # Convert single server to multi-server format if needed
        if hasattr(args, "server_paths") and hasattr(args, "server_args_list"):
            # Already in multi-server format
            server_paths = args.server_paths
            server_args_list = args.server_args_list
            server_envs = getattr(args, "server_envs", None)
        else:
            # Convert single server to multi-server format
            server_paths = [args.server]
            server_args_list = [args.server_args] if args.server_args else [None]
            server_envs = [getattr(args, "server_env", None)]

        logger.info(f"Connecting to {len(server_paths)} MCP server(s)")

        # Connect to servers (always multi-server approach)
        await client.connect_to_multiple_servers(
            server_paths, server_args_list, server_envs
        )

        # Get aggregated tools from all servers
        all_tools = await client.get_all_tools()
        tools_data = all_tools
        logger.info(
            f"Retrieved {len(tools_data)} tools from {len(server_paths)} MCP server(s)"
        )

        if not tools_data:
            logger.error("No valid tools found. Cannot generate tasks.")
            return

        # Create output directory if it doesn't exist
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        task_generator = TaskGenerator(
            tool_library=ToolLibrary(tools=tools_data),
            model_config=model_config,
            api_key=api_key,
            existing_tasks=[],
        )

        # Load existing tasks from the main output file
        if output_path.exists():
            logger.info(f"Loading existing tasks from {args.output}")
            task_generator.load_tasks_from_jsonl(args.output)

        # Load tasks from additional existing files if provided
        for file_path in args.existing_files:
            if os.path.exists(file_path):
                logger.info(f"Loading existing tasks from {file_path}")
                task_generator.load_tasks_from_jsonl(file_path)
            else:
                logger.warning(f"File not found: {file_path}")

        # Set num_tasks based on args
        num_tasks = getattr(args, "num_tasks", 10)

        # Generate tasks
        logger.info(f"Starting generation of {num_tasks} tasks")
        tasks_generated = 0

        while tasks_generated < num_tasks:
            try:
                # Log start of generation
                logger.info(
                    f"Starting generation for task {tasks_generated + 1}/{num_tasks}"
                )
                start_time = time.time()

                # Generate task
                task = task_generator.generate_task_from_tools(
                    tools=tools_data,
                    system_message=system_message,
                    user_message=user_message,
                )

                # Log success
                elapsed = time.time() - start_time
                logger.info(f"Task generation completed in {elapsed:.2f} seconds")

                # Save task to the output file
                task_generator.save_task_to_jsonl(task, args.output)
                tasks_generated += 1
                logger.info(
                    f"Generated task {tasks_generated}/{num_tasks}: {task.name}"
                )

                # Print task details every 5 tasks
                if tasks_generated % 5 == 0 or tasks_generated == 1:
                    print_task(task, f"Task {tasks_generated}")

                # Pause before generating next task to avoid rate limits
                await asyncio.sleep(2)

            except Exception as e:
                logger.error(f"Error generating task: {str(e)}", exc_info=True)
                # Wait longer after an error before retrying
                await asyncio.sleep(10)

        logger.info(
            f"Task generation complete. {tasks_generated} tasks saved to {args.output}"
        )

    except Exception as e:
        logger.error(f"Error during execution: {e}", exc_info=True)
    finally:
        # Clean up the client
        logger.info("Cleaning up resources")
        await client.cleanup()


def main(args):
    """Main entry point for the CLI."""
    # Set API key in environment if provided directly
    if hasattr(args, "api_key") and args.api_key:
        os.environ["OPENAI_API_KEY"] = args.api_key

    asyncio.run(generate_tasks(args))


if __name__ == "__main__":
    # When run directly, this should not happen as the main CLI handles argument parsing
    print("Please use the main CLI: python -m mcpeval.cli.main generate-tasks --help")
    import sys

    sys.exit(1)
