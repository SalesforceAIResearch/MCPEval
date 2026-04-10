"""Tests for the unified LLM JSON parsing utility."""

import pytest

from pydantic import BaseModel

from mcpeval.utils.structured_output import (
    parse_llm_json,
    parse_llm_json_model,
    LLMJsonParseError,
)


# -- Pydantic model for validation tests --

class SampleModel(BaseModel):
    name: str
    value: int


# -- Direct parsing --

class TestDirectParse:
    def test_clean_json(self):
        result = parse_llm_json('{"key": "value", "num": 42}')
        assert result == {"key": "value", "num": 42}

    def test_json_with_whitespace(self):
        result = parse_llm_json('  \n  {"a": 1}  \n  ')
        assert result == {"a": 1}

    def test_list_returns_first_dict(self):
        result = parse_llm_json('[{"a": 1}, {"b": 2}]')
        assert result == {"a": 1}

    def test_empty_string_raises(self):
        with pytest.raises(LLMJsonParseError, match="Empty response"):
            parse_llm_json("")

    def test_whitespace_only_raises(self):
        with pytest.raises(LLMJsonParseError, match="Empty response"):
            parse_llm_json("   \n  ")

    def test_no_json_raises(self):
        with pytest.raises(LLMJsonParseError):
            parse_llm_json("This is just plain text with no JSON at all.")


# -- Markdown extraction --

class TestMarkdownExtract:
    def test_json_code_block(self):
        text = 'Here is the result:\n```json\n{"tool": "search", "query": "test"}\n```'
        result = parse_llm_json(text)
        assert result == {"tool": "search", "query": "test"}

    def test_plain_code_block(self):
        text = 'Result:\n```\n{"x": 99}\n```\nDone.'
        result = parse_llm_json(text)
        assert result == {"x": 99}

    def test_multiple_code_blocks_returns_first_valid(self):
        text = (
            "```json\nnot valid json\n```\n"
            "```json\n{\"good\": true}\n```"
        )
        result = parse_llm_json(text)
        assert result == {"good": True}


# -- Brace matching --

class TestBraceMatch:
    def test_json_embedded_in_text(self):
        text = 'The answer is: {"result": "success"} and that is all.'
        result = parse_llm_json(text)
        assert result == {"result": "success"}

    def test_nested_braces(self):
        text = 'Output: {"outer": {"inner": 1}}'
        result = parse_llm_json(text)
        assert result == {"outer": {"inner": 1}}

    def test_strings_with_braces(self):
        text = '{"msg": "open { and close }"}'
        result = parse_llm_json(text)
        assert result == {"msg": "open { and close }"}

    def test_escaped_quotes(self):
        text = r'{"msg": "she said \"hello\""}'
        result = parse_llm_json(text)
        assert result["msg"] == 'she said "hello"'


# -- Cleaned parse (trailing commas, comments, single quotes) --

class TestCleanedParse:
    def test_trailing_comma(self):
        text = '{"a": 1, "b": 2,}'
        result = parse_llm_json(text)
        assert result == {"a": 1, "b": 2}

    def test_single_line_comments(self):
        text = '{\n  "a": 1, // this is a comment\n  "b": 2\n}'
        result = parse_llm_json(text)
        assert result == {"a": 1, "b": 2}

    def test_single_quotes_to_double(self):
        text = "{'name': 'test', 'value': 'hello'}"
        result = parse_llm_json(text)
        assert result["name"] == "test"
        assert result["value"] == "hello"


# -- Validation (required_fields and pydantic_model) --

class TestValidation:
    def test_required_fields_present(self):
        result = parse_llm_json(
            '{"name": "task", "goal": "do stuff"}',
            required_fields=["name", "goal"],
        )
        assert result["name"] == "task"

    def test_required_fields_missing_raises(self):
        with pytest.raises(LLMJsonParseError, match="missing required fields"):
            parse_llm_json(
                '{"name": "task"}',
                required_fields=["name", "goal"],
            )

    def test_required_fields_empty_value_raises(self):
        with pytest.raises(LLMJsonParseError, match="missing required fields"):
            parse_llm_json(
                '{"name": "", "goal": "ok"}',
                required_fields=["name", "goal"],
            )

    def test_pydantic_model_valid(self):
        result = parse_llm_json(
            '{"name": "x", "value": 42}',
            pydantic_model=SampleModel,
        )
        assert result == {"name": "x", "value": 42}

    def test_pydantic_model_invalid_raises(self):
        with pytest.raises(LLMJsonParseError, match="validation"):
            parse_llm_json(
                '{"name": "x", "value": "not_an_int"}',
                pydantic_model=SampleModel,
            )


# -- parse_llm_json_model --

class TestParseLLMJsonModel:
    def test_returns_model_instance(self):
        obj = parse_llm_json_model('{"name": "test", "value": 10}', SampleModel)
        assert isinstance(obj, SampleModel)
        assert obj.name == "test"
        assert obj.value == 10

    def test_invalid_model_raises(self):
        with pytest.raises(LLMJsonParseError, match="validation"):
            parse_llm_json_model('{"name": "test"}', SampleModel)


# -- LLMJsonParseError attributes --

class TestLLMJsonParseError:
    def test_stores_raw_response(self):
        try:
            parse_llm_json("not json")
        except LLMJsonParseError as e:
            assert e.raw_response == "not json"
