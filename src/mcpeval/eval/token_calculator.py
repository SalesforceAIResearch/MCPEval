#!/usr/bin/env python3
"""
Token Calculator for MCP Eval LLM

This module provides utilities to calculate token consumption and costs from
evaluation task conversations.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import tiktoken

logger = logging.getLogger(__name__)

# Model pricing per 1K tokens (input, output)
MODEL_PRICING = {
    "gpt-4o": (0.0025, 0.01),
    "gpt-4o-mini": (0.00015, 0.0006),
    "gpt-4": (0.03, 0.06),
    "gpt-4-turbo": (0.01, 0.03),
    "gpt-3.5-turbo": (0.0015, 0.002),
    "claude-3-sonnet": (0.003, 0.015),
    "claude-3-haiku": (0.00025, 0.00125),
    "claude-3-opus": (0.015, 0.075),
    "claude-3.5-sonnet": (0.003, 0.015),
    "claude-3.5-haiku": (0.001, 0.005),
    "gemini-pro": (0.00075, 0.0015),
    "gemini-1.5-pro": (0.00125, 0.00375),
    "gemini-1.5-flash": (0.000075, 0.0003),
    "grok-4-0709": (0.003, 0.015),  # $3/Million input, $15/Million output
    "default": (0.001, 0.002),  # Default fallback pricing
}


def get_tokenizer(model_name: str = "gpt-4") -> tiktoken.Encoding:
    """Get the appropriate tokenizer for the model."""
    try:
        if "gpt-4" in model_name.lower():
            return tiktoken.encoding_for_model("gpt-4")
        elif "gpt-3.5" in model_name.lower():
            return tiktoken.encoding_for_model("gpt-3.5-turbo")
        else:
            # Default to gpt-4 tokenizer for other models
            return tiktoken.encoding_for_model("gpt-4")
    except Exception as e:
        logger.warning(f"Could not get tokenizer for {model_name}, using default: {e}")
        return tiktoken.encoding_for_model("gpt-4")


def count_tokens(text: str, model_name: str = "gpt-4") -> int:
    """Count tokens in a text string using the appropriate tokenizer."""
    if not text:
        return 0

    try:
        tokenizer = get_tokenizer(model_name)
        return len(tokenizer.encode(text))
    except Exception as e:
        logger.warning(f"Error counting tokens: {e}")
        # Fallback: rough estimate (1 token ≈ 4 chars)
        return len(text) // 4


def extract_assistant_outputs(
    conversation: List[Dict[str, Any]],
) -> Tuple[List[str], List[str]]:
    """
    Extract assistant text outputs and tool calls from conversation.

    Args:
        conversation: List of conversation messages

    Returns:
        Tuple of (text_outputs, tool_calls_text)
    """
    text_outputs = []
    tool_calls_text = []

    for entry in conversation:
        if entry.get("role") == "assistant":
            # Extract text content
            content = entry.get("content")
            if content and isinstance(content, str):
                text_outputs.append(content)

            # Extract tool calls
            tool_calls = entry.get("tool_calls", [])
            if tool_calls:
                for tool_call in tool_calls:
                    if isinstance(tool_call, dict) and "function" in tool_call:
                        function_data = tool_call["function"]
                        # Include function name and arguments as text
                        tool_text = f"Function: {function_data.get('name', '')}\nArguments: {function_data.get('arguments', '')}"
                        tool_calls_text.append(tool_text)

    return text_outputs, tool_calls_text


def calculate_conversation_tokens(
    conversation: List[Dict[str, Any]], model_name: str = "gpt-4"
) -> Dict[str, int]:
    """
    Calculate token consumption for a conversation.

    Args:
        conversation: List of conversation messages
        model_name: Name of the model for tokenization

    Returns:
        Dict with token counts
    """
    text_outputs, tool_calls_text = extract_assistant_outputs(conversation)

    # Count tokens for text outputs
    text_tokens = sum(count_tokens(text, model_name) for text in text_outputs)

    # Count tokens for tool calls
    tool_tokens = sum(
        count_tokens(tool_text, model_name) for tool_text in tool_calls_text
    )

    # Calculate input tokens (everything except assistant output)
    input_text_parts = []
    for entry in conversation:
        role = entry.get("role", "")
        content = entry.get("content")

        if role == "system" and content:
            input_text_parts.append(content)
        elif role == "user" and content:
            input_text_parts.append(content)
        elif role == "tool" and content:
            input_text_parts.append(content)

    input_tokens = sum(count_tokens(text, model_name) for text in input_text_parts)

    return {
        "input_tokens": input_tokens,
        "output_tokens": text_tokens + tool_tokens,
        "output_text_tokens": text_tokens,
        "output_tool_tokens": tool_tokens,
        "total_tokens": input_tokens + text_tokens + tool_tokens,
    }


def calculate_cost(input_tokens: int, output_tokens: int, model_name: str) -> float:
    """
    Calculate cost based on token usage and model pricing.

    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        model_name: Name of the model

    Returns:
        Total cost in USD
    """
    # Find the best matching model in pricing
    model_key = None
    for key in MODEL_PRICING.keys():
        if key in model_name.lower():
            model_key = key
            break

    if not model_key:
        model_key = "default"
        logger.warning(
            f"Model '{model_name}' not found in pricing, using default pricing"
        )

    input_price, output_price = MODEL_PRICING[model_key]

    # Calculate cost (pricing is per 1K tokens)
    input_cost = (input_tokens / 1000) * input_price
    output_cost = (output_tokens / 1000) * output_price

    return input_cost + output_cost


def process_evaluation_file(
    file_path: str, model_name: str = "gpt-4"
) -> Dict[str, Any]:
    """
    Process an evaluation JSONL file and calculate token consumption and costs.

    Args:
        file_path: Path to the evaluation JSONL file
        model_name: Name of the model for tokenization and pricing

    Returns:
        Dict with aggregated statistics
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    total_stats = {
        "total_tasks": 0,
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "total_output_text_tokens": 0,
        "total_output_tool_tokens": 0,
        "total_tokens": 0,
        "total_cost": 0.0,
        "model_name": model_name,
        "tasks_details": [],
    }

    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            try:
                data = json.loads(line.strip())

                if "conversation" not in data:
                    logger.warning(f"Line {line_num}: No conversation found")
                    continue

                conversation = data["conversation"]
                token_stats = calculate_conversation_tokens(conversation, model_name)

                cost = calculate_cost(
                    token_stats["input_tokens"],
                    token_stats["output_tokens"],
                    model_name,
                )

                task_detail = {
                    "line_number": line_num,
                    "task_id": data.get("task_id", f"task_{line_num}"),
                    **token_stats,
                    "cost": cost,
                }

                total_stats["tasks_details"].append(task_detail)
                total_stats["total_tasks"] += 1
                total_stats["total_input_tokens"] += token_stats["input_tokens"]
                total_stats["total_output_tokens"] += token_stats["output_tokens"]
                total_stats["total_output_text_tokens"] += token_stats[
                    "output_text_tokens"
                ]
                total_stats["total_output_tool_tokens"] += token_stats[
                    "output_tool_tokens"
                ]
                total_stats["total_tokens"] += token_stats["total_tokens"]
                total_stats["total_cost"] += cost

            except json.JSONDecodeError as e:
                logger.error(f"Line {line_num}: Invalid JSON - {e}")
                continue
            except Exception as e:
                logger.error(f"Line {line_num}: Error processing task - {e}")
                continue

    return total_stats


def print_summary(stats: Dict[str, Any]) -> None:
    """Print a summary of token consumption and costs."""
    print(f"\n=== Token Consumption Summary ===")
    print(f"Model: {stats['model_name']}")
    print(f"Total Tasks: {stats['total_tasks']:,}")
    print(f"\nToken Usage:")
    print(f"  Input Tokens: {stats['total_input_tokens']:,}")
    print(f"  Output Tokens: {stats['total_output_tokens']:,}")
    print(f"    - Text Output: {stats['total_output_text_tokens']:,}")
    print(f"    - Tool Calls: {stats['total_output_tool_tokens']:,}")
    print(f"  Total Tokens: {stats['total_tokens']:,}")
    print(f"\nCost Analysis:")
    print(f"  Total Cost: ${stats['total_cost']:.4f}")
    print(
        f"  Average Cost per Task: ${stats['total_cost'] / max(stats['total_tasks'], 1):.4f}"
    )
    print(
        f"  Cost per 1K Tokens: ${stats['total_cost'] / max(stats['total_tokens'] / 1000, 1):.4f}"
    )


def main():
    """Main function for command-line usage."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Calculate token consumption and costs from evaluation files"
    )
    parser.add_argument("file_path", help="Path to the evaluation JSONL file")
    parser.add_argument(
        "--model", default="gpt-4", help="Model name for tokenization and pricing"
    )
    parser.add_argument("--output", help="Output file for detailed results (JSON)")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    try:
        stats = process_evaluation_file(args.file_path, args.model)
        print_summary(stats)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
            print(f"\nDetailed results saved to: {args.output}")

    except Exception as e:
        logger.error(f"Error processing file: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
