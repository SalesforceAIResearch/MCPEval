import os
import sys
from pathlib import Path
from utils.async_utils import run_async_function, cleanup_event_loop


class MCPClientManager:
    def __init__(self):
        self.mcp_client = None

    def connect_to_servers(
        self, servers, server_args, llm_config, server_types=None, server_envs=None
    ):
        """Connect to multiple MCP servers"""
        try:
            if not servers:
                raise ValueError("No servers provided")

            # Import required modules
            current_dir = os.path.dirname(os.path.abspath(__file__))
            backend_dir = os.path.dirname(current_dir)
            parent_dir = os.path.dirname(backend_dir)
            src_dir = os.path.join(parent_dir, "src")
            sys.path.insert(0, src_dir)

            from mcpeval.client.openai_client import OpenAIMCPClient

            # Handle server types - auto-detect and override if needed
            if server_types is None:
                server_types = []
                for server_path in servers:
                    if server_path.startswith("http://") or server_path.startswith(
                        "https://"
                    ):
                        server_types.append("http")
                    elif server_path.startswith("@"):
                        server_types.append("npm")
                    else:
                        server_types.append("local")
            else:
                # Override server types based on URL detection (frontend might get it wrong)
                corrected_types = []
                for i, server_path in enumerate(servers):
                    if server_path.startswith("http://") or server_path.startswith(
                        "https://"
                    ):
                        corrected_types.append("http")
                    elif server_path.startswith("@"):
                        corrected_types.append("npm")
                    else:
                        # Use the provided type for non-HTTP servers
                        if i < len(server_types):
                            corrected_types.append(server_types[i])
                        else:
                            corrected_types.append("local")
                server_types = corrected_types

            # Resolve server paths based on type
            resolved_servers = []
            for i, (server_path, server_type) in enumerate(zip(servers, server_types)):
                if server_type == "npm":
                    # For NPM servers, use the path as-is (it's a package name)
                    resolved_servers.append(server_path)
                elif server_type == "http":
                    # For HTTP servers, use the URL as-is
                    resolved_servers.append(server_path)
                else:
                    # For local servers, resolve to absolute path
                    if os.path.isabs(server_path):
                        resolved_servers.append(server_path)
                    else:
                        # Resolve relative to project root (parent_dir), not backend directory
                        absolute_path = os.path.join(parent_dir, server_path)
                        resolved_servers.append(absolute_path)

            # Handle server environment variables - default to empty dict if not provided
            if server_envs is None:
                server_envs = [{} for _ in servers]
            elif len(server_envs) != len(servers):
                # Pad with empty dicts if length mismatch
                server_envs = server_envs[: len(servers)]
                while len(server_envs) < len(servers):
                    server_envs.append({})

            print(f"Original server paths: {servers}")
            print(f"Server types: {server_types}")
            print(f"Resolved server paths: {resolved_servers}")
            print(f"Server args: {server_args}")
            print(f"Server envs: {server_envs}")
            print(f"LLM config: {llm_config}")

            def connect_servers():
                async def _connect():
                    try:
                        # Create a new client instance
                        system_prompt = llm_config.get(
                            "systemPrompt",
                            "You are a helpful AI assistant with access to various tools through MCP servers.",
                        )

                        # Set OpenAI API key - check config first, then environment
                        api_key = llm_config.get("apiKey")
                        if api_key and api_key.strip() and api_key != "test-key":
                            os.environ["OPENAI_API_KEY"] = api_key
                            print("Using API key from config")
                        elif os.environ.get("OPENAI_API_KEY"):
                            print("Using API key from environment")
                        else:
                            print(
                                "Warning: No valid API key provided in config and OPENAI_API_KEY not set in environment"
                            )

                        # Set environment variables for MCP servers
                        env_vars_set = []
                        for i, server_env in enumerate(server_envs):
                            if server_env:
                                for key, value in server_env.items():
                                    os.environ[key] = str(value)
                                    env_vars_set.append(f"{key}={value}")

                        if env_vars_set:
                            print(
                                f"Set environment variables: {', '.join(env_vars_set)}"
                            )

                        print(
                            f"Creating OpenAI client with model: {llm_config.get('model', 'gpt-4o')}"
                        )

                        # Prepare client arguments
                        client_args = {
                            "model": llm_config.get("model", "gpt-4o"),
                            "system_prompt": system_prompt,
                        }

                        # Add base_url if provided (for Ollama or other custom endpoints)
                        if llm_config.get("baseUrl"):
                            client_args["base_url"] = llm_config.get("baseUrl")
                            print(f"Using custom base URL: {llm_config.get('baseUrl')}")

                        # Add API key if provided
                        if api_key and api_key.strip():
                            client_args["api_key"] = api_key

                        client = OpenAIMCPClient(**client_args)

                        # Prepare server_args_list to match the number of servers
                        if not server_args:
                            server_args_list = [[] for _ in resolved_servers]
                        elif len(server_args) != len(resolved_servers):
                            # If server_args length doesn't match servers, pad with empty lists
                            server_args_list = server_args[: len(resolved_servers)]
                            while len(server_args_list) < len(resolved_servers):
                                server_args_list.append([])
                        else:
                            server_args_list = server_args

                        print(f"Calling connect_to_multiple_servers with:")
                        print(f"  servers: {resolved_servers}")
                        print(f"  server_args_list: {server_args_list}")

                        # Connect to multiple servers using resolved paths
                        server_mapping = await client.connect_to_multiple_servers(
                            resolved_servers, server_args_list, server_envs
                        )
                        print(f"Server mapping result: {list(server_mapping.keys())}")

                        return client, server_mapping

                    except Exception as e:
                        print(f"Error in _connect: {e}")
                        import traceback

                        traceback.print_exc()
                        raise

                return run_async_function(_connect)

            self.mcp_client, server_mapping = connect_servers()

            # Count connected servers and available tools
            connected_count = len([info for info in server_mapping.values() if info])
            total_tools = sum(
                len(info.get("tools", [])) for info in server_mapping.values() if info
            )

            print(f"Connection result: {connected_count} servers, {total_tools} tools")

            # Convert server mapping to JSON serializable format
            # Use original server paths as keys for the frontend
            serializable_mapping = {}
            for i, (resolved_path, info) in enumerate(server_mapping.items()):
                original_path = servers[i] if i < len(servers) else resolved_path
                tools_data = []
                if info and "tools" in info:
                    for tool in info["tools"]:
                        tools_data.append(
                            {
                                "name": tool.name,
                                "description": tool.description,
                                "inputSchema": tool.inputSchema,
                            }
                        )
                serializable_mapping[original_path] = {
                    "tools": tools_data,
                    "connected": bool(info),
                }

            return {
                "success": True,
                "connected_count": connected_count,
                "total_tools": total_tools,
                "server_mapping": serializable_mapping,
            }

        except Exception as e:
            import traceback

            print("Full traceback:")
            traceback.print_exc()
            raise

    def disconnect_from_servers(self):
        """Disconnect from MCP servers"""
        try:
            if self.mcp_client:
                try:

                    def cleanup():
                        async def _cleanup():
                            print("Starting MCP client cleanup...")
                            await self.mcp_client.cleanup()
                            print("MCP client cleanup completed")

                        return run_async_function(_cleanup)

                    cleanup()
                    print("Setting mcp_client to None")
                    self.mcp_client = None

                    # Clean up the persistent event loop
                    print("Cleaning up event loop...")
                    cleanup_event_loop()

                except Exception as cleanup_error:
                    print(f"Error during cleanup: {cleanup_error}")
                    # Still set client to None even if cleanup fails
                    self.mcp_client = None
                    # Try to cleanup event loop anyway
                    try:
                        cleanup_event_loop()
                    except:
                        pass

            return {"success": True, "message": "Disconnected from all servers"}

        except Exception as e:
            print(f"Error in disconnect: {e}")
            import traceback

            traceback.print_exc()
            raise

    def send_message(self, message):
        """Send a message to the MCP client"""
        if not self.mcp_client:
            raise ValueError("No MCP client connected")

        # Quick health check of the client
        if (
            not hasattr(self.mcp_client, "server_mapping")
            or not self.mcp_client.server_mapping
        ):
            raise ValueError("MCP client connection appears to be broken")

        if not message:
            raise ValueError("No message provided")

        def send_message_async():
            async def _send():
                try:
                    print(f"Processing message: {message}")
                    # Use the process_query method from the OpenAIMCPClient
                    result = await self.mcp_client.process_query(message)
                    print(
                        f"Response received: {result['response'][:200]}..."
                    )  # First 200 chars

                    # Log tool call information
                    if result["tool_calls"]:
                        print(f"Tool calls made: {len(result['tool_calls'])}")
                        for tool_call in result["tool_calls"]:
                            print(f"  - {tool_call['name']}({tool_call['arguments']})")

                    return result
                except Exception as e:
                    print(f"Error in process_query: {e}")
                    import traceback

                    traceback.print_exc()
                    # Check if this is a connection error and mark client as invalid
                    if (
                        "ClosedResourceError" in str(e)
                        or "connection" in str(e).lower()
                    ):
                        print(
                            "MCP connection appears to be broken, invalidating client"
                        )
                        self.mcp_client = None
                    raise

            return run_async_function(_send)

        result = send_message_async()

        return {
            "success": True,
            "response": result["response"],
            "tool_calls": result["tool_calls"],
            "tool_results": result["tool_results"],
        }

    def get_status(self):
        """Get MCP client status"""
        try:
            if self.mcp_client:
                # Check if we can get tools from the client
                def get_tools():
                    async def _get_tools():
                        return await self.mcp_client.get_all_tools()

                    return run_async_function(_get_tools)

                tools = get_tools()
                tool_count = len(tools)

                return {
                    "connected": True,
                    "tool_count": tool_count,
                    "tools": [
                        {"name": tool.name, "description": tool.description}
                        for tool in tools[:5]
                    ],  # First 5 tools
                }
            else:
                return {"connected": False, "tool_count": 0, "tools": []}

        except Exception as e:
            # If status check fails, consider client broken
            print(f"Status check failed, invalidating client: {e}")
            self.mcp_client = None
            return {"connected": False, "error": str(e), "tool_count": 0, "tools": []}
