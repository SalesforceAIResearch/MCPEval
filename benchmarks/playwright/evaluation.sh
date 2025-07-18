#!/bin/bash

# Playwright MCP Server Evaluation Script
# This script evaluates different models on Playwright browser automation tasks

echo "Starting Playwright MCP Server evaluation..."

# Set up directories
mkdir -p data/playwright
mkdir -p benchmarks/playwright/results
mkdir -p benchmarks/playwright/report

# Step 1: Generate tasks
echo "Step 1: Generating tasks..."
mcp-eval generate-tasks --server @playwright/mcp --model gpt-4.1-2025-04-14 --num-tasks 600 --prompt-file benchmarks/playwright/data_generation/task_generation_prompt.json --output data/playwright/evaluation_tasks.jsonl

# Step 2: Verify tasks
echo "Step 2: Verifying tasks..."
mcp-eval verify-tasks --server @playwright/mcp --tasks-file data/playwright/evaluation_tasks.jsonl --model gpt-4.1-2025-04-14 --output data/playwright/evaluation_tasks_verified.jsonl --prompt-file benchmarks/playwright/data_generation/task_verification_prompt.json --num-tasks 500

# Step 3: Evaluate models
echo "Step 3: Evaluating models..."

# Evaluate GPT-4o
echo "Evaluating GPT-4o..."
mcp-eval evaluate --server @playwright/mcp --model-config benchmarks/playwright/eval_models/gpt-4o.json --tasks-file data/playwright/evaluation_tasks_verified.jsonl --output benchmarks/playwright/results/gpt4o_mix_task_evaluation.json --prompt-file benchmarks/playwright/evaluation_prompt.json --max-turns 30

# Evaluate GPT-4o-mini
echo "Evaluating GPT-4o-mini..."
mcp-eval evaluate --server @playwright/mcp --model-config benchmarks/playwright/eval_models/gpt-4o-mini.json --tasks-file data/playwright/evaluation_tasks_verified.jsonl --output benchmarks/playwright/results/gpt4o-mini_mix_task_evaluation.json --prompt-file benchmarks/playwright/evaluation_prompt.json --max-turns 30

# Evaluate GPT-4.1-mini
echo "Evaluating GPT-4.1-mini..."
mcp-eval evaluate --server @playwright/mcp --model-config benchmarks/playwright/eval_models/gpt-4.1-mini.json --tasks-file data/playwright/evaluation_tasks_verified.jsonl --output benchmarks/playwright/results/gpt-4.1-mini_mix_task_evaluation.json --prompt-file benchmarks/playwright/evaluation_prompt.json --max-turns 30

# Evaluate GPT-4.1-nano
echo "Evaluating GPT-4.1-nano..."
mcp-eval evaluate --server @playwright/mcp --model-config benchmarks/playwright/eval_models/gpt-4.1-nano.json --tasks-file data/playwright/evaluation_tasks_verified.jsonl --output benchmarks/playwright/results/gpt-4.1-nano_mix_task_evaluation.json --prompt-file benchmarks/playwright/evaluation_prompt.json --max-turns 30

# Evaluate O3-mini
echo "Evaluating O3-mini..."
mcp-eval evaluate --server @playwright/mcp --model-config benchmarks/playwright/eval_models/o3-mini.json --tasks-file data/playwright/evaluation_tasks_verified.jsonl --output benchmarks/playwright/results/o3-mini_mix_task_evaluation.json --prompt-file benchmarks/playwright/evaluation_prompt.json --max-turns 30

echo "Evaluation completed! Results saved in benchmarks/playwright/results/"
echo "Reports saved in benchmarks/playwright/report/" 