#!/usr/bin/env python3
"""
Test script for HTTP MCP server support.
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcpeval.client.unified_client import UnifiedMCPClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_http_mcp_server():
    """Test connecting to an HTTP MCP server."""
    # Initialize the unified client (without OpenAI for basic testing)
    client = UnifiedMCPClient()
    
    try:
        # Connect to your HTTP MCP server
        # Try different common MCP endpoints
        possible_urls = [
            "http://127.0.0.1:8000",
            "http://127.0.0.1:8000/mcp",
            "http://127.0.0.1:8000/sse",
            "http://127.0.0.1:8000/events",
        ]
        
        server_url = None
        for url in possible_urls:
            try:
                import httpx
                async with httpx.AsyncClient() as http_client:
                    response = await http_client.get(url)
                    if response.status_code != 404:
                        server_url = url
                        logger.info(f"Found MCP server at: {url}")
                        break
            except Exception as e:
                logger.debug(f"Failed to check {url}: {e}")
        
        if not server_url:
            logger.error("Could not find MCP server at any of the expected URLs")
            logger.info("Make sure your streamable-http MCP server is running on port 8000")
            logger.info("Expected URLs tried: " + ", ".join(possible_urls))
            return
        logger.info(f"Connecting to HTTP MCP server at {server_url}")
        
        session, transport, write, tools = await client.connect_to_server(server_url)
        
        logger.info(f"Successfully connected! Available tools:")
        for tool in tools:
            logger.info(f"  - {tool.name}: {tool.description}")
        
        # Test getting all tools
        all_tools = await client.get_all_tools()
        logger.info(f"Total tools available: {len(all_tools)}")
        
        # Test tool calling if there are tools available
        if tools:
            first_tool = tools[0]
            logger.info(f"Testing tool call for: {first_tool.name}")
            
            # You can customize this based on your actual tool's expected arguments
            test_args = {}  # Add appropriate test arguments here
            
            try:
                result = await client.call_tool(first_tool.name, test_args)
                logger.info(f"Tool call result: {result}")
            except Exception as e:
                logger.warning(f"Tool call failed (expected if no args provided): {e}")
        
        logger.info("HTTP MCP server test completed successfully!")
        
    except Exception as e:
        logger.error(f"Failed to connect to HTTP MCP server: {e}")
        raise
    finally:
        # Clean up
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_http_mcp_server())