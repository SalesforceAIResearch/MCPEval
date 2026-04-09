#!/usr/bin/env python3
"""
Local OpenAI-compatible API proxy for the Salesforce Research LLM Gateway.

Exposes:
  GET  /v1/models              → lists available models from the gateway
  POST /v1/chat/completions    → forwards chat completion requests to the gateway

Run with:
  uvicorn server:app --host 0.0.0.0 --port 8000
  (or: python server.py)

Then point any OpenAI-compatible client at http://localhost:8000/v1
"""

import json
import os

import requests
import urllib3
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

load_dotenv()

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

GATEWAY_BASE_URL = os.environ.get(
    "SFR_GATEWAY_BASE_URL",
    "https://gateway.salesforceresearch.ai/openai/process",
).rstrip("/")

app = FastAPI(
    title="SFR LLM Gateway Proxy",
    description="OpenAI-compatible proxy for the Salesforce Research LLM Gateway",
    version="1.0.0",
)


def _gateway_headers() -> dict:
    api_key = os.environ.get("X_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="SFR Gateway API key not set. Set X_API_KEY in your environment.",
        )
    return {
        "X-Api-Key": api_key,
        "Content-Type": "application/json",
    }


@app.get("/v1/models")
def list_models():
    """Return the list of models available on the gateway."""
    url = f"{GATEWAY_BASE_URL}/v1/models"
    try:
        resp = requests.get(url, headers=_gateway_headers(), verify=False, timeout=30)
        resp.raise_for_status()
        return JSONResponse(content=resp.json())
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Gateway error: {e}")


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """
    Forward a chat completion request to the gateway and return the response.
    Supports both streaming and non-streaming modes.
    """
    body = await request.json()
    url = f"{GATEWAY_BASE_URL}/v1/chat/completions"
    headers = _gateway_headers()
    stream = body.get("stream", False)

    try:
        if stream:
            def _stream_generator():
                with requests.post(
                    url, headers=headers, json=body, stream=True, verify=False, timeout=120
                ) as resp:
                    resp.raise_for_status()
                    for line in resp.iter_lines():
                        if line:
                            yield line.decode("utf-8") + "\n\n"

            return StreamingResponse(_stream_generator(), media_type="text/event-stream")

        resp = requests.post(url, headers=headers, json=body, verify=False, timeout=120)
        resp.raise_for_status()
        return JSONResponse(content=resp.json())

    except requests.exceptions.HTTPError as e:
        raise HTTPException(
            status_code=e.response.status_code if e.response is not None else 502,
            detail=e.response.text if e.response is not None else str(e),
        )
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Gateway error: {e}")


@app.get("/health")
def health():
    return {"status": "ok", "gateway": GATEWAY_BASE_URL}


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PROXY_PORT", 8000))
    print(f"Starting SFR LLM Gateway proxy on http://localhost:{port}/v1")
    print(f"  Forwarding to: {GATEWAY_BASE_URL}")
    uvicorn.run(app, host="0.0.0.0", port=port)
