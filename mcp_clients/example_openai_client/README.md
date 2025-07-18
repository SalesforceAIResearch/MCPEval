# Multi-Server OpenAI MCP Client Example

This example demonstrates how to use the enhanced OpenAI MCP client to connect to multiple MCP servers simultaneously and interact with tools from all servers in a single chat session. Supports advanced server configuration including arguments and environment variables.

## Features

- ✅ **Multiple Server Connections**: Connect to 2+ MCP servers at once
- ✅ **Unified Tool Access**: All tools from all servers available in one chat
- ✅ **Smart Tool Routing**: Automatic routing of tool calls to correct servers
- ✅ **Environment Variables**: Pass environment variables to servers for API keys and configuration
- ✅ **Server Identification**: Clear indication of which server provides each tool
- ✅ **Interactive Chat**: Full conversational interface with tool usage
- ✅ **Error Handling**: Graceful handling of connection and execution errors


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
uv run client.py --servers @modelcontextprotocol/server-sequential-thinking @openbnb/mcp-server-airbnb
```

### Advanced Usage with Explicit Arguments

```bash
# Explicit arguments using colon syntax
uv run client.py --servers @modelcontextprotocol/server-sequential-thinking @openbnb/mcp-server-airbnb:--ignore-robots-txt

# Multiple arguments (comma-separated)
uv run client.py --servers @openbnb/mcp-server-airbnb:--ignore-robots-txt,--debug ../../mcp_servers/filesystem/server.py

# Override auto-detection with empty arguments
uv run client.py --servers @openbnb/mcp-server-airbnb: @modelcontextprotocol/server-sequential-thinking

# Mix of auto-detection and explicit arguments
uv run client.py --servers @modelcontextprotocol/server-sequential-thinking @openbnb/mcp-server-airbnb:--ignore-robots-txt,--verbose
```

### Environment Variables

```bash
# Server with environment variables only
uv run client.py --servers @modelcontextprotocol/server-sequential-thinking mcp-server-nationalparks^NPS_API_KEY=your-api-key-here

# Server with both arguments and environment variables
uv run client.py --servers @modelcontextprotocol/server-sequential-thinking @openbnb/mcp-server-airbnb:--ignore-robots-txt^API_KEY=your-api-key-here

# Multiple environment variables (comma-separated)
uv run client.py --servers @some-server^VAR1=value1,VAR2=value2,DEBUG=true

# Three-server example with mixed configurations
uv run client.py --servers @modelcontextprotocol/server-sequential-thinking @openbnb/mcp-server-airbnb:--ignore-robots-txt mcp-server-nationalparks^NPS_API_KEY=your-api-key-here
```

### Server Format

| Format | Description | Example |
|--------|-------------|---------|
| `server` | Auto-detection | `@openbnb/mcp-server-airbnb` |
| `server:args` | Explicit arguments | `@openbnb/mcp-server-airbnb:--ignore-robots-txt` |
| `server:arg1,arg2` | Multiple arguments | `server.py:--debug,--verbose` |
| `server:` | Empty arguments (override auto-detection) | `@openbnb/mcp-server-airbnb:` |
| `server^ENV_VAR=value` | Environment variables | `mcp-server-nationalparks^NPS_API_KEY=12345` |
| `server:args^ENV_VAR=value` | Arguments + environment variables | `@server:--debug^API_KEY=secret` |
| `server^VAR1=val1,VAR2=val2` | Multiple environment variables | `@server^DEBUG=true,TIMEOUT=30` |

### Help

```bash
uv run client.py --help
```

## Example Session

```
🚀 Multi-Server OpenAI MCP Client Demo
==================================================
📡 Connecting to 3 servers:
  1. server-sequential-thinking (no args, no env)
  2. mcp-server-airbnb (args: ['--ignore-robots-txt'])
  3. mcp-server-nationalparks (env: {'NPS_API_KEY': 'xSmGqDy380Zkze2g7Rmc...'})

⏳ Establishing connections to all servers...
✅ Successfully connected to all servers!
🔧 Total tools available: 9

🔗 Connected to 3 servers:
  📁 server-sequential-thinking: 1 tools (sequentialthinking)
  📁 mcp-server-airbnb: 2 tools (airbnb_search, airbnb_listing_details)
  📁 mcp-server-nationalparks: 6 tools (findParks, getParkDetails, getAlerts, getVisitorCenters, getCampgrounds, getEvents)

💡 Try some example queries:
  - 'Help me think through a complex problem step by step'
  - 'Find me accommodations in San Francisco for next weekend'
  - 'What national parks are near the Bay Area?'
  - 'What tools do you have available?'
  - Type 'quit' to exit or 'reset' to clear conversation history

Query: Plan a travel near Bay Area, California

🤖 Assistant: I'll help you plan travel near the Bay Area by finding national parks and accommodations.

[Tool calls to multiple servers including National Parks API with environment variables...]
```

## Environment Variables

Many MCP servers require API keys or configuration through environment variables. The multi-server client supports passing environment variables to individual servers using the `^` separator.

### Setup and Security

```bash
# Store sensitive API keys in your shell environment
export NPS_API_KEY="your-national-parks-api-key"
export WEATHER_API_KEY="your-weather-api-key"

# Then reference them in the client command
uv run client.py --servers mcp-server-nationalparks^NPS_API_KEY=$NPS_API_KEY
```

### Environment Variable Features

- **Per-server configuration**: Each server can have its own set of environment variables
- **Multiple variables**: Use comma separation for multiple environment variables
- **Security display**: Environment variable values are truncated in logs for security
- **Override system env**: Client-provided env vars take precedence over system environment

### Important: `^` vs `::` Format

⚠️ **Always use `^` for environment variables, never `::` ⚠️**

| Format | Result | Example |
|--------|---------|---------|
| `server^API_KEY=value` ✅ | Sets environment variable correctly | `mcp-server-nationalparks^NPS_API_KEY=12345` |
| `server::API_KEY=value` ❌ | Passes as command argument, **causes auth failures** | `mcp-server-nationalparks::NPS_API_KEY=12345` |

Using `::` will result in "API_KEY_MISSING" errors because the API key is passed as a command-line argument instead of an environment variable.

### Common Use Cases

| Server Type | Environment Variables | Purpose |
|-------------|----------------------|---------|
| National Parks | `NPS_API_KEY` | Access to National Parks Service API |
| Weather Services | `WEATHER_API_KEY`, `OPENWEATHER_KEY` | Weather data access |
| Map Services | `MAPBOX_TOKEN`, `GOOGLE_MAPS_KEY` | Mapping and geocoding |
| Travel APIs | `AMADEUS_KEY`, `BOOKING_API_KEY` | Travel booking platforms |
| Database | `DATABASE_URL`, `DB_PASSWORD` | Database connections |

## Supported Server Types

### Registered MCP Servers
- `@modelcontextprotocol/server-sequential-thinking` - Step-by-step reasoning
- `@openbnb/mcp-server-airbnb` - Airbnb search and booking tools
- `mcp-server-nationalparks` - National Parks information (requires `NPS_API_KEY`)
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

### Flexible Server Configuration

The client supports multiple ways to configure servers:

#### 1. Auto-Detection (Default)
When no explicit arguments are provided, the client automatically applies appropriate arguments for known server types:
- **Airbnb Server** (`@openbnb/mcp-server-airbnb`): Adds `--ignore-robots-txt` flag
- **Other Servers**: No additional arguments

#### 2. Explicit Arguments
Use the `server:args` format to specify exact arguments:
- `@openbnb/mcp-server-airbnb:--ignore-robots-txt,--debug`
- `../../mcp_servers/filesystem/server.py:--verbose`

#### 3. Environment Variables
Use the `server^ENV_VAR=value` format to pass environment variables:
- `mcp-server-nationalparks^NPS_API_KEY=your-api-key`
- `@weather-server^API_KEY=key1,TIMEOUT=30`

#### 4. Combined Configuration
Combine arguments and environment variables:
- `@server:--debug,--verbose^API_KEY=secret,DEBUG=true`

#### 5. Override Auto-Detection
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

### Environment Variable Issues
- **Missing API Keys**: Ensure environment variables are correctly formatted: `SERVER^KEY=value`
- **Invalid Characters**: Avoid special shell characters in environment variable values
- **Server Startup Failures**: Check server logs for authentication errors when using API keys
- **Format Errors**: Use `^` (caret) to separate environment variables, not `::` or other symbols
- **Common Mistake**: Using `::` instead of `^` will pass the API key as a command argument, not an environment variable, causing authentication failures like "API_KEY_MISSING" errors

### Tool Conflicts
- If multiple servers have tools with the same name, only the first one loaded will be accessible
- Use server-specific prefixes in tool descriptions to identify source

### Performance
- Multiple servers may increase startup time
- Consider server resource usage when connecting to many servers
- Tool calls are processed sequentially for reliability

### Common Error Messages
- **"Connection closed"**: Usually indicates server startup failure, check API keys and server arguments
- **"Invalid tag name"**: Environment variables may have been parsed incorrectly, verify `^` separator usage
- **"Tool not found"**: Ensure the server providing the tool is connected and working properly

## Development

To extend this example:

1. **Add new servers**: Simply include them in the command line arguments
2. **Customize system prompt**: Modify the system prompt in `client.py` for specific use cases
3. **Add server-specific handling**: Extend the client to handle server-specific arguments or configurations

## Related Examples

- [Single Server Client](../example_openai_client/) - Basic single-server client
- [Task Generator Examples](../../examples/task_generator/) - Automated task generation
- [MCP Server Implementations](../../mcp_servers/) - Example server implementations 