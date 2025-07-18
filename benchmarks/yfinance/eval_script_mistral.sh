#!/bin/bash

# Define arguments
DOMAIN="yfinance"
MODEL="mistral_small_24b"
MAX_TURNS=30
REPORT_MODEL="gpt-4.1-2025-04-14"
JUDGE_MODEL="gpt-4o"
SERVER="mcp_servers/${DOMAIN}/server.py"
MODEL_CONFIG="benchmarks/${DOMAIN}/eval_models/${MODEL}.json"
TASKS_FILE="data/${DOMAIN}/evaluation_tasks_verified.jsonl"
OUTPUT="benchmarks/${DOMAIN}/results/${MODEL}_evaluation.json"
PROMPT_FILE="benchmarks/${DOMAIN}/evaluation_prompt.json"
EVAL_LOG="benchmarks/${DOMAIN}/logs/${MODEL}_evaluation.log"
ANALYSIS_LOG="benchmarks/${DOMAIN}/logs/${MODEL}_evaluation.log"
REPORT_OUTPUT="benchmarks/${DOMAIN}/report/${MODEL}_evaluation.md"
TRAJECTORY_FILE="benchmarks/${DOMAIN}/results/${MODEL}_evaluation_judge_results_with_gpt-4o_trajectory.json"
COMPLETION_FILE="benchmarks/${DOMAIN}/results/${MODEL}_evaluation_judge_results_with_gpt-4o_completion.json"
RESULTS_DIR="benchmarks/${DOMAIN}/results"
REPORT_DIR="benchmarks/${DOMAIN}/report"

# mcp-eval evaluate \
#     --server $SERVER \
#     --model-config $MODEL_CONFIG \
#     --tasks-file $TASKS_FILE \
#     --output $OUTPUT \
#     --prompt-file $PROMPT_FILE \
#     --max-turns $MAX_TURNS

# echo "Analyzing ${DOMAIN} ${MODEL} results..."
# mcp-eval analyze \
#     --predictions $OUTPUT \
#     --ground-truth $TASKS_FILE \
#     --generate-report \
#     --report-model $REPORT_MODEL \
#     --report-output $REPORT_OUTPUT

# echo "Judging ${DOMAIN} ${MODEL}..."
# mcp-eval judge --input-file $OUTPUT --output-dir $RESULTS_DIR --model $JUDGE_MODEL

echo "Judging rubric for ${DOMAIN} ${MODEL}..."
mcp-eval judge-rubric --trajectory-file $TRAJECTORY_FILE \
    --completion-file $COMPLETION_FILE \
    --output-dir $REPORT_DIR
