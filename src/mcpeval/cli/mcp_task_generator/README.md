# MCP Task Generator

The **MCP Task Generator** is a command-line tool that automatically connects to MCP (Model Context Protocol) servers and generates tasks for testing LLM tool use capabilities. It uses AI models to create realistic, executable tasks based on the available tools from your MCP servers.

## Quick Start

```bash
# Basic usage - generate 10 tasks for a healthcare server
mcp-eval generate-tasks \
  --servers mcp_servers/healthcare/server.py \
  --model gpt-4.1-2025-04-14 \
  --num-tasks 10 \
  --output data/healthcare_tasks.jsonl
```

## Overview

The task generator works by:

1. **Connecting to MCP servers** - Establishes connections to one or more MCP servers
2. **Discovering available tools** - Retrieves all available tools and their schemas
3. **Generating tasks** - Uses AI models to create realistic tasks that utilize the available tools
4. **Saving results** - Outputs tasks in JSONL format for later verification and evaluation

## Command Syntax

```bash
mcp-eval generate-tasks --servers <server_specification> [OPTIONS]
```

## Arguments

### Required Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `--servers` | MCP server specifications (one or more) | `mcp_servers/healthcare/server.py` |

### Server Specification Format

Servers can be specified in several formats:

```bash
# Simple server path
--servers mcp_servers/healthcare/server.py

# Server with arguments
--servers @openbnb/mcp-server-airbnb:--ignore-robots-txt

# Server with environment variables
--servers mcp-server-nationalparks^NPS_API_KEY=your_key_here

# Server with both arguments and environment variables
--servers server_name:--arg1,--arg2^ENV_VAR=value1,ENV_VAR2=value2

# Multiple servers
--servers server1.py server2.py @external/server3
```

### Optional Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--output` | string | `generated_tasks.jsonl` | Output file path for generated tasks |
| `--num-tasks` | int | `10` | Number of tasks to generate |
| `--model` | string | `gpt-4.1-2025-04-14` | OpenAI model for task generation |
| `--model-config` | string | - | JSON file containing model configuration (takes priority over individual model parameters) |
| `--prompt-file` | string | - | JSON file containing custom prompts |
| `--existing-files` | list | `[]` | Existing task files to load (avoid duplicates) |
| `--temperature` | float | `0.2` | Model temperature for generation |
| `--max-tokens` | int | `4000` | Maximum tokens per generation |
| `--top-p` | float | `0.95` | Top-p sampling parameter |
| `--api-key` | string | - | OpenAI API key (or use `OPENAI_API_KEY` env var) |

## Examples

### Basic Examples

#### 1. Generate Tasks for Healthcare Server

```bash
mcp-eval generate-tasks \
  --servers mcp_servers/healthcare/server.py \
  --model gpt-4.1-2025-04-14 \
  --num-tasks 50 \
  --output data/healthcare/evaluation_tasks.jsonl
```

#### 2. Generate Tasks with Custom Prompts

```bash
mcp-eval generate-tasks \
  --servers mcp_servers/healthcare/server.py \
  --model gpt-4.1-2025-04-14 \
  --num-tasks 100 \
  --prompt-file benchmarks/healthcare/data_generation/task_generation_prompt.json \
  --output data/healthcare/evaluation_tasks.jsonl \
  --temperature 0.9 \
  --top-p 0.9
```

#### 3. Generate Tasks with Model Configuration File

```bash
mcp-eval generate-tasks \
  --servers mcp_servers/healthcare/server.py \
  --model-config benchmarks/healthcare/eval_models/gpt-4o.json \
  --num-tasks 50 \
  --output data/healthcare/evaluation_tasks.jsonl
```

#### 4. Generate Tasks for External Server (e.g., Airbnb)

```bash
mcp-eval generate-tasks \
  --servers @openbnb/mcp-server-airbnb:--ignore-robots-txt \
  --model gpt-4.1-2025-04-14 \
  --num-tasks 120 \
  --output data/airbnb/evaluation_tasks.jsonl
```

### Advanced Examples

#### 4. Generate Tasks with Environment Variables

```bash
mcp-eval generate-tasks \
  --servers mcp-server-nationalparks^NPS_API_KEY=$NPS_API_KEY \
  --model gpt-4.1-2025-04-14 \
  --num-tasks 120 \
  --prompt-file benchmarks/national_parks/task_generation_prompt.json \
  --output data/national_parks/evaluation_tasks.jsonl \
  --temperature 0.9 \
  --top-p 0.9
```

#### 5. Generate Tasks from Multiple Servers

```bash
mcp-eval generate-tasks \
  --servers mcp_servers/healthcare/server.py mcp_servers/travel_assistant/server.py \
  --model gpt-4.1-2025-04-14 \
  --num-tasks 200 \
  --output data/multi_server_tasks.jsonl
```

#### 6. Resume Generation with Existing Tasks

```bash
mcp-eval generate-tasks \
  --servers mcp_servers/healthcare/server.py \
  --model gpt-4.1-2025-04-14 \
  --num-tasks 200 \
  --existing-files data/healthcare/existing_tasks.jsonl data/healthcare/more_tasks.jsonl \
  --output data/healthcare/complete_tasks.jsonl
```

#### 7. High Creativity Generation

```bash
mcp-eval generate-tasks \
  --servers mcp_servers/sports/server.py \
  --model gpt-4.1-2025-04-14 \
  --num-tasks 100 \
  --temperature 0.9 \
  --top-p 0.9 \
  --max-tokens 5000 \
  --output data/sports/creative_tasks.jsonl
```

## Model Configuration

You can specify model settings using a JSON configuration file with the `--model-config` parameter:

### Model Configuration File Format

Create a JSON file with model settings:

```json
{
  "model": "gpt-4.1-2025-04-14",
  "temperature": 0.2,
  "max_tokens": 4000,
  "top_p": 0.95
}
```

**Important**: Model configuration files take priority over individual CLI parameters. If you specify `--model-config`, the individual `--model`, `--temperature`, `--max-tokens`, and `--top-p` arguments will be ignored.

### Example Model Configuration Files

You can find example model configuration files in the benchmarks directory:

- `benchmarks/healthcare/eval_models/gpt-4o.json`
- `benchmarks/national_parks/eval_models/gpt-4.1-mini.json`
- `benchmarks/airbnb/eval_models/gpt-4o.json`

## Custom Prompts

You can customize task generation by providing a JSON file with system and user messages:

### Prompt File Format

Create a JSON file with the following structure:

```json
{
  "system": "You are a helpful assistant that generates tasks for testing LLM tool use capabilities regarding a set of healthcare and medical tools.\nTasks should be specific, clear, and include expected tool calls where applicable. Ensure all the required information from the tools arguments is explicitly mentioned in the task description, especially those related to patient identifiers, medical conditions, medications, and appointment scheduling.\n\nCreate real-world healthcare tasks such as practical scenarios that healthcare professionals, patients, or administrative staff might actually encounter when using medical management tools.\n\nIMPORTANT: Your response MUST be ONLY valid JSON, with NO markdown, NO comments, and NO extra text. Do NOT include any explanations or formatting outside the JSON. All property names and string values must be double-quoted. The output must be directly parsable by Python's json.loads().\n\nThe required JSON structure is:\n{\n  \"name\": \"Task name\",\n  \"description\": \"Detailed task description\",\n  \"goal\": \"Goal of the task\",\n  \"tool_calls\": [\n    {\n      \"tool_name\": \"name of the tool\",\n      \"tool_parameters\": {\n        \"param1\": \"value1\",\n        \"param2\": \"value2\"\n      }\n    }\n  ]\n}",
  "user": "Generate a realistic healthcare task that requires using the available medical tools."
}
```

### Example Prompt Files

You can find example prompt files in the benchmarks directory:

- `benchmarks/healthcare/data_generation/task_generation_prompt.json`
- `benchmarks/national_parks/task_generation_prompt.json`
- `benchmarks/airbnb/data_generation/task_generation_prompt.json`
- `benchmarks/sports/data_generation/task_generation_prompt.json`

## Output Format

The generated tasks are saved in JSONL format, where each line contains a JSON object representing a task:

```json
{
  "name": "Find patient medication history",
  "description": "Retrieve the complete medication history for patient ID 'P12345' and check for any potential drug interactions with a newly prescribed medication 'Warfarin'.",
  "goal": "Obtain comprehensive medication history and identify potential drug interactions",
  "tool_calls": [
    {
      "tool_name": "get_patient_medications",
      "tool_parameters": {
        "patient_id": "P12345"
      }
    },
    {
      "tool_name": "check_drug_interactions",
      "tool_parameters": {
        "medication": "Warfarin",
        "patient_id": "P12345"
      }
    }
  ]
}
```

## Environment Variables

The tool supports the following environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for task generation | `sk-...` |
| `NPS_API_KEY` | National Parks Service API key | `your_nps_key` |
| `X_API_KEY` | API key for external services | `your_api_key` |

### Using Environment Variables

```bash
# Set environment variables
export OPENAI_API_KEY="sk-your-openai-key"
export NPS_API_KEY="your-nps-api-key"

# Use in server specification
mcp-eval generate-tasks \
  --servers mcp-server-nationalparks^NPS_API_KEY=$NPS_API_KEY \
  --model gpt-4.1-2025-04-14 \
  --num-tasks 50 \
  --output data/national_parks_tasks.jsonl
```

## Best Practices

### 1. Model Selection

- Use `gpt-4.1-2025-04-14` for high-quality task generation
- Use `gpt-4o-mini` for faster, cost-effective generation
- Use `gpt-4o` for balanced quality and speed

### 2. Temperature Settings

- **Low creativity** (0.0-0.3): For consistent, focused tasks
- **Balanced** (0.3-0.7): For varied but reasonable tasks
- **High creativity** (0.7-1.0): For diverse, creative tasks

### 3. Prompt Engineering

- Be specific about task requirements
- Include domain-specific context
- Specify expected tool usage patterns
- Request realistic scenarios

### 4. Batch Processing

```bash
# Generate tasks in batches to avoid rate limits
for i in {1..5}; do
  mcp-eval generate-tasks \
    --servers mcp_servers/healthcare/server.py \
    --num-tasks 40 \
    --existing-files data/healthcare/tasks_batch_*.jsonl \
    --output data/healthcare/tasks_batch_$i.jsonl
  sleep 10
done
```

## Troubleshooting

### Common Issues

#### 1. Connection Errors

```bash
# Check server accessibility
mcp-eval generate-tasks --servers mcp_servers/healthcare/server.py --num-tasks 1

# For external servers, verify installation
npm install -g @openbnb/mcp-server-airbnb
```

#### 2. API Rate Limits

```bash
# Reduce generation speed
mcp-eval generate-tasks \
  --servers mcp_servers/healthcare/server.py \
  --num-tasks 50 \
  --temperature 0.1 \
  --output data/healthcare_tasks.jsonl
```

#### 3. Environment Variable Issues

```bash
# Verify environment variables are set
echo $OPENAI_API_KEY
echo $NPS_API_KEY

# Use .env file
echo "OPENAI_API_KEY=sk-your-key" > .env
echo "NPS_API_KEY=your-nps-key" >> .env
```

#### 4. JSON Parsing Errors

```bash
# Check prompt file format
python -c "import json; print(json.load(open('your_prompt.json')))"

# Use verbose logging
export MCP_EVAL_LOG_LEVEL=DEBUG
mcp-eval generate-tasks --servers mcp_servers/healthcare/server.py --num-tasks 1
```

## Integration with Other Tools

The generated tasks can be used with other MCP-Eval tools:

```bash
# Complete workflow
# 1. Generate tasks
mcp-eval generate-tasks \
  --servers mcp_servers/healthcare/server.py \
  --num-tasks 100 \
  --output data/healthcare/tasks.jsonl

# 2. Verify tasks
mcp-eval verify-tasks \
  --servers mcp_servers/healthcare/server.py \
  --tasks-file data/healthcare/tasks.jsonl \
  --output data/healthcare/verified_tasks.jsonl

# 3. Evaluate models
mcp-eval evaluate \
  --servers mcp_servers/healthcare/server.py \
  --tasks-file data/healthcare/verified_tasks.jsonl \
  --model-config eval_models/gpt-4o.json \
  --output results/healthcare_evaluation.json

# 4. Analyze results
mcp-eval analyze \
  --predictions results/healthcare_evaluation.json \
  --ground-truth data/healthcare/verified_tasks.jsonl \
  --generate-report \
  --report-output results/healthcare_report.md
```

## Performance Tips

### 1. Optimize for Speed

```bash
# Use faster model with lower temperature
mcp-eval generate-tasks \
  --servers mcp_servers/healthcare/server.py \
  --model gpt-4o-mini \
  --temperature 0.1 \
  --num-tasks 100 \
  --output data/healthcare_tasks.jsonl
```

### 2. Optimize for Quality

```bash
# Use best model with higher temperature
mcp-eval generate-tasks \
  --servers mcp_servers/healthcare/server.py \
  --model gpt-4.1-2025-04-14 \
  --temperature 0.7 \
  --max-tokens 5000 \
  --num-tasks 50 \
  --output data/healthcare_tasks.jsonl
```

### 3. Cost Optimization

```bash
# Use cost-effective settings
mcp-eval generate-tasks \
  --servers mcp_servers/healthcare/server.py \
  --model gpt-4o-mini \
  --temperature 0.2 \
  --max-tokens 2000 \
  --num-tasks 200 \
  --output data/healthcare_tasks.jsonl
```

## Support

For additional help:

- Use `mcp-eval generate-tasks --help` for command-specific help
- Check the main CLI documentation: `src/mcpeval/cli/README.md`
- Review example benchmark configurations in `benchmarks/`
- Enable debug logging: `export MCP_EVAL_LOG_LEVEL=DEBUG`

## Related Commands

- `mcp-eval verify-tasks` - Verify generated tasks
- `mcp-eval evaluate` - Evaluate models with tasks
- `mcp-eval analyze` - Analyze evaluation results
- `mcp-eval auto` - Run complete evaluation workflow 