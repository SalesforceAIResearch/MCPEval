import asyncio
import shutil
import os
from pathlib import Path
from contextlib import AsyncExitStack
from typing import Tuple, Any, Optional, List, Dict
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


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


async def connect_mcp_server(
    server_script_path: str,
    exit_stack: AsyncExitStack,
    server_args: Optional[List[str]] = None,
    env: Optional[Dict[str, str]] = None,
) -> Tuple[ClientSession, Any, Any]:
    """Connect to an MCP server and return the session and IO interfaces

    Args:
        server_script_path: Path to the server script (.py or .js)
        exit_stack: AsyncExitStack for resource management
        server_args: Optional list of arguments to pass to the server
        env: Optional environment variables dictionary

    Returns:
        Tuple containing (session, stdio, write)
    """
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
