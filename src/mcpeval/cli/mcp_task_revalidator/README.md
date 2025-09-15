# MCP Task Revalidator

The **MCP Task Revalidator** is a command-line tool that improves task descriptions by analyzing the actual tool conversations and outcomes from verified tasks. It takes tasks that have been successfully verified (with conversation history and tool calls) and uses AI models to generate more accurate, detailed, and actionable task descriptions based on what really happened during execution.

## Quick Start

```bash
# Basic usage - revalidate task descriptions from verified tasks
mcp-eval revalidate-tasks \
  --verified-tasks-file data/healthcare/evaluation_tasks_verified.jsonl \
  --model gpt-4.1-2025-04-14 \
  --output data/healthcare/evaluation_tasks_revalidated.jsonl
```

## Installation

The task revalidator is installed as part of the mcpeval package:

```bash
# From the repository root directory
uv pip install -e .
```

## Overview

The task revalidator works by:

1. **Loading verified tasks** - Reads tasks with conversation history from JSONL files
2. **Analyzing conversations** - Examines the actual tool calls and responses
3. **Identifying gaps** - Finds discrepancies between original descriptions and actual execution
4. **Generating improvements** - Creates more accurate task descriptions and goals
5. **Saving results** - Outputs revalidated tasks with improved descriptions

## What Task Revalidation Does

### 🔄 **Description Enhancement**
- **Analyzes actual tool usage** - Reviews what tools were really called during execution
- **Identifies missing details** - Finds information that wasn't in the original description
- **Improves clarity** - Makes task descriptions more specific and actionable
- **Updates goals** - Refines task goals based on actual outcomes

### 📝 **Content Improvements**
- **Adds missing context** - Includes important details discovered during execution
- **Clarifies ambiguities** - Resolves unclear or vague instructions
- **Corrects assumptions** - Fixes incorrect assumptions in original descriptions
- **Enhances specificity** - Makes descriptions more precise and detailed

## When to Use Task Revalidation

Task revalidation is most beneficial when:

- **After task verification** - You have verified tasks with conversation history
- **Improving task quality** - Original descriptions are too vague or incomplete
- **Dataset refinement** - Creating high-quality evaluation datasets
- **Iterative improvement** - Refining tasks based on actual execution patterns

## Command Syntax

```bash
mcp-eval revalidate-tasks --verified-tasks-file <verified_tasks_file> [OPTIONS]
```

## Arguments

### Required Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `--verified-tasks-file` | Path to JSONL file containing verified tasks with conversation history | `data/healthcare/tasks_verified.jsonl` |

### Optional Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--output` | string | `revalidated_<input_filename>` | Output file path for revalidated tasks |
| `--model` | string | `gpt-4o` | OpenAI model for revalidation |
| `--model-config` | string | - | JSON file containing model configuration |
| `--num-tasks` | int | `-1` (all) | Number of tasks to revalidate |
| `--prompt-file` | string | - | JSON file containing custom revalidation prompts |
| `--non-interactive` | flag | `false` | Run in non-interactive mode |
| `--on-existing-file` | string | `timestamp` | Action when output file exists: `timestamp`, `overwrite`, `append` |
| `--api-key` | string | - | OpenAI API key (or use `OPENAI_API_KEY` env var) |

## Examples

### Basic Examples

```bash
# Revalidate all verified tasks
mcp-eval revalidate-tasks \
  --verified-tasks-file data/healthcare/tasks_verified.jsonl

# Revalidate with specific output file
mcp-eval revalidate-tasks \
  --verified-tasks-file data/healthcare/tasks_verified.jsonl \
  --output data/healthcare/tasks_improved.jsonl

# Revalidate only first 10 tasks
mcp-eval revalidate-tasks \
  --verified-tasks-file data/healthcare/tasks_verified.jsonl \
  --num-tasks 10
```

### Advanced Examples

```bash
# Use custom model configuration
mcp-eval revalidate-tasks \
  --verified-tasks-file data/healthcare/tasks_verified.jsonl \
  --model-config configs/revalidation_model.json

# Use custom revalidation prompts
mcp-eval revalidate-tasks \
  --verified-tasks-file data/healthcare/tasks_verified.jsonl \
  --prompt-file prompts/custom_revalidation.json

# Append to existing output file
mcp-eval revalidate-tasks \
  --verified-tasks-file data/healthcare/tasks_verified.jsonl \
  --output data/healthcare/tasks_revalidated.jsonl \
  --on-existing-file append

# Use different model
mcp-eval revalidate-tasks \
  --verified-tasks-file data/healthcare/tasks_verified.jsonl \
  --model gpt-4.1-2025-04-14
```

## Configuration Files

### Model Configuration

You can specify model settings using a JSON configuration file with the `--model-config` parameter:

#### Model Configuration File Format

Create a JSON file with model settings:

```json
{
  "model": "gpt-4.1-2025-04-14",
  "temperature": 0.01,
  "max_tokens": 16384,
  "top_p": 1.0
}
```

**Important**: Model configuration files take priority over individual CLI parameters. If you specify `--model-config`, the individual `--model` parameter will be ignored.

#### Example Model Configuration Files

You can find example model configuration files in the benchmarks directory:

- `benchmarks/healthcare/eval_models/gpt-4o.json`
- `benchmarks/national_parks/eval_models/gpt-4.1-mini.json`
- `benchmarks/airbnb/eval_models/gpt-4o.json`

### Custom Revalidation Prompts

Create a JSON file with custom prompts:

```json
{
  "system_message": "You are an expert at improving task descriptions based on actual execution patterns...",
  "revalidation_prompt": "Analyze the following task conversation and improve the description..."
}
```

## Input Requirements

### Verified Tasks File Format

The input file must contain verified tasks in JSONL format with:

- **conversation**: Array of message objects from task execution
- **tool_calls**: Array of tool calls made during execution
- **tool_call_results**: Results from tool call executions
- **tools**: Available tools during execution

Example task structure:
```json
{
  "id": "task_001",
  "name": "Patient Data Analysis",
  "description": "Analyze patient data",
  "goal": "Find patient information",
  "conversation": [...],
  "tool_calls": [...],
  "tool_call_results": [...],
  "tools": [...]
}
```

## Output

### Revalidated Tasks

The output contains tasks with improved descriptions:

```json
{
  "id": "task_001",
  "name": "Patient Data Analysis",
  "description": "Analyze patient data using the search_patients tool to find specific patients by condition, then retrieve detailed medical records using get_patient_details to examine symptoms, treatments, and outcomes for comprehensive analysis",
  "goal": "Search for patients with specific medical conditions and analyze their complete medical history including symptoms, treatments, and outcomes to identify patterns and treatment effectiveness",
  "conversation": [...],
  "tool_calls": [...],
  "tool_call_results": [...],
  "tools": [...]
}
```

## Quality Improvements

The revalidator typically improves tasks by:

### 📋 **Adding Specificity**
- **Tool usage details** - Specifies which tools should be used and how
- **Parameter requirements** - Clarifies what parameters are needed
- **Expected outcomes** - Describes what results to expect

### 🎯 **Clarifying Goals**
- **Success criteria** - Defines what constitutes successful completion
- **Scope boundaries** - Clarifies what is and isn't included
- **Measurement metrics** - Specifies how success is measured

### 🔧 **Technical Details**
- **Tool sequences** - Describes the order of tool operations
- **Data relationships** - Explains how data flows between tools
- **Error handling** - Addresses potential failure scenarios

## Best Practices

### 📝 **Preparation**
- **Verify tasks first** - Always run task verification before revalidation
- **Check conversation quality** - Ensure verified tasks have meaningful conversations
- **Review tool coverage** - Confirm tasks used relevant tools effectively

### 🔄 **Execution**
- **Start small** - Test with a few tasks before processing large batches
- **Review results** - Manually check improved descriptions for quality
- **Iterate prompts** - Refine custom prompts based on results

### 📊 **Quality Control**
- **Compare before/after** - Review changes made to descriptions
- **Validate improvements** - Ensure new descriptions are actually better
- **Test with evaluators** - Use improved tasks in evaluation pipelines

## Troubleshooting

### Common Issues

**No tasks with conversation data found**
- Ensure input file contains verified tasks with conversation history
- Check that tasks were successfully verified (not just generated)

**Low-quality improvements**
- Try different models or model configurations
- Customize revalidation prompts for your domain
- Ensure original conversations were meaningful

**Rate limiting errors**
- Increase delay between requests
- Use smaller batch sizes with `--num-tasks`
- Check API key quotas and limits

### Debug Options

```bash
# Enable debug logging
DEBUG=true mcp-eval revalidate-tasks --verified-tasks-file tasks.jsonl

# Process fewer tasks for testing
mcp-eval revalidate-tasks --verified-tasks-file tasks.jsonl --num-tasks 5

# Use interactive mode to review file handling
mcp-eval revalidate-tasks --verified-tasks-file tasks.jsonl --interactive
```

## Related Commands

- **[generate-tasks](../mcp_task_generator/README.md)** - Generate initial tasks from tools
- **[verify-tasks](../mcp_task_verifier/README.md)** - Verify tasks can be executed
- **[evaluate](../mcp_model_evaluator/README.md)** - Evaluate models using revalidated tasks

## Integration Examples

### Complete Task Development Pipeline

```bash
# 1. Generate initial tasks
mcp-eval generate-tasks \
  --servers mcp_servers/healthcare/server.py \
  --output data/healthcare/tasks_generated.jsonl

# 2. Verify tasks can be executed
mcp-eval verify-tasks \
  --servers mcp_servers/healthcare/server.py \
  --tasks-file data/healthcare/tasks_generated.jsonl \
  --output data/healthcare/tasks_verified.jsonl

# 3. Revalidate descriptions based on actual execution
mcp-eval revalidate-tasks \
  --verified-tasks-file data/healthcare/tasks_verified.jsonl \
  --output data/healthcare/tasks_final.jsonl

# 4. Use improved tasks for evaluation
mcp-eval evaluate \
  --servers mcp_servers/healthcare/server.py \
  --tasks-file data/healthcare/tasks_final.jsonl \
  --model-config configs/model_to_evaluate.json
```

### Batch Processing Multiple Domains

```bash
# Process all verified task files in a directory
for file in data/*/tasks_verified.jsonl; do
  echo "Revalidating $file"
  mcp-eval revalidate-tasks \
    --verified-tasks-file "$file" \
    --output "${file%_verified.jsonl}_revalidated.jsonl"
done
```

## Performance

### Processing Speed
- **Small tasks** (1-5 tool calls): ~2-3 seconds per task
- **Medium tasks** (5-15 tool calls): ~5-10 seconds per task  
- **Large tasks** (15+ tool calls): ~10-20 seconds per task

### Resource Usage
- **Memory**: Moderate (loads all tasks at once)
- **API calls**: 1-2 calls per task for revalidation
- **Storage**: Output files are similar size to input files

### Optimization Tips
- Use `--num-tasks` to process in batches
- Run during off-peak hours for better API performance
- Consider parallel processing for large datasets

## Support

For issues specific to task revalidation:
1. Check the [main CLI documentation](../README.md)
2. Review [troubleshooting guide](#troubleshooting)
3. Examine log output with `DEBUG=true`
4. Test with a small number of tasks first

The task revalidator is designed to work seamlessly with other MCPEval tools to create a complete task development and evaluation pipeline.
