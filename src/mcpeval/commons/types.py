import uuid
from typing import Any, Dict, List, Optional, Tuple, Union

from mcp.types import Tool as ToolDefinition
from pydantic import BaseModel, ConfigDict, Field


# Add the method to convert ToolDefinition to OpenAI function schema
def _to_openai_function_schema(self) -> Dict[str, Any]:
    """Convert tool to openai function schema format."""
    return {
        "type": "function",
        "function": {
            "name": self.name,
            "description": self.description or "",
            "parameters": self.inputSchema,
        },
    }


# Monkey patch the ToolDefinition class
ToolDefinition.to_openai_function_schema = _to_openai_function_schema


# Simple message format with support for system, user, assistant, and tool messages
class Message(BaseModel):
    """Message model for conversation history."""

    model_config = ConfigDict(extra="allow")

    role: str
    content: Optional[str] = None  # Can be None for tool call messages
    tool_call_id: Optional[str] = None  # Only required for tool messages
    tool_calls: Optional[List[Dict[str, Any]]] = (
        None  # For assistant messages with tool calls
    )
    name: Optional[str] = None  # Added for the new message format


class Tool(BaseModel):
    type: str
    function: Dict[str, Any]


class ToolCall(BaseModel):
    tool_name: str
    tool_parameters: Dict[str, Any]


class OneStepChatBasedSample(BaseModel):
    messages: List[Message]
    reference: Optional[str] = None
    criteria: Optional[Dict[str, Any]] = None


class OneStepToolBasedSample(BaseModel):
    messages: List[Message]
    tools: List[Tool]
    reference: Optional[str] = None
    reference_tool_calls: Optional[List[ToolCall]] = None
    criteria: Optional[Dict[str, Any]] = None


class ToolParameter(BaseModel):
    """Definition of a tool parameter for creating tool schemas."""

    name: str = Field(..., description="Name of the parameter")
    type: str = Field(..., description="Type of the parameter (string, integer, etc.)")
    description: str = Field(..., description="Description of the parameter")
    required: bool = Field(True, description="Whether the parameter is required")
    enum: Optional[List[Any]] = Field(
        None, description="List of allowed values for the parameter"
    )
    default: Optional[Any] = Field(None, description="Default value for the parameter")


class ToolCallResult(BaseModel):
    """Result of a tool call."""

    content: str = Field(..., description="Text content returned by the tool")
    is_error: bool = Field(False, description="Whether this result represents an error")


class ToolLibrary(BaseModel):
    """Collection of tool definitions."""

    tools: List[ToolDefinition] = Field(default_factory=list)

    def add_tool(self, tool: ToolDefinition) -> None:
        """Add a tool to the library."""
        self.tools.append(tool)

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Get a tool by name."""
        for tool in self.tools:
            if tool.name == name:
                return tool
        return None

    def to_openai_function_schema(self) -> List[Dict[str, Any]]:
        """Convert all tools to openai function schema format."""
        return [tool.to_openai_function_schema() for tool in self.tools]


def format_tools_for_prompt(tools: List[ToolDefinition]) -> str:
    """Format tools for inclusion in a prompt."""
    tool_descriptions = []

    for tool in tools:
        tool_str = f"Tool: {tool.name}\nDescription: {tool.description}\nParameters: {tool.inputSchema}"
        tool_descriptions.append(tool_str)

    return "\n\n".join(tool_descriptions)


class Persona(BaseModel):
    """A user persona for the user simulator."""

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for the persona",
    )
    name: str = Field(..., description="Persona name, e.g. 'Busy Project Manager'")
    description: str = Field(..., description="Persona background and traits")
    communication_style: Optional[str] = Field(
        None, description="How this persona communicates (e.g. terse, verbose, simple)"
    )
    expertise_level: Optional[str] = Field(
        None, description="novice/intermediate/expert"
    )


class TurnResult(BaseModel):
    """Result of a single conversation turn in a multi-turn interaction."""

    model_config = ConfigDict(extra="allow")

    turn_number: int = Field(..., description="1-indexed turn number")
    user_message: Dict[str, Any] = Field(
        ..., description="The user message for this turn"
    )
    agent_messages: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="All agent messages in this turn, including tool calls and responses",
    )
    tool_calls_in_turn: List[ToolCall] = Field(default_factory=list)
    agent_final_response: Optional[str] = None


class MultiTurnScenario(BaseModel):
    """A multi-turn conversation scenario for evaluation."""

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for the scenario",
    )
    name: str = Field(..., description="Scenario name")
    description: str = Field(..., description="Detailed scenario description")
    goal: str = Field(
        ..., description="What the user wants to accomplish across multiple turns"
    )
    persona: Optional[Persona] = Field(
        None, description="User persona for the simulator"
    )
    tools: Optional[List[ToolDefinition]] = Field(
        None, description="List of tools available in this scenario"
    )
    scenario_type: str = Field(
        default="standard",
        description="standard/missing_params/missing_functions/composite",
    )
    max_turns: int = Field(
        default=5, description="Maximum number of conversation turns"
    )
    initial_context: Optional[str] = Field(
        None, description="Additional context hint for the user simulator"
    )
    # Populated after execution:
    turns: Optional[List[TurnResult]] = None
    full_conversation: Optional[List[Dict[str, Any]]] = None

    class Config:
        arbitrary_types_allowed = True


class Task(BaseModel):
    """A task definition for an LLM to complete."""

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for the task",
    )
    name: str = Field(..., description="Name of the task")
    description: str = Field(..., description="Description of the task")
    goal: str = Field(..., description="Goal of the task")
    tools: Optional[List[ToolDefinition]] = Field(
        None, description="List of tools available for the task"
    )
    tool_calls: Optional[List[ToolCall]] = Field(
        None, description="Expected tool calls for this task"
    )
    final_response: Optional[str] = Field(
        None, description="Final response for the task"
    )
    conversation: Optional[List[Message]] = Field(
        None, description="Conversation history for the task"
    )
    tool_call_results: Optional[
        List[
            Union[Tuple[ToolCall, Optional[ToolCallResult]], Tuple[ToolCall, Any], Any]
        ]
    ] = Field(None, description="Results of the tool calls")

    class Config:
        arbitrary_types_allowed = True
