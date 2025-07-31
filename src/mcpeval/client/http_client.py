"""
HTTP-based MCP client for connecting to HTTP MCP servers.
"""
import asyncio
import logging
from contextlib import AsyncExitStack
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from .BaseClient import BaseClient

logger = logging.getLogger(__name__)


class MCPClientHTTP(BaseClient):
    """HTTP-based MCP client for connecting to HTTP MCP servers."""

    def __init__(self):
        """Initialize HTTP MCP client."""
        self.exit_stack = AsyncExitStack()
        self.server_mapping = {}  # mapping of server URLs to their sessions
        self.tool_mapping = {}  # mapping of tool names to their sessions

    async def connect_to_server(
        self,
        server_url: str,
        server_args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
    ):
        """Connect to an HTTP MCP server.

        Args:
            server_url: HTTP URL of the MCP server (e.g., http://127.0.0.1:8000)
            server_args: Not used for HTTP servers (kept for compatibility)
            env: Not used for HTTP servers (kept for compatibility)

        Returns:
            tuple: session, http_transport, write objects for the connected server
        """
        logger.info(f"Connecting to HTTP MCP server at {server_url}")
        
        # Validate URL
        parsed_url = urlparse(server_url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError(f"Invalid server URL: {server_url}")
        
        if parsed_url.scheme not in ['http', 'https']:
            raise ValueError(f"Unsupported scheme: {parsed_url.scheme}. Only http and https are supported.")

        try:
            # Create streamable HTTP client for HTTP transport
            http_transport = await self.exit_stack.enter_async_context(
                streamablehttp_client(server_url)
            )
            read, write, get_session_id = http_transport
            
            # Create client session
            session = await self.exit_stack.enter_async_context(
                ClientSession(read, write)
            )
            
            # Initialize the session
            await session.initialize()
            
            # Get available tools
            response = await session.list_tools()
            tools = response.tools
            logger.info(f"Connected to HTTP server with tools: {[tool.name for tool in tools]}")

            # Map tools to session
            for tool in tools:
                self.tool_mapping[tool.name] = session

            # Store server mapping
            self.server_mapping[server_url] = {
                "session": session,
                "transport": http_transport,
                "write": write,
                "tools": tools,
            }

            # Set default session if this is the first server
            if not hasattr(self, 'session') or self.session is None:
                self.session = session
                self.stdio = read  # For compatibility
                self.write = write

            return session, http_transport, write, tools

        except Exception as e:
            logger.error(f"Failed to connect to HTTP MCP server {server_url}: {e}")
            raise

    async def connect_to_multiple_servers(
        self,
        server_urls: List[str],
        server_args: List[Optional[List[str]]] = None,
        server_envs: List[Optional[Dict[str, str]]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """Connect to multiple HTTP MCP servers.

        Args:
            server_urls: List of HTTP URLs to connect to
            server_args: Not used for HTTP servers (kept for compatibility)
            server_envs: Not used for HTTP servers (kept for compatibility)

        Returns:
            Dict: A dictionary mapping server URLs to their respective sessions and tools
        """
        if server_args is None:
            server_args = [None] * len(server_urls)
        if server_envs is None:
            server_envs = [None] * len(server_urls)

        for server_url, args, env in zip(server_urls, server_args, server_envs):
            session, transport, write, tools = await self.connect_to_server(
                server_url, args, env
            )
            self.server_mapping[server_url] = {
                "session": session,
                "transport": transport,
                "write": write,
                "tools": tools,
            }

        return self.server_mapping

    async def get_all_tools(self):
        """Get all tools from all connected servers.

        Returns:
            List of tool objects from all connected servers
        """
        all_tools = []
        for server_info in self.server_mapping.values():
            all_tools.extend(server_info["tools"])
        return all_tools

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]):
        """Call a tool by name with the given arguments.

        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool

        Returns:
            The result of the tool call
        """
        if tool_name not in self.tool_mapping:
            raise ValueError(f"Tool '{tool_name}' not found in any connected server")

        session = self.tool_mapping[tool_name]
        return await session.call_tool(tool_name, arguments)

    async def cleanup(self):
        """Clean up resources (required by BaseClient)."""
        await self.close()

    async def close(self):
        """Close all connections."""
        await self.exit_stack.aclose()