mcp-eval evaluate --server mcp_servers/yfinance/server.py --model-config benchmarks/yfinance/eval_models/gpt-4o.json --tasks-file data/yfinance/mix_verified_evaluation.jsonl --output benchmarks/yfinance/results/gpt4o_mix_task_evaluation.json --prompt-file benchmarks/yfinance/evaluation_prompt.json --max-turns 30
mcp-eval analyze --predictions benchmarks/yfinance/results/gpt4o_mix_task_evaluation.json --ground-truth data/yfinance/mix_verified_evaluation.jsonl --generate-report --report-model gpt-4.1-2025-04-14 --report-output benchmarks/yfinance/report/gpt4o_evaluation_tasks_verified_report.md

mcp-eval evaluate --server mcp_servers/yfinance/server.py --model-config benchmarks/yfinance/eval_models/gpt-4o-mini.json --tasks-file data/yfinance/mix_verified_evaluation.jsonl --output benchmarks/yfinance/results/gpt4o-mini_mix_task_evaluation.json --prompt-file benchmarks/yfinance/evaluation_prompt.json --max-turns 30
mcp-eval analyze --predictions benchmarks/yfinance/results/gpt4o-mini_mix_task_evaluation.json --ground-truth data/yfinance/mix_verified_evaluation.jsonl --generate-report --report-model gpt-4.1-2025-04-14 --report-output benchmarks/yfinance/report/gpt4o-mini_evaluation_tasks_verified_report.md

mcp-eval evaluate --server mcp_servers/yfinance/server.py --model-config benchmarks/yfinance/eval_models/gpt-4.1-mini.json  --tasks-file data/yfinance/mix_verified_evaluation.jsonl --output benchmarks/yfinance/results/gpt4.1-mini_mix_task_evaluation.json --prompt-file benchmarks/yfinance/evaluation_prompt.json --max-turns 30
mcp-eval analyze --predictions benchmarks/yfinance/results/gpt4.1-mini_mix_task_evaluation.json --ground-truth data/yfinance/mix_verified_evaluation.jsonl --generate-report --report-model gpt-4.1-2025-04-14 --report-output benchmarks/yfinance/report/gpt4.1-mini_evaluation_tasks_verified_report.md

mcp-eval evaluate --server mcp_servers/yfinance/server.py --model-config benchmarks/yfinance/eval_models/gpt-4.1-nano.json --tasks-file data/yfinance/mix_verified_evaluation.jsonl --output benchmarks/yfinance/results/gpt4.1-nano_mix_task_evaluation.json --prompt-file benchmarks/yfinance/evaluation_prompt.json --max-turns 30
mcp-eval analyze --predictions benchmarks/yfinance/results/gpt4.1-nano_mix_task_evaluation.json --ground-truth data/yfinance/mix_verified_evaluation.jsonl --generate-report --report-model gpt-4.1-2025-04-14 --report-output benchmarks/yfinance/report/gpt4.1-nano_evaluation_tasks_verified_report.md

mcp-eval evaluate --server mcp_servers/yfinance/server.py --model-config benchmarks/yfinance/eval_models/o3-mini.json --tasks-file data/yfinance/mix_verified_evaluation.jsonl --output benchmarks/yfinance/results/o3-mini_mix_task_evaluation.json --prompt-file benchmarks/yfinance/evaluation_prompt.json --max-turns 30
mcp-eval analyze --predictions benchmarks/yfinance/results/o3-mini_mix_task_evaluation.json --ground-truth data/yfinance/mix_verified_evaluation.jsonl --generate-report --report-model gpt-4.1-2025-04-14 --report-output benchmarks/yfinance/report/o3-mini_evaluation_tasks_verified_report.md

mcp-eval evaluate --server mcp_servers/yfinance/server.py --model-config benchmarks/yfinance/eval_models/o3.json --tasks-file data/yfinance/mix_verified_evaluation.jsonl --output benchmarks/yfinance/results/o3_mix_task_evaluation.json --prompt-file benchmarks/yfinance/evaluation_prompt.json --max-turns 30
mcp-eval analyze --predictions benchmarks/yfinance/results/o3_mix_task_evaluation.json --ground-truth data/yfinance/mix_verified_evaluation.jsonl --generate-report --report-model gpt-4.1-2025-04-14 --report-output benchmarks/yfinance/report/o3_evaluation_tasks_verified_report.md

mcp-eval evaluate --server mcp_servers/yfinance/server.py --model-config benchmarks/yfinance/eval_models/o4-mini.json --tasks-file data/yfinance/mix_verified_evaluation.jsonl --output benchmarks/yfinance/results/o4-mini_mix_task_evaluation.json --prompt-file benchmarks/yfinance/evaluation_prompt.json --max-turns 30
mcp-eval analyze --predictions benchmarks/yfinance/results/o4-mini_mix_task_evaluation.json --ground-truth data/yfinance/mix_verified_evaluation.jsonl --generate-report --report-model gpt-4.1-2025-04-14 --report-output benchmarks/yfinance/report/o4-mini_evaluation_tasks_verified_report.md


mkdir -p benchmarks/yfinance/logs
mkdir -p benchmarks/yfinance/results
mkdir -p benchmarks/yfinance/report

nohup mcp-eval evaluate --server mcp_servers/yfinance/server.py --model-config benchmarks/yfinance/eval_models/xlam_2_32b.json --tasks-file data/yfinance/mix_verified_evaluation.jsonl --output benchmarks/yfinance/results/xlam_2_32b_mix_task_evaluation.json --prompt-file benchmarks/yfinance/evaluation_prompt.json --max-turns 30 > benchmarks/yfinance/logs/xlam_2_32b_mix_task_evaluation.log 2>&1 &
nohup mcp-eval analyze --predictions benchmarks/yfinance/results/xlam_2_32b_mix_task_evaluation.json --ground-truth data/yfinance/mix_verified_evaluation.jsonl --generate-report --report-model gpt-4.1-2025-04-14 --report-output benchmarks/yfinance/report/xlam_2_32b_evaluation_tasks_verified_report.md > benchmarks/yfinance/logs/xlam_2_32b_evaluation_tasks_verified_report.log 2>&1 &

nohup mcp-eval evaluate --server mcp_servers/yfinance/server.py --model-config benchmarks/yfinance/eval_models/xlam_2_70b.json --tasks-file data/yfinance/mix_verified_evaluation.jsonl --output benchmarks/yfinance/results/xlam_2_70b_mix_task_evaluation.json --prompt-file benchmarks/yfinance/evaluation_prompt.json --max-turns 30 > benchmarks/yfinance/logs/xlam_2_70b_mix_task_evaluation.log 2>&1 &
nohup mcp-eval analyze --predictions benchmarks/yfinance/results/xlam_2_70b_mix_task_evaluation.json --ground-truth data/yfinance/mix_verified_evaluation.jsonl --generate-report --report-model gpt-4.1-2025-04-14 --report-output benchmarks/yfinance/report/xlam_2_70b_evaluation_tasks_verified_report.md > benchmarks/yfinance/logs/xlam_2_70b_evaluation_tasks_verified_report.log 2>&1 &