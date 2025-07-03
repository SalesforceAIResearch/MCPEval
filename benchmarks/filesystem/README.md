# Filesystem Benchmark

This benchmark evaluates an LLM's ability to interact with a filesystem through the MCP protocol.

## Installation

To use the filesystem benchmark, you need to install the MCP filesystem server.

### Install the MCP Filesystem Server

The filesystem server allows an LLM to interact with your local filesystem in a controlled manner.

```bash
# Install the MCP filesystem server
npm install -g @modelcontextprotocol/server-filesystem
```

### Usage

The filesystem benchmark follows a three-step workflow: **Task Generation** → **Task Verification** → **Model Evaluation**

#### Step 1: Task Generation

Generate filesystem tasks using the MCP task generator:

```bash
# Generate filesystem tasks
mcp-eval generate-tasks \
  --server @modelcontextprotocol/server-filesystem \
  --server-args "benchmarks/filesystem/working" \
  --model gpt-4.1-2025-04-14 \
  --num-tasks 500 \
  --prompt-file benchmarks/filesystem/task_generation_prompt.json \
  --output data/filesystem/tasks.jsonl

# For testing, you can generate a smaller set:
# --num-tasks 2 --output data/filesystem/tasks_test.jsonl
```

The working directory `benchmarks/filesystem/working` serves as the sandbox environment where all filesystem operations are performed.

#### Step 2: Task Verification

Verify that generated tasks are valid and executable:

```bash
# Verify tasks using the simplified script
uv run benchmarks/filesystem/task_verification.py

# Or use the CLI tool directly
mcp-eval verify-tasks \
  --server @modelcontextprotocol/server-filesystem \
  --server-args "benchmarks/filesystem/working" \
  --model gpt-4.1-2025-04-14 \
  --prompt-file benchmarks/filesystem/task_verification_prompt.json \
  --tasks-file data/filesystem/tasks.jsonl \
  --output data/filesystem/tasks_verified.jsonl
```

**Key Features:**
- **Working Directory Clearing**: The verification script automatically clears the working directory before each task to ensure complete task independence
- **Task Validation**: Ensures tasks can be completed successfully with the available filesystem tools
- **Output**: Produces verified tasks ready for model evaluation

#### Step 3: Model Evaluation

Evaluate model performance on the filesystem tasks:

```bash
# Run simplified evaluation (recommended)
uv run benchmarks/filesystem/evaluation.py

# Or use the full CLI evaluator
mcp-eval evaluate \
  --server @modelcontextprotocol/server-filesystem \
  --server-args "benchmarks/filesystem/working" \
  --tasks-file data/filesystem/tasks_verified.jsonl \
  --model gpt-4o \
  --output data/filesystem/evaluation_results.json \
  --max-turns 10
```

**Evaluation Features:**
- **Clean Environment**: Each task starts with a fresh, empty working directory
- **Comprehensive Metrics**: Tracks success rate, execution time, and tool usage
- **Incremental Saving**: Results are saved after each task to prevent data loss
- **Resume Capability**: Can skip already evaluated tasks if rerun

#### Output Files

- `data/filesystem/tasks.jsonl` - Generated filesystem tasks
- `data/filesystem/tasks_verified.jsonl` - Verified tasks ready for evaluation  
- `data/filesystem/evaluation_results.json` - Model performance results

#### Configuration Options

You can customize the evaluation by modifying these parameters in the scripts:

- **Model**: Change `model_name` to test different models (gpt-4o, gpt-4, etc.)
- **Working Directory**: Modify `working_dir` path for different sandbox locations  
- **Max Turns**: Adjust `max_turns` for complex multi-step tasks
- **Task Count**: Use `--num-tasks` to limit evaluation scope