#!/bin/bash

# Run LLM judge evaluation for all task evaluation files
echo "🧠 Running LLM judge evaluation for all models..."

# GPT-4o
echo "Processing gpt4o..."
mcp-eval judge --input-file benchmarks/travel_assistant/results/gpt4o_mix_task_evaluation.json --output-dir benchmarks/travel_assistant/results --model gpt-4o

echo "Analyzing gpt4o..."
mcp-eval judge-rubric \
    --trajectory-file benchmarks/travel_assistant/results/gpt4o_mix_task_evaluation_trajectory.json \
    --completion-file benchmarks/travel_assistant/results/gpt4o_mix_task_evaluation_completion.json \
    --output-dir benchmarks/travel_assistant/report

# GPT-4.1-mini
echo "Processing gpt4.1-mini..."
mcp-eval judge --input-file benchmarks/travel_assistant/results/gpt4.1-mini_mix_task_evaluation.json --output-dir benchmarks/travel_assistant/results --model gpt-4o

echo "Analyzing gpt4.1-mini..."
mcp-eval judge-rubric \
    --trajectory-file benchmarks/travel_assistant/results/gpt4.1-mini_mix_task_evaluation_trajectory.json \
    --completion-file benchmarks/travel_assistant/results/gpt4.1-mini_mix_task_evaluation_completion.json \
    --output-dir benchmarks/travel_assistant/report

# GPT-4.1-nano
echo "Processing gpt4.1-nano..."
mcp-eval judge --input-file benchmarks/travel_assistant/results/gpt4.1-nano_mix_task_evaluation.json --output-dir benchmarks/travel_assistant/results --model gpt-4o --resume

echo "Analyzing gpt4.1-nano..."
mcp-eval judge-rubric \
    --trajectory-file benchmarks/travel_assistant/results/gpt4.1-nano_mix_task_evaluation_trajectory.json \
    --completion-file benchmarks/travel_assistant/results/gpt4.1-nano_mix_task_evaluation_completion.json \
    --output-dir benchmarks/travel_assistant/report

# GPT-4o-mini
echo "Processing gpt4o-mini..."
mcp-eval judge --input-file benchmarks/travel_assistant/results/gpt4o-mini_mix_task_evaluation.json --output-dir benchmarks/travel_assistant/results --model gpt-4o

echo "Analyzing gpt4o-mini..."
mcp-eval judge-rubric \
    --trajectory-file benchmarks/travel_assistant/results/gpt4o-mini_mix_task_evaluation_trajectory.json \
    --completion-file benchmarks/travel_assistant/results/gpt4o-mini_mix_task_evaluation_completion.json \
    --output-dir benchmarks/travel_assistant/report

# O3
echo "Processing o3..."
mcp-eval judge --input-file benchmarks/travel_assistant/results/o3_mix_task_evaluation.json --output-dir benchmarks/travel_assistant/results --model gpt-4o

echo "Analyzing o3..."
mcp-eval judge-rubric \
    --trajectory-file benchmarks/travel_assistant/results/o3_mix_task_evaluation_trajectory.json \
    --completion-file benchmarks/travel_assistant/results/o3_mix_task_evaluation_completion.json \
    --output-dir benchmarks/travel_assistant/report

# O3-mini
echo "Processing o3-mini..."
mcp-eval judge --input-file benchmarks/travel_assistant/results/o3-mini_mix_task_evaluation.json --output-dir benchmarks/travel_assistant/results --model gpt-4o

echo "Analyzing o3-mini..."
mcp-eval judge-rubric \
    --trajectory-file benchmarks/travel_assistant/results/o3-mini_mix_task_evaluation_trajectory.json \
    --completion-file benchmarks/travel_assistant/results/o3-mini_mix_task_evaluation_completion.json \
    --output-dir benchmarks/travel_assistant/report

# O4-mini
echo "Processing o4-mini..."
mcp-eval judge --input-file benchmarks/travel_assistant/results/o4-mini_mix_task_evaluation.json --output-dir benchmarks/travel_assistant/results --model gpt-4o

echo "Analyzing o4-mini..."
mcp-eval judge-rubric \
    --trajectory-file benchmarks/travel_assistant/results/o4-mini_mix_task_evaluation_trajectory.json \
    --completion-file benchmarks/travel_assistant/results/o4-mini_mix_task_evaluation_completion.json \
    --output-dir benchmarks/travel_assistant/report

# xlam_2_32b
echo "Processing xlam_2_32b..."
nohup mcp-eval judge --input-file benchmarks/travel_assistant/results/xlam_2_32b_mix_task_evaluation.json --output-dir benchmarks/travel_assistant/results --model gpt-4o > benchmarks/travel_assistant/logs/xlam_2_32b_mix_task_evaluation.log 2>&1 &

echo "Analyzing xlam_2_32b..."
nohup mcp-eval judge-rubric \
    --trajectory-file benchmarks/travel_assistant/results/xlam_2_32b_mix_task_evaluation_trajectory.json \
    --completion-file benchmarks/travel_assistant/results/xlam_2_32b_mix_task_evaluation_completion.json \
    --output-dir benchmarks/travel_assistant/report > benchmarks/travel_assistant/logs/xlam_2_32b_evaluation_tasks_verified_report.log 2>&1 &

# xlam_2_70b
echo "Processing xlam_2_70b..."
nohup mcp-eval judge --input-file benchmarks/travel_assistant/results/xlam_2_70b_mix_task_evaluation.json --output-dir benchmarks/travel_assistant/results --model gpt-4o > benchmarks/travel_assistant/logs/xlam_2_70b_mix_task_evaluation.log 2>&1 &

echo "Analyzing xlam_2_70b..."
nohup mcp-eval judge-rubric \
    --trajectory-file benchmarks/travel_assistant/results/xlam_2_70b_mix_task_evaluation_trajectory.json \
    --completion-file benchmarks/travel_assistant/results/xlam_2_70b_mix_task_evaluation_completion.json \
    --output-dir benchmarks/travel_assistant/report > benchmarks/travel_assistant/logs/xlam_2_70b_evaluation_tasks_verified_report.log 2>&1 &

echo "✅ LLM judge evaluation and analysis completed for all models!" 