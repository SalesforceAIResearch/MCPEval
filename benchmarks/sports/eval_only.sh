#!/bin/bash

# Run evaluations only in parallel (assumes verified tasks already exist)
echo "🚀 Starting parallel evaluations for all models..."

# Run all evaluations in parallel
mcp-eval evaluate --server mcp_servers/sports/server.py --model-config benchmarks/sports/eval_models/gpt-4o.json --tasks-file data/sports/evaluation_tasks_verified.jsonl --output benchmarks/sports/results/gpt4o_mix_task_evaluation.json --prompt-file benchmarks/sports/evaluation_prompt.json --max-turns 30 &

mcp-eval evaluate --server mcp_servers/sports/server.py --model-config benchmarks/sports/eval_models/gpt-4o-mini.json --tasks-file data/sports/evaluation_tasks_verified.jsonl --output benchmarks/sports/results/gpt4o-mini_mix_task_evaluation.json --prompt-file benchmarks/sports/evaluation_prompt.json --max-turns 30 &

mcp-eval evaluate --server mcp_servers/sports/server.py --model-config benchmarks/sports/eval_models/gpt-4.1-mini.json --tasks-file data/sports/evaluation_tasks_verified.jsonl --output benchmarks/sports/results/gpt4.1-mini_mix_task_evaluation.json --prompt-file benchmarks/sports/evaluation_prompt.json --max-turns 30 &

mcp-eval evaluate --server mcp_servers/sports/server.py --model-config benchmarks/sports/eval_models/gpt-4.1-nano.json --tasks-file data/sports/evaluation_tasks_verified.jsonl --output benchmarks/sports/results/gpt4.1-nano_mix_task_evaluation.json --prompt-file benchmarks/sports/evaluation_prompt.json --max-turns 30 &

mcp-eval evaluate --server mcp_servers/sports/server.py --model-config benchmarks/sports/eval_models/o3.json --tasks-file data/sports/evaluation_tasks_verified.jsonl --output benchmarks/sports/results/o3_mix_task_evaluation.json --prompt-file benchmarks/sports/evaluation_prompt.json --max-turns 30 &

mcp-eval evaluate --server mcp_servers/sports/server.py --model-config benchmarks/sports/eval_models/o3-mini.json --tasks-file data/sports/evaluation_tasks_verified.jsonl --output benchmarks/sports/results/o3-mini_mix_task_evaluation.json --prompt-file benchmarks/sports/evaluation_prompt.json --max-turns 30 &

mcp-eval evaluate --server mcp_servers/sports/server.py --model-config benchmarks/sports/eval_models/o4-mini.json --tasks-file data/sports/evaluation_tasks_verified.jsonl --output benchmarks/sports/results/o4-mini_mix_task_evaluation.json --prompt-file benchmarks/sports/evaluation_prompt.json --max-turns 30 &

# Wait for all background jobs to complete
wait

echo "✅ All evaluations completed!" 