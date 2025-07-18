from .mcp_clients import MCPClientStdio
import json
import logging
import sys
import asyncio
import os

from ..models.api_based_llm import APIBasedLLM

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


class LLMMCPClient(MCPClientStdio):
    def __init__(
        self,
        model_name: str = "default",
        system_prompt: str = None,
        config: dict = None,
    ):
        """
        Initialize the LLM MCP client with a specified model

        Args:
            model: LLM model to use
            system_prompt: System prompt to use
            model_config: Model configuration to use
        """
        super().__init__()
        self.llm = APIBasedLLM(name=model_name, config=config)
        self.model_name = model_name
        self.system_prompt = system_prompt

        if system_prompt:
            self.messages.append({"role": "system", "content": system_prompt})
        logger.info(f"LLM MCP Client initialized with model: {self.model_name}")

    async def _get_available_tools(self):
        """Get available tools from the MCP server"""
        response = await self.session.list_tools()
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                },
            }
            for tool in response.tools
        ]

    async def generate_response(
        self, available_tools=None, max_tokens=None, temperature=None, top_p=None
    ):
        """Generate a response from the LLM API using the current conversation history"""
        if available_tools is None:
            available_tools = await self._get_available_tools()

        response = self.llm.chat_completion(
            messages=self.messages,
            tools=available_tools,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
        )
        logger.debug(f"LLM response: {response}")

        return response["choices"][0]["message"]

    async def _handle_tool_calls(self, assistant_message):
        """Execute tool calls and return their results

        This method executes the tool calls but doesn't modify the message history.

        Args:
            assistant_message: The message from the assistant containing tool calls

        Returns:
            list: List of (tool_call, result) tuples for each executed tool call
        """
        results = []

        # Execute all tool calls and collect results
        for tool_call in assistant_message["tool_calls"]:
            tool_name = tool_call["function"]["name"]
            tool_args = json.loads(tool_call["function"]["arguments"])

            # Log tool calls to console
            logger.info(f"Calling tool {tool_name} with args {tool_args}")

            # Execute tool call
            result = await self.session.call_tool(tool_name, tool_args)

            # Log tool results to console
            logger.info(f"Tool {tool_name} returned: {result.content}")

            # Add to results
            results.append((tool_call, result))

        return results

    async def process_query(self, query: str) -> dict:
        """Process a query using LLM and available tools

        Returns:
            dict: Contains 'response', 'tool_calls', and 'tool_results'
        """
        # Add the user message to the conversation history
        self.messages.append({"role": "user", "content": query})

        logger.debug(f"Processing query: {query}")

        # Get available tools
        available_tools = await self._get_available_tools()

        final_text = []
        has_tool_calls = True
        all_tool_calls = []
        all_tool_results = []

        # Continue processing responses until no more tool calls are generated
        while has_tool_calls:
            # Generate response
            assistant_message = await self.generate_response(
                available_tools,
                max_tokens=self.llm.model_config.get("max_tokens", 1000),
                temperature=self.llm.model_config.get("temperature", 0.5),
                top_p=self.llm.model_config.get("top_p", 1),
            )
            logger.debug(f"Assistant response: {assistant_message['content']}")

            # Check if the response contains tool calls
            if "tool_calls" in assistant_message and assistant_message["tool_calls"]:
                logger.info(
                    f"Processing response with {len(assistant_message['tool_calls'])} tool calls"
                )

                # Create a message with the tool calls
                tool_call_message = {
                    "role": "assistant",
                    "content": assistant_message["content"],
                    "tool_calls": [],
                }

                # Process tool call info
                for tool_call in assistant_message["tool_calls"]:
                    tool_call_info = {
                        "id": tool_call["id"],
                        "type": "function",
                        "function": {
                            "name": tool_call["function"]["name"],
                            "arguments": tool_call["function"]["arguments"],
                        },
                    }
                    tool_call_message["tool_calls"].append(tool_call_info)

                # Add the assistant message with tool calls to conversation history
                self.messages.append(tool_call_message)

                # Execute tool calls
                tool_results = await self._handle_tool_calls(assistant_message)

                # Capture tool call information for frontend
                for tool_call, result in tool_results:
                    # Store tool call info
                    tool_call_info = {
                        "id": tool_call["id"],
                        "name": tool_call["function"]["name"],
                        "arguments": json.loads(tool_call["function"]["arguments"]),
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
                        "tool_call_id": tool_call["id"],
                        "name": tool_call["function"]["name"],
                        "result": result_text,
                    }
                    all_tool_results.append(tool_result_info)

                    # Add tool results to conversation history
                    self.messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "content": result_text,
                        }
                    )

                # Continue the loop to get a follow-up response after tools execution
                has_tool_calls = True
            else:
                # No tool calls, add the response content to final text
                if assistant_message["content"]:
                    final_text.append(assistant_message["content"])
                    # Add assistant's response to conversation history
                    self.messages.append(
                        {"role": "assistant", "content": assistant_message["content"]}
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
        print(
            "Type your queries, 'reset' to clear conversation history, or 'quit' to exit."
        )
        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == "quit":
                    break

                if query.lower() == "reset":
                    self.messages = []
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


async def main():
    logger.info(f"Received command line arguments: {sys.argv}")
    if len(sys.argv) < 2:
        logger.error("Missing server script path argument")
        print("Usage: python client.py <path_to_server_script> <server_args>")
        sys.exit(1)
    logger.info(f"Received server script path: {sys.argv[1]}")
    logger.info(f"Received server args: {sys.argv[2:]}")

    client = LLMMCPClient()
    logger.info("LLM MCP client created")
    try:
        # Convert single server to list format for connect_to_multiple_servers
        server_paths = [sys.argv[1]]
        server_args_list = [sys.argv[2:]] if len(sys.argv) > 2 else [None]
        server_envs = None
        await client.connect_to_multiple_servers(
            server_paths, server_args_list, server_envs
        )
        await client.chat()
    finally:
        logger.info("Cleaning up resources")
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
