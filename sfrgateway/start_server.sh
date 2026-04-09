#!/bin/bash
# Start the SFR LLM Gateway proxy server on port 8000
port=8008
host=0.0.0.0
base_url=http://$host:$port/v1
cd "$(dirname "$0")"
export $(grep -v '^#' .env | xargs)
echo "Starting SFR LLM Gateway proxy..."
echo "  Gateway: $SFR_GATEWAY_BASE_URL"
echo "  Listening on: $base_url"
uv run uvicorn server:app --host $host --port $port
echo "Server started. You can now use the SFR LLM Gateway proxy at $base_url"