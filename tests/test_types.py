"""Tests for Pydantic model serialization roundtrips in mcpeval.commons.types."""

import json
import uuid

import pytest

from mcpeval.commons.types import (
    Message,
    ToolCall,
    ToolParameter,
    ToolCallResult,
    Persona,
    TurnResult,
    MultiTurnScenario,
    Task,
)


class TestToolCall:
    def test_roundtrip(self):
        tc = ToolCall(tool_name="get_user", tool_parameters={"id": "U1"})
        data = tc.model_dump()
        restored = ToolCall(**data)
        assert restored.tool_name == "get_user"
        assert restored.tool_parameters == {"id": "U1"}

    def test_json_roundtrip(self):
        tc = ToolCall(tool_name="search", tool_parameters={"q": "hello", "limit": 10})
        json_str = tc.model_dump_json()
        restored = ToolCall.model_validate_json(json_str)
        assert restored == tc

    def test_empty_parameters(self):
        tc = ToolCall(tool_name="list_all", tool_parameters={})
        assert tc.tool_parameters == {}

    def test_nested_parameters(self):
        params = {"filter": {"status": "active", "tags": ["a", "b"]}}
        tc = ToolCall(tool_name="query", tool_parameters=params)
        assert tc.tool_parameters["filter"]["tags"] == ["a", "b"]


class TestMessage:
    def test_basic_user_message(self):
        msg = Message(role="user", content="Hello")
        data = msg.model_dump()
        assert data["role"] == "user"
        assert data["content"] == "Hello"

    def test_assistant_message_with_tool_calls(self):
        msg = Message(
            role="assistant",
            content=None,
            tool_calls=[{"id": "tc1", "type": "function", "function": {"name": "f"}}],
        )
        restored = Message(**msg.model_dump())
        assert restored.content is None
        assert len(restored.tool_calls) == 1

    def test_tool_message(self):
        msg = Message(role="tool", content='{"result": "ok"}', tool_call_id="tc1")
        assert msg.tool_call_id == "tc1"

    def test_extra_fields_allowed(self):
        msg = Message(role="user", content="hi", custom_field="extra")
        data = msg.model_dump()
        assert data["custom_field"] == "extra"


class TestToolParameter:
    def test_required_fields(self):
        tp = ToolParameter(
            name="query", type="string", description="Search query"
        )
        assert tp.required is True
        assert tp.enum is None

    def test_with_enum(self):
        tp = ToolParameter(
            name="status",
            type="string",
            description="Status filter",
            enum=["active", "inactive"],
            required=False,
        )
        assert tp.enum == ["active", "inactive"]
        assert tp.required is False

    def test_roundtrip(self):
        tp = ToolParameter(
            name="limit", type="integer", description="Max results", default=10
        )
        restored = ToolParameter(**tp.model_dump())
        assert restored.default == 10


class TestToolCallResult:
    def test_success(self):
        r = ToolCallResult(content='{"status": "ok"}')
        assert r.is_error is False

    def test_error(self):
        r = ToolCallResult(content="Not found", is_error=True)
        assert r.is_error is True

    def test_roundtrip(self):
        r = ToolCallResult(content="data", is_error=False)
        restored = ToolCallResult(**r.model_dump())
        assert restored == r


class TestPersona:
    def test_auto_id(self):
        p = Persona(name="Manager", description="Busy project manager")
        assert p.id  # UUID should be auto-generated
        uuid.UUID(p.id)  # Should be a valid UUID

    def test_full_persona(self):
        p = Persona(
            name="Developer",
            description="Senior engineer",
            communication_style="terse",
            expertise_level="expert",
        )
        data = p.model_dump()
        restored = Persona(**data)
        assert restored.communication_style == "terse"

    def test_json_roundtrip(self):
        p = Persona(name="User", description="Regular user")
        json_str = p.model_dump_json()
        restored = Persona.model_validate_json(json_str)
        assert restored.name == p.name


class TestTurnResult:
    def test_basic_turn(self):
        turn = TurnResult(
            turn_number=1,
            user_message={"role": "user", "content": "Hi"},
            agent_messages=[{"role": "assistant", "content": "Hello!"}],
        )
        assert turn.turn_number == 1
        assert turn.tool_calls_in_turn == []

    def test_with_tool_calls(self):
        tc = ToolCall(tool_name="search", tool_parameters={"q": "test"})
        turn = TurnResult(
            turn_number=2,
            user_message={"role": "user", "content": "Search for test"},
            agent_messages=[],
            tool_calls_in_turn=[tc],
            agent_final_response="Found results.",
        )
        assert len(turn.tool_calls_in_turn) == 1
        assert turn.agent_final_response == "Found results."

    def test_roundtrip(self):
        turn = TurnResult(
            turn_number=1,
            user_message={"role": "user", "content": "Go"},
            agent_messages=[{"role": "assistant", "content": "Done"}],
        )
        data = turn.model_dump()
        restored = TurnResult(**data)
        assert restored.turn_number == turn.turn_number


class TestMultiTurnScenario:
    def test_minimal(self):
        s = MultiTurnScenario(
            name="Test scenario",
            description="A test",
            goal="Complete the task",
        )
        assert s.scenario_type == "standard"
        assert s.max_turns == 5
        assert s.turns is None

    def test_with_persona(self):
        persona = Persona(name="PM", description="Project manager")
        s = MultiTurnScenario(
            name="PM scenario",
            description="PM asks questions",
            goal="Get project status",
            persona=persona,
        )
        data = s.model_dump()
        restored = MultiTurnScenario(**data)
        assert restored.persona.name == "PM"

    def test_json_roundtrip(self):
        s = MultiTurnScenario(
            name="S1",
            description="desc",
            goal="goal",
            scenario_type="missing_params",
            max_turns=3,
        )
        json_str = s.model_dump_json()
        restored = MultiTurnScenario.model_validate_json(json_str)
        assert restored.scenario_type == "missing_params"
        assert restored.max_turns == 3


class TestTask:
    def test_minimal(self):
        t = Task(name="Test", description="A test task", goal="Do something")
        assert t.id  # auto-generated
        assert t.tools is None
        assert t.tool_calls is None

    def test_with_tool_calls(self):
        tcs = [
            ToolCall(tool_name="get_user", tool_parameters={"id": "1"}),
            ToolCall(tool_name="get_dept", tool_parameters={"name": "Eng"}),
        ]
        t = Task(
            name="Lookup",
            description="Look up user and dept",
            goal="Get info",
            tool_calls=tcs,
        )
        assert len(t.tool_calls) == 2

    def test_json_roundtrip(self):
        t = Task(
            id="task-001",
            name="Task One",
            description="First task",
            goal="Goal one",
            final_response="All done",
        )
        json_str = t.model_dump_json()
        restored = Task.model_validate_json(json_str)
        assert restored.id == "task-001"
        assert restored.final_response == "All done"

    def test_dict_roundtrip(self):
        t = Task(name="T", description="D", goal="G")
        data = t.model_dump()
        restored = Task(**data)
        assert restored.name == t.name
        assert restored.id == t.id
