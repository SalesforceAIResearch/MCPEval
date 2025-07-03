#!/bin/bash

# Generate and verify travel assistant tasks
mcp-eval generate-tasks --server mcp_servers/travel_assistant/server.py --model gpt-4.1-2025-04-14 --num-tasks 200 --prompt-file benchmarks/travel_assistant/data_generation/task_generation_prompt.json --output data/travel_assistant/evaluation_tasks.jsonl
mcp-eval verify-tasks --server mcp_servers/travel_assistant/server.py --tasks-file data/travel_assistant/evaluation_tasks.jsonl --model gpt-4.1-2025-04-14 --output data/travel_assistant/evaluation_tasks_verified.jsonl --prompt-file benchmarks/travel_assistant/data_generation/task_verification_prompt.json

# Evaluate GPT-4o
mcp-eval evaluate --server mcp_servers/travel_assistant/server.py --model-config benchmarks/travel_assistant/eval_models/gpt-4o.json --tasks-file data/travel_assistant/evaluation_tasks_verified.jsonl --output benchmarks/travel_assistant/results/gpt4o_mix_task_evaluation.json --prompt-file benchmarks/travel_assistant/evaluation_prompt.json --max-turns 30
mcp-eval analyze --predictions benchmarks/travel_assistant/results/gpt4o_mix_task_evaluation.json --ground-truth data/travel_assistant/evaluation_tasks_verified.jsonl --generate-report --report-model gpt-4.1-2025-04-14 --report-output benchmarks/travel_assistant/results/gpt4o_travel_assistant_report.md

# Evaluate GPT-4o-mini
mcp-eval evaluate --server mcp_servers/travel_assistant/server.py --model-config benchmarks/travel_assistant/eval_models/gpt-4o-mini.json --tasks-file data/travel_assistant/evaluation_tasks_verified.jsonl --output benchmarks/travel_assistant/results/gpt4o-mini_mix_task_evaluation.json --prompt-file benchmarks/travel_assistant/evaluation_prompt.json --max-turns 30
mcp-eval analyze --predictions benchmarks/travel_assistant/results/gpt4o-mini_mix_task_evaluation.json --ground-truth data/travel_assistant/evaluation_tasks_verified.jsonl --generate-report --report-model gpt-4.1-2025-04-14 --report-output benchmarks/travel_assistant/results/gpt4o-mini_travel_assistant_report.md

# Evaluate GPT-4.1-mini
mcp-eval evaluate --server mcp_servers/travel_assistant/server.py --model-config benchmarks/travel_assistant/eval_models/gpt-4.1-mini.json --tasks-file data/travel_assistant/evaluation_tasks_verified.jsonl --output benchmarks/travel_assistant/results/gpt4.1-mini_mix_task_evaluation.json --prompt-file benchmarks/travel_assistant/evaluation_prompt.json --max-turns 30
mcp-eval analyze --predictions benchmarks/travel_assistant/results/gpt4.1-mini_mix_task_evaluation.json --ground-truth data/travel_assistant/evaluation_tasks_verified.jsonl --generate-report --report-model gpt-4.1-2025-04-14 --report-output benchmarks/travel_assistant/results/gpt4.1-mini_travel_assistant_report.md

# Evaluate GPT-4.1-nano
mcp-eval evaluate --server mcp_servers/travel_assistant/server.py --model-config benchmarks/travel_assistant/eval_models/gpt-4.1-nano.json --tasks-file data/travel_assistant/evaluation_tasks_verified.jsonl --output benchmarks/travel_assistant/results/gpt4.1-nano_mix_task_evaluation.json --prompt-file benchmarks/travel_assistant/evaluation_prompt.json --max-turns 30
mcp-eval analyze --predictions benchmarks/travel_assistant/results/gpt4.1-nano_mix_task_evaluation.json --ground-truth data/travel_assistant/evaluation_tasks_verified.jsonl --generate-report --report-model gpt-4.1-2025-04-14 --report-output benchmarks/travel_assistant/results/gpt4.1-nano_travel_assistant_report.md

# Evaluate o3
mcp-eval evaluate --server mcp_servers/travel_assistant/server.py --model-config benchmarks/travel_assistant/eval_models/o3.json --tasks-file data/travel_assistant/evaluation_tasks_verified.jsonl --output benchmarks/travel_assistant/results/o3_mix_task_evaluation.json --prompt-file benchmarks/travel_assistant/evaluation_prompt.json --max-turns 30
mcp-eval analyze --predictions benchmarks/travel_assistant/results/o3_mix_task_evaluation.json --ground-truth data/travel_assistant/evaluation_tasks_verified.jsonl --generate-report --report-model gpt-4.1-2025-04-14 --report-output benchmarks/travel_assistant/results/o3_travel_assistant_report.md

# Evaluate o3-mini
mcp-eval evaluate --server mcp_servers/travel_assistant/server.py --model-config benchmarks/travel_assistant/eval_models/o3-mini.json --tasks-file data/travel_assistant/evaluation_tasks_verified.jsonl --output benchmarks/travel_assistant/results/o3-mini_mix_task_evaluation.json --prompt-file benchmarks/travel_assistant/evaluation_prompt.json --max-turns 30
mcp-eval analyze --predictions benchmarks/travel_assistant/results/o3-mini_mix_task_evaluation.json --ground-truth data/travel_assistant/evaluation_tasks_verified.jsonl --generate-report --report-model gpt-4.1-2025-04-14 --report-output benchmarks/travel_assistant/results/o3-mini_travel_assistant_report.md

# Evaluate o4-mini
mcp-eval evaluate --server mcp_servers/travel_assistant/server.py --model-config benchmarks/travel_assistant/eval_models/o4-mini.json --tasks-file data/travel_assistant/evaluation_tasks_verified.jsonl --output benchmarks/travel_assistant/results/o4-mini_mix_task_evaluation.json --prompt-file benchmarks/travel_assistant/evaluation_prompt.json --max-turns 30
mcp-eval analyze --predictions benchmarks/travel_assistant/results/o4-mini_mix_task_evaluation.json --ground-truth data/travel_assistant/evaluation_tasks_verified.jsonl --generate-report --report-model gpt-4.1-2025-04-14 --report-output benchmarks/travel_assistant/results/o4-mini_travel_assistant_report.md 