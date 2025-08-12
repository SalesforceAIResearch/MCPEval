# Development Roadmap

### MCP Server 🖥️
- ✅ Python stdio server support
- ✅ node.js stdio server support
- ✅ http mcp server support
- 🔲 connecting mcp servers with json file as a standard way

### MCP Client 🤖
- ✅ Stdio client implementation
- ✅ message processing ability for LLM generation
- ✅ chatting ability
- ✅ support for connecting multiple servers

### Synthetic Data Generation 📝
- ✅ Tool use task generation
    - ✅ single turn
    - 🔲 multi-turn
- ✅ Task verification

### Evaluation 📊
- ✅ Implement core evaluation metrics (accuracy, latency)
- ✅ Create automated testing framework
- 🔲 Automatic Deep Evaluating 
- 🔲 Evaluating the implementation of MCP server

### Data Pipeline 🔄
- ✅ Design unified data schema for all benchmarks
- ✅ Implement data preprocessing tools
- ✅ Add support for multiple data formats

### LLM Provider 🧠
- ✅ OpenAI API integration (used for data generation and testing)
- ✅ local vllm-based model 

### CLI 🔧
- ✅ Task generator
- ✅ Task verifier
- ✅ Data converter
- ✅ Model evaluator
- ✅ Report generator
- ✅ Auto end-to-end evaluation

### Front-end 🎨
- ✅ React application setup with TypeScript
- ✅ Core navigation and routing
- ✅ MCP server configuration interface
- ✅ Chat client for MCP interactions
- ✅ Task generation and verification UI
- ✅ Model evaluation dashboard
- ✅ Results and analytics pages
- ✅ Data management interfaces
- 🔲 Unifying the model config for all the pages and sharing the same component
- 🔲 Saving any existing model config as a config file and support load it again

## Issues
- Evluating multiple models does not working
- Analyze feature does not support not generating AI report
- Judge Rubrics select not generate report