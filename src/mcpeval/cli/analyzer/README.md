# MCP Analyzer

The **MCP Analyzer** is a command-line tool that provides comprehensive analysis of model evaluation results by comparing predictions against ground truth data. It generates detailed performance metrics, identifies patterns, and creates AI-powered reports to help understand model strengths and weaknesses.

## Quick Start

```bash
# Basic usage - analyze model predictions against ground truth
mcp-eval analyze \
  --predictions results/healthcare_gpt4o_evaluation.json \
  --ground-truth data/healthcare/evaluation_tasks_verified.jsonl \
  --generate-report
```

## Installation

The analyzer is installed as part of the mcpeval package:

```bash
# From the repository root directory
uv pip install -e .
```

## Overview

The analyzer performs three main functions:

1. **Quantitative Analysis** - Calculates precise metrics for tool usage accuracy
2. **Pattern Recognition** - Identifies common failure modes and success patterns
3. **AI Report Generation** - Creates comprehensive performance reports with insights

## Arguments

### Required Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `--predictions` | Path to predictions JSON file (from model evaluation) | `results/evaluation.json` |
| `--ground-truth` | Path to ground truth JSONL/JSON file | `data/tasks_verified.jsonl` |

### Optional Arguments

#### Output Configuration
| Argument | Default | Description |
|----------|---------|-------------|
| `--evaluation-output` | `<predictions>_task_metrics.json` | Path to save task-level metrics |
| `--analysis-output` | `<predictions>_summary_analysis.json` | Path to save summary analysis |

#### Scoring Weights (must sum to 1.0)
| Argument | Default | Description |
|----------|---------|-------------|
| `--name-weight` | `0.4` | Weight for tool name matching |
| `--params-weight` | `0.4` | Weight for parameter matching |
| `--order-weight` | `0.2` | Weight for tool order matching |

#### Flexible Matching Thresholds
| Argument | Default | Description |
|----------|---------|-------------|
| `--param-threshold` | `0.6` | Parameter similarity threshold for flexible matching |
| `--order-threshold` | `0.5` | Order similarity threshold for flexible matching |

#### AI Report Generation
| Argument | Default | Description |
|----------|---------|-------------|
| `--generate-report` | `false` | Generate AI-powered performance report |
| `--report-model` | `gpt-4o` | Model to use for AI report generation |
| `--report-output` | `<predictions>_ai_report.md` | Path to save AI report |

#### Chart Generation
| Argument | Default | Description |
|----------|---------|-------------|
| `--include-charts` | `false` | Generate interactive charts and visualizations |
| `--chart-formats` | `['html', 'png']` | Chart output formats (html, png, svg) |

## Examples

### Basic Examples

#### 1. Simple Analysis

Compare model predictions against ground truth:

```bash
mcp-eval analyze \
  --predictions results/healthcare_gpt4o_evaluation.json \
  --ground-truth data/healthcare/evaluation_tasks_verified.jsonl
```

**Output files:**
- `healthcare_gpt4o_evaluation_task_metrics.json` - Detailed per-task evaluation
- `healthcare_gpt4o_evaluation_summary_analysis.json` - Aggregated analysis and patterns

#### 2. Generate AI Report

Create an AI-powered analysis report:

```bash
# Set OpenAI API key
export OPENAI_API_KEY="your-api-key-here"

mcp-eval analyze \
  --predictions results/healthcare_gpt4o_evaluation.json \
  --ground-truth data/healthcare/evaluation_tasks_verified.jsonl \
  --generate-report \
  --report-model gpt-4o
```

**Additional output:**
- `healthcare_gpt4o_evaluation_ai_report.md` - AI-generated performance report

#### 3. Analysis with Charts

Generate interactive visualizations:

```bash
mcp-eval analyze \
  --predictions results/healthcare_gpt4o_evaluation.json \
  --ground-truth data/healthcare/evaluation_tasks_verified.jsonl \
  --include-charts \
  --chart-formats html png
```

**Chart output:**
- Interactive HTML charts for web viewing
- PNG images for reports and presentations

### Advanced Examples

#### 4. Custom Scoring Weights

Prioritize parameter accuracy over tool name matching:

```bash
mcp-eval analyze \
  --predictions results/sports_gpt4o_evaluation.json \
  --ground-truth data/sports/evaluation_tasks_verified.jsonl \
  --name-weight 0.3 \
  --params-weight 0.5 \
  --order-weight 0.2 \
  --generate-report
```

#### 5. Stricter Flexible Matching

Use higher thresholds for more stringent evaluation:

```bash
mcp-eval analyze \
  --predictions results/national_parks_gpt4o_evaluation.json \
  --ground-truth data/national_parks/evaluation_tasks_verified.jsonl \
  --param-threshold 0.8 \
  --order-threshold 0.7 \
  --generate-report
```

#### 6. Complete Custom Configuration

Full customization with custom output paths:

```bash
mcp-eval analyze \
  --predictions results/healthcare_gpt4o_evaluation.json \
  --ground-truth data/healthcare/evaluation_tasks_verified.jsonl \
  --evaluation-output analysis/detailed_metrics.json \
  --analysis-output analysis/summary_report.json \
  --generate-report \
  --report-model gpt-4.1-2025-04-14 \
  --report-output analysis/performance_analysis.md \
  --include-charts \
  --chart-formats html png svg
```

### Batch Analysis

#### 7. Analyze Multiple Models

Compare different models on the same tasks:

```bash
# Analyze GPT-4o
mcp-eval analyze \
  --predictions results/healthcare_gpt4o_evaluation.json \
  --ground-truth data/healthcare/evaluation_tasks_verified.jsonl \
  --generate-report \
  --report-output reports/gpt4o_analysis.md &

# Analyze GPT-4o-mini
mcp-eval analyze \
  --predictions results/healthcare_gpt4o_mini_evaluation.json \
  --ground-truth data/healthcare/evaluation_tasks_verified.jsonl \
  --generate-report \
  --report-output reports/gpt4o_mini_analysis.md &

# Analyze GPT-4.1-mini
mcp-eval analyze \
  --predictions results/healthcare_gpt41_mini_evaluation.json \
  --ground-truth data/healthcare/evaluation_tasks_verified.jsonl \
  --generate-report \
  --report-output reports/gpt41_mini_analysis.md &

# Wait for all analyses to complete
wait
```

### Integration Examples

#### 8. Complete Workflow Example

From evaluation to analysis:

```bash
# 1. Evaluate a model
mcp-eval evaluate \
  --servers mcp_servers/healthcare/server.py \
  --model-config benchmarks/healthcare/eval_models/gpt-4o.json \
  --tasks-file data/healthcare/evaluation_tasks_verified.jsonl \
  --output results/healthcare_gpt4o_evaluation.json

# 2. Analyze the results with custom settings
mcp-eval analyze \
  --predictions results/healthcare_gpt4o_evaluation.json \
  --ground-truth data/healthcare/evaluation_tasks_verified.jsonl \
  --name-weight 0.35 \
  --params-weight 0.45 \
  --order-weight 0.2 \
  --param-threshold 0.7 \
  --generate-report \
  --include-charts \
  --report-model gpt-4o
```

## Analysis Metrics

The analyzer uses a comprehensive scoring system to evaluate model performance:

### Scoring Components

1. **Tool Name Matching** (default weight: 0.4)
   - Exact match: Full score
   - Partial match: Proportional score based on similarity

2. **Parameter Matching** (default weight: 0.4)
   - Exact match: Full score
   - Flexible match: Uses similarity threshold (default: 0.6)
   - Missing/Extra parameters: Proportional penalty

3. **Tool Order Matching** (default weight: 0.2)
   - Sequential order: Full score
   - Flexible order: Uses similarity threshold (default: 0.5)
   - Out-of-order: Proportional penalty

### Performance Metrics

- **Success Rate**: Percentage of tasks completed successfully
- **Tool Usage Accuracy**: Precision of tool selection and usage
- **Parameter Accuracy**: Correctness of tool parameters
- **Execution Efficiency**: Optimal vs. actual tool call sequences

## Input File Formats

### Predictions File Format

The predictions file should contain evaluation results from `mcp-eval evaluate`:

```json
[
  {
    "task_id": "task_001",
    "success": true,
    "tool_calls": [
      {
        "tool_name": "search_properties",
        "tool_parameters": {
          "location": "New York",
          "max_price": 200
        }
      }
    ],
    "conversation": [
      {
        "role": "user",
        "content": "Find apartments in New York under $200"
      },
      {
        "role": "assistant",
        "content": "I'll search for apartments in New York under $200.",
        "tool_calls": [...]
      }
    ]
  }
]
```

### Ground Truth File Format

The ground truth file should be in JSONL format from `mcp-eval verify-tasks`:

```json
{
  "id": "task_001",
  "name": "Search for affordable apartments",
  "description": "Find apartments in New York under $200",
  "tool_calls": [
    {
      "tool_name": "search_properties", 
      "tool_parameters": {
        "location": "New York",
        "max_price": 200
      }
    }
  ],
  "expected_conversation": [...]
}
```

## Output Files

### Task Metrics File (`*_task_metrics.json`)

Contains detailed evaluation results for each individual task:

```json
{
  "task_id": "task_001",
  "exact_match": {
    "score": 0.85,
    "tool_name_score": 1.0,
    "params_score": 0.8,
    "order_score": 0.9
  },
  "flexible_match": {
    "score": 0.92,
    "tool_name_score": 1.0,
    "params_score": 0.9,
    "order_score": 0.9
  },
  "mismatches": [
    {
      "type": "parameter",
      "expected": "max_price: 200",
      "actual": "max_price: 250",
      "tool_name": "search_properties"
    }
  ]
}
```

### Summary Analysis File (`*_summary_analysis.json`)

Contains aggregated analysis and patterns:

```json
{
  "summary": {
    "total_tasks": 100,
    "exact_match_success_rate": 0.75,
    "flexible_match_success_rate": 0.85,
    "average_exact_score": 0.78,
    "average_flexible_score": 0.82
  },
  "tool_usage": {
    "most_used_tools": ["search_properties", "get_details"],
    "accuracy_by_tool": {
      "search_properties": 0.85,
      "get_details": 0.78
    }
  },
  "parameter_mismatches": {
    "common_errors": [
      "Incorrect price range",
      "Missing location filters"
    ]
  },
  "success_patterns": {
    "high_success_combinations": [
      ["search_properties", "get_details"]
    ],
    "low_success_combinations": [
      ["search_properties", "filter_results", "get_details"]
    ]
  }
}
```

### AI Report File (`*_ai_report.md`)

Contains an AI-generated performance analysis report:

```markdown
# Model Performance Analysis Report

## Executive Summary
The model achieved an 85% success rate on flexible matching...

## Key Findings
- **Strength**: Excellent tool selection accuracy (95%)
- **Weakness**: Parameter precision needs improvement (78%)
- **Pattern**: Complex multi-step tasks show lower success rates

## Recommendations
1. Improve parameter validation
2. Enhance multi-step task handling
3. Focus on edge case scenarios
```

### Chart Files (when `--include-charts` is used)

Generated visualizations in specified formats:

- **Success Rate Charts**: Overall and per-tool success rates
- **Parameter Accuracy Charts**: Accuracy breakdown by parameter type
- **Tool Usage Patterns**: Frequency and success correlation
- **Performance Heatmaps**: Success rates across different task types

## Environment Variables

The analyzer supports the following environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for AI report generation | `sk-...` |
| `MCP_EVAL_LOG_LEVEL` | Log level for debugging | `DEBUG` |

### Setting Environment Variables

```bash
# Set OpenAI API key
export OPENAI_API_KEY="sk-your-openai-key"

# Enable debug logging
export MCP_EVAL_LOG_LEVEL="DEBUG"

# Run analysis with AI report
mcp-eval analyze \
  --predictions results/healthcare_evaluation.json \
  --ground-truth data/healthcare/tasks_verified.jsonl \
  --generate-report
```

## Best Practices

### 1. Scoring Configuration

- **Standard Tasks**: Use default weights (0.4, 0.4, 0.2)
- **Precision-Critical**: Increase parameter weight (0.3, 0.5, 0.2)
- **Sequence-Critical**: Increase order weight (0.3, 0.3, 0.4)

### 2. Threshold Tuning

- **Lenient Evaluation**: Lower thresholds (0.5, 0.4)
- **Strict Evaluation**: Higher thresholds (0.8, 0.7)
- **Balanced**: Default thresholds (0.6, 0.5)

### 3. Report Generation

- **Quick Analysis**: Skip AI reports for faster results
- **Detailed Insights**: Always generate AI reports for comprehensive analysis
- **Batch Processing**: Use parallel analysis for multiple models

### 4. Chart Generation

- **Web Viewing**: Use HTML format for interactive charts
- **Documentation**: Use PNG format for static images
- **Print Quality**: Use SVG format for high-resolution output

## Performance Monitoring

The analyzer provides real-time progress updates:

```bash
# Example output
🔍 Analyzing model performance...
📂 Loading prediction data from: results/healthcare_evaluation.json
📂 Loading ground truth data from: data/healthcare/tasks_verified.jsonl
🔍 Found 100 prediction tasks and 100 ground truth tasks
⚖️  Performing evaluation with custom weights and thresholds...
📊 Performing detailed analysis...
💾 Summary analysis saved to: results/healthcare_evaluation_summary_analysis.json
🤖 Generating AI report...
💾 AI report saved to: results/healthcare_evaluation_ai_report.md
```

## Troubleshooting

### Common Issues

#### 1. API Key Errors

```bash
# Check API key is set
echo $OPENAI_API_KEY

# Set API key if missing
export OPENAI_API_KEY="sk-your-key-here"

# Test with simple analysis
mcp-eval analyze \
  --predictions results/test_evaluation.json \
  --ground-truth data/test_tasks.jsonl \
  --generate-report
```

#### 2. Weight Validation Errors

```bash
# Weights must sum to 1.0
# ❌ This will cause normalization:
mcp-eval analyze \
  --predictions results/evaluation.json \
  --ground-truth data/tasks.jsonl \
  --name-weight 0.5 \
  --params-weight 0.5 \
  --order-weight 0.3  # Total: 1.3

# ✅ Correct weights:
mcp-eval analyze \
  --predictions results/evaluation.json \
  --ground-truth data/tasks.jsonl \
  --name-weight 0.4 \
  --params-weight 0.4 \
  --order-weight 0.2  # Total: 1.0
```

#### 3. File Format Issues

```bash
# Validate predictions file format
python -c "
import json
with open('results/evaluation.json') as f:
    data = json.load(f)
    print(f'Predictions: {len(data)} tasks')
    print(f'First task fields: {list(data[0].keys())}')
"

# Validate ground truth file format
python -c "
import json
with open('data/tasks.jsonl') as f:
    for i, line in enumerate(f):
        task = json.loads(line)
        print(f'Task {i+1}: {task.get(\"id\", \"Unknown\")}')
        if i >= 4:  # Show first 5 tasks
            break
"
```

#### 4. Memory Issues

```bash
# For large files, process in chunks
python -c "
import json
import os

# Check file size
size = os.path.getsize('results/large_evaluation.json')
print(f'File size: {size / (1024*1024):.2f} MB')

# If > 100MB, consider splitting
if size > 100 * 1024 * 1024:
    print('Consider processing in smaller batches')
"
```

#### 5. Missing Dependencies

```bash
# Install required packages
pip install openai plotly pandas numpy

# Verify installation
python -c "import openai, plotly, pandas, numpy; print('All dependencies installed')"
```

## Support

For additional help:

- **Documentation**: See the main MCPEval documentation
- **Issues**: Report bugs on the project repository
- **Examples**: Check the `benchmarks/` directory for usage examples

*For more information about the MCPEval system, see the main project documentation.* 