# MCP Model Evaluator - Metrics Documentation

This document explains the various metrics and analysis outputs provided by the MCP evaluation system, particularly the `analyze` command that compares model predictions against ground truth data.

## Overview

The MCP evaluator performs both **strict** and **flexible** matching to assess how well a model's tool calls match the expected ground truth. The system provides detailed metrics at both individual task and aggregate levels.

## 📊 Core Evaluation Metrics

### Matching Types

#### Strict Matching
- **Exact parameter matching**: All parameter values must match exactly
- **Exact order matching**: Tool calls must be in the exact same sequence
- **Binary success**: Task either completely succeeds or fails

#### Flexible Matching  
- **Fuzzy parameter matching**: Parameters are compared with similarity thresholds
- **Flexible order matching**: Allows some deviation in tool call sequence
- **Gradual scoring**: Tasks can have partial success scores

---

## 🎯 Summary Metrics Explained

### Basic Statistics
- **Total tasks evaluated**: Number of tasks processed in the comparison
- **Tasks with matching tool names**: Tasks where at least some predicted tools match ground truth tool names

### Weights Configuration
The evaluation uses a weighted scoring system:
- **Name weight** (default: 0.4): Importance of tool name matching
- **Parameters weight** (default: 0.4): Importance of parameter value matching  
- **Order weight** (default: 0.2): Importance of tool call sequence

### Thresholds Configuration
For flexible matching:
- **Parameter threshold** (default: 0.6): Minimum similarity score for parameter matching
- **Order threshold** (default: 0.5): Minimum similarity score for sequence matching

---

## 📈 Detailed Metric Definitions

### Success Metrics

#### Tasks with Complete Success
- **Strict**: Number of tasks where all tool calls match exactly (100% match)
- **Flexible**: Number of tasks meeting the flexible matching criteria
- **Interpretation**: Higher numbers indicate better model performance

#### Average Scores (0.0 - 1.0 scale)

##### Average Name Match Score
- **What it measures**: How well predicted tool names match expected tool names
- **Calculation**: Proportion of correctly named tools across all tasks
- **Perfect score**: 1.0 (all tool names correct)
- **Example**: 0.625 means 62.5% of tool names were correctly predicted

##### Average Parameter Match Score  
- **What it measures**: How well predicted parameters match expected parameters
- **Strict**: Exact value matching required
- **Flexible**: Similarity-based matching with threshold
- **Perfect score**: 1.0 (all parameters correct)
- **Example**: 1.000 means all parameter values matched perfectly

##### Average Order Match Score
- **What it measures**: How well the sequence of tool calls matches expected order
- **Calculation**: Sequence alignment scoring
- **Perfect score**: 1.0 (perfect sequence match)
- **Example**: 0.625 means moderate sequence similarity

##### Average Overall Score
- **What it measures**: Weighted combination of name, parameter, and order scores
- **Formula**: `(name_score × name_weight) + (param_score × param_weight) + (order_score × order_weight)`
- **Perfect score**: 1.0 (perfect match on all dimensions)
- **Example**: 0.775 indicates good overall performance with room for improvement

---

## 🔍 Detailed Analysis Sections

### Parameter Mismatches
- **What it shows**: Which specific parameters are most commonly incorrect
- **Format**: Tool name → Parameter name → Count of mismatches
- **Use case**: Identify systematic parameter prediction errors

### Tool Success Rates
- **What it shows**: Success percentage for each individual tool type
- **Calculation**: `(successful_predictions / total_attempts) × 100`
- **Use case**: Identify which tools the model struggles with most

### Success Rate by Tool Count
- **What it shows**: How success rate varies by task complexity (number of tools)
- **Pattern**: Usually decreases as number of tools increases
- **Use case**: Understand model limitations with complex multi-tool tasks

### Tool Combinations Analysis
- **What it shows**: Success rates for specific combinations of tools
- **Minimum threshold**: Only shows combinations appearing ≥5 times
- **Use case**: Identify problematic tool interaction patterns

### Missing Tools Analysis
- **What it shows**: Tools that were expected but not predicted
- **Count**: How many tasks had each tool missing
- **Use case**: Identify systematic omissions in model predictions

### Extra Tools Analysis  
- **What it shows**: Tools that were predicted but not expected
- **Count**: How many tasks had each extra tool
- **Use case**: Identify over-prediction patterns

---

## 📋 Interpreting Results

### Good Performance Indicators
- ✅ High overall scores (>0.8)
- ✅ High success rates for individual tools
- ✅ Low counts in missing/extra tools
- ✅ Consistent performance across tool counts

### Areas for Improvement
- ❌ Low parameter match scores → Review parameter prediction logic
- ❌ Low order match scores → Improve sequence planning
- ❌ High missing tool counts → Address systematic omissions
- ❌ High extra tool counts → Reduce over-prediction

### Flexible vs Strict Comparison
- **Similar scores**: Model is precise and accurate
- **Flexible > Strict**: Model has right idea but lacks precision
- **Both low**: Fundamental prediction issues

---

## 🛠 Customizing Evaluation

### Adjusting Weights
```bash
mcp-eval analyze --name-weight 0.5 --params-weight 0.3 --order-weight 0.2
```

### Adjusting Thresholds
```bash
mcp-eval analyze --param-threshold 0.7 --order-threshold 0.6
```

### Use Cases for Different Configurations
- **High name weight**: When tool selection is most critical
- **High params weight**: When parameter accuracy is paramount  
- **High order weight**: When execution sequence matters most
- **Higher thresholds**: For stricter flexible matching
- **Lower thresholds**: For more lenient flexible matching

---

## 📁 Output Files

### Task Metrics (`*_task_metrics.json`)
Contains detailed evaluation results for each individual task:
- Task ID and ground truth/prediction tool calls
- Individual scoring breakdowns
- Specific mismatch details

### Summary Analysis (`*_summary_analysis.json`)  
Contains aggregated analysis and patterns:
- Overall statistics and success rates
- Tool usage patterns and mismatches
- Success pattern analysis by combinations and complexity

---

## 🎯 Best Practices

1. **Baseline Establishment**: Run analysis on multiple model outputs to establish performance baselines
2. **Iterative Improvement**: Use mismatch analysis to guide model training improvements  
3. **Task Complexity Analysis**: Examine performance degradation with increasing tool counts
4. **Tool-Specific Training**: Focus training on tools with consistently low success rates
5. **Parameter Precision**: Address systematic parameter prediction errors identified in mismatch analysis

---

*For more information about the MCP evaluation system, see the main project documentation.* 