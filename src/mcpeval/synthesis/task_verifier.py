from typing import Dict, List, Any, Optional, Union, Tuple
import logging
from ..commons.types import ToolCall, Task, ToolDefinition, ToolCallResult
from .utils import extract_content_from_mcp_result
from ..commons.prompts import task_verification_system_prompt

logger = logging.getLogger(__name__)


class LLMTaskVerifier:
    """
    Verifier that uses an LLM to verify task completion.
    """

    def __init__(self, llm: Any):
        self.llm = llm

    @staticmethod
    def request_task_updating_tool() -> Dict[str, Any]:
        """
        Return a special tool call definition for requesting task clarification.
        """
        return {
            "type": "function",
            "function": {
                "name": "request_task_updating",
                "description": "Request that the task be updated with additional information or clarification",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reason": {
                            "type": "string",
                            "description": "Detailed explanation of why the task needs to be updated and what information is missing",
                        }
                    },
                    "required": ["reason"],
                },
            },
        }

    def get_request_task_clarification_response(self, reason: str) -> Dict[str, Any]:
        """
        Format the task clarification response in the expected structure.
        """
        return {
            "function": {
                "name": "request_task_updating",
                "parameters": {"reason": reason},
            }
        }

    def _convert_tools_to_openai_format(
        self, tools: List[ToolDefinition]
    ) -> List[Dict[str, Any]]:
        """
        Convert ToolDefinition objects to the format expected by OpenAI API.

        Note: ToolDefinition already has a to_openai_function_schema method added
        via monkey patching in tools.py.
        """
        formatted_tools = []
        for tool in tools:
            try:
                # The to_openai_function_schema method is already added to ToolDefinition in tools.py
                # It returns the tool formatted as an OpenAI function
                formatted_tool = tool.to_openai_function_schema()
                formatted_tools.append(formatted_tool)
                logger.debug(f"Converted tool: {tool.name}")
            except Exception as e:
                logger.error(
                    f"Error formatting tool {getattr(tool, 'name', 'unknown')}: {e}"
                )

        return formatted_tools

    async def task_verification(
        self,
        task: Task,
        tools: Optional[List[ToolDefinition]] = None,
        tool_name_to_session: Dict[
            str, Any
        ] = None,  # tool_name -> MCPClientStdio or compatible
        messages: Optional[List[Dict[str, Any]]] = None,
        system_message: Optional[str] = None,  # Flexible system message
        max_turns: int = 5,  # Maximum number of conversation turns
        **llm_kwargs,
    ) -> Tuple[bool, Union[str, Dict[str, Any]]]:
        """
        Use the LLM to generate tool calls for the given task.
        For each tool call, identify the correct MCP session using tool_name_to_session.
        Executes the tool calls and returns the final response.

        Args:
            task: The task definition
            tools: Optional list of tools to use (defaults to task.tools)
            tool_name_to_session: Mapping from tool name to session for executing the tool
            messages: Optional starting chat messages
            system_message: Optional custom system message (if None, uses default)
            max_turns: Maximum number of conversation turns
            **llm_kwargs: Additional kwargs for LLM

        Returns:
            Tuple of (success, result) where:
            - If success is False, result is a reason string for clarification
            - If success is True, result is a dict with tool_calls, final_response, and conversation
        """
        # Ensure tool_name_to_session is initialized
        if tool_name_to_session is None:
            tool_name_to_session = {}

        # Use task's tools if not provided
        if tools is None and task.tools:
            tools = task.tools

        # Prepare messages
        if messages is None:
            # Use flexible system message or default
            if system_message is None:
                system_message = task_verification_system_prompt

            # Include task information in the user prompt
            task_info = f"""Task: {task.name}
Description: {task.description}
Goal: {task.goal}"""

            user_prompt = f"""{task_info}"""

            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_prompt},
            ]

        # Convert tools to OpenAI format
        openai_tools = []
        if tools:
            openai_tools = self._convert_tools_to_openai_format(tools)

        # Add the special request_task_updating tool
        openai_tools.append(self.request_task_updating_tool())

        # Keep track of all tool calls across all turns
        all_tool_calls = []
        # Keep track of all tool call results across all turns
        all_tool_call_results = []

        # Process the conversation in turns
        for turn in range(max_turns):
            logger.debug(f"Turn {turn+1}/{max_turns}")
            logger.debug(
                f"Tools available: {[t['function']['name'] for t in openai_tools if 'function' in t]}"
            )

            # Call the LLM to get response
            response = self.llm.chat_completion(
                messages=messages, tools=openai_tools, **llm_kwargs
            )
            assistant_message = response["choices"][0]["message"]

            logger.debug(f"Assistant response: {assistant_message.get('content')}")
            if assistant_message.get("tool_calls"):
                logger.debug(
                    f"Tool calls: {[tc['function']['name'] for tc in assistant_message.get('tool_calls', [])]}"
                )

            # Add the assistant message to conversation history
            messages.append(
                {
                    "role": "assistant",
                    "content": assistant_message.get("content"),
                    "tool_calls": assistant_message.get("tool_calls", []),
                }
            )

            # Check if the response contains tool calls
            tool_calls = assistant_message.get("tool_calls", [])

            # If no tool calls, we're done
            if not tool_calls:
                return True, {
                    "tool_calls": all_tool_calls,
                    "tool_call_results": all_tool_call_results,
                    "final_response": assistant_message.get("content", ""),
                    "conversation": messages,
                }

            # Check for request_task_updating
            for tool_call in tool_calls:
                if (
                    tool_call["type"] == "function"
                    and tool_call["function"]["name"] == "request_task_updating"
                ):
                    try:
                        import json

                        arguments = tool_call["function"].get("arguments", "{}")
                        if isinstance(arguments, str):
                            arguments = json.loads(arguments)
                        reason = arguments.get("reason", "No specific reason provided.")
                    except Exception:
                        reason = "Parsing error in request_task_updating arguments."

                    return False, reason

            # Process all tool calls in this turn
            for tool_call in tool_calls:
                if tool_call["type"] == "function":
                    tool_name = tool_call["function"]["name"]

                    # Skip the request_task_updating tool as it was already checked
                    if tool_name == "request_task_updating":
                        continue

                    arguments = tool_call["function"].get("arguments", "{}")

                    # Parse arguments (might be a JSON string)
                    import json

                    try:
                        tool_parameters = (
                            json.loads(arguments)
                            if isinstance(arguments, str)
                            else arguments
                        )
                    except Exception:
                        tool_parameters = {}

                    # Get the appropriate session for this tool
                    session = tool_name_to_session.get(tool_name)

                    # Create ToolCall object and add to our list
                    tool_call_obj = ToolCall(
                        tool_name=tool_name, tool_parameters=tool_parameters
                    )
                    all_tool_calls.append(tool_call_obj)

                    # Execute the tool call if session is available
                    if session:
                        try:
                            result = await session.call_tool(tool_name, tool_parameters)
                            content = extract_content_from_mcp_result(result)
                            # Create a proper ToolCallResult object
                            tool_call_result = ToolCallResult(
                                content=content, is_error=False
                            )
                            all_tool_call_results.append(
                                (tool_call_obj, tool_call_result)
                            )
                            # Add tool result to conversation history
                            messages.append(
                                {
                                    "role": "tool",
                                    "tool_call_id": tool_call.get("id", ""),
                                    "name": tool_name,
                                    "content": content,
                                }
                            )
                        except Exception as e:
                            # Handle error in tool execution
                            error_message = (
                                f"Error executing tool {tool_name}: {str(e)}"
                            )
                            # Create a ToolCallResult object for errors
                            tool_call_result = ToolCallResult(
                                content=error_message, is_error=True
                            )
                            all_tool_call_results.append(
                                (tool_call_obj, tool_call_result)
                            )
                            messages.append(
                                {
                                    "role": "tool",
                                    "tool_call_id": tool_call.get("id", ""),
                                    "name": tool_name,
                                    "content": error_message,
                                }
                            )

        # If we reach max turns without completion, return what we have
        return True, {
            "tool_calls": all_tool_calls,
            "tool_call_results": all_tool_call_results,
            "final_response": messages[-1].get("content", ""),
            "conversation": messages,
        }
