from typing import Dict, List, Any, Optional, Union, Tuple
import logging
from ..commons.types import ToolCall, Task, ToolDefinition
from ..commons.prompts import task_executor_system_prompt

logger = logging.getLogger(__name__)

class LLMTaskExecutor:
    """
    Executor that uses an LLM to execute tasks by calling tools.
    """
    def __init__(self, llm: Any):
        self.llm = llm

    def _convert_tools_to_openai_format(self, tools: List[ToolDefinition]) -> List[Dict[str, Any]]:
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
                logger.error(f"Error formatting tool {getattr(tool, 'name', 'unknown')}: {e}")
        
        return formatted_tools

    async def execute_task(
        self,
        task: Task,
        tools: Optional[List[ToolDefinition]] = None,
        tool_name_to_session: Dict[str, Any] = None,  # tool_name -> MCPClientStdio or compatible
        messages: Optional[List[Dict[str, Any]]] = None,
        system_message: Optional[str] = None,
        max_turns: int = 30,  # Maximum number of conversation turns
        **llm_kwargs
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Use the LLM to generate tool calls for the given task in a multi-turn conversation.
        For each tool call, identify the correct MCP session using tool_name_to_session.
        Executes the tool calls and continues the conversation until completion or max_turns.
        
        Args:
            task: The task definition
            tools: Optional list of tools to use (defaults to task.tools)
            tool_name_to_session: Mapping from tool name to session for executing the tool
            messages: Optional starting chat messages
            system_message: Optional custom system message (defaults to standard task completion prompt)
            max_turns: Maximum number of conversation turns
            **llm_kwargs: Additional kwargs for LLM
            
        Returns:
            Tuple of (success, result) where:
            - result is always a dict with tool_calls, final_response, and conversation
            - success is True if the task was completed, False otherwise
        """
        # Ensure tool_name_to_session is initialized
        if tool_name_to_session is None:
            tool_name_to_session = {}
            
        # Use task's tools if not provided
        if tools is None and task.tools:
            tools = task.tools
            
        # Prepare messages
        if messages is None:
            # Use custom system message if provided, otherwise use default
            if system_message is None:
                system_message = task_executor_system_prompt
            
            tool_descriptions = "\n".join([f"- {tool.name}: {getattr(tool, 'description', '')}" for tool in tools]) if tools else ""
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"Please complete the following task: {task.name}. {task.description}."}
            ]
            
        # Convert tools to OpenAI format
        openai_tools = []
        if tools:
            openai_tools = self._convert_tools_to_openai_format(tools)

        # Keep track of all tool calls across all turns
        all_tool_calls = []
        tool_call_results = []
        
        # Process the conversation in turns
        for turn in range(max_turns):
            logger.debug(f"Turn {turn+1}/{max_turns}")
            logger.debug(f"Tools available: {[t['function']['name'] for t in openai_tools if 'function' in t]}")
            
            # Call the LLM to get response
            response = self.llm.chat_completion(messages=messages, tools=openai_tools, **llm_kwargs)
            assistant_message = response["choices"][0]["message"]
            
            logger.debug(f"Assistant response: {assistant_message.get('content')}")
            if assistant_message.get("tool_calls"):
                # Check the type of tool_calls to determine how to log them
                tool_calls = assistant_message.get("tool_calls", [])
                if tool_calls and hasattr(tool_calls[0], "function") and hasattr(tool_calls[0].function, "name"):
                    # For Pydantic model or object-style tool calls
                    logger.debug(f"Tool calls: {[tc.function.name for tc in tool_calls]}")
                elif tool_calls and isinstance(tool_calls[0], dict) and "function" in tool_calls[0]:
                    # For dictionary-style tool calls
                    logger.debug(f"Tool calls: {[tc['function']['name'] for tc in tool_calls]}")
                else:
                    # Just log that tool calls exist without trying to access their structure
                    logger.debug(f"Tool calls present but in unknown format: {type(tool_calls[0]).__name__ if tool_calls else 'none'}")
            
            # Add the assistant message to conversation history
            messages.append({
                "role": "assistant",
                "content": assistant_message.get("content"),
                "tool_calls": assistant_message.get("tool_calls", [])
            })
            
            # Check if the response contains tool calls
            tool_calls = assistant_message.get("tool_calls", [])
            
            # If no tool calls, we're done
            if not tool_calls:
                return True, {
                    "tool_calls": all_tool_calls,
                    "tool_call_results": tool_call_results,
                    "final_response": assistant_message.get("content", ""),
                    "conversation": messages
                }
            
            # Process all tool calls in this turn
            for tool_call in tool_calls:
                # Check if tool_call is a dictionary or an object with attributes
                if isinstance(tool_call, dict) and tool_call.get("type") == "function":
                    tool_name = tool_call["function"]["name"]
                    arguments = tool_call["function"].get("arguments", "{}")
                elif hasattr(tool_call, "type") and tool_call.type == "function" and hasattr(tool_call, "function"):
                    tool_name = tool_call.function.name
                    arguments = getattr(tool_call.function, "arguments", "{}")
                else:
                    logger.warning(f"Unsupported tool call format: {type(tool_call).__name__}")
                    continue
                
                # Parse arguments (might be a JSON string)
                import json
                try:
                    tool_parameters = json.loads(arguments) if isinstance(arguments, str) else arguments
                except Exception:
                    tool_parameters = {}
                
                # Get the appropriate session for this tool
                session = tool_name_to_session.get(tool_name)
                
                # Create ToolCall object and add to our list
                tool_call_obj = ToolCall(tool_name=tool_name, tool_parameters=tool_parameters)
                all_tool_calls.append(tool_call_obj)
                
                # Execute the tool call if session is available
                if session:
                    try:
                        result = await session.call_tool(tool_name, tool_parameters)
                        # Handle content properly, accessing it via content[0].text if it has that structure
                        if hasattr(result, 'content') and isinstance(result.content, list) and len(result.content) > 0 and hasattr(result.content[0], 'text'):
                            content = result.content[0].text
                        elif hasattr(result, 'content'):
                            content = result.content
                        else:
                            content = str(result)
                        
                        tool_call_results.append((tool_call_obj, content))
                        
                        # Get tool_call_id for the response
                        tool_call_id = ""
                        if isinstance(tool_call, dict) and "id" in tool_call:
                            tool_call_id = tool_call["id"]
                        elif hasattr(tool_call, "id"):
                            tool_call_id = tool_call.id
                            
                        # Add tool result to conversation history
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "name": tool_name,
                            "content": content
                        })
                    except Exception as e:
                        # Handle error in tool execution
                        error_message = f"Error executing tool {tool_name}: {str(e)}"
                        
                        # Get tool_call_id for the response
                        tool_call_id = ""
                        if isinstance(tool_call, dict) and "id" in tool_call:
                            tool_call_id = tool_call["id"]
                        elif hasattr(tool_call, "id"):
                            tool_call_id = tool_call.id
                            
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "name": tool_name,
                            "content": error_message
                        })
        
        # If we reach max turns without completion, return what we have
        return False, {
            "tool_calls": all_tool_calls,
            "tool_call_results": tool_call_results,
            "final_response": messages[-1].get("content", ""),
            "conversation": messages
        }
