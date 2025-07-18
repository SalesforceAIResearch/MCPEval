#!/usr/bin/env python3
"""
CLI Utility Functions

This module contains common utility functions used across different CLI modules
to avoid code duplication.
"""
import json
import logging
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from mcpeval.commons.types import Task, ToolCall

# Configure logging
logger = logging.getLogger(__name__)


# Color utilities for terminal output
class Colors:
    """ANSI color codes for terminal output."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright colors
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"


def colored_print(message: str, color: str = Colors.RESET, bold: bool = False):
    """Print a colored message to stdout."""
    if not sys.stdout.isatty():
        # Don't use colors if not in a terminal
        print(message)
        return

    prefix = Colors.BOLD if bold else ""
    print(f"{prefix}{color}{message}{Colors.RESET}")


# File loading utilities
def load_jsonl(file_path: str) -> List[Dict[str, Any]]:
    """Load data from a JSONL file."""
    data = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data


def load_json(file_path: str) -> List[Dict[str, Any]]:
    """Load data from a JSON file."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        # Handle both list and single object formats
        if isinstance(data, dict):
            return [data]
        return data


def load_prompt_from_file(prompt_file_path: str) -> Optional[str]:
    """Load system message from a JSON prompt file.

    Args:
        prompt_file_path: Path to JSON file containing prompt

    Returns:
        str: System message from the file, or None if not found
    """
    if not prompt_file_path:
        return None

    try:
        with open(prompt_file_path, "r", encoding="utf-8") as f:
            prompt_data = json.load(f)

        system_message = prompt_data.get("system")
        if system_message:
            logger.info(f"Loaded system message from {prompt_file_path}")
            return system_message
        else:
            logger.warning(f"No 'system' key found in {prompt_file_path}")
            return None

    except FileNotFoundError:
        logger.error(f"Prompt file not found: {prompt_file_path}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in prompt file {prompt_file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error reading prompt file {prompt_file_path}: {e}")
        return None


# Task display utilities
def print_task(task: Task, title: Optional[str] = None):
    """Print task details in a readable format.

    Args:
        task: Task object to print
        title: Optional title for the task (if None, uses task name)
    """
    display_title = title if title else f"Task: {task.name}"

    print(f"\n{'='*50}")
    print(f"{display_title}")
    print(f"{'='*50}")
    print(f"Name: {task.name}")
    print(f"Description: {task.description}")
    print(f"Goal: {task.goal}")
    logger.debug(f"Tools available ({len(task.tools)}):")
    for tool in task.tools:
        tool_desc = tool.description if hasattr(tool, "description") else ""
        logger.debug(f"  - {tool.name}{': ' + tool_desc if tool_desc else ''}")

    if hasattr(task, "tool_calls") and task.tool_calls:
        print("\nExpected Tool Calls:")
        for call in task.tool_calls:
            print(f"  - {call.tool_name}")
            print(f"    Parameters: {call.tool_parameters}")

    print("=" * 50)


def print_tool_calls(tool_calls):
    """Print tool calls in a detailed format.

    Args:
        tool_calls: List of ToolCall objects or (tool_call, session) tuples
    """
    print(f"\n{'='*20} TOOL CALLS {'='*20}")
    for i, item in enumerate(tool_calls):
        # Check if the item is a tuple (tool_call, session) or just a ToolCall
        if isinstance(item, tuple) and len(item) == 2:
            tool_call, session = item
        else:
            tool_call = item
            session = None

        print(f"Tool Call #{i+1}:")
        print(f"  Tool Name: {tool_call.tool_name}")
        if session:
            print(
                f"  Session: {session.name if hasattr(session, 'name') else str(session)}"
            )
        print(f"  Parameters:")
        try:
            # Pretty print the parameters as JSON
            print(
                json.dumps(tool_call.tool_parameters, indent=4).replace("\n", "\n    ")
            )
        except:
            print(f"    {tool_call.tool_parameters}")
        print()
    print(f"{'='*50}")


# File handling utilities
def handle_existing_file(
    file_path: str, non_interactive: bool = False, default_action: str = "timestamp"
) -> Tuple[str, bool]:
    """Handle existing file by asking user what to do or using default action.

    Args:
        file_path: Path to the file that might exist
        non_interactive: If True, don't prompt user and use default_action
        default_action: Default action when non_interactive is True:
                       - "overwrite": Overwrite existing file
                       - "append": Append to existing file
                       - "timestamp": Create new file with timestamp (default)

    Returns:
        tuple: (file_path_to_use, append_mode) where append_mode is True if should append
    """
    if not os.path.exists(file_path):
        return file_path, False

    # Non-interactive mode: use default action
    if non_interactive:
        if default_action == "overwrite":
            logger.info(f"Non-interactive mode: Overwriting existing file: {file_path}")
            return file_path, False
        elif default_action == "append":
            logger.info(
                f"Non-interactive mode: Appending to existing file: {file_path}"
            )
            return file_path, True
        else:  # default_action == "timestamp"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name, ext = os.path.splitext(file_path)
            new_file_path = f"{base_name}_{timestamp}{ext}"
            logger.info(
                f"Non-interactive mode: Creating new file with timestamp: {new_file_path}"
            )
            return new_file_path, False

    # Interactive mode: prompt user
    print(f"\nOutput file already exists: {file_path}")
    while True:
        choice = input(
            "Choose an option:\n1. Overwrite existing file\n2. Append to existing file\n3. Create new file with timestamp\nEnter choice (1/2/3): "
        ).strip()

        if choice == "1":
            # Overwrite existing file
            return file_path, False
        elif choice == "2":
            # Append to existing file
            return file_path, True
        elif choice == "3":
            # Create new file with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name, ext = os.path.splitext(file_path)
            new_file_path = f"{base_name}_{timestamp}{ext}"
            return new_file_path, False
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")


def generate_output_filename(
    input_file: str, output_file: Optional[str] = None, prefix: str = "output"
) -> str:
    """Generate output filename with timestamp if not specified.

    Args:
        input_file: Path to input file
        output_file: Specified output file (can be None)
        prefix: Prefix for the generated filename

    Returns:
        str: Generated output file path
    """
    if output_file:
        return output_file

    # Create output file in the same directory as input file with timestamp
    input_dir = os.path.dirname(input_file)
    input_name = os.path.basename(input_file)
    base_name, ext = os.path.splitext(input_name)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{prefix}_{base_name}_{timestamp}{ext}"
    return os.path.join(input_dir, output_filename)


def save_tasks_to_jsonl(tasks, output_file: str, append: bool = False):
    """Save one or multiple tasks to a JSONL file.

    Args:
        tasks: A single Task object or a list of Task objects with results included
        output_file: Path to output JSONL file
        append: Whether to append to the file (True) or overwrite (False)
    """
    mode = "a" if append else "w"

    # Convert to list if single task
    task_list = tasks if isinstance(tasks, list) else [tasks]

    if len(task_list) > 1:
        logger.info(f"Saving {len(task_list)} results to {output_file}")

    with open(output_file, mode) as f:
        for task in task_list:
            # Convert task to dictionary
            task_dict = task.model_dump()

            # Write as a single line JSON
            f.write(json.dumps(task_dict) + "\n")

    if len(task_list) == 1:
        logger.info(f"Saved result for task: {task_list[0].name}")
    else:
        logger.info(f"Saved {len(task_list)} task results")


# Logging configuration
def setup_colored_logging(level=logging.INFO):
    """Set up colored logging for CLI applications."""

    class ColoredFormatter(logging.Formatter):
        """Colored logging formatter."""

        COLORS = {
            "DEBUG": Colors.BRIGHT_BLACK,
            "INFO": Colors.BRIGHT_BLUE,
            "WARNING": Colors.BRIGHT_YELLOW,
            "ERROR": Colors.BRIGHT_RED,
            "CRITICAL": Colors.BRIGHT_MAGENTA,
        }

        def format(self, record):
            if sys.stdout.isatty():
                log_color = self.COLORS.get(record.levelname, Colors.RESET)
                record.levelname = f"{log_color}{record.levelname}{Colors.RESET}"
            return super().format(record)

    # Configure basic logging
    logging.basicConfig(
        level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Apply colored formatter if in terminal
    if sys.stdout.isatty():
        root_logger = logging.getLogger()
        handler = logging.StreamHandler()
        handler.setFormatter(
            ColoredFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        root_logger.handlers.clear()
        root_logger.addHandler(handler)
        root_logger.propagate = False


# Tool call extraction utilities for analyzer
def extract_tool_calls_from_prediction(
    task_data: Dict[str, Any],
) -> Tuple[str, List[ToolCall]]:
    """Extract tool calls from a prediction task data dictionary."""
    task_id = task_data.get("task_id", "") or task_data.get("id", "")

    # Extract tool calls from the data
    tool_calls = []

    # Handle different formats
    if "tool_calls" in task_data:
        for call in task_data["tool_calls"]:
            if (
                isinstance(call, dict)
                and "tool_name" in call
                and "tool_parameters" in call
            ):
                tool_calls.append(
                    ToolCall(
                        tool_name=call["tool_name"],
                        tool_parameters=call["tool_parameters"],
                    )
                )

    return task_id, tool_calls


def extract_tool_calls_from_ground_truth(
    task_data: Dict[str, Any],
) -> Tuple[str, List[ToolCall]]:
    """Extract tool calls from a ground truth task data dictionary."""
    task_id = task_data.get("id", "") or task_data.get("task_id", "")

    tool_calls = []
    if "tool_calls" in task_data:
        for call in task_data["tool_calls"]:
            if (
                isinstance(call, dict)
                and "tool_name" in call
                and "tool_parameters" in call
            ):
                tool_calls.append(
                    ToolCall(
                        tool_name=call["tool_name"],
                        tool_parameters=call["tool_parameters"],
                    )
                )

    return task_id, tool_calls


def parse_servers_argument(args):
    """
    Parse servers argument with support for arguments and environment variables.

    Supported formats:
    - server                           # Just server path
    - server:arg1,arg2                 # Server with arguments
    - server^ENV_VAR=value             # Server with environment variables
    - server:arg1,arg2^ENV_VAR=value   # Server with both arguments and environment variables

    Args:
        args: Parsed command line arguments object

    Returns:
        tuple: (server_paths, server_args_list, server_env_list) where:
            - server_paths is a list of server paths
            - server_args_list is a list of argument lists for each server
            - server_env_list is a list of environment variable dictionaries for each server
    """
    import re

    # Parse --servers format only
    if not hasattr(args, "servers") or not args.servers:
        raise ValueError("No servers specified. Use --servers argument.")

    server_paths = []
    server_args_list = []
    server_env_list = []

    # Handle both space-separated and comma-separated servers
    all_servers = []
    for server_group in args.servers:
        # Check if this looks like comma-separated servers
        # We need to be careful not to split on commas that are part of server arguments
        if "," in server_group:
            # Split smartly: look for pattern where comma is followed by @ (indicating next server)
            # Split on comma followed by @ or comma at start of string followed by @
            parts = re.split(r",(?=@)", server_group)
            if len(parts) > 1:
                all_servers.extend([s.strip() for s in parts if s.strip()])
            else:
                # No comma-separated servers found, treat as single server
                all_servers.append(server_group)
        else:
            all_servers.append(server_group)

    for server_spec in all_servers:
        server_spec = server_spec.strip()

        # Split on ^ to separate server+args from environment variables
        if "^" in server_spec:
            server_and_args, env_vars_str = server_spec.split("^", 1)
        else:
            server_and_args = server_spec
            env_vars_str = ""

        # Parse server path and arguments
        if ":" in server_and_args:
            # Format: server:arg1,arg2 or server: (empty args)
            server_path, args_str = server_and_args.split(":", 1)
            if args_str:
                server_args = [
                    arg.strip() for arg in args_str.split(",") if arg.strip()
                ]
            else:
                server_args = []  # Explicitly empty
        else:
            # Format: server (no args specified)
            server_path = server_and_args
            server_args = []

        # Parse environment variables
        server_env = {}
        if env_vars_str:
            # Split environment variables by comma, but be careful with values that contain commas
            env_pairs = []
            current_pair = ""
            paren_count = 0

            for char in env_vars_str:
                if char == "," and paren_count == 0:
                    if current_pair.strip():
                        env_pairs.append(current_pair.strip())
                    current_pair = ""
                else:
                    if char in "([{":
                        paren_count += 1
                    elif char in ")]}":
                        paren_count -= 1
                    current_pair += char

            # Add the last pair
            if current_pair.strip():
                env_pairs.append(current_pair.strip())

            # Parse each environment variable pair
            for env_pair in env_pairs:
                if "=" in env_pair:
                    key, value = env_pair.split("=", 1)
                    server_env[key.strip()] = value.strip()
                else:
                    logger.warning(f"Invalid environment variable format: {env_pair}")

        server_paths.append(server_path)
        server_args_list.append(server_args)
        server_env_list.append(server_env)

    return server_paths, server_args_list, server_env_list
