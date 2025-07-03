#!/bin/bash

# Auto Evaluation Script for Special Calculator MCP Server
# This script uses the built-in mcp-eval auto command to run the complete evaluation pipeline

set -e  # Exit on any error

echo "🧮 Starting Auto Evaluation for Special Calculator MCP Server"
echo "=============================================================="

# Configuration
SERVER="mcp_servers/special_calculator/server.py"
WORKING_DIR="benchmarks/special_calculator/auto_results_$(date +%Y%m%d_%H%M%S)"
TASK_MODEL="gpt-4.1-2025-04-14"
NUM_TASKS=3
MAX_TURNS=30

# Prompt files
TASK_GENERATION_PROMPT="benchmarks/special_calculator/data_generation/task_generation_prompt.json"
TASK_VERIFICATION_PROMPT="benchmarks/special_calculator/data_generation/task_verification_prompt.json"
EVALUATION_PROMPT="benchmarks/special_calculator/evaluation_prompt.json"

# Model configurations to evaluate
MODEL_CONFIGS=(
    "benchmarks/special_calculator/eval_models/gpt-4o.json"
    "benchmarks/special_calculator/eval_models/gpt-4o-mini.json"
    "benchmarks/special_calculator/eval_models/gpt-4.1-mini.json"
    "benchmarks/special_calculator/eval_models/gpt-4.1-nano.json"
    "benchmarks/special_calculator/eval_models/o3.json"
    "benchmarks/special_calculator/eval_models/o3-mini.json"
    "benchmarks/special_calculator/eval_models/o4-mini.json"
)

# Check if model config files exist
echo "📋 Checking model configurations..."
EXISTING_CONFIGS=()
for config in "${MODEL_CONFIGS[@]}"; do
    if [[ -f "$config" ]]; then
        EXISTING_CONFIGS+=("$config")
        echo "  ✓ Found: $(basename "$config")"
    else
        echo "  ⚠ Missing: $(basename "$config")"
    fi
done

if [[ ${#EXISTING_CONFIGS[@]} -eq 0 ]]; then
    echo "❌ No model configuration files found. Please ensure eval_models directory contains JSON config files."
    exit 1
fi

echo "📊 Will evaluate ${#EXISTING_CONFIGS[@]} model(s)"

# Check if prompt files exist
echo "📝 Checking prompt files..."
for prompt_file in "$TASK_GENERATION_PROMPT" "$TASK_VERIFICATION_PROMPT" "$EVALUATION_PROMPT"; do
    if [[ -f "$prompt_file" ]]; then
        echo "  ✓ Found: $(basename "$prompt_file")"
    else
        echo "  ⚠ Missing: $(basename "$prompt_file")"
    fi
done

# Create the working directory
echo "📁 Creating working directory: $WORKING_DIR"
mkdir -p "$WORKING_DIR"

# Build the mcp-eval auto command
echo "🚀 Building automation command..."
CMD=(
    "mcp-eval" "auto"
    "--servers" "$SERVER"
    "--working-dir" "$WORKING_DIR"
    "--task-model" "$TASK_MODEL"
    "--eval-model-configs" "${EXISTING_CONFIGS[@]}"
    "--num-tasks" "$NUM_TASKS"
    "--max-turns" "$MAX_TURNS"
)

# Add prompt files if they exist
if [[ -f "$TASK_GENERATION_PROMPT" ]]; then
    CMD+=("--task-generation-prompt" "$TASK_GENERATION_PROMPT")
fi

if [[ -f "$TASK_VERIFICATION_PROMPT" ]]; then
    CMD+=("--task-verification-prompt" "$TASK_VERIFICATION_PROMPT")
fi

if [[ -f "$EVALUATION_PROMPT" ]]; then
    CMD+=("--evaluation-prompt" "$EVALUATION_PROMPT")
fi

# Optional: Enable LLM judging (uncomment the next line to enable)
# CMD+=("--enable-llm-judge" "--llm-judge-model" "gpt-4o")

echo "🎯 Running complete evaluation pipeline..."
echo "Command: ${CMD[*]}"
echo ""

# Execute the command
"${CMD[@]}"

# Final summary
echo ""
echo "🎉 Auto evaluation completed!"
echo "📊 Results are available in: $WORKING_DIR"
echo "   - Raw data: $WORKING_DIR/data/"
echo "   - Evaluation results: $WORKING_DIR/results/"
echo "   - Analysis reports: $WORKING_DIR/report/"
echo "   - Execution logs: $WORKING_DIR/logs/"
echo ""
echo "💡 To view a specific report:"
echo "   ls $WORKING_DIR/report/"
echo "   cat $WORKING_DIR/report/<model_name>_report.md"
