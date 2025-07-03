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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class LLMMCPClient(MCPClientStdio):
    def __init__(self, model_name: str = "default", system_prompt: str = None, config: dict = None):
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
            self.messages.append({
                "role": "system",
                "content": system_prompt
            })
        logger.info(f"LLM MCP Client initialized with model: {self.model_name}")
    
    async def _get_available_tools(self):
        """Get available tools from the MCP server"""
        response = await self.session.list_tools()
        return [{
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema
            }
        } for tool in response.tools]
    
    async def generate_response(self, available_tools=None, max_tokens=None, temperature=None, top_p=None):
        """Generate a response from the LLM API using the current conversation history"""
        if available_tools is None:
            available_tools = await self._get_available_tools()
            
        response = self.llm.chat_completion(
            messages=self.messages,
            tools=available_tools,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p
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

    async def process_query(self, query: str) -> str:
        """Process a query using LLM and available tools"""
        # Add the user message to the conversation history
        self.messages.append({
            "role": "user",
            "content": query
        })
        
        logger.debug(f"Processing query: {query}")

        # Get available tools
        available_tools = await self._get_available_tools()
        
        final_text = []
        has_tool_calls = True
        
        # Continue processing responses until no more tool calls are generated
        while has_tool_calls:
            # Generate response
            assistant_message = await self.generate_response(
                available_tools,
                max_tokens=self.llm.model_config.get("max_tokens", 1000), 
                temperature=self.llm.model_config.get("temperature", 0.5),
                top_p=self.llm.model_config.get("top_p", 1)
            )
            logger.debug(f"Assistant response: {assistant_message['content']}")
            
            # Check if the response contains tool calls
            if "tool_calls" in assistant_message and assistant_message["tool_calls"]:
                logger.info(f"Processing response with {len(assistant_message['tool_calls'])} tool calls")
                
                # Create a message with the tool calls
                tool_call_message = {
                    "role": "assistant",
                    "content": assistant_message["content"],
                    "tool_calls": []
                }
                
                # Process tool call info
                for tool_call in assistant_message["tool_calls"]:
                    tool_call_info = {
                        "id": tool_call["id"],
                        "type": "function",
                        "function": {
                            "name": tool_call["function"]["name"],
                            "arguments": tool_call["function"]["arguments"]
                        }
                    }
                    tool_call_message["tool_calls"].append(tool_call_info)
                
                # Add the assistant message with tool calls to conversation history
                self.messages.append(tool_call_message)
                
                # Execute tool calls
                tool_results = await self._handle_tool_calls(assistant_message)
                
                # Add tool results to conversation history
                for tool_call, result in tool_results:
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": result.content[0].text
                    })
                
                # Continue the loop to get a follow-up response after tools execution
                has_tool_calls = True
            else:
                # No tool calls, add the response content to final text
                if assistant_message["content"]:
                    final_text.append(assistant_message["content"])
                    # Add assistant's response to conversation history
                    self.messages.append({
                        "role": "assistant",
                        "content": assistant_message["content"]
                    })
                # Exit the loop as there are no more tool calls
                has_tool_calls = False

        logger.info("Query processing completed")
        return "\n".join(final_text)
    
    async def chat(self):
        """Run an interactive chat loop for the client"""
        logger.info("MCP Client Started!")
        print("Type your queries, 'reset' to clear conversation history, or 'quit' to exit.")
        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == 'quit':
                    break
                
                if query.lower() == 'reset':
                    self.messages = []
                    logger.info("Conversation history has been reset.")
                    print("\nConversation history has been reset.")
                    continue

                response = await self.process_query(query)
                # Add color and assistant prefix to the response
                colored_response = f"\033[94m🤖 Assistant: {response}\033[0m"
                print("\n" + colored_response)

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
        await client.connect_to_server(sys.argv[1], sys.argv[2:])
        await client.chat_loop()
    finally:
        logger.info("Cleaning up resources")
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())