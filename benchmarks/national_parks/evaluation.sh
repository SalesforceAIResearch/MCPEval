#!/bin/bash

# Define arguments
DOMAIN="national_parks"
# MODELS=("qwen3-32b" "qwen3-30b-a3b" "mistral_small_24b")    
# MODELS=("qwen3_30b_a3b" "mistral_small_24b")
MODELS=("qwen3_32b")
# MODELS=("qwen3_32b")
MAX_TURNS=30
REPORT_MODEL="gpt-4.1-2025-04-14"
JUDGE_MODEL="gpt-4o"
SERVERS="mcp-server-nationalparks^NPS_API_KEY=$NPS_API_KEY"
TASKS_FILE="data/${DOMAIN}/evaluation_tasks_verified.jsonl"
PROMPT_FILE="benchmarks/${DOMAIN}/evaluation_prompt.json"
RESULTS_DIR="benchmarks/${DOMAIN}/results"
REPORT_DIR="benchmarks/${DOMAIN}/report"
JUDGE_LOG="benchmarks/${DOMAIN}/logs/judge.log"
EVAL_LOG="benchmarks/${DOMAIN}/logs/evaluate.log"
ANALYSIS_LOG="benchmarks/${DOMAIN}/logs/analyze.log"
JUDGE_LOG="benchmarks/${DOMAIN}/logs/judge.log"

mkdir -p benchmarks/${DOMAIN}/logs

for model in "${MODELS[@]}"; do
    MODEL_CONFIG="benchmarks/${DOMAIN}/eval_models/${model}.json"
    OUTPUT="benchmarks/${DOMAIN}/results/${model}_task_evaluation.jsonl"
    REPORT_OUTPUT="benchmarks/${DOMAIN}/report/${model}_task_evaluation.md"
    mcp-eval evaluate --servers $SERVERS --model-config $MODEL_CONFIG --tasks-file $TASKS_FILE --output $OUTPUT --prompt-file $PROMPT_FILE --max-turns $MAX_TURNS
    mcp-eval judge --input-file $OUTPUT --output-dir $RESULTS_DIR --model $JUDGE_MODEL
done


