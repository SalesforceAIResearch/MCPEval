# Lumify Sports Intelligence MCP Server

A Model Context Protocol (MCP) server that exposes [Lumify](https://lumify.ai) sports intelligence to MCPEval — schedules, teams, players, events/scores, betting odds, and explainable bet confidence across 8+ sports.

This complements the existing [`sports`](../sports/) server (balldontlie.io) with a broader multi-sport surface plus odds and intelligence tools.

## Features

- List sports, teams, and players across NBA, NFL, MLB, NHL, soccer, tennis, golf, MMA, and more
- Query events/schedules with optional date windows and scores
- Fetch current odds and explainable bet intelligence for an event
- Built-in rate limiting suitable for free-tier API keys
- Short-lived response caching for repeated evaluation prompts

## Getting Your API Key

Lumify supports a **free instant key with no signup**:

1. Open [https://lumify.ai/docs/ai](https://lumify.ai/docs/ai)
2. Complete the Turnstile check and copy the `lmfy-...` key (100 credits, 14-day expiry)
3. Or create a persistent account key at [https://lumify.ai/api-keys](https://lumify.ai/api-keys)

Set the environment variable:

```bash
export LUMIFY_API_KEY="lmfy-..."

# Optional overrides
# export LUMIFY_BASE_URL="https://lumify.ai"
# export VERIFY_SSL=false
```

## Available Tools

| Tool | Description |
|------|-------------|
| `list_sports` | List available sports (and nested leagues) |
| `list_teams` | List/search teams for a sport |
| `list_players` | List/search players for a sport |
| `list_events` | List events for a sport (optional date window, scores) |
| `get_event` | Event detail; optionally embed odds + intelligence |
| `get_event_odds` | Current betting odds for an event |
| `get_event_intelligence` | Explainable bet confidence / recommendations |

## Usage with OpenAI Client

From the project root:

```bash
uv run mcp_clients/example_openai_client/client.py \
  --servers mcp_servers/lumify/server.py^LUMIFY_API_KEY=$LUMIFY_API_KEY
```

## Usage with MCPEval CLI

```bash
mcp-eval auto \
  --servers mcp_servers/lumify/server.py^LUMIFY_API_KEY=$LUMIFY_API_KEY \
  --working-dir evaluation_results/lumify_eval \
  --num-tasks 25
```

## Example Prompts

Once connected, ask:

- "What sports does Lumify cover?"
- "List NBA teams"
- "Find players named Curry in the NBA"
- "Show tonight's NBA events with scores"
- "Get odds for event 12345"
- "What does Lumify's bet intelligence say about event 12345?"

## Notes

- Auth header: `Authorization: Bearer <LUMIFY_API_KEY>`
- Cursor pagination uses `after_id` / `next_after_id` on teams, players, and events
- Event date windows (`date_from` / `date_to`) are limited to 90 days by the Lumify API
- Odds and intelligence calls may consume additional credits when data is available
- Docs: https://lumify.ai/docs · OpenAPI: https://lumify.ai/openapi.json · Hosted MCP: https://lumify.ai/mcp
