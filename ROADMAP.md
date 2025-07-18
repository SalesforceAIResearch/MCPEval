# Development Roadmap

### MCP Server 🖥️
- ✅ Python stdio server support
- ✅ node.js stdio server support

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

### Data Pipeline 🔄
- ✅ Design unified data schema for all benchmarks
- ✅ Implement data preprocessing tools
- ✅ Add support for multiple data formats

### Benchmarks 🧪
- ✅ Airbnb MCP benchmark
- ✅ Healthcare MCP benchmark
- ✅ yahoo finance MCP benchmark
- ✅ Sports benchmark
- ✅ travel_assistant benchmark
- ✅ File System benchmark

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