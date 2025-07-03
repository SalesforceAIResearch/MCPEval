This will test a simple chat with tools ability with openai client and a special calculator server.
```
export OPENAI_API_KEY=your_openai_api_key_here
uv run ../../mcp_clients/example_openai_client/client.py ../../mcp_servers/special_calculator/server.py
```

## Example Session

Below is an example of a conversation with the calculator:

### Terminal Initialization

```
client created
Processing request of type ListToolsRequest

Connected to server with tools: ['special_add', 'special_subtract', 'special_multiply', 'special_divide']

MCP Client Started!
Type your queries, 'reset' to clear conversation history, or 'quit' to exit.
```

### User Query
```
Query: Hi 
```

### Terminal Output
```
Processing request of type ListToolsRequest

Hello! How can I assist you today?
```

### User Query
```
Query: add 3 + 4
```

### Terminal Output
```
Processing request of type ListToolsRequest
Processing request of type CallToolRequest
Processing request of type CallToolRequest

[Calling tool special_add with args {'a': 3, 'b': 4}]
The special addition of 3 and 4, with the result doubled, is 14.
```

### User Query
```
Query: can you add the results with 5
```

### Terminal Output
```
Processing request of type ListToolsRequest
Processing request of type CallToolRequest
Processing request of type CallToolRequest

[Calling tool special_add with args {'a': 14, 'b': 5}]
The special addition of 14 and 5, with the result doubled, is 38.
```

### User Query
```
Query: can you subtract the results with 5
```

### Terminal Output
```
Processing request of type ListToolsRequest
Processing request of type CallToolRequest
Processing request of type CallToolRequest

[Calling tool special_subtract with args {'a': 38, 'b': 5}]
The special subtraction of 38 and 5, with the result halved, is 16.5.
```

The special calculator adds functionality by doubling addition results and halving subtraction results.