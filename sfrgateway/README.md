# SFR LLM Gateway Proxy

A local OpenAI-compatible API proxy for the [Salesforce Research LLM Gateway](https://gateway.salesforceresearch.ai). It accepts standard OpenAI-format requests and forwards them upstream, so any OpenAI-SDK-compatible client works without modification.

## Files

| File | Description |
|---|---|
| `server.py` | FastAPI proxy server |
| `start_server.sh` | Convenience startup script |
| `test_gateway.py` | `SFRGatewayClient` class + test functions |
| `run_test.py` | Loads `.env` and runs the test suite |
| `requirements.txt` | Python dependencies |

---

## Setup

**1. Configure your API key:**

```bash
# sfrgateway/.env
X_API_KEY=<your-key>
```

Or export it directly:
```bash
export X_API_KEY=<your-key>
```

**2. Install dependencies:**

```bash
uv venv
uv pip install -r requirements.txt
```

---

## Starting the Proxy

```bash
bash start_server.sh
```

Or manually:

```bash
uv run uvicorn server:app --host 0.0.0.0 --port 8008
```

The proxy listens at `http://localhost:8008` and exposes:

| Endpoint | Description |
|---|---|
| `GET  /v1/models` | List available models from the gateway |
| `POST /v1/chat/completions` | Forward chat completion requests (streaming supported) |
| `GET  /health` | Proxy health check |

**Verify it's running:**

```bash
curl http://localhost:8008/health
# {"status":"ok","gateway":"https://gateway.salesforceresearch.ai/openai/process"}
```

---

## Testing

Run the full test suite (non-streaming, streaming, error handling):

```bash
uv run python run_test.py
```

Or call the gateway directly without the proxy:

```bash
uv run python test_gateway.py
```

---

## Usage

### With `curl`

```bash
curl -s http://localhost:8008/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Hello!"}]
  }' | jq '.choices[0].message.content'
```

### With the OpenAI Python SDK

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8008/v1",
    api_key="unused",  # auth is handled by the proxy via X_API_KEY
)

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello!"}],
)
print(response.choices[0].message.content)
```

### Streaming

```python
stream = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Write a haiku."}],
    stream=True,
)
for chunk in stream:
    print(chunk.choices[0].delta.content or "", end="", flush=True)
```

### Using `SFRGatewayClient` directly (no proxy)

```python
from test_gateway import SFRGatewayClient

client = SFRGatewayClient()  # reads X_API_KEY from environment

# Non-streaming
response = client.chat_completion(
    messages=[{"role": "user", "content": "Hello!"}],
    model="gpt-4o-mini",
)
print(response["choices"][0]["message"]["content"])

# Streaming
for chunk in client.chat_completion(
    messages=[{"role": "user", "content": "Write a haiku."}],
    model="gpt-4o-mini",
    stream=True,
):
    print(chunk, end="", flush=True)
```

---

## Configuration

| Environment Variable | Description | Default |
|---|---|---|
| `X_API_KEY` | API key for the SFR Gateway | *(required)* |
| `SFR_GATEWAY_BASE_URL` | Upstream gateway base URL | `https://gateway.salesforceresearch.ai/openai/process` |
| `PROXY_PORT` | Port the proxy listens on (when using `python server.py`) | `8000` |

---

## Available Models

| Model | Best for |
|---|---|
| `gpt-4o` | General tasks, balanced quality/speed |
| `gpt-4o-mini` | Fast, cost-effective tasks |

To list all models available on the gateway:

```bash
curl http://localhost:8008/v1/models | jq '[.data[].id]'
```
