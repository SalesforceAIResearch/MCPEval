import asyncio
from contextlib import AsyncExitStack
from typing import Tuple, Any, Optional, List
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def connect_mcp_server(server_script_path: str, exit_stack: AsyncExitStack, server_args: List[str] = None) -> Tuple[ClientSession, Any, Any]:
    """Connect to an MCP server and return the session and IO interfaces
    
    Args:
        server_script_path: Path to the server script (.py or .js)
        exit_stack: AsyncExitStack for resource management
        
    Returns:
        Tuple containing (session, stdio, write)
    """
    is_python = server_script_path.endswith('.py')

    command = "uv" if is_python else "npx"
    args = ["run", server_script_path] if is_python else ["-y", server_script_path]
    if server_args:
        args.extend(server_args)
    server_params = StdioServerParameters(
        command=command,
        args=args,
        env=None
    )

    stdio_transport = await exit_stack.enter_async_context(stdio_client(server_params))
    stdio, write = stdio_transport
    session = await exit_stack.enter_async_context(ClientSession(stdio, write))

    await session.initialize()
    
    return session, stdio, write
