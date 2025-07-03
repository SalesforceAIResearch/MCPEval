#!/bin/bash

# Comprehensive evaluation script for all YFinance+Sequential Thinking models
# This script evaluates all models with both sequential thinking and financial analysis capabilities

echo "Starting comprehensive multi-server evaluation (Sequential Thinking + YFinance)..."

# Define common parameters for multi-server setup
SERVERS="@modelcontextprotocol/server-sequential-thinking mcp_servers/yfinance/server.py"
TASKS_FILE="data/yfinance/mix_verified_evaluation.jsonl"  # Use the verified yfinance tasks
PROMPT_FILE="benchmarks/yfinance_think/evaluation_prompt.json"
MAX_TURNS=30  # Increased turns for complex multi-server tasks
REPORT_MODEL="gpt-4.1-2025-04-14"

# Create results and report directories
mkdir -p benchmarks/yfinance_think/results
mkdir -p benchmarks/yfinance_think/report
mkdir -p benchmarks/yfinance_think/logs

echo "Starting parallel evaluation of all models with multi-server setup..."
echo "Using servers: $SERVERS"
echo "Max turns: $MAX_TURNS"

# Run all evaluations in parallel with nohup
echo "Evaluating GPT-4o..."
nohup mcp-eval evaluate \
    --servers "$SERVERS" \
    --model-config benchmarks/yfinance_think/eval_models/gpt-4o.json \
    --tasks $TASKS_FILE \
    --output benchmarks/yfinance_think/results/gpt4o_multi_task_evaluation.json \
    --prompt-file $PROMPT_FILE \
    --max-turns $MAX_TURNS > benchmarks/yfinance_think/logs/gpt4o_eval.log 2>&1 &

echo "Evaluating GPT-4o-mini..."
nohup mcp-eval evaluate \
    --servers "$SERVERS" \
    --model-config benchmarks/yfinance_think/eval_models/gpt-4o-mini.json \
    --tasks $TASKS_FILE \
    --output benchmarks/yfinance_think/results/gpt4o-mini_multi_task_evaluation.json \
    --prompt-file $PROMPT_FILE \
    --max-turns $MAX_TURNS > benchmarks/yfinance_think/logs/gpt4o-mini_eval.log 2>&1 &

echo "Evaluating GPT-4.1-mini..."
nohup mcp-eval evaluate \
    --servers "$SERVERS" \
    --model-config benchmarks/yfinance_think/eval_models/gpt-4.1-mini.json \
    --tasks $TASKS_FILE \
    --output benchmarks/yfinance_think/results/gpt4.1-mini_multi_task_evaluation.json \
    --prompt-file $PROMPT_FILE \
    --max-turns $MAX_TURNS > benchmarks/yfinance_think/logs/gpt4.1-mini_eval.log 2>&1 &

echo "Evaluating GPT-4.1-nano..."
nohup mcp-eval evaluate \
    --servers "$SERVERS" \
    --model-config benchmarks/yfinance_think/eval_models/gpt-4.1-nano.json \
    --tasks $TASKS_FILE \
    --output benchmarks/yfinance_think/results/gpt4.1-nano_multi_task_evaluation.json \
    --prompt-file $PROMPT_FILE \
    --max-turns $MAX_TURNS > benchmarks/yfinance_think/logs/gpt4.1-nano_eval.log 2>&1 &

echo "Evaluating O3..."
nohup mcp-eval evaluate \
    --servers "$SERVERS" \
    --model-config benchmarks/yfinance_think/eval_models/o3.json \
    --tasks $TASKS_FILE \
    --output benchmarks/yfinance_think/results/o3_multi_task_evaluation.json \
    --prompt-file $PROMPT_FILE \
    --max-turns $MAX_TURNS > benchmarks/yfinance_think/logs/o3_eval.log 2>&1 &

echo "Evaluating O3-mini..."
nohup mcp-eval evaluate \
    --servers "$SERVERS" \
    --model-config benchmarks/yfinance_think/eval_models/o3-mini.json \
    --tasks $TASKS_FILE \
    --output benchmarks/yfinance_think/results/o3-mini_multi_task_evaluation.json \
    --prompt-file $PROMPT_FILE \
    --max-turns $MAX_TURNS > benchmarks/yfinance_think/logs/o3-mini_eval.log 2>&1 &

echo "Evaluating O4-mini..."
nohup mcp-eval evaluate \
    --servers "$SERVERS" \
    --model-config benchmarks/yfinance_think/eval_models/o4-mini.json \
    --tasks $TASKS_FILE \
    --output benchmarks/yfinance_think/results/o4-mini_multi_task_evaluation.json \
    --prompt-file $PROMPT_FILE \
    --max-turns $MAX_TURNS > benchmarks/yfinance_think/logs/o4-mini_eval.log 2>&1 &

# Wait for all evaluation processes to complete
echo "Waiting for all multi-server evaluations to complete..."
echo "You can monitor progress by checking the log files in benchmarks/yfinance_think/logs/"
echo "Use 'tail -f benchmarks/yfinance_think/logs/<model>_eval.log' to follow a specific evaluation"
wait

echo "All evaluations completed! Starting parallel analysis..."

# Run all analyses in parallel
echo "Analyzing GPT-4o results..."
mcp-eval analyze \
    --predictions benchmarks/yfinance_think/results/gpt4o_multi_task_evaluation.json \
    --ground-truth $TASKS_FILE \
    --generate-report \
    --report-model $REPORT_MODEL \
    --report-output benchmarks/yfinance_think/report/gpt4o_multi_evaluation_report.md &

echo "Analyzing GPT-4o-mini results..."
mcp-eval analyze \
    --predictions benchmarks/yfinance_think/results/gpt4o-mini_multi_task_evaluation.json \
    --ground-truth $TASKS_FILE \
    --generate-report \
    --report-model $REPORT_MODEL \
    --report-output benchmarks/yfinance_think/report/gpt4o-mini_multi_evaluation_report.md &

echo "Analyzing GPT-4.1-mini results..."
mcp-eval analyze \
    --predictions benchmarks/yfinance_think/results/gpt4.1-mini_multi_task_evaluation.json \
    --ground-truth $TASKS_FILE \
    --generate-report \
    --report-model $REPORT_MODEL \
    --report-output benchmarks/yfinance_think/report/gpt4.1-mini_multi_evaluation_report.md &

echo "Analyzing GPT-4.1-nano results..."
mcp-eval analyze \
    --predictions benchmarks/yfinance_think/results/gpt4.1-nano_multi_task_evaluation.json \
    --ground-truth $TASKS_FILE \
    --generate-report \
    --report-model $REPORT_MODEL \
    --report-output benchmarks/yfinance_think/report/gpt4.1-nano_multi_evaluation_report.md &

echo "Analyzing O3 results..."
mcp-eval analyze \
    --predictions benchmarks/yfinance_think/results/o3_multi_task_evaluation.json \
    --ground-truth $TASKS_FILE \
    --generate-report \
    --report-model $REPORT_MODEL \
    --report-output benchmarks/yfinance_think/report/o3_multi_evaluation_report.md &

echo "Analyzing O3-mini results..."
mcp-eval analyze \
    --predictions benchmarks/yfinance_think/results/o3-mini_multi_task_evaluation.json \
    --ground-truth $TASKS_FILE \
    --generate-report \
    --report-model $REPORT_MODEL \
    --report-output benchmarks/yfinance_think/report/o3-mini_multi_evaluation_report.md &

echo "Analyzing O4-mini results..."
mcp-eval analyze \
    --predictions benchmarks/yfinance_think/results/o4-mini_multi_task_evaluation.json \
    --ground-truth $TASKS_FILE \
    --generate-report \
    --report-model $REPORT_MODEL \
    --report-output benchmarks/yfinance_think/report/o4-mini_multi_evaluation_report.md &

# Wait for all analysis processes to complete
echo "Waiting for all analyses to complete..."
wait

echo "🎉 All multi-server evaluations and analyses completed!"
echo "📊 Results are in benchmarks/yfinance_think/results/"
echo "📝 Reports are in benchmarks/yfinance_think/report/"
echo ""
echo "Multi-server capabilities tested:"
echo "  ✅ Sequential Thinking - structured reasoning and planning"
echo "  ✅ YFinance Analysis - financial data analysis and insights"
echo "  ✅ Combined - complex financial tasks requiring both capabilities" 