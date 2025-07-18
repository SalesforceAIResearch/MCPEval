#!/usr/bin/env python3
"""
Filter tasks with error information from evaluation JSON files.

This script reads evaluation JSON files and filters tasks that contain
conversations with error messages, particularly "Error executing tool" messages
or other error information.
"""

import json
import argparse
import re
from pathlib import Path
from typing import Dict, List, Any, Set
import sys


def contains_error_patterns(text: str) -> bool:
    """
    Check if text contains common error patterns.

    Args:
        text: The text to check for error patterns

    Returns:
        bool: True if error patterns are found, False otherwise
    """
    if not text:
        return False

    # Convert to lowercase for case-insensitive matching
    text_lower = text.lower()

    # Common error patterns
    error_patterns = [
        r"error executing tool",
        r"error:",
        r"failed to",
        r"exception",
        r"traceback",
        r"cannot",
        r"unable to",
        r"not found",
        r"invalid",
        r"timeout",
        r"connection error",
        r"permission denied",
        r"access denied",
        r"unauthorized",
        r"forbidden",
        r"bad request",
        r"internal server error",
        r"service unavailable",
        r"network error",
        r"parse error",
        r"syntax error",
        r"runtime error",
        r"null pointer",
        r"segmentation fault",
        r"stack overflow",
        r"out of memory",
        r"file not found",
        r"directory not found",
        r"no such file",
        r"no such directory",
    ]

    # Check each pattern
    for pattern in error_patterns:
        if re.search(pattern, text_lower):
            return True

    return False


def has_error_in_conversation(conversation: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Check if a conversation contains error messages.

    Args:
        conversation: List of conversation messages

    Returns:
        Dict containing error information:
        - has_error: bool indicating if errors were found
        - error_messages: list of error messages found
        - error_tools: set of tools that had errors
        - error_count: number of error messages found
    """
    error_info = {
        "has_error": False,
        "error_messages": [],
        "error_tools": set(),
        "error_count": 0,
    }

    for message in conversation:
        role = message.get("role", "")
        content = message.get("content", "")

        # Check tool messages for errors
        if role == "tool":
            if contains_error_patterns(content):
                error_info["has_error"] = True
                error_info["error_messages"].append(
                    {
                        "role": role,
                        "content": content,
                        "tool_name": message.get("name", ""),
                        "tool_call_id": message.get("tool_call_id", ""),
                    }
                )
                error_info["error_tools"].add(message.get("name", ""))
                error_info["error_count"] += 1

        # Check assistant messages for error patterns
        elif role == "assistant":
            if contains_error_patterns(content):
                error_info["has_error"] = True
                error_info["error_messages"].append(
                    {
                        "role": role,
                        "content": (
                            content[:200] + "..." if len(content) > 200 else content
                        ),
                    }
                )
                error_info["error_count"] += 1

        # Check user messages for error patterns (less common but possible)
        elif role == "user":
            if contains_error_patterns(content):
                error_info["has_error"] = True
                error_info["error_messages"].append(
                    {
                        "role": role,
                        "content": (
                            content[:200] + "..." if len(content) > 200 else content
                        ),
                    }
                )
                error_info["error_count"] += 1

    # Convert set to list for JSON serialization
    error_info["error_tools"] = list(error_info["error_tools"])

    return error_info


def filter_error_tasks(
    input_file: Path,
    output_file: Path = None,
    summary_only: bool = False,
    verbose: bool = False,
) -> Dict[str, Any]:
    """
    Filter tasks with error information from the evaluation JSON file.

    Args:
        input_file: Path to the input JSON file
        output_file: Path to the output JSON file (optional)
        summary_only: If True, only output summary statistics
        verbose: If True, print detailed information

    Returns:
        Dict containing filtering results and statistics
    """
    try:
        # Read the input JSON file
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        if verbose:
            print(f"Loaded {len(data)} tasks from {input_file}")

        # Filter tasks with errors
        error_tasks = []
        total_tasks = len(data)
        tasks_with_errors = 0
        total_errors = 0
        error_tools_count = {}

        for task in data:
            conversation = task.get("conversation", [])
            if not conversation:
                continue

            error_info = has_error_in_conversation(conversation)

            if error_info["has_error"]:
                tasks_with_errors += 1
                total_errors += error_info["error_count"]

                # Count error tools
                for tool in error_info["error_tools"]:
                    error_tools_count[tool] = error_tools_count.get(tool, 0) + 1

                # Add error info to task
                task_copy = task.copy()
                task_copy["error_info"] = error_info
                error_tasks.append(task_copy)

                if verbose:
                    print(
                        f"Task {task.get('task_id', 'N/A')}: {error_info['error_count']} errors"
                    )
                    for error_msg in error_info["error_messages"]:
                        print(
                            f"  - {error_msg['role']}: {error_msg['content'][:100]}..."
                        )

        # Prepare results
        results = {
            "summary": {
                "total_tasks": total_tasks,
                "tasks_with_errors": tasks_with_errors,
                "error_percentage": (
                    (tasks_with_errors / total_tasks) * 100 if total_tasks > 0 else 0
                ),
                "total_errors": total_errors,
                "error_tools_count": error_tools_count,
                "most_common_error_tools": sorted(
                    error_tools_count.items(), key=lambda x: x[1], reverse=True
                ),
            },
            "error_tasks": error_tasks if not summary_only else [],
        }

        # Save to output file if specified
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"Results saved to {output_file}")

        return results

    except FileNotFoundError:
        print(f"Error: File {input_file} not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {input_file}: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def print_summary(results: Dict[str, Any]):
    """Print a summary of the filtering results."""
    summary = results["summary"]

    print("\n" + "=" * 60)
    print("ERROR TASK FILTERING SUMMARY")
    print("=" * 60)
    print(f"Total tasks: {summary['total_tasks']}")
    print(f"Tasks with errors: {summary['tasks_with_errors']}")
    print(f"Error percentage: {summary['error_percentage']:.1f}%")
    print(f"Total error messages: {summary['total_errors']}")

    if summary["most_common_error_tools"]:
        print(f"\nMost common error tools:")
        for tool, count in summary["most_common_error_tools"][:10]:
            print(f"  {tool}: {count} errors")

    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Filter tasks with error information from evaluation JSON files"
    )
    parser.add_argument("input_file", type=Path, help="Path to the input JSON file")
    parser.add_argument(
        "-o", "--output", type=Path, help="Path to the output JSON file (optional)"
    )
    parser.add_argument(
        "-s",
        "--summary-only",
        action="store_true",
        help="Only output summary statistics, not the full error tasks",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print detailed information during processing",
    )

    args = parser.parse_args()

    # Validate input file
    if not args.input_file.exists():
        print(f"Error: Input file {args.input_file} does not exist")
        sys.exit(1)

    # Set default output file if not specified
    if args.output is None and not args.summary_only:
        args.output = (
            args.input_file.parent / f"{args.input_file.stem}_error_tasks.json"
        )

    # Filter the tasks
    results = filter_error_tasks(
        args.input_file, args.output, args.summary_only, args.verbose
    )

    # Print summary
    print_summary(results)

    # Print additional info if not summary only
    if not args.summary_only and results["error_tasks"]:
        print(f"\nFound {len(results['error_tasks'])} tasks with errors")
        print("Example error task IDs:")
        for task in results["error_tasks"][:5]:
            print(f"  - {task.get('task_id', 'N/A')}")


if __name__ == "__main__":
    main()
