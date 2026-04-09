# MCPEval Development Guide

## LLM Inference via SFRGateway

This project uses the Salesforce Research LLM Gateway proxy for all LLM calls (task generation, evaluation, user simulation, judging).

### Starting the gateway

```bash
cd /Users/zhiweiliu/Documents/projects/enterprise_bench/enterprise-bench/sfrgateway
PROXY_PORT=8008 uv run python server.py
```

The `.env` file in that directory contains the `X_API_KEY` for the upstream gateway.

### Model config files

Point any model config JSON at the local proxy:

```json
{
    "model": "gpt-4o-mini",
    "base_url": "http://localhost:8008/v1",
    "api_key": "dummy",
    "temperature": 0.1,
    "max_tokens": 4000
}
```

- `api_key` must be set to any non-empty string (e.g. `"dummy"`) — the real key is handled by the proxy.
- Port 8008 is the default. MCPEval/UserBench historically use port 8009.
- Available models include `gpt-4o-mini`, `gpt-4o`, `gpt-5-nano`, and others listed at `http://localhost:8008/v1/models`.

## Running the project

```bash
uv venv && uv pip install -e ".[dev]"
uv run mcp-eval --help
```

## Key conventions

- Use `uv run` to execute commands (not raw `python`).
- Model configs are JSON files passed via `--model-config`, `--simulator-model-config`, or `--agent-model-config`.
- MCP servers live in `mcp_servers/` and are passed via `--servers mcp_servers/<name>/server.py`.
- All data I/O uses JSONL format (one JSON object per line).
