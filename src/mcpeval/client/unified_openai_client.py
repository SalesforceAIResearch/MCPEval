"""
Unified OpenAI MCP client that supports both stdio and HTTP transports.
"""
import json
import logging
from typing import Any, Dict, List, Optional

from openai import OpenAI

from .unified_client import UnifiedMCPClient

logger = logging.getLogger(__name__)


class UnifiedOpenAIMCPClient(UnifiedMCPClient):
    """OpenAI client that works with both stdio and HTTP MCP servers."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "gpt-4o",
        temperature: float = 0.1,
        max_tokens: int = 4000,
        top_p: float = 0.95,
    ):
        """Initialize the unified OpenAI MCP client.

        Args:
            api_key: OpenAI API key
            base_url: Optional base URL for OpenAI API
            model: Model name to use
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            top_p: Top-p sampling parameter
        """
        super().__init__()
        
        # Initialize OpenAI client
        client_kwargs = {}
        if api_key:
            client_kwargs["api_key"] = api_key
        if base_url:
            client_kwargs["base_url"] = base_url
            
        self.openai_client = OpenAI(**client_kwargs)
        
        # Model configuration
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p

    async def _get_available_tools(self):
        """Get available tools from all connected MCP servers (cached after first call)."""
        if not hasattr(self, "_cached_tools"):
            all_tools = await self.get_all_tools()
            
            # Convert MCP tools to OpenAI function format
            openai_tools = []
            for tool in all_tools:
                openai_tool = {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or f"Tool: {tool.name}",
                    },
                }
                
                # Add parameters if available
                if hasattr(tool, "inputSchema") and tool.inputSchema:
                    openai_tool["function"]["parameters"] = tool.inputSchema
                else:
                    # Default empty parameters
                    openai_tool["function"]["parameters"] = {
                        "type": "object",
                        "properties": {},
                    }
                
                openai_tools.append(openai_tool)
            
            self._cached_tools = openai_tools
            logger.info(f"Cached {len(openai_tools)} tools from MCP servers")
        
        return self._cached_tools

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        **kwargs
    ):
        """Create a chat completion with optional tool calling.

        Args:
            messages: List of message dictionaries
            tools: Optional list of tools (if None, uses all available MCP tools)
            **kwargs: Additional arguments for OpenAI API

        Returns:
            OpenAI chat completion response
        """
        # Get tools if not provided
        if tools is None:
            tools = await self._get_available_tools()

        # Prepare API call parameters
        api_params = {
            "model": kwargs.get("model", self.model),
            "messages": messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "top_p": kwargs.get("top_p", self.top_p),
        }

        # Add tools if available
        if tools:
            api_params["tools"] = tools

        # Make the API call
        response = self.openai_client.chat.completions.create(**api_params)
        return response

    async def execute_tool_calls(self, tool_calls: List[Any]) -> List[Dict[str, Any]]:
        """Execute tool calls using the appropriate MCP servers.

        Args:
            tool_calls: List of tool call objects from OpenAI response

        Returns:
            List of tool call results
        """
        results = []
        
        for tool_call in tool_calls:
            try:
                # Parse tool call
                tool_name = tool_call.function.name
                arguments_str = tool_call.function.arguments
                
                # Parse arguments
                try:
                    arguments = json.loads(arguments_str)
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse arguments for tool {tool_name}: {arguments_str}")
                    results.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "content": f"Error: Invalid JSON arguments: {arguments_str}",
                    })
                    continue

                # Execute the tool call
                logger.info(f"Executing tool: {tool_name} with arguments: {arguments}")
                result = await self.call_tool(tool_name, arguments)
                
                # Format result for OpenAI
                if hasattr(result, 'content'):
                    # MCP result object
                    if isinstance(result.content, list):
                        content_parts = []
                        for content_item in result.content:
                            if hasattr(content_item, 'text'):
                                content_parts.append(content_item.text)
                            else:
                                content_parts.append(str(content_item))
                        content = "\n".join(content_parts)
                    else:
                        content = str(result.content)
                else:
                    # Direct result
                    content = str(result)

                results.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "content": content,
                })
                
                logger.info(f"Tool {tool_name} executed successfully")

            except Exception as e:
                logger.error(f"Error executing tool {tool_call.function.name}: {e}")
                results.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "content": f"Error executing tool: {str(e)}",
                })

        return results

    async def chat_with_tools(
        self,
        messages: List[Dict[str, str]],
        max_turns: int = 10,
        **kwargs
    ) -> Dict[str, Any]:
        """Have a conversation with tool calling support.

        Args:
            messages: Initial messages
            max_turns: Maximum number of turns
            **kwargs: Additional arguments for chat completion

        Returns:
            Dictionary with final response and conversation history
        """
        conversation = messages.copy()
        turn_count = 0

        while turn_count < max_turns:
            # Get response from OpenAI
            response = await self.chat_completion(conversation, **kwargs)
            message = response.choices[0].message
            
            # Add assistant message to conversation
            conversation.append({
                "role": "assistant",
                "content": message.content,
                "tool_calls": message.tool_calls if hasattr(message, 'tool_calls') else None,
            })

            # Check if there are tool calls to execute
            if hasattr(message, 'tool_calls') and message.tool_calls:
                # Execute tool calls
                tool_results = await self.execute_tool_calls(message.tool_calls)
                
                # Add tool results to conversation
                conversation.extend(tool_results)
                
                turn_count += 1
            else:
                # No more tool calls, conversation is complete
                break

        return {
            "final_response": conversation[-1] if conversation else None,
            "conversation": conversation,
            "turns_used": turn_count,
        }