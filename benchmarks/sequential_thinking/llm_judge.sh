#!/bin/bash

# Run LLM judge evaluation for all task evaluation files
echo "🧠 Running LLM judge evaluation for all models..."

# GPT-4o
echo "Processing gpt4o..."
mcp-eval judge --input-file benchmarks/sequential_thinking/results/gpt4o_mix_task_evaluation.json --output-dir benchmarks/sequential_thinking/results --model gpt-4o

echo "Analyzing gpt4o..."
mcp-eval judge-rubric \
    --trajectory-file benchmarks/sequential_thinking/results/gpt4o_mix_task_evaluation_trajectory.json \
    --completion-file benchmarks/sequential_thinking/results/gpt4o_mix_task_evaluation_completion.json \
    --output-dir benchmarks/sequential_thinking/report

# GPT-4.1-mini
echo "Processing gpt4.1-mini..."
mcp-eval judge --input-file benchmarks/sequential_thinking/results/gpt4.1-mini_mix_task_evaluation.json --output-dir benchmarks/sequential_thinking/results --model gpt-4o

echo "Analyzing gpt4.1-mini..."
mcp-eval judge-rubric \
    --trajectory-file benchmarks/sequential_thinking/results/gpt4.1-mini_mix_task_evaluation_trajectory.json \
    --completion-file benchmarks/sequential_thinking/results/gpt4.1-mini_mix_task_evaluation_completion.json \
    --output-dir benchmarks/sequential_thinking/report

# GPT-4.1-nano
echo "Processing gpt4.1-nano..."
mcp-eval judge --input-file benchmarks/sequential_thinking/results/gpt4.1-nano_mix_task_evaluation.json --output-dir benchmarks/sequential_thinking/results --model gpt-4o --resume

echo "Analyzing gpt4.1-nano..."
mcp-eval judge-rubric \
    --trajectory-file benchmarks/sequential_thinking/results/gpt4.1-nano_mix_task_evaluation_trajectory.json \
    --completion-file benchmarks/sequential_thinking/results/gpt4.1-nano_mix_task_evaluation_completion.json \
    --output-dir benchmarks/sequential_thinking/report

# GPT-4o-mini
echo "Processing gpt4o-mini..."
mcp-eval judge --input-file benchmarks/sequential_thinking/results/gpt4o-mini_mix_task_evaluation.json --output-dir benchmarks/sequential_thinking/results --model gpt-4o

echo "Analyzing gpt4o-mini..."
mcp-eval judge-rubric \
    --trajectory-file benchmarks/sequential_thinking/results/gpt4o-mini_mix_task_evaluation_trajectory.json \
    --completion-file benchmarks/sequential_thinking/results/gpt4o-mini_mix_task_evaluation_completion.json \
    --output-dir benchmarks/sequential_thinking/report

# O3
echo "Processing o3..."
mcp-eval judge --input-file benchmarks/sequential_thinking/results/o3_mix_task_evaluation.json --output-dir benchmarks/sequential_thinking/results --model gpt-4o

echo "Analyzing o3..."
mcp-eval judge-rubric \
    --trajectory-file benchmarks/sequential_thinking/results/o3_mix_task_evaluation_trajectory.json \
    --completion-file benchmarks/sequential_thinking/results/o3_mix_task_evaluation_completion.json \
    --output-dir benchmarks/sequential_thinking/report

# O3-mini
echo "Processing o3-mini..."
mcp-eval judge --input-file benchmarks/sequential_thinking/results/o3-mini_mix_task_evaluation.json --output-dir benchmarks/sequential_thinking/results --model gpt-4o

echo "Analyzing o3-mini..."
mcp-eval judge-rubric \
    --trajectory-file benchmarks/sequential_thinking/results/o3-mini_mix_task_evaluation_trajectory.json \
    --completion-file benchmarks/sequential_thinking/results/o3-mini_mix_task_evaluation_completion.json \
    --output-dir benchmarks/sequential_thinking/report

# O4-mini
echo "Processing o4-mini..."
mcp-eval judge --input-file benchmarks/sequential_thinking/results/o4-mini_mix_task_evaluation.json --output-dir benchmarks/sequential_thinking/results --model gpt-4o

echo "Analyzing o4-mini..."
mcp-eval judge-rubric \
    --trajectory-file benchmarks/sequential_thinking/results/o4-mini_mix_task_evaluation_trajectory.json \
    --completion-file benchmarks/sequential_thinking/results/o4-mini_mix_task_evaluation_completion.json \
    --output-dir benchmarks/sequential_thinking/report

echo "✅ LLM judge evaluation and analysis completed for all models!"
