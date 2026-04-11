# Memory / Knowledge Graph MCP Server

MCP Server for persistent knowledge graph memory. Creates entities, relations, and observations stored in a local JSONL file.

## Installation

Install the server using npm:

```bash
# Install and run directly with npx (recommended)
npx -y @modelcontextprotocol/server-memory

# Or install globally
npm install -g @modelcontextprotocol/server-memory
```

## Usage with OpenAI Client

From the project root:

```bash
# Basic usage
uv run mcp_clients/example_openai_client/client.py --servers @modelcontextprotocol/server-memory

# With multiple servers
uv run mcp_clients/example_openai_client/client.py --servers @modelcontextprotocol/server-memory mcp_servers/hr_management/server.py
```

## Tools

### `create_entities`
Create multiple new entities in the knowledge graph.

**Required:**
- `entities` (array) - Array of entity objects with `name` (string), `entityType` (string), and `observations` (string array)

### `create_relations`
Create relations between entities.

**Required:**
- `relations` (array) - Array of relation objects with `from` (string), `to` (string), and `relationType` (string)

### `add_observations`
Add new observations to existing entities.

**Required:**
- `observations` (array) - Array of objects with `entityName` (string) and `contents` (string array)

### `delete_entities`
Delete entities and their associated relations.

**Required:**
- `entityNames` (array of strings) - Names of entities to delete

### `delete_observations`
Delete specific observations from entities.

**Required:**
- `deletions` (array) - Array of objects with `entityName` (string) and `observations` (string array)

### `delete_relations`
Delete specific relations from the knowledge graph.

**Required:**
- `relations` (array) - Array of relation objects with `from` (string), `to` (string), and `relationType` (string)

### `read_graph`
Read the entire knowledge graph.

No parameters required.

### `search_nodes`
Search for entities by name or content.

**Required:**
- `query` (string) - Search query to match against entity names, types, and observations

### `open_nodes`
Open specific entities by name.

**Required:**
- `names` (array of strings) - Names of entities to retrieve

## Storage

Data is stored in a local JSONL file. By default at `~/.claude/memory.jsonl`, configurable via `MEMORY_FILE_PATH` environment variable.

## Reference

This server is from the official [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers/tree/main/src/memory) repository.
