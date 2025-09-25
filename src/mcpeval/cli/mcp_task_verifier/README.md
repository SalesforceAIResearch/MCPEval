# MCP Task Verifier

The **MCP Task Verifier** is a command-line tool that verifies generated tasks against MCP (Model Context Protocol) servers to ensure they can be successfully executed. It uses AI models to test task completeness, validate tool usage, and enhance task descriptions through multi-turn conversations with the MCP servers.

## Quick Start

```bash
# Basic usage - verify tasks against a healthcare server
mcp-eval verify-tasks \
  --servers mcp_servers/healthcare/server.py \
  --tasks-file data/healthcare/evaluation_tasks.jsonl \
  --model gpt-4.1-2025-04-14 \
  --output data/healthcare/evaluation_tasks_verified.jsonl
```

## Installation

The task verifier is installed as part of the mcpeval package:

```bash
# From the repository root directory
uv pip install -e .
```

## Overview

The task verifier works by:

1. **Loading tasks** - Reads task descriptions from JSONL files
2. **Connecting to MCP servers** - Establishes connections to verify task executability
3. **Multi-turn verification** - Uses AI models to attempt task completion through conversation
4. **Validation and enhancement** - Identifies missing information and requests clarification
5. **Saving results** - Outputs verified tasks and unverified tasks to separate files

## What Task Verification Does

### ✅ **Successful Verification**
- **Executes tasks** - Attempts to complete tasks using available tools
- **Records conversations** - Captures multi-turn interactions with the server
- **Saves tool calls** - Records actual tool calls made during verification
- **Captures responses** - Stores final responses and tool call results

### ❌ **Failed Verification**
- **Identifies gaps** - Finds missing information or unclear specifications
- **Requests updates** - Generates feedback for task improvement
- **Separates problematic tasks** - Saves unverified tasks for manual review
- **Provides suggestions** - Offers specific improvements needed

## Command Syntax

```bash
mcp-eval verify-tasks --servers <server_specification> --tasks-file <tasks_file> [OPTIONS]
```

## Arguments

### Required Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `--servers` | MCP server specifications (one or more) | `mcp_servers/healthcare/server.py` |
| `--tasks-file` | Path to JSONL file containing tasks to verify | `data/healthcare/tasks.jsonl` |

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
| `--output` | string | `verified_<input_filename>` | Output file path for verified tasks |
| `--model` | string | `gpt-4o` | OpenAI model for verification |
| `--model-config` | string | - | JSON file containing model configuration (takes priority over individual model parameters) |
| `--num-tasks` | int | `-1` (all) | Number of tasks to verify |
| `--max-turns` | int | `10` | Maximum conversation turns per task |
| `--prompt-file` | string | - | JSON file containing system message |
| `--non-interactive` | flag | `false` | Run in non-interactive mode |
| `--api-key` | string | - | OpenAI API key (or use `OPENAI_API_KEY` env var) |

## Examples

### Basic Examples

#### 1. Verify Healthcare Tasks

```bash
mcp-eval verify-tasks \
  --servers mcp_servers/healthcare/server.py \
  --tasks-file data/healthcare/evaluation_tasks.jsonl \
  --model gpt-4.1-2025-04-14 \
  --output data/healthcare/evaluation_tasks_verified.jsonl
```

#### 2. Verify Tasks with Model Configuration File

```bash
mcp-eval verify-tasks \
  --servers mcp_servers/healthcare/server.py \
  --tasks-file data/healthcare/evaluation_tasks.jsonl \
  --model-config benchmarks/healthcare/eval_models/gpt-4o.json \
  --output data/healthcare/evaluation_tasks_verified.jsonl
```

#### 3. Verify Tasks with Custom Prompt

```bash
mcp-eval verify-tasks \
  --servers mcp_servers/healthcare/server.py \
  --tasks-file data/healthcare/evaluation_tasks.jsonl \
  --model gpt-4.1-2025-04-14 \
  --prompt-file benchmarks/healthcare/data_generation/task_verification_prompt.json \
  --output data/healthcare/evaluation_tasks_verified.jsonl
```

#### 4. Verify External Server Tasks (e.g., Airbnb)

```bash
mcp-eval verify-tasks \
  --servers @openbnb/mcp-server-airbnb:--ignore-robots-txt \
  --tasks-file data/airbnb/evaluation_tasks.jsonl \
  --model gpt-4.1-2025-04-14 \
  --output data/airbnb/evaluation_tasks_verified.jsonl
```

### Advanced Examples

#### 4. Verify with Environment Variables

```bash
mcp-eval verify-tasks \
  --servers mcp-server-nationalparks^NPS_API_KEY=$NPS_API_KEY \
  --tasks-file data/national_parks/evaluation_tasks.jsonl \
  --model gpt-4.1-2025-04-14 \
  --output data/national_parks/evaluation_tasks_verified.jsonl
```

#### 5. Verify Multiple Servers

```bash
mcp-eval verify-tasks \
  --servers mcp_servers/healthcare/server.py mcp_servers/travel_assistant/server.py \
  --tasks-file data/multi_server_tasks.jsonl \
  --model gpt-4.1-2025-04-14 \
  --output data/multi_server_tasks_verified.jsonl
```

#### 6. Limited Verification with Non-Interactive Mode

```bash
mcp-eval verify-tasks \
  --servers mcp_servers/sports/server.py \
  --tasks-file data/sports/evaluation_tasks.jsonl \
  --model gpt-4.1-2025-04-14 \
  --num-tasks 50 \
  --non-interactive \
  --output data/sports/evaluation_tasks_verified.jsonl
```

#### 7. Complex Verification with Extended Turns

```bash
mcp-eval verify-tasks \
  --servers mcp_servers/healthcare/server.py \
  --tasks-file data/healthcare/complex_tasks.jsonl \
  --model gpt-4.1-2025-04-14 \
  --max-turns 20 \
  --prompt-file benchmarks/healthcare/data_generation/task_verification_prompt.json \
  --output data/healthcare/complex_tasks_verified.jsonl
```

## Custom Verification Prompts

You can customize task verification by providing a JSON file with a system message:

### Prompt File Format

Create a JSON file with the following structure:

```json
{
  "system": "You are an AI assistant that helps verify and enhance task descriptions for healthcare and medical data management using healthcare tools. The current date is 2025-06-05.\n\nYour role is to examine healthcare task descriptions and ensure they contain all necessary information for successful completion using the available medical tools. **Required information** for healthcare tasks:\n- **Patient identifiers** (when applicable) that are realistic but anonymized\n- **Medical conditions and symptoms** that are clearly described\n- **Medication names and dosages** that are accurate and realistic\n- **Appointment dates and times** that are reasonable and future-dated\n- **Healthcare provider specialties** that match the medical needs\n- **Clear medical terminology** that is appropriate for the context\n\nEnsure tasks are:\n- Medically realistic and plausible\n- Compliant with healthcare privacy considerations (no real patient data)\n- Appropriate for the available healthcare tools\n- Clear about what medical information or action is needed\n\nIf a task is missing critical medical information, contains unrealistic medical scenarios, or has unclear healthcare specifications, use the request_task_updating tool to ask for clarification. Otherwise, proceed with the available tools to complete the requested healthcare task."
}
```

### Example Prompt Files

You can find example verification prompt files in the benchmarks directory:

- `benchmarks/healthcare/data_generation/task_verification_prompt.json`
- `benchmarks/sports/data_generation/task_verification_prompt.json`
- `benchmarks/filesystem/task_verification_prompt.json`
- `benchmarks/yfinance/data_generation/task_verification_prompt.json`

## Model Configuration

You can specify model settings using a JSON configuration file with the `--model-config` parameter:

### Model Configuration File Format

Create a JSON file with model settings:

```json
{
  "model": "gpt-4.1-2025-04-14",
  "temperature": 0.01,
  "max_tokens": 16384
}
```

**Important**: Model configuration files take priority over individual CLI parameters. If you specify `--model-config`, the individual `--model` parameter will be ignored.

### Example Model Configuration Files

You can find example model configuration files in the benchmarks directory:

- `benchmarks/healthcare/eval_models/gpt-4o.json`
- `benchmarks/national_parks/eval_models/gpt-4.1-mini.json`
- `benchmarks/airbnb/eval_models/gpt-4o.json`

## Output Files

The verification process creates two output files:

### 1. Verified Tasks File
**Default**: `verified_<input_filename>.jsonl`

Contains successfully verified tasks with additional fields:
- `conversation` - Multi-turn conversation during verification
- `tool_calls` - Actual tool calls made during verification
- `tool_call_results` - Results from tool executions
- `final_response` - Final response from the verification

```json
{
  "name": "Find patient medication history",
  "description": "Retrieve the complete medication history for patient ID 'P12345' and check for any potential drug interactions.",
  "goal": "Obtain comprehensive medication history and identify potential drug interactions",
  "tool_calls": [
    {
      "tool_name": "get_patient_medications",
      "tool_parameters": {
        "patient_id": "P12345"
      }
    }
  ],
  "conversation": [
    {
      "role": "user",
      "content": "Find patient medication history for patient P12345"
    },
    {
      "role": "assistant",
      "content": "I'll retrieve the medication history for patient P12345.",
      "tool_calls": [...]
    }
  ],
  "tool_call_results": [...],
  "final_response": "Successfully retrieved medication history for patient P12345. The patient is currently taking..."
}
```

### 2. Unverified Tasks File
**Default**: `verified_<input_filename>_unverified.jsonl`

Contains tasks that failed verification with improvement suggestions:
- Original task information
- Feedback for task improvement
- Specific issues identified

## Verification Process

### Step 1: Task Loading
- Loads tasks from JSONL input file
- Skips already verified tasks (resume capability)
- Applies task count limits if specified

### Step 2: Server Connection
- Connects to specified MCP servers
- Retrieves available tools and schemas
- Builds tool name to session mapping

### Step 3: Multi-Turn Verification
- Attempts to complete each task using available tools
- Engages in conversation with the server
- Records all interactions and tool calls

### Step 4: Result Classification
- **Success**: Task completed successfully → saves to verified file
- **Failure**: Task needs improvement → saves to unverified file
- **Error**: Technical issues → logs error and continues

### Step 5: Output Generation
- Saves verified tasks with conversation history
- Saves unverified tasks with improvement feedback
- Provides summary statistics

## Environment Variables

The tool supports the following environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for verification | `sk-...` |
| `NPS_API_KEY` | National Parks Service API key | `your_nps_key` |
| `DEBUG` | Enable debug logging | `true` |
| `MCP_EVAL_LOG_LEVEL` | Log level | `DEBUG` |

### Using Environment Variables

```bash
# Set environment variables
export OPENAI_API_KEY="sk-your-openai-key"
export NPS_API_KEY="your-nps-api-key"
export DEBUG="true"

# Use in server specification
mcp-eval verify-tasks \
  --servers mcp-server-nationalparks^NPS_API_KEY=$NPS_API_KEY \
  --tasks-file data/national_parks_tasks.jsonl \
  --model gpt-4.1-2025-04-14 \
  --output data/national_parks_tasks_verified.jsonl
```

## Best Practices

### 1. Model Selection

- **`gpt-4.1-2025-04-14`**: Best for complex verification tasks
- **`gpt-4o`**: Balanced performance and cost (default)
- **`gpt-4o-mini`**: Cost-effective for simple verification

### 2. Max Turns Configuration

- **Simple tasks**: 5-10 turns
- **Complex tasks**: 15-20 turns
- **Multi-step tasks**: 20+ turns

### 3. Prompt Engineering

- Be specific about domain requirements
- Include validation criteria
- Specify expected information completeness
- Define quality standards

### 4. Batch Processing

```bash
# Process tasks in batches
for batch in data/healthcare/tasks_batch_*.jsonl; do
  mcp-eval verify-tasks \
    --servers mcp_servers/healthcare/server.py \
    --tasks-file "$batch" \
    --model gpt-4.1-2025-04-14 \
    --output "${batch%.jsonl}_verified.jsonl"
  sleep 5
done
```

## Resume Capability

The verifier automatically skips already verified tasks:

```bash
# First run - verifies 50 tasks
mcp-eval verify-tasks \
  --servers mcp_servers/healthcare/server.py \
  --tasks-file data/healthcare/tasks.jsonl \
  --num-tasks 50 \
  --output data/healthcare/tasks_verified.jsonl

# Second run - continues from task 51
mcp-eval verify-tasks \
  --servers mcp_servers/healthcare/server.py \
  --tasks-file data/healthcare/tasks.jsonl \
  --num-tasks 100 \
  --output data/healthcare/tasks_verified.jsonl
```

## Troubleshooting

### Common Issues

#### 1. Server Connection Problems

```bash
# Check server accessibility
mcp-eval verify-tasks \
  --servers mcp_servers/healthcare/server.py \
  --tasks-file data/healthcare/tasks.jsonl \
  --num-tasks 1

# For external servers, verify installation
npm install -g @openbnb/mcp-server-airbnb
```

#### 2. Task Format Issues

```bash
# Validate task file format
python -c "
import json
with open('data/healthcare/tasks.jsonl') as f:
    for i, line in enumerate(f):
        try:
            json.loads(line)
        except json.JSONDecodeError as e:
            print(f'Line {i+1}: {e}')
"
```

#### 3. API Rate Limits

```bash
# Add delay between tasks and reduce concurrency
mcp-eval verify-tasks \
  --servers mcp_servers/healthcare/server.py \
  --tasks-file data/healthcare/tasks.jsonl \
  --model gpt-4o-mini \
  --num-tasks 20 \
  --output data/healthcare/tasks_verified.jsonl
```

#### 4. Memory Issues

```bash
# Process smaller batches
split -l 100 data/large_tasks.jsonl data/batch_
for file in data/batch_*; do
  mcp-eval verify-tasks \
    --servers mcp_servers/healthcare/server.py \
    --tasks-file "$file" \
    --output "${file}_verified.jsonl"
done
```

#### 5. Debug Mode

```bash
# Enable detailed logging
export DEBUG="true"
export MCP_EVAL_LOG_LEVEL="DEBUG"

mcp-eval verify-tasks \
  --servers mcp_servers/healthcare/server.py \
  --tasks-file data/healthcare/tasks.jsonl \
  --num-tasks 1 \
  --output data/healthcare/debug_verified.jsonl
```

## Integration with Other Tools

The verified tasks can be used with other MCP-Eval tools:

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
# Use faster model with fewer turns
mcp-eval verify-tasks \
  --servers mcp_servers/healthcare/server.py \
  --tasks-file data/healthcare/tasks.jsonl \
  --model gpt-4o-mini \
  --max-turns 5 \
  --output data/healthcare/tasks_verified.jsonl
```

### 2. Optimize for Quality

```bash
# Use best model with more turns
mcp-eval verify-tasks \
  --servers mcp_servers/healthcare/server.py \
  --tasks-file data/healthcare/tasks.jsonl \
  --model gpt-4.1-2025-04-14 \
  --max-turns 20 \
  --output data/healthcare/tasks_verified.jsonl
```

### 3. Cost Optimization

```bash
# Use cost-effective settings
mcp-eval verify-tasks \
  --servers mcp_servers/healthcare/server.py \
  --tasks-file data/healthcare/tasks.jsonl \
  --model gpt-4o-mini \
  --max-turns 8 \
  --output data/healthcare/tasks_verified.jsonl
```

## Verification Quality Metrics

After verification, you can analyze the results:

```bash
# Count verification success rate
echo "Verified tasks: $(wc -l < data/healthcare/verified_tasks.jsonl)"
echo "Unverified tasks: $(wc -l < data/healthcare/verified_tasks_unverified.jsonl)"

# Analyze verification patterns
python -c "
import json
with open('data/healthcare/verified_tasks.jsonl') as f:
    tasks = [json.loads(line) for line in f]
    
# Count tool usage
tool_usage = {}
for task in tasks:
    for tool_call in task.get('tool_calls', []):
        tool_name = tool_call.get('tool_name')
        tool_usage[tool_name] = tool_usage.get(tool_name, 0) + 1

print('Tool usage:', tool_usage)
"
```

## Support

For additional help:

- Use `mcp-eval verify-tasks --help` for command-specific help
- Check the main CLI documentation: `src/mcpeval/cli/README.md`
- Review example benchmark configurations in `benchmarks/`
- Enable debug logging: `export DEBUG=true`

## Related Commands

- `mcp-eval generate-tasks` - Generate tasks for verification
- `mcp-eval evaluate` - Evaluate models with verified tasks
- `mcp-eval analyze` - Analyze evaluation results
- `mcp-eval auto` - Run complete evaluation workflow 