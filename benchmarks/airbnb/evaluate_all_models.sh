#!/bin/bash

# Comprehensive evaluation script for all Airbnb models
# This script evaluates all models in the eval_models directory in parallel

echo "Starting comprehensive evaluation of all Airbnb models..."

# Define common parameters
SERVER="@openbnb/mcp-server-airbnb"
SERVER_ARGS="--ignore-robots-txt"
TASKS_FILE="data/airbnb/verified_results.jsonl"
PROMPT_FILE="benchmarks/airbnb/evaluation_prompt.json"
MAX_TURNS=30
REPORT_MODEL="gpt-4.1-2025-04-14"

# Create results and report directories
mkdir -p benchmarks/airbnb/results
mkdir -p benchmarks/airbnb/report
mkdir -p benchmarks/airbnb/logs

echo "Starting parallel evaluation of all models..."

# Run all evaluations in parallel with nohup
# echo "Evaluating GPT-4o..."
# nohup mcp-eval evaluate \
#     --server $SERVER \
#     --server-args="$SERVER_ARGS" \
#     --model-config benchmarks/airbnb/eval_models/gpt-4o.json \
#     --tasks-file $TASKS_FILE \
#     --output benchmarks/airbnb/results/gpt4o_task_evaluation.json \
#     --prompt-file $PROMPT_FILE \
#     --max-turns $MAX_TURNS > benchmarks/airbnb/logs/gpt4o_eval.log 2>&1 &

# echo "Evaluating GPT-4o-mini..."
# nohup mcp-eval evaluate \
#     --server $SERVER \
#     --server-args="$SERVER_ARGS" \
#     --model-config benchmarks/airbnb/eval_models/gpt-4o-mini.json \
#     --tasks-file $TASKS_FILE \
#     --output benchmarks/airbnb/results/gpt4o-mini_task_evaluation.json \
#     --prompt-file $PROMPT_FILE \
#     --max-turns $MAX_TURNS > benchmarks/airbnb/logs/gpt4o-mini_eval.log 2>&1 &

# echo "Evaluating GPT-4.1-mini..."
# nohup mcp-eval evaluate \
#     --server $SERVER \
#     --server-args="$SERVER_ARGS" \
#     --model-config benchmarks/airbnb/eval_models/gpt-4.1-mini.json \
#     --tasks-file $TASKS_FILE \
#     --output benchmarks/airbnb/results/gpt4.1-mini_task_evaluation.json \
#     --prompt-file $PROMPT_FILE \
#     --max-turns $MAX_TURNS > benchmarks/airbnb/logs/gpt4.1-mini_eval.log 2>&1 &

# echo "Evaluating GPT-4.1-nano..."
# nohup mcp-eval evaluate \
#     --server $SERVER \
#     --server-args="$SERVER_ARGS" \
#     --model-config benchmarks/airbnb/eval_models/gpt-4.1-nano.json \
#     --tasks-file $TASKS_FILE \
#     --output benchmarks/airbnb/results/gpt4.1-nano_task_evaluation.json \
#     --prompt-file $PROMPT_FILE \
#     --max-turns $MAX_TURNS > benchmarks/airbnb/logs/gpt4.1-nano_eval.log 2>&1 &

# echo "Evaluating O3..."
# nohup mcp-eval evaluate \
#     --server $SERVER \
#     --server-args="$SERVER_ARGS" \
#     --model-config benchmarks/airbnb/eval_models/o3.json \
#     --tasks-file $TASKS_FILE \
#     --output benchmarks/airbnb/results/o3_task_evaluation.json \
#     --prompt-file $PROMPT_FILE \
#     --max-turns $MAX_TURNS > benchmarks/airbnb/logs/o3_eval.log 2>&1 &

# echo "Evaluating O3-mini..."
# nohup mcp-eval evaluate \
#     --server $SERVER \
#     --server-args="$SERVER_ARGS" \
#     --model-config benchmarks/airbnb/eval_models/o3-mini.json \
#     --tasks-file $TASKS_FILE \
#     --output benchmarks/airbnb/results/o3-mini_task_evaluation.json \
#     --prompt-file $PROMPT_FILE \
#     --max-turns $MAX_TURNS > benchmarks/airbnb/logs/o3-mini_eval.log 2>&1 &

# echo "Evaluating O4-mini..."
# nohup mcp-eval evaluate \
#     --server $SERVER \
#     --server-args="$SERVER_ARGS" \
#     --model-config benchmarks/airbnb/eval_models/o4-mini.json \
#     --tasks-file $TASKS_FILE \
#     --output benchmarks/airbnb/results/o4-mini_task_evaluation.json \
#     --prompt-file $PROMPT_FILE \
#     --max-turns $MAX_TURNS > benchmarks/airbnb/logs/o4-mini_eval.log 2>&1 &

echo "Evaluating xlam_2_32b"
nohup mcp-eval evaluate \
    --server "@openbnb/mcp-server-airbnb" \
    --server-args="--ignore-robots-txt" \
    --model-config benchmarks/airbnb/eval_models/xlam_2_32b.json \
    --tasks-file "data/airbnb/verified_results.jsonl" \
    --output benchmarks/airbnb/results/xlam_2_32b_task_evaluation.json \
    --prompt-file "benchmarks/airbnb/evaluation_prompt.json" \
    --max-turns 30 > benchmarks/airbnb/logs/xlam_2_32b_eval.log 2>&1 &

echo "Evaluating xlam_2_70b"
nohup mcp-eval evaluate \
    --server "@openbnb/mcp-server-airbnb" \
    --server-args="--ignore-robots-txt" \
    --model-config benchmarks/airbnb/eval_models/xlam_2_70b.json \
    --tasks-file "data/airbnb/verified_results.jsonl" \
    --output benchmarks/airbnb/results/xlam_2_70b_task_evaluation.json \
    --prompt-file "benchmarks/airbnb/evaluation_prompt.json" \
    --max-turns 30 > benchmarks/airbnb/logs/xlam_2_70b_eval.log 2>&1 &

echo "Evaluating qwen3_30b_a3b"
nohup mcp-eval evaluate \
    --server "@openbnb/mcp-server-airbnb" \
    --server-args="--ignore-robots-txt" \
    --model-config benchmarks/airbnb/eval_models/qwen3-30b-a3b.json \
    --tasks-file "data/airbnb/verified_results.jsonl" \
    --output benchmarks/airbnb/results/qwen3-30b-a3b_task_evaluation.json \
    --prompt-file "benchmarks/airbnb/evaluation_prompt.json" \
    --max-turns 30 > benchmarks/airbnb/logs/qwen3-30b-a3b_eval.log 2>&1 &

echo "Evaluating qwen3_32b"
nohup mcp-eval evaluate \
    --server "@openbnb/mcp-server-airbnb" \
    --server-args="--ignore-robots-txt" \
    --model-config benchmarks/airbnb/eval_models/qwen3-32b.json \
    --tasks-file "data/airbnb/verified_results.jsonl" \
    --output benchmarks/airbnb/results/qwen3-32b_task_evaluation.json \
    --prompt-file "benchmarks/airbnb/evaluation_prompt.json" \
    --max-turns 30 > benchmarks/airbnb/logs/qwen3-32b_eval.log 2>&1 &

echo "Evaluating mistral_small_24b"
nohup mcp-eval evaluate \
    --server "@openbnb/mcp-server-airbnb" \
    --server-args="--ignore-robots-txt" \
    --model-config benchmarks/airbnb/eval_models/mistral_small_24b.json \
    --tasks-file "data/airbnb/verified_results.jsonl" \
    --output benchmarks/airbnb/results/mistral_small_24b_task_evaluation.json \
    --prompt-file "benchmarks/airbnb/evaluation_prompt.json" \
    --max-turns 30 > benchmarks/airbnb/logs/mistral_small_24b_eval.log 2>&1 &
# Wait for all evaluation processes to complete
echo "Waiting for all evaluations to complete..."
echo "You can monitor progress by checking the log files in benchmarks/airbnb/logs/"
echo "Use 'tail -f benchmarks/airbnb/logs/<model>_eval.log' to follow a specific evaluation"
wait

echo "All evaluations completed! Starting parallel analysis..."

# Run all analyses in parallel
# echo "Analyzing GPT-4o results..."
# mcp-eval analyze \
#     --predictions benchmarks/airbnb/results/gpt4o_task_evaluation.json \
#     --ground-truth $TASKS_FILE \
#     --generate-report \
#     --report-model $REPORT_MODEL \
#     --report-output benchmarks/airbnb/report/gpt4o_evaluation_report.md &

# echo "Analyzing GPT-4o-mini results..."
# mcp-eval analyze \
#     --predictions benchmarks/airbnb/results/gpt4o-mini_task_evaluation.json \
#     --ground-truth $TASKS_FILE \
#     --generate-report \
#     --report-model $REPORT_MODEL \
#     --report-output benchmarks/airbnb/report/gpt4o-mini_evaluation_report.md &

# echo "Analyzing GPT-4.1-mini results..."
# mcp-eval analyze \
#     --predictions benchmarks/airbnb/results/gpt4.1-mini_task_evaluation.json \
#     --ground-truth $TASKS_FILE \
#     --generate-report \
#     --report-model $REPORT_MODEL \
#     --report-output benchmarks/airbnb/report/gpt4.1-mini_evaluation_report.md &

# echo "Analyzing GPT-4.1-nano results..."
# mcp-eval analyze \
#     --predictions benchmarks/airbnb/results/gpt4.1-nano_task_evaluation.json \
#     --ground-truth $TASKS_FILE \
#     --generate-report \
#     --report-model $REPORT_MODEL \
#     --report-output benchmarks/airbnb/report/gpt4.1-nano_evaluation_report.md &

# echo "Analyzing O3 results..."
# mcp-eval analyze \
#     --predictions benchmarks/airbnb/results/o3_task_evaluation.json \
#     --ground-truth $TASKS_FILE \
#     --generate-report \
#     --report-model $REPORT_MODEL \
#     --report-output benchmarks/airbnb/report/o3_evaluation_report.md &

# echo "Analyzing O3-mini results..."
# mcp-eval analyze \
#     --predictions benchmarks/airbnb/results/o3-mini_task_evaluation.json \
#     --ground-truth $TASKS_FILE \
#     --generate-report \
#     --report-model $REPORT_MODEL \
#     --report-output benchmarks/airbnb/report/o3-mini_evaluation_report.md &

# echo "Analyzing O4-mini results..."
# mcp-eval analyze \
#     --predictions benchmarks/airbnb/results/o4-mini_task_evaluation.json \
#     --ground-truth $TASKS_FILE \
#     --generate-report \
#     --report-model $REPORT_MODEL \
#     --report-output benchmarks/airbnb/report/o4-mini_evaluation_report.md &

echo "Analyzing xlam_2_32b results..."
mcp-eval analyze \
    --predictions benchmarks/airbnb/results/xlam_2_32b_task_evaluation.json \
    --ground-truth data/airbnb/verified_results.jsonl \
    --generate-report \
    --report-model gpt-4.1-2025-04-14 \
    --report-output benchmarks/airbnb/report/xlam_2_32b_evaluation_report.md &

echo "Analyzing xlam_2_70b results..."
mcp-eval analyze \
    --predictions benchmarks/airbnb/results/xlam_2_70b_task_evaluation.json \
    --ground-truth data/airbnb/verified_results.jsonl \
    --generate-report \
    --report-model gpt-4.1-2025-04-14 \
    --report-output benchmarks/airbnb/report/xlam_2_70b_evaluation_report.md &

echo "Analyzing mistral_small_24b results..."
mcp-eval analyze \
    --predictions benchmarks/airbnb/results/mistral_small_24b_task_evaluation.json \
    --ground-truth data/airbnb/verified_results.jsonl \
    --generate-report \
    --report-model gpt-4.1-2025-04-14 \
    --report-output benchmarks/airbnb/report/mistral_small_24b_evaluation_report.md &

echo "Analyzing qwen3_30b_a3b results..."
mcp-eval analyze \
    --predictions benchmarks/airbnb/results/qwen3-30b-a3b_task_evaluation.json \
    --ground-truth data/airbnb/verified_results.jsonl \
    --generate-report \
    --report-model gpt-4.1-2025-04-14 \
    --report-output benchmarks/airbnb/report/qwen3-30b-a3b_evaluation_report.md &

echo "Analyzing qwen3_32b results..."
mcp-eval analyze \
    --predictions benchmarks/airbnb/results/qwen3-32b_task_evaluation.json \
    --ground-truth data/airbnb/verified_results.jsonl \
    --generate-report \
    --report-model gpt-4.1-2025-04-14 \
    --report-output benchmarks/airbnb/report/qwen3-32b_evaluation_report.md &

# Wait for all analysis processes to complete
echo "Waiting for all analyses to complete..."
wait

echo "All evaluations and analyses completed! Results are in benchmarks/airbnb/results/ and reports are in benchmarks/airbnb/report/" 