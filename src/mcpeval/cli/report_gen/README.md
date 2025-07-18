# Report Generation CLI

Generate AI-powered evaluation reports from analysis files. Supports tool usage reports, LLM judge reports, and comprehensive reports combining both using established evaluation frameworks.

## Features

1. **Tool Usage Reports** - Generate reports from tool analysis summary files (when only `--tool-analysis-file` is provided)
2. **LLM Judge Reports** - Generate reports from LLM judge analysis files (when only `--llm-judge-file` is provided)
3. **Comprehensive Reports** - Combine both analyses into a unified report using established evaluation rubrics and metrics (when both files are provided)
4. **Framework-Based Analysis** - Uses detailed evaluation rubrics and metrics for structured, consistent analysis
5. **Chart Generation** - Automatically include charts by default (can be disabled)
6. **Auto-Detection** - Automatically detect file types and generate appropriate reports

## Enhanced Comprehensive Reports

When both tool analysis and LLM judge files are provided, the system generates comprehensive reports that:

- **Follow Established Rubrics**: Uses the detailed LLM multi-aspect evaluation rubrics including:
  - Trajectory evaluation aspects (Planning, Execution Flow, Tool Selection, Tool Usage, Adaptability, Efficiency, Context Awareness)
  - Task completion aspects (Requirement Coverage, Accuracy, Completeness, Usefulness)

- **Apply Standardized Metrics**: Incorporates tool evaluation metrics including:
  - Strict vs Flexible matching performance
  - Parameter accuracy and mismatch patterns
  - Tool success rates and combination analysis
  - Efficiency metrics and error patterns

- **Provide Structured Analysis**: Delivers consistent, framework-based evaluation with:
  - Quantitative metrics with proper context
  - Qualitative insights based on established criteria
  - Correlation analysis between tool usage and LLM judge scores
  - Actionable recommendations aligned with evaluation frameworks

## Usage

### Basic Examples

```bash
# Generate tool usage report
mcp-eval report-gen \
    --tool-analysis-file path/to/model_summary_analysis.json

# Generate LLM judge report
mcp-eval report-gen \
    --llm-judge-file path/to/model_llm_judger_analysis.json

# Generate comprehensive report combining both (with framework-based analysis)
mcp-eval report-gen \
    --tool-analysis-file path/to/model_summary_analysis.json \
    --llm-judge-file path/to/model_llm_judger_analysis.json
```

### Advanced Options

```bash
# Custom output file and model name
mcp-eval report-gen \
    --tool-analysis-file path/to/analysis.json \
    --output-file custom_report.md \
    --model-name "gpt-4o-mini" \
    --model gpt-4o

# Disable charts
mcp-eval report-gen \
    --tool-analysis-file path/to/analysis.json \
    --no-charts

# Tool analysis file only (generates tool usage report)
mcp-eval report-gen \
    --tool-analysis-file path/to/analysis.json
```

## Arguments

### Input Files
- `--tool-analysis-file` - Path to tool usage analysis JSON file (summary analysis format)
- `--llm-judge-file` - Path to LLM judge analysis JSON file

### Output Configuration
- `--output-file`, `-o` - Output file path for generated report (auto-generated if not specified)
- `--model-name` - Name of the model being analyzed (extracted from filename if not specified)

### Report Generation Options
- `--model`, `-m` - OpenAI model to use for report generation (default: gpt-4o)

### Chart Options
- `--include-charts` - Include charts in the report (default: enabled, so this flag is optional)
- `--no-charts` - Disable chart generation
- `--verbose`, `-v` - Print detailed information

## File Format Requirements

### Tool Analysis Files
Should contain the following structure:
```json
{
  "summary": { ... },
  "tool_usage": { ... },
  "parameter_mismatches": { ... },
  "success_patterns": { ... }
}
```

### LLM Judge Analysis Files  
Should contain the following structure:
```json
{
  "summary_statistics": { ... },
  "correlations": { ... },
  "patterns": { ... },
  "insights": [ ... ]
}
```

## Output

The tool generates:
1. **AI-powered markdown reports** with comprehensive, framework-based analysis
2. **Charts and visualizations** (when enabled)
3. **Structured tables** with key metrics
4. **Actionable recommendations** aligned with evaluation rubrics

For comprehensive reports, the output includes:
- Executive Summary with rubric-based scoring
- Tool Usage Analysis following established metrics
- LLM Judge Analysis based on trajectory and task completion rubrics
- Integrated Analysis correlating both evaluation dimensions
- Detailed findings with quantitative and qualitative insights
- Actionable recommendations for improvement

## Evaluation Framework Integration

The comprehensive reports automatically incorporate:

### LLM Judge Rubrics (rubrics.md)
- 11 evaluation aspects with 0.0-1.0 scoring scales
- Detailed criteria for planning, execution, tool usage, adaptability, efficiency, context awareness
- Task completion evaluation for coverage, accuracy, completeness, usefulness

### Tool Usage Metrics (metrics.md)
- Strict vs flexible matching analysis
- Parameter accuracy and mismatch patterns
- Tool success rates and combination patterns
- Efficiency metrics and systematic error identification

## Examples with Real Files

```bash
# Using files from yfinance benchmark
mcp-eval report-gen \
    --tool-analysis-file benchmarks/yfinance/report/gpt4o_summary_analysis.json \
    --llm-judge-file benchmarks/yfinance/report/gpt4o_llm_judger_analysis.json \
    --model-name gpt-4o

# Healthcare benchmark tool report only
mcp-eval report-gen \
    --tool-analysis-file benchmarks/healthcare/report/gpt4.1-mini_summary_analysis.json \
    --model-name "gpt-4.1-mini"
``` 