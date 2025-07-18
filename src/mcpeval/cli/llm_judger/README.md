# LLM Judger Module

This module provides comprehensive LLM judger capabilities for evaluating AI agent execution results and analyzing the generated scores.

## Overview

The LLM Judger module consists of two main commands:

1. **`llm-judge`** - Evaluates execution results using LLM judges to generate trajectory and completion scores
2. **`judge-rubric`** - Analyzes LLM judger results to provide statistical analysis and insights

## Commands

### 1. LLM Judge (`llm-judge`)

The main command for evaluating AI agent execution results using LLM judges. It processes evaluation files and generates trajectory and completion scores.

#### Usage

```bash
# Basic usage
python -m mcpeval.cli.main llm-judge \
    --input-file path/to/evaluation_results.json \
    --output-dir path/to/output/directory

# With ground truth and custom model
python -m mcpeval.cli.main llm-judge \
    --input-file path/to/evaluation_results.json \
    --output-dir path/to/output/directory \
    --ground-truth path/to/ground_truth.json \
    --model gpt-4o-mini

# With custom prompts and model configuration
python -m mcpeval.cli.main llm-judge \
    --input-file path/to/evaluation_results.json \
    --output-dir path/to/output/directory \
    --model-config path/to/model_config.json \
    --prompt-file path/to/custom_prompts.json \
    --verbose

# Resume interrupted evaluation
python -m mcpeval.cli.main llm-judge \
    --input-file path/to/evaluation_results.json \
    --output-dir path/to/output/directory \
    --resume

# Evaluate only trajectory or completion
python -m mcpeval.cli.main llm-judge \
    --input-file path/to/evaluation_results.json \
    --output-dir path/to/output/directory \
    --trajectory-only

python -m mcpeval.cli.main llm-judge \
    --input-file path/to/evaluation_results.json \
    --output-dir path/to/output/directory \
    --completion-only
```

#### Arguments

- `--input-file`: Path to evaluation results JSON/JSONL file (required)
- `--output-dir`: Directory to save LLM judge results (optional)
- `--ground-truth`: Path to ground truth JSON/JSONL file (optional)
- `--model`: Model to use for evaluation (default: gpt-4o)
- `--model-config`: Path to model configuration JSON file (optional)
- `--max-samples`: Maximum number of samples to evaluate (optional)
- `--trajectory-only`: Only evaluate trajectory scores (optional)
- `--completion-only`: Only evaluate completion scores (optional)
- `--verbose`: Enable verbose output (optional)
- `--quiet`: Enable quiet mode (optional)
- `--prompt-file`: Path to custom prompts JSON file (optional)
- `--resume`: Resume from existing results (optional)
- `--api-key`: OpenAI API key (optional, can use environment variable)

#### Input File Format

The input file should contain evaluation results in JSON or JSONL format:

```json
[
  {
    "task_id": "unique-task-id",
    "task": {
      "name": "Task Name",
      "description": "Task description",
      "requirements": ["requirement1", "requirement2"]
    },
    "conversation": [
      {
        "role": "user",
        "content": "User message"
      },
      {
        "role": "assistant",
        "content": "Assistant response",
        "tool_calls": [...]
      }
    ],
    "final_response": "Final response from the agent",
    "success": true,
    "tool_calls": [...]
  }
]
```

#### Ground Truth File Format

Optional ground truth file for reference evaluation:

```json
[
  {
    "id": "unique-task-id",
    "final_response": "Expected response",
    "conversation": [
      {
        "role": "user",
        "content": "User message"
      },
      {
        "role": "assistant",
        "content": "Expected assistant response"
      }
    ]
  }
]
```

#### Model Configuration File Format

Optional model configuration file:

```json
{
  "model": "gpt-4o-mini",
  "temperature": 0.1,
  "max_tokens": 4000,
  "timeout": 60
}
```

#### Custom Prompts File Format

Optional custom prompts file:

```json
{
  "trajectory": "Custom trajectory evaluation prompt...",
  "completion": "Custom completion evaluation prompt..."
}
```

#### Output Files

The command generates three output files:

1. **Combined Results**: `{input_name}_with_{model}_judge_results.jsonl`
2. **Trajectory Results**: `{input_name}_with_{model}_trajectory.jsonl`
3. **Completion Results**: `{input_name}_with_{model}_completion.jsonl`

Each output file contains:

```json
{
  "task_id": "unique-task-id",
  "task_name": "Task Name",
  "original_success": true,
  "trajectory_score": 0.95,
  "trajectory_scores": {
    "planning": 1.0,
    "execution_flow": 0.9,
    "tool_selection": 1.0,
    "tool_usage": 0.9,
    "adaptability": 1.0,
    "efficiency": 0.9,
    "context_awareness": 0.95
  },
  "trajectory_comments": "Detailed evaluation comments...",
  "completion_score": 0.92,
  "completion_scores": {
    "requirement_coverage": 1.0,
    "accuracy": 0.9,
    "completeness": 0.9,
    "usefulness": 0.85
  },
  "completion_comments": "Detailed evaluation comments...",
  "used_ground_truth_trajectory": false,
  "used_ground_truth_response": false
}
```

#### Examples

```bash
# Evaluate yfinance benchmark results
python -m mcpeval.cli.main llm-judge \
    --input-file benchmarks/yfinance/results/gpt4o_mix_task_evaluation.json \
    --output-dir benchmarks/yfinance/results/ \
    --model gpt-4o \
    --verbose

# Evaluate with ground truth reference
python -m mcpeval.cli.main llm-judge \
    --input-file benchmarks/healthcare/results/model_evaluation.json \
    --output-dir benchmarks/healthcare/results/ \
    --ground-truth benchmarks/healthcare/data/ground_truth.json \
    --model gpt-4o-mini

# Resume interrupted evaluation
python -m mcpeval.cli.main llm-judge \
    --input-file benchmarks/sports/results/evaluation_results.json \
    --output-dir benchmarks/sports/results/ \
    --resume \
    --verbose

# Limit evaluation to first 10 samples
python -m mcpeval.cli.main llm-judge \
    --input-file benchmarks/airbnb/results/evaluation_results.json \
    --output-dir benchmarks/airbnb/results/ \
    --max-samples 10 \
    --model gpt-4o
```

### 2. Judge Rubric Analysis (`judge-rubric`)

Analyzes LLM judger results to provide statistical analysis and insights. This command processes the output files generated by the `llm-judge` command.

#### Features

##### 1. **Statistical Analysis**
- Summary statistics for trajectory and completion scores
- Distribution analysis (high/medium/low score counts)
- Combined score calculations and analysis
- Aspect-level analysis for both trajectory and completion evaluations

##### 2. **Correlation Analysis**
- Correlation between trajectory and completion scores
- Analysis of original success vs. LLM judge scores
- Cross-aspect correlation insights

##### 3. **Pattern Identification**
- High performers (≥0.9 combined score)
- Low performers (≤0.5 combined score)
- Tasks with large gaps between trajectory and completion scores
- Consistent performers (scores within 0.1 of each other)
- Aspect-specific weaknesses identification

##### 4. **Insights Generation**
- Automated insight generation based on analysis results
- Performance gap identification
- Success alignment analysis
- Aspect-specific recommendations

##### 5. **AI Report Generation**
- Generate comprehensive AI-powered performance reports using OpenAI models
- Professional markdown reports with structured tables and analysis
- Executive summaries and actionable recommendations
- Support for generating reports from existing analysis files

#### Usage

##### Command Line Interface

```bash
# Basic analysis
python -m mcpeval.cli.main judge-rubric \
    --trajectory-file path/to/trajectory_scores.json \
    --completion-file path/to/completion_scores.json

# With output file and verbose mode
python -m mcpeval.cli.main judge-rubric \
    --trajectory-file path/to/trajectory_scores.json \
    --completion-file path/to/completion_scores.json \
    --output path/to/analysis_results.json \
    --verbose
```

##### Arguments

- `--trajectory-file`: Path to trajectory scores JSON file (required)
- `--completion-file`: Path to completion scores JSON file (required)
- `--output-dir`, `-o`: Directory to save analysis results and AI report (default: same as input files)
- `--verbose`, `-v`: Print detailed analysis information (optional)
- `--generate-report`: Generate AI-powered performance report: 1=enabled (default), 0=disabled (analysis only)
- `--report-model`: Model to use for AI report generation (default: gpt-4o)

##### Example with Real Files

```bash
# Default: Generate both analysis and AI report (saves to same directory as input files)
python -m mcpeval.cli.main judge-rubric \
    --trajectory-file benchmarks/yfinance/results/gpt4o_mix_task_evaluation_judged_trajectory_scores.json \
    --completion-file benchmarks/yfinance/results/gpt4o_mix_task_evaluation_judged_completion_scores.json

# Specify custom output directory
python -m mcpeval.cli.main judge-rubric \
    --trajectory-file benchmarks/yfinance/results/gpt4o_mix_task_evaluation_judged_trajectory_scores.json \
    --completion-file benchmarks/yfinance/results/gpt4o_mix_task_evaluation_judged_completion_scores.json \
    --output-dir custom/analysis/directory

# Analysis only (disable AI report generation)
python -m mcpeval.cli.main judge-rubric \
    --trajectory-file benchmarks/yfinance/results/gpt4o_mix_task_evaluation_judged_trajectory_scores.json \
    --completion-file benchmarks/yfinance/results/gpt4o_mix_task_evaluation_judged_completion_scores.json \
    --generate-report 0
```

#### Input File Format

##### Trajectory Scores File
```json
[
  {
    "task_id": "unique-task-id",
    "task_name": "Task Name",
    "original_success": true,
    "trajectory_score": 0.95,
    "trajectory_scores": {
      "planning": 1.0,
      "execution_flow": 0.9,
      "tool_selection": 1.0,
      "tool_usage": 0.9,
      "adaptability": 1.0,
      "efficiency": 0.9,
      "context_awareness": 0.95
    },
    "trajectory_comments": "Detailed evaluation comments..."
  }
]
```

##### Completion Scores File
```json
[
  {
    "task_id": "unique-task-id",
    "task_name": "Task Name",
    "original_success": true,
    "completion_score": 0.92,
    "completion_scores": {
      "requirement_coverage": 1.0,
      "accuracy": 0.9,
      "completeness": 0.9,
      "usefulness": 0.85
    },
    "completion_comments": "Detailed evaluation comments..."
  }
]
```

#### Output Format

The analysis results are saved in JSON format with the following structure:

```json
{
  "summary_statistics": {
    "total_tasks": 185,
    "trajectory_stats": {
      "count": 185,
      "mean": 0.970,
      "median": 1.0,
      "std_dev": 0.080,
      "min": 0.143,
      "max": 1.0,
      "high_scores": 178,
      "medium_scores": 6,
      "low_scores": 1
    },
    "completion_stats": { /* similar structure */ },
    "combined_stats": { /* similar structure */ },
    "task_coverage": {
      "tasks_with_both_scores": 185,
      "tasks_with_trajectory_only": 0,
      "tasks_with_completion_only": 0
    },
    "aspect_analysis": {
      "trajectory": {
        "planning": { "mean": 0.969, "median": 1.0, /* ... */ },
        /* other aspects */
      },
      "completion": {
        "requirement_coverage": { "mean": 0.966, "median": 1.0, /* ... */ },
        /* other aspects */
      }
    }
  },
  "correlations": {
    "trajectory_completion_correlation": 0.725,
    "original_success_correlation": {
      "success_trajectory_mean": 0.974,
      "failure_trajectory_mean": 0.143,
      "success_completion_mean": 0.928,
      "failure_completion_mean": 0.0,
      "success_count": 184,
      "failure_count": 1
    }
  },
  "patterns": {
    "high_performers": [
      {
        "task_id": "task-id",
        "task_name": "Task Name",
        "trajectory_score": 1.0,
        "completion_score": 1.0,
        "combined_score": 1.0
      }
    ],
    "low_performers": [ /* similar structure */ ],
    "trajectory_completion_gaps": [ /* tasks with large score gaps */ ],
    "consistent_performers": [ /* tasks with consistent scores */ ],
    "aspect_weaknesses": {
      "trajectory": { /* aspects with low scores */ },
      "completion": { /* aspects with low scores */ }
    }
  },
  "insights": [
    "Overall Performance: Average combined score of 0.946 with 180 high-performing tasks (≥0.8)",
    "Strong Correlation: Trajectory and completion scores are highly correlated (r=0.725)",
    /* more insights */
  ],
  "metadata": {
    "analysis_type": "llm_judger_results",
    "version": "1.0"
  }
}
```

#### AI Report Output

When using `--generate-report`, the tool creates a comprehensive markdown report with:

##### Executive Summary
- Overall performance overview
- Key performance indicators

##### Structured Tables
- Overall Performance Summary (trajectory vs completion vs combined scores)
- Aspect Performance Breakdown with improvement recommendations
- Performance Distribution by score ranges
- Top and Bottom Performers identification
- Correlation Analysis Results

##### Analysis Sections
- **Strengths and Weaknesses**: Key areas of excellence and improvement
- **Areas for Improvement**: Specific aspects requiring attention
- **Actionable Recommendations**: Concrete steps for performance enhancement
- **Conclusion**: Summary and next steps

##### Example AI Report Structure
```markdown
# LLM Judger Performance Report

## Executive Summary
The LLM judger evaluation indicates a robust overall performance...

## Overall Performance Summary
| Metric | Trajectory Score | Completion Score | Combined Score |
|--------|------------------|------------------|----------------|
| Mean   | 0.970           | 0.923           | 0.946         |

## Aspect Performance Breakdown
| Aspect | Mean Score | Performance Level | Improvement Needed |
|--------|------------|-------------------|-------------------|
| Planning | 0.969 | Excellent | Minimal |

## Actionable Recommendations
1. **Enhance Accuracy**: Focus on improving the accuracy of completion tasks...
2. **Optimize Efficiency**: Streamline processes and decision-making pathways...
```

#### Analysis Output

The tool provides a comprehensive console output with:

##### 📊 Overview
- Total tasks analyzed
- Task coverage (both scores, trajectory only, completion only)

##### 🛤️ Trajectory Scores & ✅ Completion Scores
- Mean ± standard deviation
- Range (min - max)
- Score distribution (high/medium/low)

##### 🎯 Combined Scores
- Statistics for the average of trajectory and completion scores

##### 🔗 Correlations
- Trajectory ↔ Completion correlation coefficient
- Original success impact analysis

##### 🎭 Aspect Analysis
- Detailed breakdown by evaluation aspects
- Color-coded display (green: ≥0.8, yellow: 0.6-0.8, red: <0.6)

##### 🔍 Key Patterns
- Count of high/low/consistent performers
- Score gap analysis

##### 💡 Key Insights
- Automated insights and recommendations
- Performance analysis
- Areas for improvement

#### Integration

##### Programmatic Usage

```python
from mcpeval.cli.llm_judger.analyze import analyze_llm_judger_results

# Run analysis
analyze_llm_judger_results(
    trajectory_file="path/to/trajectory_scores.json",
    completion_file="path/to/completion_scores.json",
    output_file="path/to/analysis_results.json",
    verbose=True
)
```

##### Loading Results

```python
import json

with open("analysis_results.json", "r") as f:
    results = json.load(f)

# Access statistics
stats = results["summary_statistics"]
print(f"Average trajectory score: {stats['trajectory_stats']['mean']:.3f}")

# Access insights
for insight in results["insights"]:
    print(f"• {insight}")
```

## Related Commands

- `llm-judge`: Generate LLM judge scores for evaluation results
- `analyze`: Analyze static tool evaluation results
- `evaluate`: Run model evaluation on tasks

## Workflow Example

Here's a complete workflow showing how to use both commands together:

```bash
# Step 1: Generate LLM judge scores from evaluation results
python -m mcpeval.cli.main llm-judge \
    --input-file benchmarks/yfinance/results/gpt4o_mix_task_evaluation.json \
    --output-dir benchmarks/yfinance/results/ \
    --model gpt-4o \
    --verbose

# Step 2: Analyze the generated LLM judge results
python -m mcpeval.cli.main judge-rubric \
    --trajectory-file benchmarks/yfinance/results/gpt4o_mix_task_evaluation_with_gpt-4o_trajectory.jsonl \
    --completion-file benchmarks/yfinance/results/gpt4o_mix_task_evaluation_with_gpt-4o_completion.jsonl \
    --output-dir benchmarks/yfinance/results/ \
    --verbose

# The complete workflow generates:
# 1. LLM judge scores (3 files: combined, trajectory, completion)
# 2. Statistical analysis results
# 3. AI-powered performance report
```

## Examples

See `examples/llm_judger_analysis_example.py` for a complete usage example. 