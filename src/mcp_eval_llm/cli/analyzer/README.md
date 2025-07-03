# MCPEval - Analyzer Usage Guide

This document provides comprehensive usage instructions for the MCP evaluation analyzer, which compares model predictions against ground truth data and provides detailed performance metrics.

## Installation

The analyzer is installed as part of the mcp_eval_llm package:

```bash
# From the repository root directory
uv pip install -e .
```

## Command Line Usage

The analyzer can be used directly via the MCPEval CLI:

```bash
mcp-eval analyze --predictions <predictions_file> --ground-truth <ground_truth_file> [options]
```

### Required Arguments

- `--predictions`: Path to the predictions JSON file (typically `evaluation_results.json` from model evaluation)
- `--ground-truth`: Path to the ground truth JSONL or JSON file containing expected tool calls

### Optional Arguments

#### Output Configuration
- `--evaluation-output`: Path to save task-level metrics (default: `<predictions>_task_metrics.json`)
- `--analysis-output`: Path to save summary analysis (default: `<predictions>_summary_analysis.json`)

#### Scoring Weights (must sum to 1.0)
- `--name-weight`: Weight for tool name matching (default: 0.4)
- `--params-weight`: Weight for parameter matching (default: 0.4)  
- `--order-weight`: Weight for tool order matching (default: 0.2)

#### Flexible Matching Thresholds
- `--param-threshold`: Parameter similarity threshold for flexible matching (default: 0.6)
- `--order-threshold`: Order similarity threshold for flexible matching (default: 0.5)

#### AI Report Generation
- `--generate-report`: Generate an AI-powered performance report using OpenAI models
- `--report-model`: Model to use for AI report generation (default: gpt-4o)
- `--report-output`: Path to save AI report (default: `<predictions>_ai_report.md`)
- `--from-summary`: Generate report directly from an existing summary analysis JSON file

## Usage Examples

### 1. Basic Analysis

Compare model predictions against ground truth:

```bash
mcp-eval analyze \
  --predictions evaluation_results.json \
  --ground-truth tasks.jsonl
```

This produces:
- `evaluation_results_task_metrics.json` - detailed per-task evaluation
- `evaluation_results_summary_analysis.json` - aggregated analysis and patterns

### 2. Custom Scoring Weights

Prioritize parameter accuracy over tool name matching:

```bash
mcp-eval analyze \
  --predictions evaluation_results.json \
  --ground-truth tasks.jsonl \
  --name-weight 0.3 \
  --params-weight 0.5 \
  --order-weight 0.2
```

### 3. Stricter Flexible Matching

Use higher thresholds for more stringent flexible evaluation:

```bash
mcp-eval analyze \
  --predictions evaluation_results.json \
  --ground-truth tasks.jsonl \
  --param-threshold 0.8 \
  --order-threshold 0.7
```

### 4. Generate AI Performance Report

Create an AI-powered analysis report:

```bash
# Set OpenAI API key
export OPENAI_API_KEY="your-api-key-here"

mcp-eval analyze \
  --predictions evaluation_results.json \
  --ground-truth tasks.jsonl \
  --generate-report \
  --report-model gpt-4o
```

This produces an additional markdown report: `evaluation_results_ai_report.md`

### 5. Generate Report from Existing Analysis

Create a new AI report from previously saved analysis results:

```bash
mcp-eval analyze \
  --from-summary evaluation_results_summary_analysis.json \
  --report-model gpt-4o \
  --report-output custom_report.md
```

### 6. Custom Output Paths

Specify custom output file locations:

```bash
mcp-eval analyze \
  --predictions evaluation_results.json \
  --ground-truth tasks.jsonl \
  --evaluation-output detailed_metrics.json \
  --analysis-output summary_report.json \
  --generate-report \
  --report-output performance_analysis.md
```

### 7. Complete Workflow Example

Here's a complete example from evaluation to analysis:

```bash
# 1. Evaluate a model (produces evaluation_results.json)
mcp-eval evaluate \
  --server @openbnb/mcp-server-airbnb \
  --tasks-file verified_tasks.jsonl \
  --model xlam-p \
  --output evaluation_results.json

# 2. Analyze the results with custom settings
mcp-eval analyze \
  --predictions evaluation_results.json \
  --ground-truth verified_tasks.jsonl \
  --name-weight 0.35 \
  --params-weight 0.45 \
  --order-weight 0.2 \
  --param-threshold 0.7 \
  --generate-report \
  --report-model gpt-4o
```

## Input File Formats

### Predictions File Format
The predictions file should contain evaluation results in JSON format:

```json
[
  {
    "task_id": "task_001",
    "tool_calls": [
      {
        "tool_name": "search_properties",
        "tool_parameters": {
          "location": "New York",
          "max_price": 200
        }
      }
    ]
  }
]
```

### Ground Truth File Format
The ground truth file should be in JSONL or JSON format:

```json
{
  "id": "task_001",
  "tool_calls": [
    {
      "tool_name": "search_properties", 
      "tool_parameters": {
        "location": "New York",
        "max_price": 200
      }
    }
  ]
}
```

## Output Files

### Task Metrics File (`*_task_metrics.json`)
Contains detailed evaluation results for each individual task including:
- Task ID and tool call comparisons
- Individual scoring breakdowns  
- Specific mismatch details

### Summary Analysis File (`*_summary_analysis.json`)
Contains aggregated analysis and patterns including:
- Overall statistics and success rates
- Tool usage patterns and mismatches
- Success pattern analysis by combinations and complexity

### AI Report File (`*_ai_report.md`) 
Contains an AI-generated performance analysis report with:
- Executive summary of model performance
- Detailed insights and recommendations
- Specific areas for improvement

## Troubleshooting

### Common Issues

**Missing API Key for AI Reports:**
```bash
export OPENAI_API_KEY="your-api-key-here"
```

**Weight Validation Errors:**
Ensure weights sum to 1.0. The analyzer will auto-normalize if they don't.

**File Format Errors:**
- Ensure predictions file is valid JSON
- Ensure ground truth file is valid JSONL or JSON
- Check that required fields (`task_id`, `tool_calls`) are present

**Memory Issues with Large Files:**
For very large evaluation sets, consider processing in smaller batches.

---

## Understanding Metrics

For detailed information about the metrics and analysis outputs provided by the analyzer, see [metrics.md](./metrics.md).

---

*For more information about the MCPEval system, see the main project documentation.* 