#!/usr/bin/env python3
"""
Test script for Salesforce Research LLM Gateway
Endpoint: https://gateway.salesforceresearch.ai/openai/process/v1/chat/completions
Auth: X-Api-Key header
"""

import os
import json
import requests
from typing import Optional, Iterator, Dict, Any


class SFRGatewayClient:
    """Client for the Salesforce Research LLM Gateway"""

    def __init__(self, api_key: Optional[str] = None, verify_ssl: bool = True):
        self.api_key = api_key or os.environ.get("X_API_KEY")
        if not self.api_key:
            raise ValueError("API key must be provided or set in X_API_KEY environment variable")

        self.base_url = os.environ.get(
            "SFR_GATEWAY_BASE_URL",
            "https://gateway.salesforceresearch.ai/openai/process",
        ).rstrip("/")
        self.headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json",
        }
        self.verify_ssl = verify_ssl

    def list_models(self) -> list:
        url = f"{self.base_url}/v1/models"
        response = requests.get(url, headers=self.headers, verify=self.verify_ssl)
        response.raise_for_status()
        data = response.json()
        return [model["id"] for model in data.get("data", [])]

    def chat_completion(
        self,
        messages: list,
        model: str = "gpt-4o-mini",
        stream: bool = False,
        **kwargs,
    ) -> Dict[str, Any] | Iterator[str]:
        url = f"{self.base_url}/v1/chat/completions"
        payload = {"model": model, "messages": messages, "stream": stream, **kwargs}

        if stream:
            return self._stream_completion(url, payload)

        response = requests.post(url, headers=self.headers, json=payload, verify=self.verify_ssl)
        response.raise_for_status()
        return response.json()

    def _stream_completion(self, url: str, payload: Dict[str, Any]) -> Iterator[str]:
        with requests.post(url, headers=self.headers, json=payload, stream=True, verify=self.verify_ssl) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                line = line.decode("utf-8")
                if not line.startswith("data: "):
                    continue
                data = line[6:]
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    if "choices" in chunk and chunk["choices"]:
                        content = chunk["choices"][0].get("delta", {}).get("content", "")
                        if content:
                            yield content
                except json.JSONDecodeError:
                    continue


def test_list_models():
    print("=" * 60)
    print("Testing: List Available Models")
    print("=" * 60)
    client = SFRGatewayClient()
    models = client.list_models()
    print(f"\nFound {len(models)} models:")
    for m in models:
        print(f"  - {m}")
    print()


def test_non_streaming():
    print("=" * 60)
    print("Testing: Non-Streaming Chat Completion (gpt-4o-mini)")
    print("=" * 60)
    client = SFRGatewayClient()
    messages = [{"role": "user", "content": "Hello from proxy! Reply in one sentence."}]
    response = client.chat_completion(messages, model="gpt-4o-mini", temperature=0.7)
    content = response["choices"][0]["message"]["content"]
    usage = response.get("usage", {})
    print(f"\nResponse: {content}")
    print(f"Tokens — prompt: {usage.get('prompt_tokens')}, completion: {usage.get('completion_tokens')}, total: {usage.get('total_tokens')}")
    print()


def test_streaming():
    print("=" * 60)
    print("Testing: Streaming Chat Completion (gpt-4o-mini)")
    print("=" * 60)
    client = SFRGatewayClient()
    messages = [{"role": "user", "content": "Write a haiku about Python programming."}]
    print("\nStreaming response:")
    print("-" * 40)
    for chunk in client.chat_completion(messages, model="gpt-4o-mini", stream=True):
        print(chunk, end="", flush=True)
    print()
    print("-" * 40)
    print()


def test_error_handling():
    print("=" * 60)
    print("Testing: Error Handling (Invalid Model)")
    print("=" * 60)
    client = SFRGatewayClient()
    try:
        client.chat_completion([{"role": "user", "content": "Hello"}], model="invalid-model-xyz")
        print("No error raised (unexpected)")
    except requests.exceptions.HTTPError as e:
        print(f"\nExpected error — Status: {e.response.status_code}, Body: {e.response.text}")
    print()


def main():
    print("\n")
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║    Salesforce Research LLM Gateway - Test Suite          ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print()

    api_key = os.environ.get("X_API_KEY")
    if not api_key:
        print("ERROR: X_API_KEY environment variable not set!")
        print("  export X_API_KEY=<your-api-key>")
        return

    print(f"API Key: {'*' * 8} (set, length={len(api_key)})")
    print(f"Gateway: {os.environ.get('SFR_GATEWAY_BASE_URL', 'https://gateway.salesforceresearch.ai/openai/process')}")
    print()

    try:
        test_non_streaming()
        test_streaming()
        test_error_handling()
        print("=" * 60)
        print("✓ All tests completed!")
        print("=" * 60)
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"Status: {e.response.status_code}, Body: {e.response.text}")


if __name__ == "__main__":
    main()
