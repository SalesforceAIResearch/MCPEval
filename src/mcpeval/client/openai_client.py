from .mcp_clients import MCPClientStdio
from openai import OpenAI
import json
import logging
import sys
import asyncio
import os

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


class OpenAIMCPClient(MCPClientStdio):
    def __init__(
        self,
        model: str = "gpt-4o",
        system_prompt: str = None,
        api_key: str = None,
        base_url: str = None,
        **kwargs,
    ):
        """
        Initialize the OpenAI MCP client with a specified model

        Args:
            model: OpenAI model to use
            system_prompt: Optional system prompt to use
            api_key: Optional API key to use (will fall back to environment variable)
        """
        super().__init__()

        # Check for API key
        api_key = api_key or os.environ.get("OPENAI_API_KEY")
        # Initialize OpenAI client
        self.openai = OpenAI(api_key=api_key, base_url=base_url, **kwargs)
        self.model = model
        self.system_prompt = system_prompt
        self.cached_tools = None  # Cache tools to avoid repeated calls
        if system_prompt:
            self.messages.append({"role": "system", "content": system_prompt})
        logger.info(f"OpenAI MCP Client initialized with model: {model}")

    async def _get_available_tools(self):
        """Get available tools from all connected MCP servers (cached after first call)"""
        # Return cached tools if available
        if self.cached_tools is not None:
            return self.cached_tools

        tools = []

        # Use the base class helper method to get all tools
        all_tools = await self.get_all_tools()

        # If we have multiple servers, add server identification to descriptions
        if self.server_mapping:
            # Create a reverse mapping to find which server each tool belongs to
            tool_to_server = {}
            for server_path, server_info in self.server_mapping.items():
                for tool in server_info["tools"]:
                    tool_to_server[tool.name] = server_path

            # Format tools with server identification
            for tool in all_tools:
                server_path = tool_to_server.get(tool.name, "unknown")
                server_name = (
                    server_path.split("/")[-1] if "/" in server_path else server_path
                )
                tool_def = {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": f"[{server_name}] {tool.description}",
                        "parameters": tool.inputSchema,
                    },
                }
                tools.append(tool_def)
        else:
            # Single server mode - no need for server identification
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema,
                    },
                }
                for tool in all_tools
            ]

        # Cache the tools for future use
        self.cached_tools = tools
        logger.info(
            f"Cached {len(tools)} tools: {[tool['function']['name'] for tool in tools]}"
        )
        return tools

    async def generate_response(
        self, available_tools=None, max_tokens=None, temperature=None, top_p=None
    ):
        """Generate a response from the OpenAI API using the current conversation history"""
        if available_tools is None:
            available_tools = await self._get_available_tools()

        # Debug: Log tools being passed to OpenAI
        logger.debug(f"Sending {len(available_tools)} tools to OpenAI API")

        try:
            response = self.openai.chat.completions.create(
                model=self.model,
                messages=self.messages,
                tools=available_tools if available_tools else None,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
            )

            # Debug: Log whether the response has tool calls
            message = response.choices[0].message
            if hasattr(message, "tool_calls") and message.tool_calls:
                logger.debug(
                    f"OpenAI response contains {len(message.tool_calls)} tool calls"
                )
            else:
                logger.debug("OpenAI response contains no tool calls")

            return message
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            raise

    async def _handle_tool_calls(self, assistant_message):
        """Execute tool calls and return their results, routing to the correct server

        This method executes the tool calls but doesn't modify the message history.

        Args:
            assistant_message: The message from the assistant containing tool calls

        Returns:
            list: List of (tool_call, result) tuples for each executed tool call
        """
        results = []

        # Execute all tool calls and collect results
        for tool_call in assistant_message.tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)

            # Log tool calls to console
            logger.info(f"Calling tool {tool_name} with args {tool_args}")

            # Find the correct session for this tool
            target_session = None
            if tool_name in self.tool_name_to_session:
                target_session = self.tool_name_to_session[tool_name]
            elif self.session:
                # Fallback to single session mode
                target_session = self.session
            else:
                logger.error(f"No session found for tool {tool_name}")
                result = type(
                    "Result",
                    (),
                    {
                        "content": f"Error: No server connection found for tool {tool_name}"
                    },
                )()
                results.append((tool_call, result))
                continue

            try:
                # Execute tool call on the correct server
                result = await target_session.call_tool(tool_name, tool_args)

                # Log tool results to console
                logger.info(f"Tool {tool_name} returned: {result.content}")

                # Add to results
                results.append((tool_call, result))
            except Exception as e:
                import traceback

                error_details = f"{str(e)}\n{traceback.format_exc()}"
                logger.error(f"Error calling tool {tool_name}: {error_details}")
                # Create error result
                error_result = type(
                    "Result",
                    (),
                    {
                        "content": f"Error calling tool {tool_name}: {str(e) if str(e) else 'Unknown error occurred'}"
                    },
                )()
                results.append((tool_call, error_result))

        return results

    async def process_query(self, query: str) -> dict:
        """Process a query using OpenAI and available tools

        Returns:
            dict: Contains 'response', 'tool_calls', and 'tool_results'
        """
        # Add the user message to the conversation history
        self.messages.append({"role": "user", "content": query})

        logger.debug(f"Processing query: {query}")

        # Get available tools from all connected servers
        available_tools = await self._get_available_tools()

        final_text = []
        has_tool_calls = True
        all_tool_calls = []
        all_tool_results = []

        # Continue processing responses until no more tool calls are generated
        while has_tool_calls:
            # Generate response
            assistant_message = await self.generate_response(available_tools)
            logger.debug(f"Assistant response: {assistant_message.content}")

            # Check if the response contains tool calls
            if (
                hasattr(assistant_message, "tool_calls")
                and assistant_message.tool_calls
            ):
                logger.info(
                    f"Processing response with {len(assistant_message.tool_calls)} tool calls"
                )

                # Create a message with the tool calls
                tool_call_message = {
                    "role": "assistant",
                    "content": assistant_message.content,
                    "tool_calls": [],
                }

                # Process tool call info
                for tool_call in assistant_message.tool_calls:
                    tool_call_info = {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        },
                    }
                    tool_call_message["tool_calls"].append(tool_call_info)

                # Add the assistant message with tool calls to conversation history
                self.messages.append(tool_call_message)

                # Execute tool calls (routed to appropriate servers)
                tool_results = await self._handle_tool_calls(assistant_message)

                # Capture tool call information for frontend
                for tool_call, result in tool_results:
                    # Store tool call info
                    tool_call_info = {
                        "id": tool_call.id,
                        "name": tool_call.function.name,
                        "arguments": json.loads(tool_call.function.arguments),
                    }
                    all_tool_calls.append(tool_call_info)

                    # Store tool result info - extract text content for JSON serialization
                    result_content = result.content
                    if hasattr(result_content, "text"):
                        # Single TextContent object
                        result_text = result_content.text
                    elif isinstance(result_content, list) and len(result_content) > 0:
                        # List of TextContent objects
                        result_text = "\n".join(
                            [
                                item.text if hasattr(item, "text") else str(item)
                                for item in result_content
                            ]
                        )
                    else:
                        # Fallback to string representation
                        result_text = str(result_content)

                    tool_result_info = {
                        "tool_call_id": tool_call.id,
                        "name": tool_call.function.name,
                        "result": result_text,
                    }
                    all_tool_results.append(tool_result_info)

                    # Add tool results to conversation history
                    self.messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result_text,
                        }
                    )

                # Continue the loop to get a follow-up response after tools execution
                has_tool_calls = True
            else:
                # No tool calls, add the response content to final text
                if assistant_message.content:
                    final_text.append(assistant_message.content)
                    # Add assistant's response to conversation history
                    self.messages.append(
                        {"role": "assistant", "content": assistant_message.content}
                    )
                # Exit the loop as there are no more tool calls
                has_tool_calls = False

        logger.info("Query processing completed")
        return {
            "response": "\n".join(final_text),
            "tool_calls": all_tool_calls,
            "tool_results": all_tool_results,
        }

    async def chat(self):
        """Run an interactive chat loop for the client"""
        logger.info("MCP Client Started!")

        # Show connected servers and their tools
        if self.server_mapping:
            print(f"\n🔗 Connected to {len(self.server_mapping)} servers:")
            for server_path, server_info in self.server_mapping.items():
                tool_names = [tool.name for tool in server_info["tools"]]
                server_name = (
                    server_path.split("/")[-1] if "/" in server_path else server_path
                )
                print(
                    f"  📁 {server_name}: {len(tool_names)} tools ({', '.join(tool_names)})"
                )
        else:
            # Single server mode - get tools using the helper method
            all_tools = await self.get_all_tools()
            tool_names = [tool.name for tool in all_tools]
            print(
                f"\n🔗 Connected to single server with {len(tool_names)} tools: {', '.join(tool_names)}"
            )

        print(
            "\nType your queries, 'reset' to clear conversation history, or 'quit' to exit."
        )

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == "quit":
                    break

                if query.lower() == "reset":
                    self.messages = []
                    if self.system_prompt:
                        self.messages.append(
                            {"role": "system", "content": self.system_prompt}
                        )
                    logger.info("Conversation history has been reset.")
                    print("\nConversation history has been reset.")
                    continue

                result = await self.process_query(query)
                response = result["response"]
                # Add color and assistant prefix to the response
                colored_response = f"\033[94m🤖 Assistant: {response}\033[0m"
                print("\n" + colored_response)

                # Show tool call details if any
                if result["tool_calls"]:
                    print(
                        f"\n\033[92m🔧 Tool Calls ({len(result['tool_calls'])}):\033[0m"
                    )
                    for i, tool_call in enumerate(result["tool_calls"]):
                        print(f"  {i+1}. {tool_call['name']}({tool_call['arguments']})")
                        # Find corresponding result
                        for tool_result in result["tool_results"]:
                            if tool_result["tool_call_id"] == tool_call["id"]:
                                result_preview = (
                                    str(tool_result["result"])[:100] + "..."
                                    if len(str(tool_result["result"])) > 100
                                    else str(tool_result["result"])
                                )
                                print(f"     → {result_preview}")
                                break

            except Exception as e:
                logger.error(f"Error processing query: {str(e)}", exc_info=True)
                print(f"\nError: {str(e)}")
