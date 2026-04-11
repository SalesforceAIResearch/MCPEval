"""Shared test fixtures for MCPEval."""

import pytest

from mcpeval.commons.types import ToolCall


@pytest.fixture
def sample_tool_calls():
    """Create sample tool calls for testing."""
    return [
        ToolCall(
            tool_name="get_employee",
            tool_parameters={"employee_id": "EMP001"},
        ),
        ToolCall(
            tool_name="get_department",
            tool_parameters={"department_name": "Engineering"},
        ),
    ]


@pytest.fixture
def sample_prediction_calls():
    """Create sample prediction tool calls that partially match."""
    return [
        ToolCall(
            tool_name="get_employee",
            tool_parameters={"employee_id": "EMP001"},
        ),
        ToolCall(
            tool_name="get_department",
            tool_parameters={"department_name": "engineering"},  # lowercase
        ),
    ]
