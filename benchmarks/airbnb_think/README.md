# Airbnb + Sequential Thinking Multi-Server Benchmark

This benchmark evaluates AI models on complex tasks that require both **structured reasoning** and **domain-specific search capabilities** by combining two MCP servers:

- **Sequential Thinking Server** (`@modelcontextprotocol/server-sequential-thinking`) - For structured problem decomposition and step-by-step reasoning
- **Airbnb Server** (`@openbnb/mcp-server-airbnb`) - For property search and accommodation analysis

## 🎯 Purpose

This benchmark tests models' ability to:
1. **Break down complex problems** using structured thinking
2. **Search and analyze** real-world accommodation data
3. **Coordinate between multiple tools** from different servers
4. **Synthesize information** from various sources into coherent recommendations

## 🏗️ Multi-Server Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        AI Model                                 │
└─────────────────────────┬───────────────────────────────────────┘
                          │
        ┌─────────────────┴─────────────────┐
        │                                   │
┌───────▼────────┐                 ┌───────▼────────┐
│ Sequential     │                 │ Airbnb         │
│ Thinking       │                 │ Server         │
│ Server         │                 │                │
│                │                 │                │
│ Tools:         │                 │ Tools:         │
│ • structured   │                 │ • search       │
│   reasoning    │                 │ • details      │
│ • planning     │                 │ • analysis     │
└────────────────┘                 └────────────────┘
```

## 📋 Task Dataset

This benchmark uses the **verified Airbnb tasks** from `data/airbnb/verified_results.jsonl` - a comprehensive collection of real-world accommodation search and analysis tasks that have been verified to work correctly with the Airbnb MCP server.

### Why Use Verified Airbnb Tasks?
- **Comprehensive Coverage**: Multiple diverse tasks covering different scenarios
- **Quality Assurance**: All tasks have been verified to work correctly
- **Comparative Analysis**: Compare single-server vs multi-server performance on identical tasks
- **Real-World Relevance**: Tasks based on actual accommodation search patterns

### Task Categories Include:
- **Family Vacation Planning** - Multi-generational group accommodations
- **Business Travel** - Corporate housing and meeting spaces  
- **Special Events** - Wedding venues, reunion properties
- **Accessibility Needs** - Accommodations with specific requirements
- **Budget Optimization** - Cost-effective options with desired amenities
- **Location-Specific** - Properties near landmarks, beaches, or attractions

### Multi-Server Enhancement
While these tasks were originally designed for single-server (Airbnb-only) evaluation, adding the Sequential Thinking server provides:
- **Structured Problem Decomposition** - Breaking complex searches into logical steps
- **Systematic Analysis** - Methodical comparison of options
- **Decision Justification** - Clear reasoning for final recommendations
- **Quality Assurance** - Verification steps for chosen properties

## 🚀 Running the Benchmark

### Prerequisites
- OpenAI API key set in environment
- MCP servers installed:
  ```bash
  npm install -g @modelcontextprotocol/server-sequential-thinking
  npm install -g @openbnb/mcp-server-airbnb
  ```

### Quick Start
```bash
# Run all model evaluations
./benchmarks/airbnb_think/evaluate_all_models.sh

# Or run individual model evaluation
mcp-eval evaluate \
  --servers "@modelcontextprotocol/server-sequential-thinking,@openbnb/mcp-server-airbnb:--ignore-robots-txt" \
  --model-config benchmarks/airbnb_think/eval_models/gpt-4.1-mini.json \
  --tasks data/airbnb/verified_results.jsonl \
  --output results/multi_server_test.json \
  --max-turns 30
```

### Monitor Progress
```bash
# Watch specific model evaluation
tail -f benchmarks/airbnb_think/logs/gpt4.1-mini_eval.log

# Check all running processes
ps aux | grep mcp-eval
```

## 📊 Results Structure

### Output Files
- **Results**: `benchmarks/airbnb_think/results/`
  - Raw evaluation data with tool calls and conversations
- **Reports**: `benchmarks/airbnb_think/report/`
  - Analyzed reports with insights and comparisons
- **Logs**: `benchmarks/airbnb_think/logs/`
  - Detailed execution logs for debugging

### Evaluation Metrics
- **Success Rate**: Task completion percentage
- **Tool Usage**: Frequency and effectiveness of each tool
- **Reasoning Quality**: Structure and coherence of thinking process
- **Final Recommendations**: Quality and justification of decisions

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
SERVERS="@modelcontextprotocol/server-sequential-thinking,@openbnb/mcp-server-airbnb:--ignore-robots-txt"

# Key parameters
MAX_TURNS=30  # Increased for complex multi-step tasks
```

## 🧪 Creating New Tasks

### Task Generation
```bash
# Generate new multi-server tasks
mcp-eval generate-tasks \
  --servers "$SERVERS" \
  --num-tasks 5 \
  --output new_multi_server_tasks.jsonl
```

### Task Structure
Multi-server tasks should:
1. **Require both capabilities** - Can't be solved with just one server
2. **Have clear success criteria** - Objective measures of completion
3. **Be realistic** - Based on real-world scenarios
4. **Scale appropriately** - Complex enough to benefit from structured thinking

## 🔍 Analysis Tools

### Built-in Analysis
```bash
# Generate comprehensive reports
mcp-eval analyze \
  --predictions results/model_evaluation.json \
  --ground-truth data/airbnb/verified_results.jsonl \
  --generate-report \
  --report-output report/analysis.md
```

### Custom Analysis
The results JSON contains detailed tool call traces, enabling custom analysis of:
- Tool coordination patterns
- Reasoning vs. action ratios
- Error recovery strategies
- Multi-server communication effectiveness

## 📈 Expected Outcomes

### High-Performing Models Should:
- **Break down complex tasks** into manageable steps
- **Use sequential thinking** to plan and structure approach
- **Make strategic tool calls** with proper context
- **Synthesize information** from multiple sources
- **Provide well-justified recommendations**

### Common Failure Modes:
- **Premature conclusions** without proper analysis
- **Poor tool coordination** between servers
- **Incomplete reasoning** due to turn limits
- **Information silos** - not integrating data across tools

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