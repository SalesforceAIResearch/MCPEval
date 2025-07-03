#!/usr/bin/env python3
"""
Direct execution of the LLM judger module.

Usage:
    python -m mcp_eval_llm.cli.llm_judger.judge
    python -m mcp_eval_llm.cli.main judge --help
"""

if __name__ == "__main__":
    print("For help, run:")
    print("python -m mcp_eval_llm.cli.main judge --help")
    print()
    print("Example usage:")
    print("python -m mcp_eval_llm.cli.main judge evaluation_results.json --output-dir ./results")
    print("python -m mcp_eval_llm.cli.main judge evaluation_results.json --ground-truth ground_truth.jsonl --output-dir ./results")
    print("python -m mcp_eval_llm.cli.main judge evaluation_results.json --model-config model_config.json --output-dir ./results")
    import sys
    sys.exit(1) 