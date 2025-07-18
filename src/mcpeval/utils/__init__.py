"""
Utility modules for MCP Eval LLM.

This package contains common utility functions and modules used across the codebase.
"""

from .task_converter import (
    process_jsonl_file,
    process_file,
    convert_to_xlam_format,
    extract_task_from_evaluation_results,
)

from .cli import (
    Colors,
    colored_print,
    load_jsonl,
    load_json,
    load_prompt_from_file,
    print_task,
    print_tool_calls,
    handle_existing_file,
    generate_output_filename,
    save_tasks_to_jsonl,
    setup_colored_logging,
    extract_tool_calls_from_prediction,
    extract_tool_calls_from_ground_truth,
    parse_servers_argument,
)

__all__ = [
    # Task converter
    "process_jsonl_file",
    "process_file",
    "convert_to_xlam_format",
    "extract_task_from_evaluation_results",
    # CLI utilities
    "Colors",
    "colored_print",
    "load_jsonl",
    "load_json",
    "load_prompt_from_file",
    "print_task",
    "print_tool_calls",
    "handle_existing_file",
    "generate_output_filename",
    "save_tasks_to_jsonl",
    "setup_colored_logging",
    "extract_tool_calls_from_prediction",
    "extract_tool_calls_from_ground_truth",
    "parse_servers_argument",
]
