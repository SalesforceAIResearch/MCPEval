# MCP Auto Workflow

The **MCP Auto Workflow** is a command-line tool that automatically runs the complete evaluation pipeline from task generation to analysis. It orchestrates all evaluation steps in sequence, creating a structured working directory with organized results.

## Quick Start

```bash
# Basic usage - complete evaluation pipeline
mcp-eval auto \
  --servers mcp_servers/healthcare/server.py \
  --working-dir workspace/healthcare_eval \
  --task-model gpt-4.1-2025-04-14 \
  --eval-model-configs benchmarks/healthcare/eval_models/gpt-4o.json benchmarks/healthcare/eval_models/gpt-4o-mini.json \
  --num-tasks 50
```

## Installation

The auto workflow is installed as part of the mcpeval package:

```bash
# From the repository root directory
uv pip install -e .
```

## Overview

The auto workflow executes five main steps:

1. **Task Generation** - Generate tasks using the task model
2. **Task Verification** - Verify tasks work correctly with the servers
3. **Model Evaluation** - Evaluate all specified models on verified tasks
4. **Analysis & Reporting** - Generate comprehensive analysis reports with charts
5. **LLM Judging** (Optional) - Generate trajectory and completion scores

## Arguments

### Required Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `--servers` | MCP server specifications (one or more) | `mcp_servers/healthcare/server.py` |
| `--working-dir` | Working directory for all operations | `workspace/healthcare_eval` |
| `--task-model` | Model for task generation and verification | `gpt-4.1-2025-04-14` |
| `--eval-model-configs` | Model configuration files for evaluation | `eval_models/gpt-4o.json eval_models/gpt-4o-mini.json` |

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
| `--num-tasks` | int | `200` | Number of tasks to generate |
| `--max-turns` | int | `30` | Maximum conversation turns per task |
| `--task-generation-prompt` | string | - | JSON file with task generation prompts |
| `--task-verification-prompt` | string | - | JSON file with task verification prompts |
| `--evaluation-prompt` | string | - | JSON file with evaluation system message |
| `--enable-llm-judge` | flag | `false` | Enable LLM judging after evaluation |
| `--llm-judge-model` | string | `gpt-4o` | Model to use for LLM judging |
| `--api-key` | string | - | OpenAI API key (or use `OPENAI_API_KEY` env var) |

## Examples

### Basic Examples

#### 1. Healthcare Domain Evaluation

```bash
mcp-eval auto \
  --servers mcp_servers/healthcare/server.py \
  --working-dir workspace/healthcare_eval \
  --task-model gpt-4.1-2025-04-14 \
  --eval-model-configs \
    benchmarks/healthcare/eval_models/gpt-4o.json \
    benchmarks/healthcare/eval_models/gpt-4o-mini.json \
    benchmarks/healthcare/eval_models/gpt-4.1-mini.json \
  --num-tasks 100 \
  --max-turns 30
```

#### 2. Multi-Server Evaluation (Sequential Thinking + YFinance)

```bash
mcp-eval auto \
  --servers @modelcontextprotocol/server-sequential-thinking mcp_servers/yfinance/server.py \
  --working-dir workspace/yfinance_thinking_eval \
  --task-model gpt-4.1-2025-04-14 \
  --eval-model-configs \
    benchmarks/yfinance_think/eval_models/gpt-4o.json \
    benchmarks/yfinance_think/eval_models/o3.json \
  --num-tasks 75 \
  --max-turns 40
```

#### 3. External Server with Environment Variables

```bash
export NPS_API_KEY="your-nps-api-key"

mcp-eval auto \
  --servers mcp-server-nationalparks^NPS_API_KEY=$NPS_API_KEY \
  --working-dir workspace/national_parks_eval \
  --task-model gpt-4.1-2025-04-14 \
  --eval-model-configs \
    benchmarks/national_parks/eval_models/gpt-4o.json \
    benchmarks/national_parks/eval_models/gpt-4o-mini.json \
  --num-tasks 80
```

### Advanced Examples

#### 4. Complete Evaluation with Custom Prompts

```bash
mcp-eval auto \
  --servers mcp_servers/sports/server.py \
  --working-dir workspace/sports_comprehensive_eval \
  --task-model gpt-4.1-2025-04-14 \
  --eval-model-configs \
    benchmarks/sports/eval_models/gpt-4o.json \
    benchmarks/sports/eval_models/gpt-4o-mini.json \
    benchmarks/sports/eval_models/gpt-4.1-mini.json \
    benchmarks/sports/eval_models/o3.json \
  --num-tasks 150 \
  --max-turns 30 \
  --task-generation-prompt benchmarks/sports/data_generation/task_generation_prompt.json \
  --task-verification-prompt benchmarks/sports/data_generation/task_verification_prompt.json \
  --evaluation-prompt benchmarks/sports/evaluation_prompt.json
```

#### 5. Evaluation with LLM Judging

```bash
mcp-eval auto \
  --servers mcp_servers/healthcare/server.py \
  --working-dir workspace/healthcare_with_judging \
  --task-model gpt-4.1-2025-04-14 \
  --eval-model-configs \
    benchmarks/healthcare/eval_models/gpt-4o.json \
    benchmarks/healthcare/eval_models/gpt-4o-mini.json \
  --num-tasks 100 \
  --enable-llm-judge \
  --llm-judge-model gpt-4o
```

#### 6. Airbnb with Complex Server Arguments

```bash
mcp-eval auto \
  --servers @openbnb/mcp-server-airbnb:--ignore-robots-txt \
  --working-dir workspace/airbnb_eval \
  --task-model gpt-4.1-2025-04-14 \
  --eval-model-configs \
    benchmarks/airbnb/eval_models/gpt-4o.json \
    benchmarks/airbnb/eval_models/gpt-4.1-mini.json \
  --num-tasks 120 \
  --max-turns 25
```

## Working Directory Structure

The auto workflow creates an organized directory structure:

```
workspace/
└── your_eval_name/
    ├── data/
    │   ├── evaluation_tasks.jsonl              # Generated tasks
    │   └── evaluation_tasks_verified.jsonl     # Verified tasks
    ├── results/
    │   ├── gpt4o_evaluation.json              # Model evaluation results
    │   ├── gpt4o_mini_evaluation.json         # 
    │   └── gpt41_mini_evaluation.json         # 
    ├── report/
    │   ├── gpt4o_report.md                    # Analysis reports with charts
    │   ├── gpt4o_mini_report.md               # 
    │   ├── gpt41_mini_report.md               # 
    │   └── charts/                            # Interactive visualizations
    │       ├── success_rates.html
    │       ├── tool_usage.png
    │       └── performance_radar.html
    └── logs/
        ├── 01_task_generation.log             # Step-by-step execution logs
        ├── 02_task_verification.log           # 
        ├── 03_evaluation_gpt4o.log            # 
        ├── 04_analysis_gpt4o.log              # 
        └── 05_llm_judge_gpt4o.log             # (if enabled)
```

## Model Configuration Files

Model configurations define how each model should be evaluated:

### OpenAI Models

```json
{
    "model": "gpt-4o-2024-11-20",
    "temperature": 0.01,
    "max_tokens": 16384
}
```

### Custom API Models

```json
{
    "model": "mistral-large-2411",
    "api_key": "your-mistral-api-key",
    "temperature": 0.01,
    "max_tokens": 4000,
    "base_url": "https://api.mistral.ai/v1"
}
```

## Prompt Files

### Task Generation Prompt (`task_generation_prompt.json`)

```json
{
    "system": "You are an expert at creating challenging but realistic tasks for healthcare scenarios.",
    "user": "Generate diverse tasks that test different aspects of the healthcare system."
}
```

### Task Verification Prompt (`task_verification_prompt.json`)

```json
{
    "system": "You are verifying that healthcare tasks can be completed successfully using the available tools."
}
```

### Evaluation Prompt (`evaluation_prompt.json`)

```json
{
    "system": "You are an AI assistant that uses tools to complete healthcare tasks. The current date is 2025-01-15. Use the available tools to complete each task thoroughly."
}
```

## Environment Variables

The auto workflow supports the following environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for model access | `sk-...` |
| `NPS_API_KEY` | National Parks Service API key | `your_nps_key` |
| `MISTRAL_API_KEY` | Mistral API key for model access | `your_mistral_key` |
| `MCP_EVAL_LOG_LEVEL` | Log level for debugging | `DEBUG` |

### Setting Environment Variables

```bash
# Set API keys
export OPENAI_API_KEY="sk-your-openai-key"
export NPS_API_KEY="your-nps-api-key"

# Enable debug logging
export MCP_EVAL_LOG_LEVEL="DEBUG"

# Run auto workflow
mcp-eval auto \
  --servers mcp-server-nationalparks^NPS_API_KEY=$NPS_API_KEY \
  --working-dir workspace/parks_eval \
  --task-model gpt-4.1-2025-04-14 \
  --eval-model-configs benchmarks/national_parks/eval_models/gpt-4o.json
```

## Progress Monitoring

The auto workflow provides real-time progress updates:

```bash
# Example output
🎯 Starting Auto Evaluation Workflow
Working Directory: workspace/healthcare_eval
Server: mcp_servers/healthcare/server.py
Task Model: gpt-4.1-2025-04-14
Models to Evaluate: 3
Number of Tasks: 100
LLM Judging: Disabled

📝 Prompt Configuration:
  ✓ Task generation prompt: benchmarks/healthcare/data_generation/task_generation_prompt.json
  ✓ Task verification prompt: benchmarks/healthcare/data_generation/task_verification_prompt.json
  ✓ Evaluation prompt: benchmarks/healthcare/evaluation_prompt.json

══════════════════════════════════════════════════════════════
STEP 1: TASK GENERATION
══════════════════════════════════════════════════════════════
🚀 Running: Task Generation
✅ Task Generation completed successfully in 45.32s

══════════════════════════════════════════════════════════════
STEP 2: TASK VERIFICATION
══════════════════════════════════════════════════════════════
🚀 Running: Task Verification
✅ Task Verification completed successfully in 120.45s

══════════════════════════════════════════════════════════════
STEP 3: MODEL EVALUATION
══════════════════════════════════════════════════════════════

📊 Evaluating Model 1/3: gpt4o
🚀 Running: Model Evaluation - gpt4o
✅ gpt4o evaluation completed

📊 Evaluating Model 2/3: gpt4o_mini
🚀 Running: Model Evaluation - gpt4o_mini
✅ gpt4o_mini evaluation completed

══════════════════════════════════════════════════════════════
STEP 4: ANALYSIS AND REPORTING
══════════════════════════════════════════════════════════════

🔍 Analyzing results for: gpt4o
🚀 Running: Analysis - gpt4o
✅ gpt4o analysis completed

══════════════════════════════════════════════════════════════
🎉 AUTO WORKFLOW COMPLETED SUCCESSFULLY! 🎉
══════════════════════════════════════════════════════════════
Results available in: workspace/healthcare_eval
📊 Evaluation files: results/
📝 Reports: report/
📋 Logs: logs/
```

## Best Practices

### 1. Resource Management

- **Memory**: Start with smaller task counts (50-100) for large models
- **Time**: Allow several hours for complete workflows with multiple models
- **Storage**: Each evaluation can generate 100MB-1GB of data

### 2. Model Selection

- **Task Model**: Use `gpt-4.1-2025-04-14` for high-quality task generation
- **Evaluation Models**: Mix different model types for comprehensive comparison
- **Judge Model**: Use `gpt-4o` for reliable LLM judging

### 3. Server Configuration

- **Single Server**: Ideal for domain-specific evaluations
- **Multi-Server**: Test complex reasoning requiring multiple tools
- **External Servers**: Ensure API keys are properly configured

### 4. Workflow Optimization

- **Incremental Development**: Start with few tasks, scale up gradually
- **Prompt Tuning**: Use custom prompts for domain-specific improvements
- **Parallel Processing**: Auto workflow handles parallelization automatically

## Troubleshooting

### Common Issues

#### 1. Server Connection Errors

```bash
# Check server installation
npm list -g | grep mcp

# Test server connectivity
mcp-eval generate-tasks \
  --servers mcp_servers/healthcare/server.py \
  --model gpt-4.1-2025-04-14 \
  --num-tasks 1 \
  --output test_task.jsonl
```

#### 2. API Key Issues

```bash
# Verify API key
echo $OPENAI_API_KEY

# Test API access
python -c "import openai; client = openai.OpenAI(); print('API key valid')"
```

#### 3. Working Directory Permissions

```bash
# Check directory permissions
ls -la workspace/

# Fix permissions if needed
chmod -R 755 workspace/your_eval_name/
```

#### 4. Memory Issues

```bash
# Monitor memory usage
htop

# Reduce task count for large models
--num-tasks 25  # Instead of 200
```

#### 5. Model Configuration Issues

```bash
# Validate model config files
python -c "
import json
with open('benchmarks/healthcare/eval_models/gpt-4o.json') as f:
    config = json.load(f)
    print('Model config valid:', config)
"
```

## Advanced Usage

### Custom Automation Scripts

Create reusable evaluation scripts:

```bash
#!/bin/bash
# custom_healthcare_eval.sh

DOMAIN="healthcare"
WORKING_DIR="workspace/${DOMAIN}_$(date +%Y%m%d_%H%M%S)"
TASK_MODEL="gpt-4.1-2025-04-14"

mcp-eval auto \
  --servers mcp_servers/${DOMAIN}/server.py \
  --working-dir "$WORKING_DIR" \
  --task-model "$TASK_MODEL" \
  --eval-model-configs \
    benchmarks/${DOMAIN}/eval_models/gpt-4o.json \
    benchmarks/${DOMAIN}/eval_models/gpt-4o-mini.json \
    benchmarks/${DOMAIN}/eval_models/gpt-4.1-mini.json \
  --num-tasks 150 \
  --max-turns 30 \
  --task-generation-prompt benchmarks/${DOMAIN}/data_generation/task_generation_prompt.json \
  --task-verification-prompt benchmarks/${DOMAIN}/data_generation/task_verification_prompt.json \
  --evaluation-prompt benchmarks/${DOMAIN}/evaluation_prompt.json \
  --enable-llm-judge

echo "Evaluation completed in: $WORKING_DIR"
```

### Comparative Studies

Compare multiple domains:

```bash
# Healthcare evaluation
mcp-eval auto --servers mcp_servers/healthcare/server.py --working-dir workspace/healthcare_study ...

# Sports evaluation  
mcp-eval auto --servers mcp_servers/sports/server.py --working-dir workspace/sports_study ...

# Travel evaluation
mcp-eval auto --servers mcp_servers/travel_assistant/server.py --working-dir workspace/travel_study ...
```

## Support

For additional help:

- **Documentation**: See the main MCPEval documentation
- **Issues**: Report bugs on the project repository
- **Examples**: Check the `benchmarks/` directory for complete examples

*For more information about the MCPEval system, see the main project documentation.* 