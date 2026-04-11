"""
Unified JSON parsing for LLM responses.

Consolidates the various ad-hoc JSON extraction strategies used across the codebase
into a single, reliable utility with clear error reporting.
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional, Type, TypeVar

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMJsonParseError(Exception):
    """Raised when JSON cannot be extracted from an LLM response."""

    def __init__(self, message: str, raw_response: str):
        self.raw_response = raw_response
        super().__init__(message)


def parse_llm_json(
    raw_response: str,
    pydantic_model: Optional[Type[T]] = None,
    required_fields: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Parse JSON from an LLM response string.

    Tries multiple extraction strategies in order:
    1. Direct json.loads
    2. Extract from markdown code blocks (```json ... ```)
    3. Find first complete JSON object via brace matching
    4. Clean common issues (trailing commas, comments, single quotes)

    Args:
        raw_response: Raw LLM response text.
        pydantic_model: Optional Pydantic model class for validation.
        required_fields: Optional list of field names that must be present.

    Returns:
        Parsed JSON as a dictionary.

    Raises:
        LLMJsonParseError: If no valid JSON can be extracted.
    """
    text = raw_response.strip()
    if not text:
        raise LLMJsonParseError("Empty response", raw_response)

    # Strategy 1: Direct parse
    result = _try_direct_parse(text)
    if result is not None:
        return _validate(result, pydantic_model, required_fields, raw_response)

    # Strategy 2: Extract from markdown code blocks
    result = _try_markdown_extract(text)
    if result is not None:
        return _validate(result, pydantic_model, required_fields, raw_response)

    # Strategy 3: Brace matching — find first complete JSON object
    result = _try_brace_match(text)
    if result is not None:
        return _validate(result, pydantic_model, required_fields, raw_response)

    # Strategy 4: Clean common issues and retry
    result = _try_cleaned_parse(text)
    if result is not None:
        return _validate(result, pydantic_model, required_fields, raw_response)

    raise LLMJsonParseError(
        f"Could not extract valid JSON from LLM response (length={len(text)}): {text[:300]}...",
        raw_response,
    )


def parse_llm_json_model(raw_response: str, model_class: Type[T]) -> T:
    """Parse JSON from an LLM response and return a validated Pydantic model instance.

    Args:
        raw_response: Raw LLM response text.
        model_class: Pydantic model class to validate and instantiate.

    Returns:
        Validated Pydantic model instance.

    Raises:
        LLMJsonParseError: If JSON extraction or validation fails.
    """
    data = parse_llm_json(raw_response)
    try:
        return model_class(**data)
    except ValidationError as e:
        raise LLMJsonParseError(
            f"JSON parsed but failed {model_class.__name__} validation: {e}",
            raw_response,
        )


# --- Internal strategies ---


def _try_direct_parse(text: str) -> Optional[Dict[str, Any]]:
    """Try parsing the text directly as JSON."""
    try:
        result = json.loads(text)
        if isinstance(result, dict):
            return result
        if isinstance(result, list) and result and isinstance(result[0], dict):
            return result[0]
    except json.JSONDecodeError:
        pass
    return None


def _try_markdown_extract(text: str) -> Optional[Dict[str, Any]]:
    """Extract JSON from markdown code blocks."""
    patterns = [
        r"```json\s*\n?([\s\S]*?)\n?\s*```",
        r"```\s*\n?([\s\S]*?)\n?\s*```",
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            try:
                result = json.loads(match.strip())
                if isinstance(result, dict):
                    return result
            except json.JSONDecodeError:
                continue
    return None


def _try_brace_match(text: str) -> Optional[Dict[str, Any]]:
    """Find the first complete JSON object by matching braces."""
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    in_string = False
    escape_next = False
    for i in range(start, len(text)):
        c = text[i]
        if escape_next:
            escape_next = False
            continue
        if c == "\\":
            escape_next = True
            continue
        if c == '"' and not escape_next:
            in_string = not in_string
            continue
        if in_string:
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                candidate = text[start : i + 1]
                try:
                    result = json.loads(candidate)
                    if isinstance(result, dict):
                        return result
                except json.JSONDecodeError:
                    break
    return None


def _try_cleaned_parse(text: str) -> Optional[Dict[str, Any]]:
    """Apply common cleanups and retry parsing."""
    # Remove single-line comments
    cleaned = re.sub(r"//.*?$", "", text, flags=re.MULTILINE)
    # Remove block comments
    cleaned = re.sub(r"/\*[\s\S]*?\*/", "", cleaned)
    # Remove trailing commas before } or ]
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)

    result = _try_direct_parse(cleaned)
    if result is not None:
        return result

    result = _try_brace_match(cleaned)
    if result is not None:
        return result

    # Try fixing single quotes -> double quotes (apply to already-cleaned text)
    quote_fixed = re.sub(r"'([^']*)':", r'"\1":', cleaned)
    quote_fixed = re.sub(r":\s*'([^']*)'", r': "\1"', quote_fixed)
    return _try_brace_match(quote_fixed)


def _validate(
    data: Dict[str, Any],
    pydantic_model: Optional[Type[T]],
    required_fields: Optional[List[str]],
    raw_response: str,
) -> Dict[str, Any]:
    """Validate parsed JSON against optional constraints."""
    if required_fields:
        missing = [f for f in required_fields if f not in data or not data[f]]
        if missing:
            raise LLMJsonParseError(
                f"Parsed JSON is missing required fields: {missing}",
                raw_response,
            )

    if pydantic_model:
        try:
            pydantic_model(**data)
        except ValidationError as e:
            raise LLMJsonParseError(
                f"JSON parsed but failed {pydantic_model.__name__} validation: {e}",
                raw_response,
            )

    return data
