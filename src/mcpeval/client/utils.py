import asyncio
import shutil
import os
from pathlib import Path
from contextlib import AsyncExitStack
from typing import Tuple, Any, Optional, List, Dict
from urllib.parse import urlparse
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client


def find_npx_path() -> str:
    """Find the path to npx, checking various locations including nvm"""
    # First try to find npx in PATH
    npx_path = shutil.which("npx")
    if npx_path:
        return npx_path

    # If not found, try to find it in nvm directory
    home_dir = os.path.expanduser("~")
    nvm_dir = os.path.join(home_dir, ".nvm")

    if os.path.exists(nvm_dir):
        # Look for npx in nvm versions
        versions_dir = os.path.join(nvm_dir, "versions", "node")
        if os.path.exists(versions_dir):
            # Get all node versions and try to find npx
            for version_dir in os.listdir(versions_dir):
                npx_candidate = os.path.join(versions_dir, version_dir, "bin", "npx")
                if os.path.exists(npx_candidate) and os.access(npx_candidate, os.X_OK):
                    return npx_candidate

    # If still not found, try some common locations
    common_paths = [
        "/usr/local/bin/npx",
        "/usr/bin/npx",
        "/opt/homebrew/bin/npx",  # macOS Homebrew
    ]

    for path in common_paths:
        if os.path.exists(path) and os.access(path, os.X_OK):
            return path

    # Fallback to just "npx" and let the system handle it
    return "npx"


def is_http_server(server_path: str) -> bool:
    """Check if the server path is an HTTP URL."""
    try:
        parsed = urlparse(server_path)
        return parsed.scheme in ["http", "https"]
    except Exception:
        return False


async def connect_http_mcp_server(
    server_url: str,
    exit_stack: AsyncExitStack,
    server_args: Optional[List[str]] = None,
    env: Optional[Dict[str, str]] = None,
) -> Tuple[ClientSession, Any, Any]:
    """Connect to an HTTP MCP server and return the session and IO interfaces

    Args:
        server_url: HTTP URL of the MCP server
        exit_stack: AsyncExitStack for managing resources
        server_args: Not used for HTTP servers (kept for compatibility)
        env: Not used for HTTP servers (kept for compatibility)

    Returns:
        Tuple containing (session, sse_transport, write)
    """
    # Validate URL
    parsed_url = urlparse(server_url)
    if not parsed_url.scheme or not parsed_url.netloc:
        raise ValueError(f"Invalid server URL: {server_url}")

    if parsed_url.scheme not in ["http", "https"]:
        raise ValueError(
            f"Unsupported scheme: {parsed_url.scheme}. Only http and https are supported."
        )

    # Create streamable HTTP client for HTTP transport
    http_transport = await exit_stack.enter_async_context(
        streamablehttp_client(server_url)
    )
    read, write, get_session_id = http_transport

    # Create client session
    session = await exit_stack.enter_async_context(ClientSession(read, write))

    # Initialize the session
    await session.initialize()

    return session, http_transport, write


async def connect_mcp_server(
    server_script_path: str,
    exit_stack: AsyncExitStack,
    server_args: Optional[List[str]] = None,
    env: Optional[Dict[str, str]] = None,
) -> Tuple[ClientSession, Any, Any]:
    """Connect to an MCP server and return the session and IO interfaces

    Args:
        server_script_path: Path to the server script (.py or .js) or HTTP URL
        exit_stack: AsyncExitStack for resource management
        server_args: Optional list of arguments to pass to the server (ignored for HTTP)
        env: Optional environment variables dictionary (ignored for HTTP)

    Returns:
        Tuple containing (session, stdio/transport, write)
    """
    # Check if this is an HTTP server
    if is_http_server(server_script_path):
        return await connect_http_mcp_server(
            server_script_path, exit_stack, server_args, env
        )
    is_python = server_script_path.endswith(".py")

    if is_python:
        command = "uv"
        args = ["run", server_script_path]
    else:
        command = find_npx_path()
        args = ["-y", server_script_path]

    if server_args:
        args.extend(server_args)

    # Set up environment variables - start with current environment
    process_env = os.environ.copy()
    if env:
        process_env.update(env)

    # Add Node.js bin directory to PATH for npm servers
    if not is_python:
        npx_path = command
        if npx_path != "npx":  # If we found a specific path
            node_bin_dir = os.path.dirname(npx_path)
            current_path = process_env.get("PATH", "")
            if node_bin_dir not in current_path:
                process_env["PATH"] = f"{node_bin_dir}:{current_path}"

    server_params = StdioServerParameters(command=command, args=args, env=process_env)

    stdio_transport = await exit_stack.enter_async_context(stdio_client(server_params))
    stdio, write = stdio_transport
    session = await exit_stack.enter_async_context(ClientSession(stdio, write))

    await session.initialize()

    return session, stdio, write
