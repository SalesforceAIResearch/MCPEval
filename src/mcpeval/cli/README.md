# MCPEval: Command Line Tools

This package provides comprehensive command-line tools for working with MCP (Model Context Protocol) servers and evaluating Large Language Models (LLMs).

## Installation

The CLI is installed as part of the mcpeval package:

```bash
# From the repository root directory
uv pip install -e .
```

## Usage

The main command-line interface provides access to multiple subcommands:

```bash
mcp-eval <subcommand> [options]
```

Available subcommands:
- `generate-tasks` - Generate tasks for MCP servers
- `verify-tasks` - Verify generated tasks against an MCP server
- `convert-data` - Convert data to different formats (e.g., XLAM)
- `evaluate` - Evaluate models using MCP servers and tasks
- `analyze` - Analyze evaluation results against ground truth
- `judge` - Evaluate execution results using LLM judges
- `judge-rubric` - Analyze LLM judgment results and generate performance reports
- `auto` - Automatically run complete evaluation workflow (generate, verify, evaluate, analyze)

## Global Options

All subcommands support the following common options:

- `--api-key`: OpenAI API key (uses `OPENAI_API_KEY` environment variable if not provided)
- `--help`: Show help information for the subcommand

## Subcommands

### Generate Tasks

Generate tasks for MCP servers using AI models:

```bash
mcp-eval generate-tasks --server <server_script_path> [options]
```

#### Arguments

**Required:**

- `--server`: MCP server script path (e.g., `@openbnb/mcp-server-airbnb` or `mcp_servers/healthcare/server.py`)

**Optional:**

- `--server-args`: Additional arguments to pass to the MCP server (space-separated)
- `--output`: Output file path for generated tasks (default: `generated_tasks.jsonl`)
- `--num-tasks`: Number of tasks to generate (default: 10)
- `--existing-files`: List of existing files to load tasks from (space-separated)
- `--prompt-file`: JSON file containing system and user messages (format: `{"system": "...", "user": "..."}`)
- `--model`: Model to use for task generation (default: `gpt-4.1-2025-04-14`)
- `--temperature`: Temperature for model generation (default: 0.2)
- `--max-tokens`: Maximum number of tokens to generate (default: 2000)
- `--top-p`: Top-p sampling parameter (default: 0.95)

#### Examples

1. Generate 200 tasks for a healthcare MCP server:

```bash
mcp-eval generate-tasks \
  --server mcp_servers/healthcare/server.py \
  --model gpt-4.1-2025-04-14 \
  --num-tasks 200 \
  --prompt-file benchmarks/healthcare/data_generation/task_generation_prompt.json \
  --output data/healthcare/evaluation_tasks.jsonl
```

2. Generate tasks for Airbnb server with server arguments:

```bash
mcp-eval generate-tasks \
  --server @openbnb/mcp-server-airbnb \
  --server-args "--ignore-robots-txt" \
  --num-tasks 50 \
  --output data/airbnb_tasks.jsonl
```

### Verify Tasks

Verify generated tasks against an MCP server to ensure they can be successfully executed:

```bash
mcp-eval verify-tasks --server <server_script_path> --tasks-file <path_to_tasks_file> [options]
```

#### Arguments

**Required:**

- `--server`: MCP server script path (e.g., `@openbnb/mcp-server-airbnb` or `mcp_servers/healthcare/server.py`)
- `--tasks-file`: Path to the JSONL file containing tasks to verify

**Optional:**

- `--server-args`: Additional arguments to pass to the MCP server (space-separated)
- `--output`: Output file path for verified tasks (default: `verified_<input_filename>`)
- `--model`: Model to use for verification (default: `gpt-4.1-2025-04-14`)
- `--num-tasks`: Number of tasks to verify (default: all tasks, use -1 for all)
- `--prompt-file`: JSON file containing system message for verification

#### Examples

1. Verify healthcare tasks:

```bash
mcp-eval verify-tasks \
  --server mcp_servers/healthcare/server.py \
  --tasks-file data/healthcare/evaluation_tasks.jsonl \
  --model gpt-4.1-2025-04-14 \
  --output data/healthcare/evaluation_tasks_verified.jsonl \
  --prompt-file benchmarks/healthcare/data_generation/task_verification_prompt.json
```

2. Verify Airbnb tasks with server arguments:

```bash
mcp-eval verify-tasks \
  --server @openbnb/mcp-server-airbnb \
  --server-args "--ignore-robots-txt" \
  --tasks-file data/airbnb_tasks.jsonl \
  --num-tasks 50
```

### Convert Data

Convert task data to different formats, such as XLAM format for training or evaluation:

```bash
mcp-eval convert-data --input <input_file> --output <output_file> [options]
```

#### Arguments

**Required:**

- `--input`: Input file path with tasks (JSONL or JSON format)
- `--output`: Output file path for converted data

**Optional:**

- `--prefix`: Prefix for unique trajectory IDs (default: `task`)
- `--split`: Dataset split (train, test, val) (default: `train`)
- `--task-id`: Task ID to extract from evaluation results (only for single JSON file input)
- `--instruction`: Default instruction to use if no specific task_instruction is provided (default: "You are a helpful assistant that can use tools to complete tasks.")
- `--system-message`: System message to include in the conversation. Use "-1" to ignore system messages (default: `-1`)

#### Examples

1. Convert a JSONL file to XLAM format:

```bash
mcp-eval convert-data \
  --input data/healthcare/evaluation_tasks_verified.jsonl \
  --output data/healthcare/xlam_format.json \
  --prefix healthcare --split train
```

2. Convert with custom instruction and system message:

```bash
mcp-eval convert-data \
  --input data/tasks.jsonl \
  --output data/converted.json \
  --instruction "Complete the following task using the available tools" \
  --system-message "You are an AI assistant."
```

### Evaluate Models

Evaluate models using MCP servers and tasks:

```bash
mcp-eval evaluate --server <server_script_path> --tasks-file <path_to_tasks_file> [options]
```

#### Arguments

**Required:**

- `--server`: MCP server script path (e.g., `@openbnb/mcp-server-airbnb` or `mcp_servers/healthcare/server.py`)
- `--tasks-file`: Path to the JSONL file containing tasks for evaluation

**Optional:**

- `--server-args`: Additional arguments to pass to the MCP server (space-separated)
- `--model-config`: Path to JSON file containing model configuration (see Model Configuration Format below)
- `--output`: Output file path for evaluation results (default: `evaluation_results.json`)
- `--num-tasks`: Number of tasks to evaluate (default: all tasks, use -1 for all)
- `--max-turns`: Maximum number of turns for task execution (default: 30)
- `--prompt-file`: JSON file containing system message (format: {"system": "..."})
- `--force-rerun`: Force rerun all tasks even if already tested

#### Model Configuration Format

Model configurations are specified in JSON files with the following structure:

```json
{
  "model": "gpt-4o-mini-2024-07-18",
  "temperature": 0.01,
  "max_tokens": 16000
}
```

For custom API endpoints (like XLAM models):

```json
{
  "model": "xlam_2_32b_fc_r",
  "api_key": "default",
  "temperature": 0.01,
  "max_tokens": 3000,
  "base_url": "http://10.3.91.185:8002/v1"
}
```

For OpenAI's newer models:

```json
{
  "model": "o3-mini-2025-01-31",
  "max_completion_tokens": 100000
}
```

#### Examples

1. Evaluate GPT-4o on healthcare tasks:

```bash
mcp-eval evaluate \
  --server mcp_servers/healthcare/server.py \
  --model-config benchmarks/healthcare/eval_models/gpt-4o.json \
  --tasks-file data/healthcare/evaluation_tasks_verified.jsonl \
  --output benchmarks/healthcare/results/gpt4o_mix_task_evaluation.json \
  --prompt-file benchmarks/healthcare/evaluation_prompt.json \
  --max-turns 30
```

2. Evaluate multiple models in parallel:

```bash
# GPT-4o evaluation
mcp-eval evaluate \
  --server mcp_servers/sports/server.py \
  --model-config benchmarks/sports/eval_models/gpt-4o.json \
  --tasks-file data/sports/evaluation_tasks_verified.jsonl \
  --output benchmarks/sports/results/gpt4o_mix_task_evaluation.json \
  --prompt-file benchmarks/sports/evaluation_prompt.json \
  --max-turns 30 &

# GPT-4o-mini evaluation
mcp-eval evaluate \
  --server mcp_servers/sports/server.py \
  --model-config benchmarks/sports/eval_models/gpt-4o-mini.json \
  --tasks-file data/sports/evaluation_tasks_verified.jsonl \
  --output benchmarks/sports/results/gpt4o-mini_mix_task_evaluation.json \
  --prompt-file benchmarks/sports/evaluation_prompt.json \
  --max-turns 30 &

wait  # Wait for both evaluations to complete
```

### Analyze Results

Analyze evaluation results against ground truth to get detailed performance metrics:

```bash
mcp-eval analyze --predictions <predictions_file> --ground-truth <ground_truth_file> [options]
```

#### Arguments

**Required:**

- `--predictions`: Path to predictions JSON file (typically from model evaluation)
- `--ground-truth`: Path to ground truth JSONL or JSON file

**Optional:**

**Output Configuration:**
- `--evaluation-output`: Path to save task-level metrics (default: `<predictions>_task_metrics.json`)
- `--analysis-output`: Path to save summary analysis (default: `<predictions>_summary_analysis.json`)

**Scoring Weights (must sum to 1.0):**
- `--name-weight`: Weight for tool name matching (default: 0.4)
- `--params-weight`: Weight for parameter matching (default: 0.4)
- `--order-weight`: Weight for tool order matching (default: 0.2)

**Flexible Matching Thresholds:**
- `--param-threshold`: Parameter similarity threshold for flexible matching (default: 0.6)
- `--order-threshold`: Order similarity threshold for flexible matching (default: 0.5)

**AI Report Generation:**
- `--generate-report`: Generate AI-powered performance report using OpenAI models
- `--report-model`: Model for AI report generation (default: `gpt-4.1-2025-04-14`)
- `--report-output`: Path to save AI report (default: `<predictions>_ai_report.md`)
- `--from-summary`: Generate report directly from an existing summary analysis JSON file

#### Examples

1. Analyze model evaluation results with report generation:

```bash
mcp-eval analyze \
  --predictions benchmarks/healthcare/results/gpt4o_mix_task_evaluation.json \
  --ground-truth data/healthcare/evaluation_tasks_verified.jsonl \
  --generate-report \
  --report-model gpt-4.1-2025-04-14 \
  --report-output benchmarks/healthcare/results/gpt4o_healthcare_report.md
```

2. Custom scoring weights and thresholds:

```bash
mcp-eval analyze \
  --predictions evaluation_results.json \
  --ground-truth verified_tasks.jsonl \
  --name-weight 0.3 --params-weight 0.5 --order-weight 0.2 \
  --param-threshold 0.8 --order-threshold 0.7
```

### Judge (LLM Evaluation)

Evaluate execution results using LLM judges to provide qualitative assessment:

```bash
mcp-eval judge --input-file <evaluation_file> --output-dir <output_directory> [options]
```

#### Arguments

**Required:**

- `--input-file`: Path to evaluation results JSON file
- `--output-dir`: Directory to save judge results

**Optional:**

- `--model`: Model to use for judging (default: `gpt-4o`)
- `--resume`: Resume from previous incomplete judging session

#### Examples

1. Run LLM judge on evaluation results:

```bash
mcp-eval judge \
  --input-file benchmarks/healthcare/results/gpt4o_mix_task_evaluation.json \
  --output-dir benchmarks/healthcare/results \
  --model gpt-4o
```

2. Resume interrupted judging session:

```bash
mcp-eval judge \
  --input-file benchmarks/sports/results/gpt4.1-nano_mix_task_evaluation.json \
  --output-dir benchmarks/sports/results \
  --model gpt-4o \
  --resume
```

### Judge Rubric (LLM Judgment Analysis)

Analyze LLM judgment results and generate performance reports:

```bash
mcp-eval judge-rubric --trajectory-file <trajectory_file> --completion-file <completion_file> --output-dir <output_directory> [options]
```

#### Arguments

**Required:**

- `--trajectory-file`: Path to trajectory judgment file (created by judge command)
- `--completion-file`: Path to completion judgment file (created by judge command)
- `--output-dir`: Directory to save analysis reports

**Optional:**

- `--report-model`: Model for report generation (default: `gpt-4.1-2025-04-14`)

#### Examples

1. Analyze LLM judgment results:

```bash
mcp-eval judge-rubric \
  --trajectory-file benchmarks/healthcare/results/gpt4o_mix_task_evaluation_trajectory.json \
  --completion-file benchmarks/healthcare/results/gpt4o_mix_task_evaluation_completion.json \
  --output-dir benchmarks/healthcare/report
```

2. Complete LLM judging workflow:

```bash
# Step 1: Run LLM judge
mcp-eval judge \
  --input-file benchmarks/sports/results/gpt4.1-mini_mix_task_evaluation.json \
  --output-dir benchmarks/sports/results \
  --model gpt-4o

# Step 2: Analyze judgment results
mcp-eval judge-rubric \
  --trajectory-file benchmarks/sports/results/gpt4.1-mini_mix_task_evaluation_trajectory.json \
  --completion-file benchmarks/sports/results/gpt4.1-mini_mix_task_evaluation_completion.json \
  --output-dir benchmarks/sports/report
```

### Auto Workflow

Automatically run the complete evaluation workflow including task generation, verification, model evaluation, and analysis. The auto command intelligently generates domain-specific prompts using GPT based on the server type (healthcare, travel, finance, etc.), or uses custom prompt files if provided:

```bash
mcp-eval auto --servers <server> --working-dir <work_dir> --task-model <model> --eval-model-configs <config1> [config2 ...] [options]
```

#### Arguments

**Required:**

- `--servers`: Server path to connect to (e.g., `mcp_servers/healthcare/server.py` or `@openbnb/mcp-server-airbnb`)
- `--working-dir`: Working directory to create and use for all operations
- `--task-model`: Model to use for task generation and verification (default: `gpt-4.1-2025-04-14`)
- `--eval-model-configs`: Paths to model configuration JSON files for evaluation

**Optional:**
- `--num-tasks`: Number of tasks to generate (default: 200)
- `--max-turns`: Maximum number of turns for task execution (default: 30)
- `--task-generation-prompt`: JSON file containing system and user messages for task generation
- `--task-verification-prompt`: JSON file containing system message for task verification
- `--evaluation-prompt`: JSON file containing system message for evaluation
- `--enable-llm-judge`: Enable LLM judging after evaluation (default: disabled)
- `--llm-judge-model`: Model to use for LLM judging (default: `gpt-4o`)

#### Examples

1. **Basic auto workflow with auto-generated prompts:**

```bash
# Simplest usage - prompts are automatically generated based on server tools
mcp-eval auto \
  --servers mcp_servers/healthcare/server.py \
  --working-dir evaluation_results/healthcare_eval_$(date +%Y%m%d) \
  --task-model gpt-4.1-2025-04-14 \
  --eval-model-configs benchmarks/healthcare/eval_models/gpt-4o.json benchmarks/healthcare/eval_models/gpt-4o-mini.json \
  --num-tasks 50
```

2. **Complete auto workflow with custom prompts and LLM judging:**

```bash
mcp-eval auto \
  --servers mcp_servers/healthcare/server.py \
  --working-dir evaluation_results/healthcare_full_eval \
  --task-model gpt-4.1-2025-04-14 \
  --eval-model-configs benchmarks/healthcare/eval_models/gpt-4o.json benchmarks/healthcare/eval_models/gpt-4o-mini.json benchmarks/healthcare/eval_models/gpt-4.1-mini.json \
  --num-tasks 200 \
  --max-turns 30 \
  --task-generation-prompt benchmarks/healthcare/data_generation/task_generation_prompt.json \
  --task-verification-prompt benchmarks/healthcare/data_generation/task_verification_prompt.json \
  --evaluation-prompt benchmarks/healthcare/evaluation_prompt.json \
  --enable-llm-judge \
  --llm-judge-model gpt-4o
```

3. **Auto workflow with NPM package server:**

```bash
mcp-eval auto \
  --servers @openbnb/mcp-server-airbnb \
  --working-dir evaluation_results/airbnb_eval \
  --task-model gpt-4.1-2025-04-14 \
  --eval-model-configs benchmarks/airbnb/eval_models/gpt-4o.json benchmarks/airbnb/eval_models/gpt-4o-mini.json \
  --num-tasks 100
```

#### Workflow Steps

The auto command orchestrates the following steps:

1. **🎯 Task Generation**: Generate tasks using the task model and task generation prompt (auto-generated or custom)
2. **✅ Task Verification**: Verify generated tasks using the task model and verification prompt (auto-generated or custom)  
3. **📊 Model Evaluation**: Evaluate each model configuration against the verified tasks
4. **🔍 Analysis**: Analyze evaluation results and generate reports for each model
5. **🧠 LLM Judging** (Optional): Use LLM judges to evaluate execution trajectories

#### Output Structure

The auto workflow creates the following directory structure in your working directory:

```
working_dir/
├── data/
│   ├── evaluation_tasks.jsonl           # Generated tasks
│   └── evaluation_tasks_verified.jsonl  # Verified tasks
├── results/
│   ├── model1_evaluation.json           # Evaluation results for each model
│   ├── model2_evaluation.json
│   └── ...
├── report/
│   ├── model1_report.md                 # Analysis reports for each model
│   ├── model2_report.md
│   ├── judge_model1/                    # LLM judging results (if enabled)
│   │   ├── combined.json
│   │   ├── trajectory.json
│   │   └── completion.json
│   └── ...
├── prompts/                             # Auto-generated prompts (if no custom prompts provided)
│   ├── task_generation_prompt.json
│   ├── task_verification_prompt.json
│   └── evaluation_prompt.json
└── logs/
    ├── 01_task_generation.log           # Detailed logs for each step
    ├── 02_task_verification.log
    ├── 03_evaluation_model1.log
    ├── 04_analysis_model1.log
    ├── 05_llm_judge_model1.log
    └── ...
```

> **Note:** The auto workflow is designed to be resumable. If a step fails, you can fix the issue and re-run the command - it will skip completed steps and continue from where it left off.

## Output Formats

### Generated Tasks Format

The task generator produces tasks in JSONL format with the following structure for each task:

```json
{
  "name": "Task Name",
  "description": "Detailed task description",
  "goal": "What the user should accomplish",
  "tools": [
    {
      "name": "tool_name",
      "description": "Tool description",
      "parameters": {...}
    }
  ],
  "tool_calls": [
    {
      "tool_name": "tool_name",
      "tool_parameters": {...}
    }
  ]
}
```

### Verified Tasks Format

The task verifier adds additional fields to the task format:

```json
{
  "name": "Task Name",
  "description": "Detailed task description",
  "goal": "What the user should accomplish",
  "tools": [...],
  "tool_calls": [...],
  "final_response": "Final response from the LLM after executing all tool calls",
  "conversation": [
    {
      "role": "user/assistant/tool",
      "content": "Message content"
    }
  ],
  "tool_call_results": [
    {
      "tool_name": "tool_name",
      "content": "Result content from the tool call"
    }
  ]
}
```

### Converted Data Format (XLAM)

The data converter produces XLAM format data with the following structure:

```json
{
  "unique_trajectory_id": "prefix---split---task_id",
  "dataset": "converted_dataset",
  "split": "train",
  "task_instruction": "You are a helpful assistant that can use tools to complete tasks.",
  "few_shot_examples": null,
  "tools": [
    {
      "name": "tool_name",
      "description": "Tool description",
      "parameters": {...}
    }
  ],
  "conversation": [
    {
      "role": "user",
      "content": "Task description"
    },
    {
      "role": "assistant",
      "content": "Response content",
      "tool_calls": [...]
    },
    {
      "role": "tool",
      "name": "tool_name",
      "content": "Tool result",
      "tool_call_id": "call_id"
    }
  ]
}
```

### Evaluation Results Format

The model evaluator produces results in JSON format:

```json
{
  "model": "gpt-4o-mini-2024-07-18",
  "server": "mcp_servers/healthcare/server.py",
  "timestamp": "2024-01-15T10:30:00Z",
  "task_results": [
    {
      "task_id": "task_001",
      "status": "completed",
      "tool_calls": [...],
      "conversation": [...],
      "execution_time": 2.5
    }
  ],
  "summary": {
    "total_tasks": 10,
    "completed": 8,
    "failed": 2,
    "average_execution_time": 2.1
  }
}
```

### Analysis Results Format

The analyzer produces detailed metrics and summary files:

**Task Metrics (`*_task_metrics.json`):**
```json
[
  {
    "task_id": "task_001",
    "exact_match": true,
    "flexible_match": true,
    "tool_name_score": 1.0,
    "parameter_score": 0.95,
    "order_score": 1.0,
    "overall_score": 0.98
  }
]
```

**Summary Analysis (`*_summary_analysis.json`):**
```json
{
  "metrics": {
    "exact_match_rate": 0.75,
    "flexible_match_rate": 0.85,
    "average_overall_score": 0.82
  },
  "common_errors": [...],
  "performance_insights": [...]
}
```

## Common Workflows

### Auto Workflow (Recommended)

The simplest way to run a complete evaluation pipeline:

```bash
# Auto workflow - everything in one command with auto-generated prompts!
mcp-eval auto \
  --servers mcp_servers/healthcare/server.py \
  --working-dir evaluation_results/healthcare_$(date +%Y%m%d) \
  --task-model gpt-4.1-2025-04-14 \
  --eval-model-configs benchmarks/healthcare/eval_models/gpt-4o.json benchmarks/healthcare/eval_models/gpt-4o-mini.json \
  --num-tasks 50
```

This single command will:
1. Auto-generate healthcare-specific prompts based on the server type
2. Generate 50 tasks using gpt-4.1-2025-04-14
3. Verify all generated tasks
4. Evaluate both gpt-4o and gpt-4o-mini models
5. Generate analysis reports for each model
6. Create a complete organized directory structure

### Manual Step-by-Step Pipeline

For more control over each step, you can run the pipeline manually:

```bash
# 1. Generate tasks for a server
mcp-eval generate-tasks \
  --server mcp_servers/healthcare/server.py \
  --model gpt-4.1-2025-04-14 \
  --num-tasks 200 \
  --prompt-file benchmarks/healthcare/data_generation/task_generation_prompt.json \
  --output data/healthcare/evaluation_tasks.jsonl

# 2. Verify the generated tasks
mcp-eval verify-tasks \
  --server mcp_servers/healthcare/server.py \
  --tasks-file data/healthcare/evaluation_tasks.jsonl \
  --model gpt-4.1-2025-04-14 \
  --output data/healthcare/evaluation_tasks_verified.jsonl \
  --prompt-file benchmarks/healthcare/data_generation/task_verification_prompt.json

# 3. Evaluate models using the verified tasks
mcp-eval evaluate \
  --server mcp_servers/healthcare/server.py \
  --model-config benchmarks/healthcare/eval_models/gpt-4o.json \
  --tasks-file data/healthcare/evaluation_tasks_verified.jsonl \
  --output benchmarks/healthcare/results/gpt4o_mix_task_evaluation.json \
  --prompt-file benchmarks/healthcare/evaluation_prompt.json \
  --max-turns 30

# 4. Analyze the results
mcp-eval analyze \
  --predictions benchmarks/healthcare/results/gpt4o_mix_task_evaluation.json \
  --ground-truth data/healthcare/evaluation_tasks_verified.jsonl \
  --generate-report \
  --report-model gpt-4.1-2025-04-14 \
  --report-output benchmarks/healthcare/results/gpt4o_healthcare_report.md

# 5. Optional: Run LLM judge evaluation
mcp-eval judge \
  --input-file benchmarks/healthcare/results/gpt4o_mix_task_evaluation.json \
  --output-dir benchmarks/healthcare/results \
  --model gpt-4o

# 6. Optional: Analyze LLM judgment results
mcp-eval judge-rubric \
  --trajectory-file benchmarks/healthcare/results/gpt4o_mix_task_evaluation_trajectory.json \
  --completion-file benchmarks/healthcare/results/gpt4o_mix_task_evaluation_completion.json \
  --output-dir benchmarks/healthcare/report

# 7. Convert data for training (optional)
mcp-eval convert-data \
  --input data/healthcare/evaluation_tasks_verified.jsonl \
  --output data/healthcare/training_data.json \
  --prefix healthcare \
  --split train
```

### Parallel Evaluation Workflow

For evaluating multiple models efficiently:

```bash
# Run multiple evaluations in parallel
mcp-eval evaluate \
  --server mcp_servers/sports/server.py \
  --model-config benchmarks/sports/eval_models/gpt-4o.json \
  --tasks-file data/sports/evaluation_tasks_verified.jsonl \
  --output benchmarks/sports/results/gpt4o_mix_task_evaluation.json \
  --prompt-file benchmarks/sports/evaluation_prompt.json \
  --max-turns 30 &

mcp-eval evaluate \
  --server mcp_servers/sports/server.py \
  --model-config benchmarks/sports/eval_models/gpt-4o-mini.json \
  --tasks-file data/sports/evaluation_tasks_verified.jsonl \
  --output benchmarks/sports/results/gpt4o-mini_mix_task_evaluation.json \
  --prompt-file benchmarks/sports/evaluation_prompt.json \
  --max-turns 30 &

mcp-eval evaluate \
  --server mcp_servers/sports/server.py \
  --model-config benchmarks/sports/eval_models/gpt-4.1-mini.json \
  --tasks-file data/sports/evaluation_tasks_verified.jsonl \
  --output benchmarks/sports/results/gpt4.1-mini_mix_task_evaluation.json \
  --prompt-file benchmarks/sports/evaluation_prompt.json \
  --max-turns 30 &

# Wait for all evaluations to complete
wait

# Run analyses in parallel
mcp-eval analyze \
  --predictions benchmarks/sports/results/gpt4o_mix_task_evaluation.json \
  --ground-truth data/sports/evaluation_tasks_verified.jsonl \
  --generate-report \
  --report-model gpt-4.1-2025-04-14 \
  --report-output benchmarks/sports/results/gpt4o_sports_report.md &

mcp-eval analyze \
  --predictions benchmarks/sports/results/gpt4o-mini_mix_task_evaluation.json \
  --ground-truth data/sports/evaluation_tasks_verified.jsonl \
  --generate-report \
  --report-model gpt-4.1-2025-04-14 \
  --report-output benchmarks/sports/results/gpt4o-mini_sports_report.md &

mcp-eval analyze \
  --predictions benchmarks/sports/results/gpt4.1-mini_mix_task_evaluation.json \
  --ground-truth data/sports/evaluation_tasks_verified.jsonl \
  --generate-report \
  --report-model gpt-4.1-2025-04-14 \
  --report-output benchmarks/sports/results/gpt4.1-mini_sports_report.md &

wait
```

## Adding Support for New MCP Servers

The CLI is designed to work with any MCP server that follows the standard protocol. Simply specify the server path with the `--server` argument. The server can be:

- An npm package (e.g., `@openbnb/mcp-server-airbnb`)
- A local Python script (e.g., `mcp_servers/healthcare/server.py`)
- Any executable that implements the MCP protocol

## Environment Variables

The CLI supports the following environment variables:

- `OPENAI_API_KEY`: OpenAI API key for task generation, verification, and analysis
- `X_API_KEY`: API key for XLAM model evaluation
- `MCP_EVAL_LOG_LEVEL`: Log level (DEBUG, INFO, WARNING, ERROR)

## Troubleshooting

### Common Issues

- **Connection Issues**: Ensure the MCP server is specified correctly and is accessible
- **API Key Errors**: Check that your API keys are set in the environment or `.env` file
- **Rate Limiting**: If you encounter rate limits, try reducing the number of tasks or increasing wait times
- **Memory Issues**: For large datasets, consider processing tasks in smaller batches using `--num-tasks`

### Server Arguments

For servers that require special arguments (especially those starting with `--`), pass them using `--server-args`:

```bash
# Correct way to pass server arguments
mcp-eval generate-tasks \
  --server @openbnb/mcp-server-airbnb \
  --server-args "--ignore-robots-txt" "--debug"
```

### Debugging

Enable debug logging to troubleshoot issues:

```bash
export MCP_EVAL_LOG_LEVEL=DEBUG
mcp-eval generate-tasks --server mcp_servers/healthcare/server.py --num-tasks 1
```

## Support

For additional help:
- Use `mcp-eval <subcommand> --help` for detailed command-specific documentation
- Check the [Analyzer Usage Guide](analyzer/README.md) for analysis-specific examples
- Review the `examples/` directory for complete workflow demonstrations
- Look at the `benchmarks/` directory for real-world usage patterns and script examples 