uv run mcp-eval revalidate-tasks --verified-tasks-file data/national_parks/evaluation_tasks_verified.jsonl --model-config benchmarks/national_parks/eval_models/gpt-5.json --output data/national_parks/revalidated_tasks_gpt-5.jsonl --prompt-file benchmarks/national_parks/data_generation/revalidation_prompt.json

