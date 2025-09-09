#!/usr/bin/env python3
"""
MCPEval: Automatic MCP-based Deep Evaluation for AI Agent Models

This module provides the main entry point for the CLI, with support for multiple
subcommands like task generation, task verification, model evaluation, etc.
"""
import argparse
import logging
import sys
import os
from importlib import import_module
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import centralized utilities
from mcpeval.utils.cli import (
    Colors,
    colored_print,
    setup_colored_logging,
    parse_servers_argument,
)


def print_banner():
    """Print a colorful banner for the CLI."""
    if not sys.stdout.isatty():
        print("MCPEval CLI")
        return

    banner = """
┌──────────────────────────────────────────────────────────────┐
│                         MCPEval CLI                          │
│      Automatic MCP-based Deep Evaluation for AI Models       │
└──────────────────────────────────────────────────────────────┘
"""
    colored_print(banner, Colors.BRIGHT_CYAN, bold=True)


class ColoredHelpFormatter(argparse.HelpFormatter):
    """Custom help formatter that adds colors to subcommands."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.command_colors = {
            "generate-tasks": Colors.BRIGHT_YELLOW,
            "verify-tasks": Colors.BRIGHT_BLUE,
            "convert-data": Colors.BRIGHT_MAGENTA,
            "split-data": Colors.BRIGHT_RED,
            "evaluate": Colors.BRIGHT_GREEN,
            "analyze": Colors.BRIGHT_CYAN,
            "judge": Colors.BRIGHT_MAGENTA,
            "judge-rubric": Colors.BRIGHT_CYAN,
            "report-gen": Colors.BRIGHT_WHITE,
            "auto": Colors.BRIGHT_GREEN,
        }

    def _format_action(self, action):
        # Get the original formatted action
        result = super()._format_action(action)

        # Only apply colors if we're in a terminal
        if not sys.stdout.isatty():
            return result

        # Color the subcommands in the help text
        emoji_map = {
            "generate-tasks": "🎯",
            "verify-tasks": "✅",
            "convert-data": "🔄",
            "split-data": "✂️",
            "evaluate": "📊",
            "analyze": "🔍",
            "judge": "🧠",
            "judge-rubric": "📋",
            "report-gen": "📄",
            "auto": "🚀",
        }

        # Sort commands by length (longest first) to avoid partial matches
        sorted_commands = sorted(
            self.command_colors.items(), key=lambda x: len(x[0]), reverse=True
        )

        for command, color in sorted_commands:
            emoji = emoji_map.get(command, "⚙️")

            # Only replace exact matches to avoid double replacements
            import re

            # Simple pattern for word boundaries since we fixed the command naming conflicts
            pattern = rf"(?<!🎯 )(?<!✅ )(?<!🔄 )(?<!✂️ )(?<!📊 )(?<!🔍 )(?<!🧠 )(?<!📋 )(?<!📄 )\b{re.escape(command)}\b"
            colored_command = f"{emoji} {color}{Colors.BOLD}{command}{Colors.RESET}"
            result = re.sub(pattern, colored_command, result)

        # Also color some descriptions
        description_replacements = {
            "Generate tasks for MCP servers": f"{Colors.DIM}Generate tasks for MCP servers{Colors.RESET}",
            "Verify generated tasks against an MCP server": f"{Colors.DIM}Verify generated tasks against an MCP server{Colors.RESET}",
            "Convert data to different formats (e.g., XLAM) as a single file": f"{Colors.DIM}Convert data to different formats (e.g., XLAM) as a single file{Colors.RESET}",
            "Randomly split JSONL task file into train/valid/test sets": f"{Colors.DIM}Randomly split JSONL task file into train/valid/test sets{Colors.RESET}",
            "Evaluate models using MCP servers and tasks": f"{Colors.DIM}Evaluate models using MCP servers and tasks{Colors.RESET}",
            "Analyze evaluation results against ground truth": f"{Colors.DIM}Analyze evaluation results against ground truth{Colors.RESET}",
            "Evaluate execution results using LLM judges": f"{Colors.DIM}Evaluate execution results using LLM judges{Colors.RESET}",
            "Analyze LLM judgment results and generate performance reports": f"{Colors.DIM}Analyze LLM judgment results and generate performance reports{Colors.RESET}",
            "Generate AI-powered evaluation reports from analysis files": f"{Colors.DIM}Generate AI-powered evaluation reports from analysis files{Colors.RESET}",
            "Automatically run complete evaluation workflow (generate, verify, evaluate, analyze)": f"{Colors.DIM}Automatically run complete evaluation workflow (generate, verify, evaluate, analyze){Colors.RESET}",
        }

        for original, colored in description_replacements.items():
            if original in result:
                result = result.replace(original, colored)

        return result


# Configure logging using the centralized setup
setup_colored_logging(level=logging.INFO)
logger = logging.getLogger(__name__)


def task_generator(args):
    """Entry point for task generator subcommand."""
    # Parse servers argument with environment variable support
    server_paths, server_args_list, server_env_list = parse_servers_argument(args)

    if len(server_paths) > 1:
        colored_print(
            f"✨ Connecting to {len(server_paths)} servers for multi-server task generation",
            Colors.BRIGHT_GREEN,
        )
        # Set multi-server attributes
        args.server_paths = server_paths
        args.server_args_list = server_args_list
        args.server_env_list = server_env_list
    else:
        colored_print(
            f"🔗 Connecting to single server: {server_paths[0]}", Colors.BRIGHT_BLUE
        )

    # Set the server and server_args for backward compatibility with underlying function
    args.server = server_paths[0]
    args.server_args = server_args_list[0]
    args.server_env = server_env_list[0]

    from mcpeval.cli.mcp_task_generator.generate import main

    main(args)


def task_verifier(args):
    """Entry point for task verification subcommand."""
    # Parse servers argument with environment variable support
    server_paths, server_args_list, server_env_list = parse_servers_argument(args)

    if len(server_paths) > 1:
        colored_print(
            f"✨ Connecting to {len(server_paths)} servers for multi-server task verification",
            Colors.BRIGHT_GREEN,
        )
        # Set multi-server attributes
        args.server_paths = server_paths
        args.server_args_list = server_args_list
        args.server_env_list = server_env_list
    else:
        colored_print(
            f"🔗 Connecting to single server: {server_paths[0]}", Colors.BRIGHT_BLUE
        )

    # Set the server and server_args for backward compatibility with underlying function
    args.server = server_paths[0]
    args.server_args = server_args_list[0]
    args.server_env = server_env_list[0]

    from mcpeval.cli.mcp_task_verifier.verify import main

    main(args)


def data_converter(args):
    """Entry point for data format conversion subcommand."""
    from mcpeval.utils.task_converter import process_jsonl_file, process_file
    import json
    import os

    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        colored_print(f"✓ Created output directory: {output_dir}", Colors.GREEN)

    # Determine system message from prompt file or use default
    system_message = args.system_message
    if args.prompt_file:
        try:
            with open(args.prompt_file, "r") as f:
                prompt_data = json.load(f)
                system_message = prompt_data.get("system", system_message)
                colored_print(
                    f"✓ Loaded system message from {args.prompt_file}", Colors.GREEN
                )
        except Exception as e:
            colored_print(
                f"⚠️  Warning: Could not load prompt file {args.prompt_file}: {e}",
                Colors.YELLOW,
            )
            colored_print(f"Using default system message instead", Colors.YELLOW)

    # Process input file based on whether it's a single JSON file or JSONL
    if args.input.endswith(".jsonl"):
        # Always output to a single file for JSONL
        process_jsonl_file(
            args.input,
            args.output,
            args.prefix,
            args.split,
            system_message=system_message,
        )
    else:
        # Process a single JSON file
        process_file(
            args.input,
            args.output,
            args.task_id,
            args.prefix,
            args.split,
            system_message=system_message,
        )

    colored_print(
        f"✓ Data format conversion completed. Output saved to {args.output}",
        Colors.BRIGHT_GREEN,
        bold=True,
    )


def data_splitter(args):
    """Entry point for data splitting subcommand."""
    from mcpeval.utils.data_splitter import split_jsonl_file

    split_jsonl_file(
        input_file=args.input,
        output_dir=args.output_dir,
        train_ratio=args.train_ratio,
        valid_ratio=args.valid_ratio,
        test_ratio=args.test_ratio,
        seed=args.seed,
    )


def model_evaluator(args):
    """Entry point for model evaluation subcommand."""
    # Parse servers argument with environment variable support
    server_paths, server_args_list, server_env_list = parse_servers_argument(args)

    if len(server_paths) > 1:
        colored_print(
            f"✨ Connecting to {len(server_paths)} servers for multi-server model evaluation",
            Colors.BRIGHT_GREEN,
        )
        # Set multi-server attributes
        args.server_paths = server_paths
        args.server_args_list = server_args_list
        args.server_env_list = server_env_list
    else:
        colored_print(
            f"🔗 Connecting to single server: {server_paths[0]}", Colors.BRIGHT_BLUE
        )

    # Set the server and server_args for backward compatibility with underlying function
    args.server = server_paths[0]
    args.server_args = server_args_list[0]
    args.server_env = server_env_list[0]

    from mcpeval.cli.mcp_model_evaluator.evaluate import main

    main(args)


def analyzer(args):
    """Entry point for analysis subcommand."""
    from mcpeval.cli.analyzer.analyze import main

    main(args)


def llm_judger(args):
    """Entry point for LLM judger subcommand."""
    from mcpeval.cli.llm_judger.judge import main

    main(args)


def llm_judger_analyzer(args):
    """Entry point for LLM judger analyzer subcommand."""
    from mcpeval.cli.llm_judger.analyze import main

    main(args)


def auto_workflow(args):
    """Entry point for auto workflow subcommand."""
    from mcpeval.cli.auto.auto import main

    main(args)


def report_generator(args):
    """Entry point for report generation subcommand."""
    from mcpeval.cli.report_gen.report_gen import main

    main(args)


def parse_arguments():
    """Parse command line arguments."""
    # Create a colorful description
    if sys.stdout.isatty():
        description = (
            f"{Colors.BRIGHT_CYAN}🔧 MCPEval CLI tools for {Colors.BRIGHT_WHITE}"
            f"MCP server management{Colors.BRIGHT_CYAN} and {Colors.BRIGHT_WHITE}"
            f"LLM evaluation{Colors.RESET}"
        )
    else:
        description = "MCPEval CLI tools for MCP server management and LLM evaluation"

    parser = argparse.ArgumentParser(
        prog="mcp-eval", description=description, formatter_class=ColoredHelpFormatter
    )

    # Create subparsers for different commands
    subparsers = parser.add_subparsers(
        title="subcommands",
        description="valid subcommands",
        dest="command",
        help="Sub-command to run",
    )

    # Make subcommands required
    subparsers.required = True

    # Common arguments for all commands
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument(
        "--api-key",
        type=str,
        help="OpenAI API key (will use OPENAI_API_KEY environment variable if not provided)",
    )

    # Task Generator subcommand
    task_gen_parser = subparsers.add_parser(
        "generate-tasks", help="Generate tasks for MCP servers", parents=[common_parser]
    )
    # Server connection arguments - support multiple servers with optional arguments
    task_gen_parser.add_argument(
        "--servers",
        type=str,
        nargs="+",
        help="Server paths to connect to. Format: server_path[:args][^env_vars] where args is comma-separated and env_vars is KEY=value,KEY2=value2. "
        "Examples: @modelcontextprotocol/server-fetch, "
        "@openbnb/mcp-server-airbnb:--ignore-robots-txt, "
        "server1^API_KEY=key123, "
        "server2:--flag1,--flag2^ENV_VAR=value1,ENV_VAR2=value2",
    )

    # Task generation arguments
    task_gen_parser.add_argument(
        "--output",
        type=str,
        default="generated_tasks.jsonl",
        help="Output file path for generated tasks (default: generated_tasks.jsonl)",
    )
    task_gen_parser.add_argument(
        "--num-tasks",
        type=int,
        default=10,
        help="Number of tasks to generate (default: 10)",
    )
    task_gen_parser.add_argument(
        "--existing-files",
        type=str,
        nargs="*",
        default=[],
        help="List of existing files to load tasks from",
    )
    task_gen_parser.add_argument(
        "--prompt-file",
        type=str,
        help='JSON file containing system and user messages (format: {"system": "...", "user": "..."})',
    )
    # Model configuration
    task_gen_parser.add_argument(
        "--model",
        type=str,
        default="gpt-4.1-2025-04-14",
        help="OpenAI model to use for task generation (default: gpt-4.1-2025-04-14)",
    )
    task_gen_parser.add_argument(
        "--temperature",
        type=float,
        default=0.2,
        help="Temperature for model generation (default: 0.2)",
    )
    task_gen_parser.add_argument(
        "--max-tokens",
        type=int,
        default=4000,
        help="Maximum number of tokens to generate (default: 4000)",
    )
    task_gen_parser.add_argument(
        "--top-p",
        type=float,
        default=0.95,
        help="Top-p sampling parameter (default: 0.95)",
    )
    task_gen_parser.add_argument(
        "--model-config",
        type=str,
        help="Path to JSON file containing model configuration (takes priority over individual model parameters)",
    )
    task_gen_parser.set_defaults(func=task_generator)

    # Task Verifier subcommand
    task_verify_parser = subparsers.add_parser(
        "verify-tasks",
        help="Verify generated tasks against MCP server(s)",
        parents=[common_parser],
    )
    # Server connection arguments - support multiple servers with optional arguments
    task_verify_parser.add_argument(
        "--servers",
        type=str,
        nargs="+",
        help="Server paths to connect to. Format: server_path[:args][^env_vars] where args is comma-separated and env_vars is KEY=value,KEY2=value2. "
        "Examples: @modelcontextprotocol/server-fetch, "
        "@openbnb/mcp-server-airbnb:--ignore-robots-txt, "
        "server1^API_KEY=key123, "
        "server2:--flag1,--flag2^ENV_VAR=value1,ENV_VAR2=value2",
    )

    task_verify_parser.add_argument(
        "--tasks-file",
        type=str,
        required=True,
        help="Path to the JSONL file containing tasks to verify",
    )
    task_verify_parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path for verification results (default: verified_<input_filename>)",
    )
    task_verify_parser.add_argument(
        "--model",
        type=str,
        default="gpt-4o",
        help="OpenAI model to use for verification (default: gpt-4o)",
    )
    task_verify_parser.add_argument(
        "--model-config",
        type=str,
        help="Path to JSON file containing model configuration (takes priority over individual model parameters)",
    )
    task_verify_parser.add_argument(
        "--num-tasks",
        type=int,
        default=-1,
        help="Number of tasks to verify (default: all tasks)",
    )
    task_verify_parser.add_argument(
        "--max-turns",
        type=int,
        default=10,
        help="Maximum number of turns for task verification (default: 10)",
    )
    task_verify_parser.add_argument(
        "--prompt-file",
        type=str,
        help='JSON file containing system message (format: {"system": "..."})',
    )
    task_verify_parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Run in non-interactive mode (automatically handle file conflicts)",
    )
    task_verify_parser.set_defaults(func=task_verifier)

    # Data Format Converter subcommand
    task_conv_parser = subparsers.add_parser(
        "convert-data",
        help="Convert data to different formats (e.g., XLAM) as a single file",
        parents=[common_parser],
    )
    task_conv_parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Input file path with tasks (JSONL or JSON)",
    )
    task_conv_parser.add_argument(
        "--output", type=str, required=True, help="Output file path for converted data"
    )
    task_conv_parser.add_argument(
        "--prefix",
        type=str,
        default="task",
        help="Prefix for unique trajectory IDs (default: task)",
    )
    task_conv_parser.add_argument(
        "--split",
        type=str,
        default="train",
        help="Dataset split (train, test, val) (default: train)",
    )
    task_conv_parser.add_argument(
        "--task-id",
        type=str,
        help="Task ID to extract from evaluation results (only for single JSON file input)",
    )
    task_conv_parser.add_argument(
        "--system-message",
        type=str,
        default="You are a helpful assistant that can use tools to complete tasks.",
        help="Default system message to use as task instruction and conversation system message",
    )
    task_conv_parser.add_argument(
        "--prompt-file",
        type=str,
        help='JSON file containing system message (format: {"system": "..."})',
    )
    task_conv_parser.set_defaults(func=data_converter)

    # Data Splitter subcommand
    split_parser = subparsers.add_parser(
        "split-data", help="Randomly split JSONL task file into train/valid/test sets"
    )
    split_parser.add_argument(
        "--input", type=str, required=True, help="Input JSONL file path to split"
    )
    split_parser.add_argument(
        "--output-dir",
        type=str,
        help="Output directory for split files (default: current directory)",
    )
    split_parser.add_argument(
        "--train-ratio",
        type=float,
        default=0.7,
        help="Ratio of data for training set (default: 0.7)",
    )
    split_parser.add_argument(
        "--valid-ratio",
        type=float,
        default=0.15,
        help="Ratio of data for validation set (default: 0.15)",
    )
    split_parser.add_argument(
        "--test-ratio",
        type=float,
        default=0.15,
        help="Ratio of data for test set (default: 0.15)",
    )
    split_parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible splits (default: 42)",
    )
    split_parser.set_defaults(func=data_splitter)

    # Model Evaluator subcommand
    eval_parser = subparsers.add_parser(
        "evaluate",
        help="Evaluate models using MCP servers and tasks",
        parents=[common_parser],
    )
    # Server connection arguments - support multiple servers with optional arguments
    eval_parser.add_argument(
        "--servers",
        type=str,
        nargs="+",
        help="Server paths to connect to. Format: server_path[:args][^env_vars] where args is comma-separated and env_vars is KEY=value,KEY2=value2. "
        "Examples: @modelcontextprotocol/server-fetch, "
        "@openbnb/mcp-server-airbnb:--ignore-robots-txt, "
        "server1^API_KEY=key123, "
        "server2:--flag1,--flag2^ENV_VAR=value1,ENV_VAR2=value2",
    )

    eval_parser.add_argument(
        "--tasks-file",
        type=str,
        required=True,
        help="Path to the JSONL file containing tasks for evaluation",
    )
    eval_parser.add_argument(
        "--model",
        type=str,
        default="gpt-4o",
        help="Model to evaluate (default: gpt-4o)",
    )
    eval_parser.add_argument(
        "--output",
        type=str,
        default="evaluation_results.jsonl",
        help="Output file path for evaluation results (default: evaluation_results.jsonl)",
    )
    eval_parser.add_argument(
        "--num-tasks",
        type=int,
        default=-1,
        help="Number of tasks to evaluate (default: all tasks)",
    )
    eval_parser.add_argument(
        "--max-turns",
        type=int,
        default=30,
        help="Maximum number of turns for task execution (default: 30)",
    )
    eval_parser.add_argument(
        "--force-rerun",
        action="store_true",
        help="Force rerun all tasks even if already tested",
    )
    eval_parser.add_argument(
        "--prompt-file",
        type=str,
        help='JSON file containing system message (format: {"system": "..."})',
    )
    eval_parser.add_argument(
        "--client-type",
        type=str,
        choices=["gateway", "openai"],
        default="openai",
        help='Type of client to use (default: openai) - "gateway" for XLAM, "openai" for OpenAI',
    )
    eval_parser.add_argument(
        "--model-config",
        type=str,
        help='Path to JSON file containing model configuration (e.g., {"api_key": "...", "base_url": "...", "temperature": 0.1})',
    )
    eval_parser.set_defaults(func=model_evaluator)

    # Analyzer subcommand
    analyze_parser = subparsers.add_parser(
        "analyze", help="Analyze evaluation results against ground truth"
    )
    analyze_parser.add_argument(
        "--predictions",
        type=str,
        required=True,
        help="Path to predictions JSON file (e.g., evaluation_results.json)",
    )
    analyze_parser.add_argument(
        "--ground-truth",
        type=str,
        required=True,
        help="Path to ground truth JSONL/JSON file",
    )
    analyze_parser.add_argument(
        "--evaluation-output",
        type=str,
        default=None,
        help="Path to save task-level metrics (default: <predictions>_task_metrics.json)",
    )
    analyze_parser.add_argument(
        "--analysis-output",
        type=str,
        default=None,
        help="Path to save summary analysis (default: <predictions>_summary_analysis.json)",
    )
    # Weight customization options
    analyze_parser.add_argument(
        "--name-weight",
        type=float,
        default=0.4,
        help="Weight for tool name matching (default: 0.4)",
    )
    analyze_parser.add_argument(
        "--params-weight",
        type=float,
        default=0.4,
        help="Weight for parameter matching (default: 0.4)",
    )
    analyze_parser.add_argument(
        "--order-weight",
        type=float,
        default=0.2,
        help="Weight for tool order matching (default: 0.2)",
    )
    # Threshold customization options
    analyze_parser.add_argument(
        "--param-threshold",
        type=float,
        default=0.6,
        help="Parameter match threshold for flexible matching (default: 0.6)",
    )
    analyze_parser.add_argument(
        "--order-threshold",
        type=float,
        default=0.5,
        help="Order match threshold for flexible matching (default: 0.5)",
    )
    # AI Report generation options
    analyze_parser.add_argument(
        "--generate-report",
        action="store_true",
        help="Generate an AI-powered performance report using OpenAI models",
    )
    analyze_parser.add_argument(
        "--report-model",
        type=str,
        default="gpt-4o",
        help="Model to use for AI report generation (default: gpt-4o)",
    )
    analyze_parser.add_argument(
        "--report-output",
        type=str,
        default=None,
        help="Path to save AI report (default: <predictions>_ai_report.md)",
    )

    # Chart generation options
    analyze_parser.add_argument(
        "--include-charts",
        action="store_true",
        help="Generate interactive charts and visualizations",
    )
    analyze_parser.add_argument(
        "--chart-formats",
        nargs="+",
        choices=["html", "png", "svg"],
        default=["html", "png"],
        help="Chart output formats (default: html png)",
    )
    analyze_parser.set_defaults(func=analyzer)

    # LLM Judger subcommand
    llm_judge_parser = subparsers.add_parser(
        "judge",
        help="Evaluate execution results using LLM judges",
        parents=[common_parser],
    )

    # Required arguments
    llm_judge_parser.add_argument(
        "--input-file", type=str, help="Path to JSON evaluation file to judge"
    )

    # Optional arguments
    llm_judge_parser.add_argument(
        "--output-dir",
        "-o",
        type=str,
        help="Directory to save judgment results (will create multiple files: combined, trajectory, completion)",
    )

    llm_judge_parser.add_argument(
        "--ground-truth",
        "-g",
        type=str,
        help="Path to ground truth JSONL/JSON file for comparison and analysis",
    )

    llm_judge_parser.add_argument(
        "--model",
        "-m",
        type=str,
        default="gpt-4o",
        help="LLM model to use for judging (default: gpt-4o)",
    )

    llm_judge_parser.add_argument(
        "--model-config",
        type=str,
        help='Path to JSON file containing model configuration (e.g., {"model": "gpt-4o", "temperature": 0.1, "max_tokens": 4000})',
    )

    llm_judge_parser.add_argument(
        "--max-samples",
        "-n",
        type=int,
        help="Maximum number of samples to evaluate (default: all)",
    )

    llm_judge_parser.add_argument(
        "--trajectory-only",
        action="store_true",
        help="Only evaluate trajectory quality (skip task completion)",
    )

    llm_judge_parser.add_argument(
        "--completion-only",
        action="store_true",
        help="Only evaluate task completion (skip trajectory)",
    )

    llm_judge_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Print detailed evaluation results"
    )

    llm_judge_parser.add_argument(
        "--prompt-file",
        "-p",
        type=str,
        help='Path to JSON file containing custom prompts (keys: "trajectory", "completion")',
    )

    llm_judge_parser.add_argument(
        "--quiet", "-q", action="store_true", help="Suppress progress output"
    )

    llm_judge_parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume evaluation from existing results (skip already processed tasks)",
    )

    llm_judge_parser.set_defaults(func=llm_judger)

    # LLM Judger Analyzer subcommand
    llm_judge_analyze_parser = subparsers.add_parser(
        "judge-rubric",
        help="Analyze LLM judgment results and generate performance reports",
    )

    # Input file options - either combined file or separate files
    llm_judge_analyze_parser.add_argument(
        "--combined-file",
        type=str,
        help="Path to combined JSONL file containing both trajectory and completion data",
    )

    llm_judge_analyze_parser.add_argument(
        "--trajectory-file", type=str, help="Path to trajectory scores JSON/JSONL file"
    )

    llm_judge_analyze_parser.add_argument(
        "--completion-file", type=str, help="Path to completion scores JSON/JSONL file"
    )

    # Optional arguments
    llm_judge_analyze_parser.add_argument(
        "--output-dir",
        "-o",
        type=str,
        help="Directory to save analysis results and AI report (default: same as input files)",
    )

    llm_judge_analyze_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print detailed analysis information",
    )

    # AI Report generation options (default: enabled)
    llm_judge_analyze_parser.add_argument(
        "--generate-report",
        type=int,
        default=1,
        choices=[0, 1],
        help="Generate AI-powered performance report: 1=enabled (default), 0=disabled (analysis only)",
    )

    llm_judge_analyze_parser.add_argument(
        "--report-model",
        type=str,
        default="gpt-4o",
        help="Model to use for AI report generation (default: gpt-4o)",
    )

    llm_judge_analyze_parser.set_defaults(func=llm_judger_analyzer)

    # Report Generation subcommand
    report_gen_parser = subparsers.add_parser(
        "report-gen",
        help="Generate AI-powered evaluation reports from analysis files",
        parents=[common_parser],
    )

    # Input files
    report_gen_parser.add_argument(
        "--tool-analysis-file",
        type=str,
        help="Path to tool usage analysis JSON file (summary analysis format)",
    )

    report_gen_parser.add_argument(
        "--llm-judge-file", type=str, help="Path to LLM judge analysis JSON file"
    )

    # Output configuration
    report_gen_parser.add_argument(
        "--output-file",
        "-o",
        type=str,
        help="Output file path for generated report (auto-generated if not specified)",
    )

    report_gen_parser.add_argument(
        "--model-name",
        type=str,
        help="Name of the model being analyzed (extracted from filename if not specified)",
    )

    # Report generation options
    report_gen_parser.add_argument(
        "--model",
        "-m",
        type=str,
        default="gpt-4o",
        help="OpenAI model to use for report generation (default: gpt-4o)",
    )

    # Chart options
    report_gen_parser.add_argument(
        "--include-charts",
        action="store_true",
        help="Include charts in the report (default: enabled)",
    )

    report_gen_parser.add_argument(
        "--no-charts", action="store_true", help="Disable chart generation"
    )

    report_gen_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Print detailed information"
    )

    report_gen_parser.set_defaults(func=report_generator)

    # Auto Workflow subcommand
    auto_parser = subparsers.add_parser(
        "auto",
        help="Automatically run complete evaluation workflow (generate, verify, evaluate, analyze)",
        parents=[common_parser],
    )

    # Required arguments
    auto_parser.add_argument(
        "--servers",
        type=str,
        nargs="+",
        required=True,
        help="Server paths to connect to. Format: server_path[:args][^env_vars] where args is comma-separated and env_vars is KEY=value,KEY2=value2. "
        "Examples: @modelcontextprotocol/server-fetch, "
        "@openbnb/mcp-server-airbnb:--ignore-robots-txt, "
        "server1^API_KEY=key123, "
        "server2:--flag1,--flag2^ENV_VAR=value1,ENV_VAR2=value2",
    )

    auto_parser.add_argument(
        "--working-dir",
        type=str,
        required=True,
        help="Working directory to create and use for all operations",
    )

    auto_parser.add_argument(
        "--task-model",
        type=str,
        default="gpt-4.1-2025-04-14",
        help="Model to use for task generation and verification (default: gpt-4.1-2025-04-14)",
    )

    auto_parser.add_argument(
        "--eval-model-configs",
        type=str,
        nargs="+",
        required=True,
        help="Paths to model configuration JSON files for evaluation (e.g., eval_models/gpt-4o.json eval_models/gpt-4o-mini.json)",
    )

    # Optional arguments

    auto_parser.add_argument(
        "--num-tasks",
        type=int,
        default=200,
        help="Number of tasks to generate (default: 200)",
    )

    auto_parser.add_argument(
        "--max-turns",
        type=int,
        default=30,
        help="Maximum number of turns for task execution (default: 30)",
    )

    # Prompt files
    auto_parser.add_argument(
        "--task-generation-prompt",
        type=str,
        help="JSON file containing system and user messages for task generation",
    )

    auto_parser.add_argument(
        "--task-verification-prompt",
        type=str,
        help="JSON file containing system message for task verification",
    )

    auto_parser.add_argument(
        "--evaluation-prompt",
        type=str,
        help="JSON file containing system message for evaluation",
    )

    # LLM Judging options
    auto_parser.add_argument(
        "--enable-llm-judge",
        action="store_true",
        help="Enable LLM judging after evaluation (default: disabled)",
    )

    auto_parser.add_argument(
        "--llm-judge-model",
        type=str,
        default="gpt-4o",
        help="Model to use for LLM judging (default: gpt-4o)",
    )

    auto_parser.set_defaults(func=auto_workflow)

    return parser.parse_args()


def main():
    """Main entry point for the CLI."""
    # Show banner
    print_banner()

    try:
        args = parse_arguments()

        # Set API key in environment if provided
        if hasattr(args, "api_key") and args.api_key:
            os.environ["OPENAI_API_KEY"] = args.api_key
            colored_print("✓ API key set from command line", Colors.GREEN)

        # Show what command is being executed
        command_colors = {
            "generate-tasks": Colors.BRIGHT_YELLOW,
            "verify-tasks": Colors.BRIGHT_BLUE,
            "convert-data": Colors.BRIGHT_MAGENTA,
            "split-data": Colors.BRIGHT_RED,
            "evaluate": Colors.BRIGHT_GREEN,
            "analyze": Colors.BRIGHT_CYAN,
            "judge": Colors.BRIGHT_MAGENTA,
            "judge-rubric": Colors.BRIGHT_CYAN,
            "auto": Colors.BRIGHT_GREEN,
        }
        command_color = command_colors.get(args.command, Colors.BRIGHT_WHITE)
        colored_print(f"🚀 Executing: {args.command}", command_color, bold=True)

        # Execute the command
        args.func(args)

        # Success message
        colored_print(
            f"✅ Command '{args.command}' completed successfully!",
            Colors.BRIGHT_GREEN,
            bold=True,
        )

    except KeyboardInterrupt:
        colored_print(
            "\n⚠️  Operation interrupted by user", Colors.BRIGHT_YELLOW, bold=True
        )
        sys.exit(1)
    except Exception as e:
        colored_print(f"❌ Error: {str(e)}", Colors.BRIGHT_RED, bold=True)
        logger.exception("Detailed error information:")
        sys.exit(1)


if __name__ == "__main__":
    main()
