#!/bin/bash

# Generate and verify sqlite tasks
mcp-eval generate-tasks --server mcp_servers/sqlite/server.py --model gpt-4.1-2025-04-14 --num-tasks 200 --prompt-file benchmarks/sqlite/data_generation/task_generation_prompt.json --output data/sqlite/evaluation_tasks.jsonl
mcp-eval verify-tasks --server mcp_servers/sqlite/server.py --tasks-file data/sqlite/evaluation_tasks.jsonl --model gpt-4.1-2025-04-14 --output data/sqlite/evaluation_tasks_verified.jsonl --prompt-file benchmarks/sqlite/data_generation/task_verification_prompt.json

# Evaluate GPT-4o
mcp-eval evaluate --server mcp_servers/sqlite/server.py --model-config benchmarks/sqlite/eval_models/gpt-4o.json --tasks-file data/sqlite/evaluation_tasks_verified.jsonl --output benchmarks/sqlite/results/gpt4o_mix_task_evaluation.json --prompt-file benchmarks/sqlite/evaluation_prompt.json --max-turns 30
mcp-eval analyze --predictions benchmarks/sqlite/results/gpt4o_mix_task_evaluation.json --ground-truth data/sqlite/evaluation_tasks_verified.jsonl --generate-report --report-model gpt-4.1-2025-04-14 --report-output benchmarks/sqlite/results/gpt4o_sqlite_report.md

# Evaluate GPT-4o-mini
mcp-eval evaluate --server mcp_servers/sqlite/server.py --model-config benchmarks/sqlite/eval_models/gpt-4o-mini.json --tasks-file data/sqlite/evaluation_tasks_verified.jsonl --output benchmarks/sqlite/results/gpt4o-mini_mix_task_evaluation.json --prompt-file benchmarks/sqlite/evaluation_prompt.json --max-turns 30
mcp-eval analyze --predictions benchmarks/sqlite/results/gpt4o-mini_mix_task_evaluation.json --ground-truth data/sqlite/evaluation_tasks_verified.jsonl --generate-report --report-model gpt-4.1-2025-04-14 --report-output benchmarks/sqlite/results/gpt4o-mini_sqlite_report.md

# Evaluate GPT-4.1-mini
mcp-eval evaluate --server mcp_servers/sqlite/server.py --model-config benchmarks/sqlite/eval_models/gpt-4.1-mini.json --tasks-file data/sqlite/evaluation_tasks_verified.jsonl --output benchmarks/sqlite/results/gpt4.1-mini_mix_task_evaluation.json --prompt-file benchmarks/sqlite/evaluation_prompt.json --max-turns 30
mcp-eval analyze --predictions benchmarks/sqlite/results/gpt4.1-mini_mix_task_evaluation.json --ground-truth data/sqlite/evaluation_tasks_verified.jsonl --generate-report --report-model gpt-4.1-2025-04-14 --report-output benchmarks/sqlite/results/gpt4.1-mini_sqlite_report.md

# Evaluate GPT-4.1-nano
mcp-eval evaluate --server mcp_servers/sqlite/server.py --model-config benchmarks/sqlite/eval_models/gpt-4.1-nano.json --tasks-file data/sqlite/evaluation_tasks_verified.jsonl --output benchmarks/sqlite/results/gpt4.1-nano_mix_task_evaluation.json --prompt-file benchmarks/sqlite/evaluation_prompt.json --max-turns 30
mcp-eval analyze --predictions benchmarks/sqlite/results/gpt4.1-nano_mix_task_evaluation.json --ground-truth data/sqlite/evaluation_tasks_verified.jsonl --generate-report --report-model gpt-4.1-2025-04-14 --report-output benchmarks/sqlite/results/gpt4.1-nano_sqlite_report.md

# Evaluate o3
mcp-eval evaluate --server mcp_servers/sqlite/server.py --model-config benchmarks/sqlite/eval_models/o3.json --tasks-file data/sqlite/evaluation_tasks_verified.jsonl --output benchmarks/sqlite/results/o3_mix_task_evaluation.json --prompt-file benchmarks/sqlite/evaluation_prompt.json --max-turns 30
mcp-eval analyze --predictions benchmarks/sqlite/results/o3_mix_task_evaluation.json --ground-truth data/sqlite/evaluation_tasks_verified.jsonl --generate-report --report-model gpt-4.1-2025-04-14 --report-output benchmarks/sqlite/results/o3_sqlite_report.md

# Evaluate o3-mini
mcp-eval evaluate --server mcp_servers/sqlite/server.py --model-config benchmarks/sqlite/eval_models/o3-mini.json --tasks-file data/sqlite/evaluation_tasks_verified.jsonl --output benchmarks/sqlite/results/o3-mini_mix_task_evaluation.json --prompt-file benchmarks/sqlite/evaluation_prompt.json --max-turns 30
mcp-eval analyze --predictions benchmarks/sqlite/results/o3-mini_mix_task_evaluation.json --ground-truth data/sqlite/evaluation_tasks_verified.jsonl --generate-report --report-model gpt-4.1-2025-04-14 --report-output benchmarks/sqlite/results/o3-mini_sqlite_report.md

# Evaluate o4-mini
mcp-eval evaluate --server mcp_servers/sqlite/server.py --model-config benchmarks/sqlite/eval_models/o4-mini.json --tasks-file data/sqlite/evaluation_tasks_verified.jsonl --output benchmarks/sqlite/results/o4-mini_mix_task_evaluation.json --prompt-file benchmarks/sqlite/evaluation_prompt.json --max-turns 30
mcp-eval analyze --predictions benchmarks/sqlite/results/o4-mini_mix_task_evaluation.json --ground-truth data/sqlite/evaluation_tasks_verified.jsonl --generate-report --report-model gpt-4.1-2025-04-14 --report-output benchmarks/sqlite/results/o4-mini_sqlite_report.md 