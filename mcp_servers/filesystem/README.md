# Filesystem MCP Server

A Model Context Protocol (MCP) server that provides filesystem access capabilities.

## Reference

Official implementation: [https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem)

## Testing with OpenAI Client

To test the filesystem MCP server with the OpenAI client example:

```bash
uv run mcp_clients/example_openai_client/client.py @modelcontextprotocol/server-filesystem .
```

This command will:
- Use `uv` to run the example OpenAI client
- Connect to the `@modelcontextprotocol/server-filesystem` MCP server
- Provide access to the current directory (`.`) for filesystem operations

## Prerequisites

- Ensure you have `uv` installed
- Install the required dependencies (typically handled by `uv`)
- Have the MCP server filesystem package available

## Usage

The filesystem MCP server enables AI models to interact with the local filesystem through the MCP protocol, allowing operations like reading files, listing directories, and other filesystem-related tasks in a controlled manner.
