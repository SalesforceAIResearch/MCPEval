#!/bin/bash
# Convenience script to recreate and activate a virtual environment using uv and pyproject.toml
#
# Usage:
#   ./scripts/run_uv.sh         # installs main dependencies
#   DEV=1 ./scripts/run_uv.sh   # installs main + dev dependencies

# Exit on error
set -e

# Get the directory of the script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to the repository root
cd "$REPO_ROOT"

echo "Removing existing virtual environment if it exists..."
rm -rf .venv

echo "Creating new virtual environment..."
uv venv .venv

if [ "$DEV" = "1" ]; then
    echo "Installing main and dev dependencies from pyproject.toml..."
    uv pip install -e .[dev]
else
    echo "Installing main dependencies from pyproject.toml..."
    uv pip install -e .
fi

echo "Activating virtual environment..."
source .venv/bin/activate

# Print status message
echo ""
echo "Virtual environment is active!"
echo "Project: mcp_eval_llm"
echo "Python: $(python --version)"
echo "Working directory: $(pwd)"
echo ""
echo "Run 'deactivate' to exit the virtual environment."

# Execute any additional command passed to the script
if [ $# -gt 0 ]; then
    echo "Running command: $@"
    "$@"
fi 