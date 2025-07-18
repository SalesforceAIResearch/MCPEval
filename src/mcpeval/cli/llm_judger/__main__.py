#!/usr/bin/env python3
"""
Direct execution of the LLM judger module.

Usage:
    python -m mcpeval.cli.llm_judger.judge
    python -m mcpeval.cli.main judge --help
"""

if __name__ == "__main__":
    print("For help, run:")
    print("python -m mcpeval.cli.main judge --help")
    print()
    print("Example usage:")
    print(
        "python -m mcpeval.cli.main judge evaluation_results.json --output-dir ./results"
    )
    print(
        "python -m mcpeval.cli.main judge evaluation_results.json --ground-truth ground_truth.jsonl --output-dir ./results"
    )
    print(
        "python -m mcpeval.cli.main judge evaluation_results.json --model-config model_config.json --output-dir ./results"
    )
    import sys

    sys.exit(1)
