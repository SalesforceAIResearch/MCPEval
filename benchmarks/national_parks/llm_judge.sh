#!/bin/bash

# Define arguments
DOMAIN="national_parks"
# MODELS=("qwen3-32b" "qwen3-30b-a3b" "mistral_small_24b")    
# MODELS=("qwen3_30b_a3b" "mistral_small_24b")
MODELS=("mistral_small_24b")
JUDGE_MODEL="gpt-4o"
RESULTS_DIR="benchmarks/${DOMAIN}/results"
JUDGE_LOG="benchmarks/${DOMAIN}/logs/llm_judge.log"

mkdir -p benchmarks/${DOMAIN}/logs

for model in "${MODELS[@]}"; do
    OUTPUT="benchmarks/${DOMAIN}/results/${model}_task_evaluation.jsonl"
    mcp-eval judge --input-file $OUTPUT --output-dir $RESULTS_DIR --model $JUDGE_MODEL
done


