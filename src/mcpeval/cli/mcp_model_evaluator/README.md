# MCP Model Evaluator

The **MCP Model Evaluator** is a command-line tool that evaluates Large Language Models (LLMs) on MCP (Model Context Protocol) tasks to measure their tool-use capabilities. It connects to MCP servers, executes tasks using specified models, and generates detailed evaluation results with success metrics and conversation traces.

## Quick Start

```bash
# Basic usage - evaluate GPT-4o on healthcare tasks
mcp-eval evaluate \
  --servers mcp_servers/healthcare/server.py \
  --model-config benchmarks/healthcare/eval_models/gpt-4o.json \
  --tasks-file data/healthcare/evaluation_tasks_verified.jsonl \
  --output results/healthcare_evaluation.jsonl
```


## Overview

The model evaluator works by:

1. **Loading tasks** - Reads verified tasks from JSONL files
2. **Connecting to MCP servers** - Establishes connections to validate tool availability
3. **Model execution** - Runs tasks using specified LLM models through multi-turn conversations
4. **Result capture** - Records tool calls, conversations, and final responses
5. **Success analysis** - Determines task completion success and generates metrics

## What Model Evaluation Does

### ✅ **Successful Evaluation**
- **Task execution** - Attempts to complete tasks using the specified model
- **Tool calls** - Records all tool interactions during task execution
- **Conversation logging** - Captures multi-turn conversations between model and server
- **Success determination** - Evaluates whether tasks were completed successfully
- **Result serialization** - Saves detailed results in JSON format

### ❌ **Failed Evaluation**
- **Error handling** - Captures and logs execution errors
- **Partial results** - Saves whatever execution data was captured before failure
- **Resume capability** - Allows resuming evaluations from where they left off
- **Debugging info** - Provides detailed error information for troubleshooting

## Command Syntax

```bash
mcp-eval evaluate --servers <server_specification> --tasks-file <tasks_file> --model-config <model_config> [OPTIONS]
```

## Arguments

### Required Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `--servers` | MCP server specifications (one or more) | `mcp_servers/healthcare/server.py` |
| `--tasks-file` | Path to JSONL file containing tasks to evaluate | `data/healthcare/verified_tasks.jsonl` |

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
| `--model-config` | string | - | Path to JSON file containing model configuration |
| `--model` | string | `gpt-4o` | Model name (overridden by model-config) |
| `--output` | string | `evaluation_results.jsonl` | Output file path for results |
| `--num-tasks` | int | `-1` (all) | Number of tasks to evaluate |
| `--max-turns` | int | `30` | Maximum conversation turns per task |
| `--prompt-file` | string | - | JSON file containing system message |
| `--force-rerun` | flag | `false` | Force rerun all tasks (ignore existing results) |
| `--client-type` | string | `openai` | Client type (openai or gateway) |
| `--api-key` | string | - | OpenAI API key (or use `OPENAI_API_KEY` env var) |

## Model Configuration

Model configurations are specified in JSON files that define the model parameters and connection details.

### Standard OpenAI Models

```json
{
    "model": "gpt-4o-2024-11-20",
    "temperature": 0.01,
    "max_tokens": 16384
}
```

### OpenAI GPT-4.1 Models

```json
{
    "model": "gpt-4.1-mini-2025-04-14",
    "temperature": 0.01,
    "max_tokens": 16384
}
```

### OpenAI O3 Models

```json
{
    "model": "o3-2025-04-16",
    "max_completion_tokens": 100000
}
```

### Custom API Endpoints (e.g., Mistral)

```json
{
    "model": "mistral-large-2411",
    "api_key": "your-mistral-api-key",
    "temperature": 0.01,
    "max_tokens": 4000,
    "base_url": "https://api.mistral.ai/v1"
}
```

### Custom Self-Hosted Models

```json
{
    "model": "xlam_2_32b_fc_r",
    "api_key": "default",
    "temperature": 0.01,
    "max_tokens": 3000,
    "base_url": "http://xxx.xxx.xxx.xxx:po/v1"
}
```

### Advanced Configuration

```json
{
    "model": "gpt-4o-mini",
    "temperature": 0.1,
    "max_tokens": 4000,
    "top_p": 0.9,
    "frequency_penalty": 0.0,
    "presence_penalty": 0.0
}
```

## Examples

### Basic Examples

#### 1. Evaluate GPT-4o on Healthcare Tasks

```bash
mcp-eval evaluate \
  --servers mcp_servers/healthcare/server.py \
  --model-config benchmarks/healthcare/eval_models/gpt-4o.json \
  --tasks-file data/healthcare/evaluation_tasks_verified.jsonl \
  --output results/healthcare_gpt4o_evaluation.jsonl
```

#### 2. Evaluate with Custom Prompt

```bash
mcp-eval evaluate \
  --servers mcp_servers/healthcare/server.py \
  --model-config benchmarks/healthcare/eval_models/gpt-4o.json \
  --tasks-file data/healthcare/evaluation_tasks_verified.jsonl \
  --prompt-file benchmarks/healthcare/evaluation_prompt.json \
  --output results/healthcare_gpt4o_evaluation.jsonl \
  --max-turns 30
```

#### 3. Evaluate External Server (e.g., National Parks)

```bash
mcp-eval evaluate \
  --servers mcp-server-nationalparks^NPS_API_KEY=$NPS_API_KEY \
  --model-config benchmarks/national_parks/eval_models/gpt-4.1-mini.json \
  --tasks-file data/national_parks/evaluation_tasks_verified.jsonl \
  --output results/national_parks_gpt41mini_evaluation.jsonl
```

### Advanced Examples

#### 4. Evaluate Custom Model with API Endpoint (Mistral)

```bash
mcp-eval evaluate \
  --servers mcp_servers/sports/server.py \
  --model-config benchmarks/sports/eval_models/mistral-large.json \
  --tasks-file data/sports/evaluation_tasks_verified.jsonl \
  --output results/sports_mistral_large_evaluation.jsonl \
  --max-turns 25
```

#### 5. Evaluate Multiple Servers

```bash
mcp-eval evaluate \
  --servers mcp_servers/healthcare/server.py mcp_servers/travel_assistant/server.py \
  --model-config benchmarks/multi_server/eval_models/gpt-4o.json \
  --tasks-file data/multi_server/evaluation_tasks_verified.jsonl \
  --output results/multi_server_gpt4o_evaluation.jsonl
```

#### 6. Limited Evaluation with Force Rerun

```bash
mcp-eval evaluate \
  --servers mcp_servers/sports/server.py \
  --model-config benchmarks/sports/eval_models/gpt-4o-mini.json \
  --tasks-file data/sports/evaluation_tasks_verified.jsonl \
  --num-tasks 50 \
  --force-rerun \
  --output results/sports_gpt4o_mini_evaluation.jsonl
```

#### 7. High-Turn Evaluation for Complex Tasks

```bash
mcp-eval evaluate \
  --servers mcp_servers/healthcare/server.py \
  --model-config benchmarks/healthcare/eval_models/gpt-4.1-mini.json \
  --tasks-file data/healthcare/complex_tasks_verified.jsonl \
  --max-turns 50 \
  --prompt-file benchmarks/healthcare/evaluation_prompt.json \
  --output results/healthcare_gpt41mini_complex_evaluation.jsonl
```

## Custom Evaluation Prompts

You can customize model evaluation by providing a JSON file with a system message:

### Prompt File Format

Create a JSON file with the following structure:

```json
{
  "system": "You are an AI assistant that use tools to complete a task. The current date is 2025-06-05 (20250605). Continue to use the tools to complete task until the task is completed."
}
```

### Example Prompt Files

You can find example evaluation prompt files in the benchmarks directory:

- `benchmarks/healthcare/evaluation_prompt.json`
- `benchmarks/national_parks/evaluation_prompt.json`
- `benchmarks/sports/evaluation_prompt.json`
- `benchmarks/yfinance/evaluation_prompt.json`

## Output Format

The evaluation results are saved in JSONL format (one JSON object per line) with detailed information about each task execution:

```jsonl
{"task_id": "task_001", "success": true, "tool_calls": [{"tool_name": "get_patient_medications", "tool_parameters": {"patient_id": "P12345"}}], "final_response": "Successfully retrieved medication history for patient P12345. The patient is currently taking...", "conversation": [{"role": "user", "content": "Find patient medication history for patient P12345"}, {"role": "assistant", "content": "I'll retrieve the medication history for patient P12345.", "tool_calls": [...]}], "task": {"id": "task_001", "name": "Find patient medication history", "description": "Retrieve the complete medication history for patient ID 'P12345'", "goal": "Obtain comprehensive medication history"}, "model": "gpt-4o-2024-11-20", "client_type": "openai"}
```

Each line contains a complete evaluation result for one task.

## Parallel Evaluation

You can run multiple evaluations in parallel to evaluate different models simultaneously:

```bash
# Start multiple evaluations in parallel
mcp-eval evaluate \
  --servers mcp_servers/healthcare/server.py \
  --model-config benchmarks/healthcare/eval_models/gpt-4o.json \
  --tasks-file data/healthcare/verified_tasks.jsonl \
  --output results/healthcare_gpt4o_evaluation.jsonl &

mcp-eval evaluate \
  --servers mcp_servers/healthcare/server.py \
  --model-config benchmarks/healthcare/eval_models/gpt-4o-mini.json \
  --tasks-file data/healthcare/verified_tasks.jsonl \
  --output results/healthcare_gpt4o_mini_evaluation.jsonl &

mcp-eval evaluate \
  --servers mcp_servers/healthcare/server.py \
  --model-config benchmarks/healthcare/eval_models/gpt-4.1-mini.json \
  --tasks-file data/healthcare/verified_tasks.jsonl \
  --output results/healthcare_gpt41_mini_evaluation.jsonl &

# Wait for all evaluations to complete
wait

echo "All evaluations completed!"
```

## Resume Capability

The evaluator automatically skips already evaluated tasks:

```bash
# First run - evaluates 50 tasks
mcp-eval evaluate \
  --servers mcp_servers/healthcare/server.py \
  --model-config benchmarks/healthcare/eval_models/gpt-4o.json \
  --tasks-file data/healthcare/verified_tasks.jsonl \
  --num-tasks 50 \
  --output results/healthcare_evaluation.jsonl

# Second run - continues from task 51
mcp-eval evaluate \
  --servers mcp_servers/healthcare/server.py \
  --model-config benchmarks/healthcare/eval_models/gpt-4o.json \
  --tasks-file data/healthcare/verified_tasks.jsonl \
  --num-tasks 100 \
  --output results/healthcare_evaluation.jsonl
```

## Environment Variables

The tool supports the following environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for model access | `sk-...` |
| `MISTRAL_API_KEY` | Mistral API key for model access | `your_mistral_key` |
| `NPS_API_KEY` | National Parks Service API key | `your_nps_key` |
| `X_API_KEY` | Custom API key for external services | `your_api_key` |
| `MCP_EVAL_LOG_LEVEL` | Log level | `DEBUG` |

### Using Environment Variables

```bash
# Set environment variables
export OPENAI_API_KEY="sk-your-openai-key"
export NPS_API_KEY="your-nps-api-key"
export MISTRAL_API_KEY="your-mistral-api-key"

# Use in server specification
mcp-eval evaluate \
  --servers mcp-server-nationalparks^NPS_API_KEY=$NPS_API_KEY \
  --model-config benchmarks/national_parks/eval_models/gpt-4o.json \
  --tasks-file data/national_parks/verified_tasks.jsonl \
  --output results/national_parks_evaluation.jsonl
```

### Using Mistral API

```bash
# Create Mistral model config
cat > benchmarks/sports/eval_models/mistral-large.json << 'EOF'
{
    "model": "mistral-large-2411",
    "api_key": "your-mistral-api-key",
    "temperature": 0.01,
    "max_tokens": 4000,
    "base_url": "https://api.mistral.ai/v1"
}
EOF

# Run evaluation with Mistral
mcp-eval evaluate \
  --servers mcp_servers/sports/server.py \
  --model-config benchmarks/sports/eval_models/mistral-large.json \
  --tasks-file data/sports/evaluation_tasks_verified.jsonl \
  --output results/sports_mistral_evaluation.jsonl
```

## Best Practices

### 1. Model Selection

- **GPT-4o**: Best overall performance for most tasks
- **GPT-4.1-mini**: Cost-effective with good performance
- **GPT-4o-mini**: Fastest and most cost-effective
- **O3**: Highest capability for complex reasoning tasks
- **Mistral-large**: Strong performance for multilingual tasks and custom deployments

### 2. Max Turns Configuration

- **Simple tasks**: 10-20 turns
- **Complex tasks**: 30-50 turns
- **Multi-step workflows**: 50+ turns

### 3. Temperature Settings

- **Deterministic tasks**: 0.01-0.1
- **Creative tasks**: 0.3-0.7
- **Exploratory tasks**: 0.7-1.0

### 4. Batch Processing

```bash
# Process different domains in batches
for domain in healthcare sports yfinance; do
  mcp-eval evaluate \
    --servers mcp_servers/$domain/server.py \
    --model-config benchmarks/$domain/eval_models/gpt-4o.json \
    --tasks-file data/$domain/verified_tasks.jsonl \
    --output results/${domain}_gpt4o_evaluation.jsonl
done
```

## Performance Monitoring

The evaluator provides real-time progress updates and final statistics:

```bash
# Example output
🚀 Executing: evaluate
📊 Evaluation Summary:
──────────────────────────────────────────────────
Model: gpt-4o-2024-11-20
Client Type: openai
Tasks evaluated: 100
Tasks completed successfully: 87
Success rate: 87.00%
Results saved to: results/healthcare_evaluation.jsonl
```

## Troubleshooting

### Common Issues

#### 1. API Key Errors

```bash
# Check API key is set
echo $OPENAI_API_KEY

# Set API key if missing
export OPENAI_API_KEY="sk-your-key-here"

# Verify key works
mcp-eval evaluate \
  --servers mcp_servers/healthcare/server.py \
  --model-config benchmarks/healthcare/eval_models/gpt-4o.json \
  --tasks-file data/healthcare/verified_tasks.jsonl \
  --num-tasks 1 \
  --output test_evaluation.jsonl
```

#### 2. Server Connection Issues

```bash
# Test server connectivity
mcp-eval evaluate \
  --servers mcp_servers/healthcare/server.py \
  --model-config benchmarks/healthcare/eval_models/gpt-4o.json \
  --tasks-file data/healthcare/verified_tasks.jsonl \
  --num-tasks 1 \
  --output test_evaluation.jsonl

# For external servers, verify installation
npm install -g @openbnb/mcp-server-airbnb
```

#### 3. Model Configuration Issues

```bash
# Validate model config format
python -c "
import json
with open('benchmarks/healthcare/eval_models/gpt-4o.json') as f:
    config = json.load(f)
    print('Model config:', config)
"

# Test with minimal config
echo '{"model": "gpt-4o-mini", "temperature": 0.1}' > test_config.json
```

#### 4. Task Format Issues

```bash
# Validate task file format
python -c "
import json
with open('data/healthcare/verified_tasks.jsonl') as f:
    for i, line in enumerate(f):
        try:
            task = json.loads(line)
            print(f'Task {i+1}: {task.get(\"name\", \"Unknown\")}')
        except json.JSONDecodeError as e:
            print(f'Invalid JSON on line {i+1}: {e}')
        if i >= 4:  # Show first 5 tasks
            break
"
```

#### 5. Memory Issues

```bash
# Process in smaller batches
for i in {1..10}; do
  start=$((($i-1)*10))
  end=$(($i*10))
  
  # Create batch file
  head -n $end data/healthcare/verified_tasks.jsonl | tail -n 10 > batch_$i.jsonl
  
  # Evaluate batch
  mcp-eval evaluate \
    --servers mcp_servers/healthcare/server.py \
    --model-config benchmarks/healthcare/eval_models/gpt-4o.json \
    --tasks-file batch_$i.jsonl \
    --output results/healthcare_batch_$i_evaluation.jsonl
done
```

#### 6. Debug Mode

```bash
# Enable detailed logging
export MCP_EVAL_LOG_LEVEL=DEBUG

mcp-eval evaluate \
  --servers mcp_servers/healthcare/server.py \
  --model-config benchmarks/healthcare/eval_models/gpt-4o.json \
  --tasks-file data/healthcare/verified_tasks.jsonl \
  --num-tasks 1 \
  --output debug_evaluation.jsonl
```

## Integration with Other Tools

The evaluation results can be used with other MCP-Eval tools:

```bash
# Complete evaluation workflow
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
  --model-config benchmarks/healthcare/eval_models/gpt-4o.json \
  --tasks-file data/healthcare/verified_tasks.jsonl \
  --output results/healthcare_evaluation.jsonl

# 4. Analyze results
mcp-eval analyze \
  --predictions results/healthcare_evaluation.jsonl \
  --ground-truth data/healthcare/verified_tasks.jsonl \
  --generate-report \
  --report-output results/healthcare_report.md

# 5. LLM judging
mcp-eval judge \
  --input-file results/healthcare_evaluation.jsonl \
  --output-dir results/healthcare_judge \
  --model gpt-4o
```

## Performance Tips

### 1. Optimize for Speed

```bash
# Use faster model with fewer turns
mcp-eval evaluate \
  --servers mcp_servers/healthcare/server.py \
  --model-config benchmarks/healthcare/eval_models/gpt-4o-mini.json \
  --tasks-file data/healthcare/verified_tasks.jsonl \
  --max-turns 15 \
  --output results/healthcare_fast_evaluation.jsonl
```

### 2. Optimize for Quality

```bash
# Use best model with more turns
mcp-eval evaluate \
  --servers mcp_servers/healthcare/server.py \
  --model-config benchmarks/healthcare/eval_models/gpt-4.1-mini.json \
  --tasks-file data/healthcare/verified_tasks.jsonl \
  --max-turns 50 \
  --output results/healthcare_quality_evaluation.jsonl
```

### 3. Cost Optimization

```bash
# Use cost-effective settings
mcp-eval evaluate \
  --servers mcp_servers/healthcare/server.py \
  --model-config benchmarks/healthcare/eval_models/gpt-4o-mini.json \
  --tasks-file data/healthcare/verified_tasks.jsonl \
  --max-turns 20 \
  --output results/healthcare_cost_effective_evaluation.jsonl
```



## Support

For additional help:

- Use `mcp-eval evaluate --help` for command-specific help
- Check the main CLI documentation: `src/mcpeval/cli/README.md`
- Review example benchmark configurations in `benchmarks/`
- Enable debug logging: `export MCP_EVAL_LOG_LEVEL=DEBUG`

## Related Commands

- `mcp-eval generate-tasks` - Generate tasks for evaluation
- `mcp-eval verify-tasks` - Verify tasks before evaluation
- `mcp-eval analyze` - Analyze evaluation results
- `mcp-eval judge` - LLM judging of evaluation results
- `mcp-eval auto` - Run complete evaluation workflow