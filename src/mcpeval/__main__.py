#!/usr/bin/env python3
"""
Main entry point for the MCP Eval LLM package.

This module serves as the main entry point when the package is run with:
python -m mcpeval
"""

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from mcpeval.cli.main import main

if __name__ == "__main__":
    main()
