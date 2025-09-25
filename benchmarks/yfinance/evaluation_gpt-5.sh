#!/bin/bash

# Define arguments
DOMAIN="yfinance"
MODEL="gpt-5"
MAX_TURNS=30
REPORT_MODEL="gpt-4.1-2025-04-14"
JUDGE_MODEL="gpt-4o"
SERVERS="mcp_servers/${DOMAIN}/server.py"
MODEL_CONFIG="benchmarks/${DOMAIN}/eval_models/${MODEL}.json"
TASKS_FILE="data/${DOMAIN}/evaluation_tasks_verified.jsonl"
OUTPUT="benchmarks/${DOMAIN}/results/${MODEL}_task_evaluation.jsonl"
PROMPT_FILE="benchmarks/${DOMAIN}/evaluation_prompt.json"
EVAL_LOG="benchmarks/${DOMAIN}/logs/${MODEL}_task_evaluation.log"
ANALYSIS_LOG="benchmarks/${DOMAIN}/logs/${MODEL}_task_evaluation.log"
REPORT_OUTPUT="benchmarks/${DOMAIN}/report/${MODEL}_task_evaluation.md"
RESULTS_DIR="benchmarks/${DOMAIN}/results"
TRAJECTORY_FILE="benchmarks/${DOMAIN}/results/${MODEL}_task_evaluation_with_${JUDGE_MODEL}_trajectory.jsonl"
COMPLETION_FILE="benchmarks/${DOMAIN}/results/${MODEL}_task_evaluation_with_${JUDGE_MODEL}_completion.jsonl"
REPORT_DIR="benchmarks/${DOMAIN}/report"

echo "Evaluating ${DOMAIN} ${MODEL}..."
uv run mcp-eval evaluate \
    --servers $SERVERS \
    --model-config $MODEL_CONFIG \
    --tasks-file $TASKS_FILE \
    --output $OUTPUT \
    --prompt-file $PROMPT_FILE \
    --max-turns $MAX_TURNS

echo "Analyzing ${DOMAIN} ${MODEL} results..."
uv run mcp-eval analyze \
    --predictions $OUTPUT \
    --ground-truth $TASKS_FILE \
    --generate-report \
    --report-model $REPORT_MODEL \
    --report-output $REPORT_OUTPUT

echo "Judging ${DOMAIN} ${MODEL}..."
uv run mcp-eval judge --input-file $OUTPUT --output-dir $RESULTS_DIR --model $JUDGE_MODEL

echo "Judging rubric for ${DOMAIN} ${MODEL}..."
uv run mcp-eval judge-rubric \
    --trajectory-file $TRAJECTORY_FILE \
    --completion-file $COMPLETION_FILE \
    --output-dir $REPORT_DIR
