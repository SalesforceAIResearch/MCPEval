# Multi-Server OpenAI MCP Client Example

This example demonstrates how to use the enhanced OpenAI MCP client to connect to multiple MCP servers simultaneously and interact with tools from all servers in a single chat session.

## Features

- ✅ **Multiple Server Connections**: Connect to 2+ MCP servers at once
- ✅ **Unified Tool Access**: All tools from all servers available in one chat
- ✅ **Smart Tool Routing**: Automatic routing of tool calls to correct servers
- ✅ **Server Identification**: Clear indication of which server provides each tool
- ✅ **Interactive Chat**: Full conversational interface with tool usage
- ✅ **Error Handling**: Graceful handling of connection and execution errors

## Requirements

- Python 3.8 or higher
- OpenAI API key
- MCP servers installed and accessible

## Setup

1. **Set your OpenAI API key:**
   ```bash
   export OPENAI_API_KEY='your-api-key-here'
   ```

2. **Install required dependencies:**
   ```bash
   # From the project root
   uv sync
   ```

3. **Ensure MCP servers are available:**
   - For registered servers (like `@modelcontextprotocol/server-sequential-thinking`), they should be installed via npm/npx
   - For local servers, ensure the paths are correct

## Usage

### Basic Usage

```bash
# Auto-detection mode (Airbnb gets --ignore-robots-txt automatically)
uv run client.py @modelcontextprotocol/server-sequential-thinking @openbnb/mcp-server-airbnb
```

### Advanced Usage with Explicit Arguments

```bash
# Explicit arguments using colon syntax
uv run client.py @modelcontextprotocol/server-sequential-thinking @openbnb/mcp-server-airbnb:--ignore-robots-txt

# Multiple arguments (comma-separated)
uv run client.py @openbnb/mcp-server-airbnb:--ignore-robots-txt,--debug ../../mcp_servers/filesystem/server.py

# Override auto-detection with empty arguments
uv run client.py @openbnb/mcp-server-airbnb: @modelcontextprotocol/server-sequential-thinking

# Mix of auto-detection and explicit arguments
uv run client.py @modelcontextprotocol/server-sequential-thinking @openbnb/mcp-server-airbnb:--ignore-robots-txt,--verbose
```

### Server:Args Format

| Format | Description | Example |
|--------|-------------|---------|
| `server` | Auto-detection | `@openbnb/mcp-server-airbnb` |
| `server:args` | Explicit arguments | `@openbnb/mcp-server-airbnb:--ignore-robots-txt` |
| `server:arg1,arg2` | Multiple arguments | `server.py:--debug,--verbose` |
| `server:` | Empty arguments (override auto-detection) | `@openbnb/mcp-server-airbnb:` |

### Help

```bash
python client.py --help
```

## Example Session

```
🚀 Multi-Server OpenAI MCP Client Demo
==================================================
📡 Connecting to 2 servers:
  1. server-sequential-thinking
  2. mcp-server-airbnb

⏳ Establishing connections to all servers...
✅ Successfully connected to all servers!
🔧 Total tools available: 3

🔗 Connected to 2 servers:
  📁 server-sequential-thinking: 1 tools (sequentialthinking)
  📁 mcp-server-airbnb: 2 tools (search_listings, get_listing_details)

💡 Try some example queries:
  - 'Help me think through a complex problem step by step'
  - 'Find me accommodations in San Francisco for next weekend'
  - 'What tools do you have available?'
  - Type 'quit' to exit or 'reset' to clear conversation history

Query: Help me find an Airbnb in NYC and think through the booking process

🤖 Assistant: I'll help you find an Airbnb in NYC and then use sequential thinking to walk through the booking process step by step.

[Tool calls to both servers...]
```

## Supported Server Types

### Registered MCP Servers
- `@modelcontextprotocol/server-sequential-thinking` - Step-by-step reasoning
- `@openbnb/mcp-server-airbnb` - Airbnb search and booking tools
- Any other registered MCP servers

### Local MCP Servers
- `../../mcp_servers/filesystem/server.py` - File system operations
- `../../mcp_servers/special_calculator/server.py` - Mathematical calculations
- `../../mcp_servers/travel_assistant/server.py` - Travel planning tools
- Any other local MCP server implementations

## Architecture

The multi-server client works by:

1. **Connection Management**: Each server runs in its own process with stdio communication
2. **Tool Aggregation**: Tools from all servers are combined into a single tool list for the LLM
3. **Smart Routing**: Tool calls are automatically routed to the server that owns each tool
4. **Error Isolation**: Failures in one server don't crash the entire client
5. **Automatic Server Configuration**: Server-specific arguments are automatically applied based on server type

## Server-Specific Features

### Flexible Argument Handling

The client supports multiple ways to specify server arguments:

#### 1. Auto-Detection (Default)
When no explicit arguments are provided, the client automatically applies appropriate arguments for known server types:
- **Airbnb Server** (`@openbnb/mcp-server-airbnb`): Adds `--ignore-robots-txt` flag
- **Other Servers**: No additional arguments

#### 2. Explicit Arguments
Use the `server:args` format to specify exact arguments:
- `@openbnb/mcp-server-airbnb:--ignore-robots-txt,--debug`
- `../../mcp_servers/filesystem/server.py:--verbose`

#### 3. Override Auto-Detection
Use `server:` (with empty args) to override auto-detection:
- `@openbnb/mcp-server-airbnb:` (runs without any arguments)

This provides both convenience for common cases and flexibility for custom configurations.

## Common Use Cases

### 1. Research and Reasoning
Combine sequential thinking with information gathering tools:
```
Query: Help me research and think through whether I should visit Tokyo or Kyoto for my trip
```

### 2. Planning and Execution
Use multiple specialized tools for complex tasks:
```
Query: Plan a 3-day trip to San Francisco including finding accommodations and calculating costs
```

### 3. Cross-Domain Problem Solving
Leverage different server capabilities for comprehensive solutions:
```
Query: Help me analyze my travel options and create a step-by-step booking plan
```

## Troubleshooting

### Connection Issues
- Ensure all server paths are correct and servers are accessible
- Check that registered servers are properly installed
- Verify that your OpenAI API key is valid

### Tool Conflicts
- If multiple servers have tools with the same name, only the first one loaded will be accessible
- Use server-specific prefixes in tool descriptions to identify source

### Performance
- Multiple servers may increase startup time
- Consider server resource usage when connecting to many servers
- Tool calls are processed sequentially for reliability

## Development

To extend this example:

1. **Add new servers**: Simply include them in the command line arguments
2. **Customize system prompt**: Modify the system prompt in `client.py` for specific use cases
3. **Add server-specific handling**: Extend the client to handle server-specific arguments or configurations

## Related Examples

- [Single Server Client](../example_openai_client/) - Basic single-server client
- [Task Generator Examples](../../examples/task_generator/) - Automated task generation
- [MCP Server Implementations](../../mcp_servers/) - Example server implementations 