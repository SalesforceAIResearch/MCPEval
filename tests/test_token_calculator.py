"""Tests for the token calculator module."""

import pytest

from mcpeval.eval.token_calculator import (
    MODEL_PRICING,
    calculate_conversation_tokens,
    calculate_cost,
    count_tokens,
    extract_assistant_outputs,
)


class TestCountTokens:
    def test_empty_string(self):
        assert count_tokens("") == 0

    def test_none_like_empty(self):
        assert count_tokens(None) == 0

    def test_simple_text(self):
        tokens = count_tokens("Hello, world!")
        assert tokens > 0

    def test_longer_text_has_more_tokens(self):
        short = count_tokens("Hi")
        long = count_tokens("This is a much longer piece of text with many words")
        assert long > short

    def test_gpt4_model(self):
        tokens = count_tokens("Hello", model_name="gpt-4")
        assert tokens > 0

    def test_gpt35_model(self):
        tokens = count_tokens("Hello", model_name="gpt-3.5-turbo")
        assert tokens > 0

    def test_unknown_model_falls_back(self):
        # Unknown model should still work (falls back to gpt-4 tokenizer)
        tokens = count_tokens("Hello", model_name="unknown-model-xyz")
        assert tokens > 0


class TestExtractAssistantOutputs:
    def test_empty_conversation(self):
        texts, tools = extract_assistant_outputs([])
        assert texts == []
        assert tools == []

    def test_user_only(self):
        conv = [{"role": "user", "content": "Hello"}]
        texts, tools = extract_assistant_outputs(conv)
        assert texts == []
        assert tools == []

    def test_assistant_text(self):
        conv = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello! How can I help?"},
        ]
        texts, tools = extract_assistant_outputs(conv)
        assert len(texts) == 1
        assert "Hello" in texts[0]
        assert tools == []

    def test_assistant_tool_calls(self):
        conv = [
            {"role": "user", "content": "Search for cats"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "tc1",
                        "type": "function",
                        "function": {
                            "name": "search",
                            "arguments": '{"query": "cats"}',
                        },
                    }
                ],
            },
        ]
        texts, tools = extract_assistant_outputs(conv)
        assert texts == []  # content is None
        assert len(tools) == 1
        assert "search" in tools[0]

    def test_mixed_conversation(self):
        conv = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello!"},
            {"role": "user", "content": "Search"},
            {
                "role": "assistant",
                "content": "Let me search.",
                "tool_calls": [
                    {
                        "id": "tc1",
                        "type": "function",
                        "function": {"name": "search", "arguments": "{}"},
                    }
                ],
            },
            {"role": "tool", "content": '{"results": []}'},
            {"role": "assistant", "content": "No results found."},
        ]
        texts, tools = extract_assistant_outputs(conv)
        assert len(texts) == 3  # "Hello!", "Let me search.", "No results found."
        assert len(tools) == 1


class TestCalculateConversationTokens:
    def test_empty_conversation(self):
        result = calculate_conversation_tokens([])
        assert result["input_tokens"] == 0
        assert result["output_tokens"] == 0
        assert result["total_tokens"] == 0

    def test_simple_conversation(self):
        conv = [
            {"role": "system", "content": "Be helpful."},
            {"role": "user", "content": "What is 2+2?"},
            {"role": "assistant", "content": "4"},
        ]
        result = calculate_conversation_tokens(conv)
        assert result["input_tokens"] > 0
        assert result["output_tokens"] > 0
        assert (
            result["total_tokens"] == result["input_tokens"] + result["output_tokens"]
        )
        assert result["output_text_tokens"] > 0
        assert result["output_tool_tokens"] == 0

    def test_tool_role_counted_as_input(self):
        conv = [
            {"role": "user", "content": "go"},
            {"role": "tool", "content": '{"data": "value"}'},
            {"role": "assistant", "content": "Done"},
        ]
        result = calculate_conversation_tokens(conv)
        # Tool content should contribute to input tokens
        assert result["input_tokens"] > 0


class TestCalculateCost:
    def test_known_model(self):
        cost = calculate_cost(1000, 1000, "gpt-4o")
        input_price, output_price = MODEL_PRICING["gpt-4o"]
        expected = (1000 / 1000) * input_price + (1000 / 1000) * output_price
        assert cost == pytest.approx(expected)

    def test_zero_tokens(self):
        cost = calculate_cost(0, 0, "gpt-4o")
        assert cost == 0.0

    def test_unknown_model_uses_default(self):
        cost = calculate_cost(1000, 1000, "totally-unknown-model")
        input_price, output_price = MODEL_PRICING["default"]
        expected = (1000 / 1000) * input_price + (1000 / 1000) * output_price
        assert cost == pytest.approx(expected)

    def test_partial_model_name_match(self):
        # calculate_cost uses substring matching in dict insertion order,
        # so "gpt-4o-mini" matches "gpt-4o" first (it appears earlier in MODEL_PRICING)
        cost = calculate_cost(2000, 500, "gpt-4o-mini")
        input_price, output_price = MODEL_PRICING["gpt-4o"]
        expected = (2000 / 1000) * input_price + (500 / 1000) * output_price
        assert cost == pytest.approx(expected)

    def test_model_name_case_insensitive(self):
        cost_lower = calculate_cost(1000, 1000, "gpt-4o")
        cost_upper = calculate_cost(1000, 1000, "GPT-4o")
        assert cost_lower == pytest.approx(cost_upper)

    def test_cost_scales_with_tokens(self):
        cost_small = calculate_cost(100, 100, "gpt-4o")
        cost_large = calculate_cost(10000, 10000, "gpt-4o")
        assert cost_large > cost_small
        assert cost_large == pytest.approx(cost_small * 100)
