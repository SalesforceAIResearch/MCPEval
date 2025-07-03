"""
Main entry point for executing the mcp_task_verifier module.

This redirects to the main CLI.
"""

if __name__ == "__main__":
    print("Please use the main CLI instead:")
    print("python -m mcp_eval_llm.cli.main verify-tasks --help")
    import sys
    sys.exit(1) 