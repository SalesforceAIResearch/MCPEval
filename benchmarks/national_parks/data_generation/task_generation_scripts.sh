SERVERS="mcp-server-nationalparks^NPS_API_KEY=$NPS_API_KEY" mcp-eval generate-tasks --servers $SERVERS --model-config benchmarks/national_parks/eval_models/gpt-4o.json --num-tasks 100 --prompt-file benchmarks/national_parks/data_generation/generation_prompt.json --output data/national_parks/tasks.jsonl



