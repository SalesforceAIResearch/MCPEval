import asyncio
import os
from typing import Optional, List, Dict, Any, Callable
from contextlib import AsyncExitStack
import json
import sys
import logging
from mcp import ClientSession, StdioServerParameters
from openai import OpenAI
from dotenv import load_dotenv
from .BaseClient import BaseClient
from .utils import connect_mcp_server
from abc import ABC, abstractmethod

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Suppress httpx logs from OpenAI's client
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
# Suppress any other noisy libraries if needed
# logging.getLogger("urllib3").setLevel(logging.WARNING)

load_dotenv()  # load environment variables from .env

class MCPClientStdio(BaseClient):
    def __init__(self):
        """
        Initialize the MCP client
        """
        # Initialize parent class
        super().__init__()
        self.exit_stack = AsyncExitStack()
        # Initialize session
        self.session: Optional[ClientSession] = None
        self.messages: List[Dict[str, Any]] = []
        self.tool_session_mapping: Dict[str, Dict[str, Any]] = {} # mapping of tool names to their respective sessions
        self.server_mapping: Dict[str, Dict[str, Any]] = {} # mapping of server paths to their sessions and tools
        self.tool_name_to_session: Dict[str, ClientSession] = {} # mapping of tool names to their sessions

    
    async def connect_to_server(self, server_script_path: str, server_args: List[str] = None):
        """Connect to an MCP server

        Args:
            server_script_path: Path to the server script (.py or .js)
            server_args: List of arguments to pass to the server script
            
        Returns:
            tuple: session, stdio, write objects for the connected server
        """
        logger.info(f"Connecting to server {server_script_path} with args: {server_args}")
        session, stdio, write = await connect_mcp_server(server_script_path, self.exit_stack, server_args)

        # List available tools
        response = await session.list_tools()
        tools = response.tools
        logger.info(f"Connected to server with tools: {[tool.name for tool in tools]}")
        
        # Map tools to session
        for tool in tools:
            self.tool_name_to_session[tool.name] = session
        
        # For backward compatibility, if this is the first/only server, set as primary session
        if not self.server_mapping:
            self.session = session
            self.stdio = stdio
            self.write = write
            
        return session, stdio, write, tools
            
    async def connect_to_multiple_servers(
            self,
            server_script_paths: List[str],
            server_args: List[List[str]] = None
        ) -> Dict[str, Dict[str, Any]]:
        """Connect to multiple MCP servers and return a mapping of sessions and tools
        
        Args:
            server_script_paths: List of paths to the server scripts
            server_args: List of lists of arguments to pass to the server scripts
            
        Returns:
            Dict: A dictionary mapping server paths to their respective sessions, stdios, writes and tools
        """
        if server_args is None:
            server_args = [[] for _ in server_script_paths]
            
        self.server_mapping = {}
        
        for server_script_path, args in zip(server_script_paths, server_args):
            session, stdio, write, tools = await self.connect_to_server(server_script_path, args)
            self.server_mapping[server_script_path] = {
                "session": session,
                "stdio": stdio,
                "write": write,
                "tools": tools
            }
            
        # Log the total number of tools mapped
        logger.info(f"Total tools mapped in tool_name_to_session: {len(self.tool_name_to_session)}")
            
        return self.server_mapping
    
    async def get_all_tools(self):
        """Get all tools from all connected servers
        
        Returns:
            List of tool objects from all connected servers
        """
        all_tools = []
        
        if self.server_mapping:
            # Multi-server mode: collect tools from all servers
            for server_path, server_info in self.server_mapping.items():
                all_tools.extend(server_info["tools"])
        elif self.session:
            # Single server mode: get tools from the primary session
            response = await self.session.list_tools()
            all_tools.extend(response.tools)
            
        return all_tools
    
    @abstractmethod
    async def _get_available_tools(self):
        """Get available tools from the MCP server"""
        pass

    @abstractmethod
    async def generate_response(self, available_tools=None, max_tokens=None, temperature=None, top_p=None):
        """Generate a response from the LLM using the current conversation history"""
        pass
    
    @abstractmethod
    async def _handle_tool_calls(self, assistant_message):
        """Execute tool calls and return their results"""
        pass
    
    @abstractmethod
    async def process_query(self, query: str) -> str:
        """Process a query using the MCP tools"""
        pass

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()