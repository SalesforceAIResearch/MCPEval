"""
Unified MCP client that supports both stdio and HTTP transports.
"""
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from .mcp_clients import MCPClientStdio
from .http_client import MCPClientHTTP
from .utils import is_http_server

logger = logging.getLogger(__name__)


class UnifiedMCPClient:
    """Unified MCP client that automatically chooses the right transport."""

    def __init__(self):
        """Initialize the unified client."""
        self.stdio_client = None
        self.http_client = None
        self.active_clients = {}  # Maps server paths to their client instances

    async def connect_to_server(
        self,
        server_path: str,
        server_args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
    ):
        """Connect to a server using the appropriate transport.

        Args:
            server_path: Path to server script or HTTP URL
            server_args: Optional arguments (ignored for HTTP)
            env: Optional environment variables (ignored for HTTP)

        Returns:
            tuple: session, transport, write, tools
        """
        if is_http_server(server_path):
            # Use HTTP client
            if self.http_client is None:
                self.http_client = MCPClientHTTP()
            
            client = self.http_client
            session, transport, write, tools = await client.connect_to_server(
                server_path, server_args, env
            )
        else:
            # Use stdio client
            if self.stdio_client is None:
                self.stdio_client = MCPClientStdio()
            
            client = self.stdio_client
            session, transport, write, tools = await client.connect_to_server(
                server_path, server_args, env
            )

        # Track which client is handling this server
        self.active_clients[server_path] = client
        
        return session, transport, write, tools

    async def connect_to_multiple_servers(
        self,
        server_paths: List[str],
        server_args: List[Optional[List[str]]] = None,
        server_envs: List[Optional[Dict[str, str]]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """Connect to multiple servers using appropriate transports.

        Args:
            server_paths: List of server paths/URLs
            server_args: List of argument lists for each server
            server_envs: List of environment variable dicts for each server

        Returns:
            Dict: Mapping of server paths to their connection info
        """
        if server_args is None:
            server_args = [None] * len(server_paths)
        if server_envs is None:
            server_envs = [None] * len(server_paths)

        all_connections = {}

        for server_path, args, env in zip(server_paths, server_args, server_envs):
            session, transport, write, tools = await self.connect_to_server(
                server_path, args, env
            )
            
            all_connections[server_path] = {
                "session": session,
                "transport": transport,
                "write": write,
                "tools": tools,
            }

        return all_connections

    async def get_all_tools(self):
        """Get all tools from all connected servers."""
        all_tools = []
        
        if self.stdio_client:
            stdio_tools = await self.stdio_client.get_all_tools()
            all_tools.extend(stdio_tools)
        
        if self.http_client:
            http_tools = await self.http_client.get_all_tools()
            all_tools.extend(http_tools)
        
        return all_tools

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]):
        """Call a tool by name using the appropriate client."""
        # Try stdio client first
        if self.stdio_client and tool_name in self.stdio_client.tool_mapping:
            return await self.stdio_client.call_tool(tool_name, arguments)
        
        # Try HTTP client
        if self.http_client and tool_name in self.http_client.tool_mapping:
            return await self.http_client.call_tool(tool_name, arguments)
        
        raise ValueError(f"Tool '{tool_name}' not found in any connected server")

    async def close(self):
        """Close all connections."""
        if self.stdio_client:
            await self.stdio_client.exit_stack.aclose()
        
        if self.http_client:
            await self.http_client.close()

    @property
    def session(self):
        """Get the primary session (for backward compatibility)."""
        if self.stdio_client and hasattr(self.stdio_client, 'session'):
            return self.stdio_client.session
        if self.http_client and hasattr(self.http_client, 'session'):
            return self.http_client.session
        return None

    @property
    def stdio(self):
        """Get the primary stdio/transport (for backward compatibility)."""
        if self.stdio_client and hasattr(self.stdio_client, 'stdio'):
            return self.stdio_client.stdio
        if self.http_client and hasattr(self.http_client, 'stdio'):
            return self.http_client.stdio
        return None

    @property
    def write(self):
        """Get the primary write interface (for backward compatibility)."""
        if self.stdio_client and hasattr(self.stdio_client, 'write'):
            return self.stdio_client.write
        if self.http_client and hasattr(self.http_client, 'write'):
            return self.http_client.write
        return None