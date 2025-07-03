# YFinance + Sequential Thinking Multi-Server Benchmark

This benchmark evaluates AI models on complex financial analysis tasks that require both **structured reasoning** and **financial data analysis capabilities** by combining two MCP servers:

- **Sequential Thinking Server** (`@modelcontextprotocol/server-sequential-thinking`) - For structured problem decomposition and step-by-step reasoning
- **YFinance Server** (`mcp_servers/yfinance/server.py`) - For financial data retrieval and market analysis

## 🎯 Purpose

This benchmark tests models' ability to:
1. **Break down complex financial problems** using structured thinking
2. **Analyze real-world financial data** from Yahoo Finance
3. **Coordinate between multiple tools** from different servers
4. **Synthesize financial insights** into coherent investment recommendations

## 🏗️ Multi-Server Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        AI Model                                 │
└─────────────────────────┬───────────────────────────────────────┘
                          │
        ┌─────────────────┴─────────────────┐
        │                                   │
┌───────▼────────┐                 ┌───────▼────────┐
│ Sequential     │                 │ YFinance       │
│ Thinking       │                 │ Server         │
│ Server         │                 │                │
│                │                 │                │
│ Tools:         │                 │ Tools:         │
│ • structured   │                 │ • stock data   │
│   reasoning    │                 │ • financials   │
│ • planning     │                 │ • market info  │
└────────────────┘                 └────────────────┘
```

## 📋 Task Dataset

This benchmark uses the **verified YFinance tasks** from `data/yfinance/mix_verified_evaluation.jsonl` - a comprehensive collection of real-world financial analysis tasks that have been verified to work correctly with the YFinance MCP server.

### Why Use Verified YFinance Tasks?
- **Comprehensive Coverage**: Multiple diverse tasks covering different financial scenarios
- **Quality Assurance**: All tasks have been verified to work correctly
- **Comparative Analysis**: Compare single-server vs multi-server performance on identical tasks
- **Real-World Relevance**: Tasks based on actual financial analysis patterns

### Task Categories Include:
- **Stock Analysis** - Individual equity research and valuation
- **Portfolio Optimization** - Multi-asset allocation and risk analysis
- **Market Trends** - Sector analysis and market timing decisions
- **Financial Planning** - Retirement and investment goal planning
- **Risk Assessment** - Volatility analysis and downside protection
- **Comparative Analysis** - Stock vs stock or sector comparisons

### Multi-Server Enhancement
While these tasks were originally designed for single-server (YFinance-only) evaluation, adding the Sequential Thinking server provides:
- **Structured Financial Analysis** - Breaking complex investment decisions into logical steps
- **Systematic Research Process** - Methodical evaluation of financial metrics
- **Decision Frameworks** - Clear reasoning for investment recommendations
- **Risk-Reward Assessment** - Structured evaluation of investment trade-offs

## 🚀 Running the Benchmark

### Prerequisites
- OpenAI API key set in environment
- MCP servers installed:
  ```bash
  npm install -g @modelcontextprotocol/server-sequential-thinking
  # YFinance server is included in the repository
  ```

### Quick Start
```bash
# Run all model evaluations
./benchmarks/yfinance_think/evaluate_all_models.sh

# Or run individual model evaluation
mcp-eval evaluate \
  --servers "@modelcontextprotocol/server-sequential-thinking" "mcp_servers/yfinance/server.py" \
  --model-config benchmarks/yfinance_think/eval_models/gpt-4.1-mini.json \
  --tasks data/yfinance/mix_verified_evaluation.jsonl \
  --output results/yfinance_multi_test.json \
  --max-turns 30
```

### Monitor Progress
```bash
# Watch specific model evaluation
tail -f benchmarks/yfinance_think/logs/gpt4.1-mini_eval.log

# Check all running processes
ps aux | grep mcp-eval
```

## 📊 Results Structure

### Output Files
- **Results**: `benchmarks/yfinance_think/results/`
  - Raw evaluation data with tool calls and financial analysis
- **Reports**: `benchmarks/yfinance_think/report/`
  - Analyzed reports with investment insights and comparisons
- **Logs**: `benchmarks/yfinance_think/logs/`
  - Detailed execution logs for debugging

### Evaluation Metrics
- **Success Rate**: Task completion percentage
- **Tool Usage**: Frequency and effectiveness of each tool
- **Analysis Quality**: Depth and accuracy of financial reasoning
- **Investment Recommendations**: Quality and justification of decisions

## 🛠️ Configuration

### Model Configurations
All model configs are in `eval_models/`:
- `gpt-4o.json` - GPT-4o (most capable)
- `gpt-4.1-mini.json` - GPT-4.1 Mini (balanced)
- `o3.json` - O3 (reasoning focused)
- Plus other variants...

### Server Configuration
```bash
# Servers used in evaluation
SERVERS="@modelcontextprotocol/server-sequential-thinking mcp_servers/yfinance/server.py"

# Key parameters
MAX_TURNS=30  # Increased for complex multi-step financial analysis
```

## 🧪 Creating New Tasks

### Task Generation
```bash
# Generate new multi-server financial tasks
mcp-eval generate-tasks \
  --servers "$SERVERS" \
  --num-tasks 5 \
  --output new_financial_tasks.jsonl
```

### Task Structure
Multi-server financial tasks should:
1. **Require both capabilities** - Can't be solved with just financial data
2. **Have clear success criteria** - Objective measures of analysis quality
3. **Be realistic** - Based on real investment scenarios
4. **Scale appropriately** - Complex enough to benefit from structured thinking

## 🔍 Analysis Tools

### Built-in Analysis
```bash
# Generate comprehensive reports
mcp-eval analyze \
  --predictions results/model_evaluation.json \
  --ground-truth data/yfinance/mix_verified_evaluation.jsonl \
  --generate-report \
  --report-output report/financial_analysis.md
```

### Custom Analysis
The results JSON contains detailed tool call traces, enabling custom analysis of:
- Financial reasoning patterns
- Data retrieval vs. analysis ratios
- Investment decision quality
- Multi-server coordination in financial contexts

## 📈 Expected Outcomes

### High-Performing Models Should:
- **Structure financial analysis** into logical steps
- **Use sequential thinking** to plan investment research
- **Make strategic data queries** for relevant financial metrics
- **Synthesize quantitative data** with qualitative insights
- **Provide well-justified investment recommendations**

### Common Failure Modes:
- **Data overload** without proper analysis framework
- **Superficial analysis** missing key financial metrics
- **Poor risk assessment** ignoring downside scenarios
- **Disconnected reasoning** - not integrating data across tools

## 🤝 Contributing

### Adding New Models
1. Add model config to `eval_models/`
2. Update `evaluate_all_models.sh` with new model
3. Test with single task first
4. Run full benchmark

### Adding New Servers
1. Update `SERVERS` variable with new server
2. Modify tasks to utilize new capabilities
3. Update documentation and examples

## 📄 License

This benchmark is part of the mcp-eval-llm project and follows the same licensing terms. 