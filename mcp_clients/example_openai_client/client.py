#!/usr/bin/env python3
"""
Multi-Server OpenAI MCP Client Example

This example demonstrates how to use the enhanced OpenAI MCP client
to connect to multiple MCP servers simultaneously and interact with
tools from all servers in a single chat session.

Usage:
    uv run client.py --servers <server1> <server2> [server3] ...

Example:
    uv run client.py --servers @modelcontextprotocol/server-sequential-thinking @openbnb/mcp-server-airbnb:--ignore-robots-txt mcp-server-nationalparks^NPS_API_KEY=1234567890

Requirements:
    - OpenAI API key set in environment (OPENAI_API_KEY)
    - MCP servers installed and accessible
"""

import asyncio
import sys
import os
import logging
import argparse

# Add the parent directories to the path so we can import our modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
src_dir = os.path.join(parent_dir, 'src')
sys.path.insert(0, src_dir)

from mcpeval.client.openai_client import OpenAIMCPClient
from mcpeval.utils.cli import parse_servers_argument

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_usage():
    """Print usage information"""
    print("Multi-Server OpenAI MCP Client")
    print("=" * 40)
    print()
    print("Usage:")
    print("  uv run client.py --servers <server1> [server2] [server3] ...")
    print("  uv run client.py --servers <server1:args> [server2:args] [server3:args] ...")
    print()
    print("Server Format:")
    print("  server_path                    - Server with no arguments or env vars")
    print("  server_path:arg1,arg2          - Server with arguments (comma-separated)")
    print("  server_path^ENV_VAR=value      - Server with environment variables")
    print("  server_path:arg1^ENV_VAR=value - Server with both args and env vars")
    print()
    print("Examples:")
    print("  # Servers without arguments")
    print("  uv run client.py --servers @modelcontextprotocol/server-sequential-thinking @openbnb/mcp-server-airbnb")
    print()
    print("  # Server with arguments")
    print("  uv run client.py --servers @modelcontextprotocol/server-sequential-thinking @openbnb/mcp-server-airbnb:--ignore-robots-txt")
    print()
    print("  # Server with environment variables")
    print("  uv run client.py --servers @modelcontextprotocol/server-sequential-thinking @mcp-server-nationalparks^NPS_API_KEY=<your-api-key-here>")
    print()
    print("  # Mixed servers (args, env vars, and plain)")
    print("  uv run client.py --servers @modelcontextprotocol/server-sequential-thinking @openbnb/mcp-server-airbnb:--ignore-robots-txt^API_KEY=<your-api-key-here> @mcp-server-nationalparks^NPS_API_KEY=<your-api-key-here>")
    print()
    print("Requirements:")
    print("  - Set OPENAI_API_KEY environment variable")
    print("  - Ensure MCP servers are installed and accessible")
    print()

async def main():
    """Main function to run the multi-server chat demo"""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Multi-Server OpenAI MCP Client")
    parser.add_argument('--servers', nargs='+',
                        help='Server specifications in format: server_path[:args]^[ENV_VAR=value]')
    parser.add_argument('--help-usage', action='store_true',
                        help='Show detailed usage information')
    
    args = parser.parse_args()
    
    # Show detailed usage if requested
    if args.help_usage:
        print_usage()
        return
    
    # Check if servers are provided
    if not args.servers:
        print("❌ Error: --servers argument is required")
        print_usage()
        sys.exit(1)
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key:")
        print("  export OPENAI_API_KEY='your-api-key-here'")
        sys.exit(1)
    
    # Parse server configurations using the utility function
    try:
        server_paths, server_args_list, server_env_list = parse_servers_argument(args)
    except ValueError as e:
        print(f"❌ Error parsing servers: {e}")
        print_usage()
        sys.exit(1)
    
    # Create server configs for display purposes
    server_configs = []
    for i, server_path in enumerate(server_paths):
        server_args = server_args_list[i] if i < len(server_args_list) else []
        server_env = server_env_list[i] if i < len(server_env_list) else {}
        explicit = len(server_args) > 0 or len(server_env) > 0
        server_configs.append((server_path, server_args, server_env, explicit))
    
    print("🚀 Multi-Server OpenAI MCP Client Demo")
    print("=" * 50)
    print(f"📡 Connecting to {len(server_paths)} servers:")
    for i, (server_path, args, env, explicit) in enumerate(server_configs, 1):
        server_display = server_path.split('/')[-1] if '/' in server_path else server_path
        
        # Build display string for args and env
        display_parts = []
        if args:
            display_parts.append(f"args: {args}")
        if env:
            env_display = {k: v[:20] + "..." if len(v) > 20 else v for k, v in env.items()}
            display_parts.append(f"env: {env_display}")
        
        if display_parts:
            details = f" ({', '.join(display_parts)})"
        else:
            details = " (no args, no env)"
            
        print(f"  {i}. {server_display}{details}")
    print()
    
    # Initialize the OpenAI MCP client with enhanced system prompt
    client = OpenAIMCPClient(
        model="gpt-4o", 
        system_prompt=(
            "You are a helpful AI assistant can use multiple tools to help the user."
        )
    )
    
    try:
        # Connect to multiple servers with parsed arguments
        print("⏳ Establishing connections to all servers...")
        
        # Show what we're connecting with
        for server_path, args, env, explicit in server_configs:
            server_display = server_path.split('/')[-1] if '/' in server_path else server_path
            
            details = []
            if args:
                details.append(f"args: {args}")
            if env:
                env_display = {k: v[:20] + "..." if len(v) > 20 else v for k, v in env.items()}
                details.append(f"env: {env_display}")
            
            if details:
                print(f"  🔧 {server_display}: {', '.join(details)}")
            else:
                print(f"  📝 {server_display}: no args, no env")
        
        server_mapping = await client.connect_to_multiple_servers(
            server_paths,
            server_args_list,
            server_env_list
        )
        
        print("✅ Successfully connected to all servers!")
        
        # Display connection summary
        total_tools = sum(len(info["tools"]) for info in server_mapping.values())
        print(f"🔧 Total tools available: {total_tools}")
        print()
        
        print("💡 Try some example queries:")
        if any("sequential-thinking" in server for server in server_paths):
            print("  - 'Help me think through a complex problem step by step'")
        if any("airbnb" in server for server in server_paths):
            print("  - 'Find me accommodations in San Francisco for next weekend'")
        if any("filesystem" in server for server in server_paths):
            print("  - 'List the files in the current directory'")
        if any("calculator" in server for server in server_paths):
            print("  - 'Calculate 15 + 25 * 3'")
        print("  - 'What tools do you have available?'")
        print("  - Type 'quit' to exit or 'reset' to clear conversation history")
        print()
        
        # Start the interactive chat
        await client.chat()
        
    except KeyboardInterrupt:
        print("\n👋 Chat session ended by user")
    except Exception as e:
        logger.error(f"Error in multi-server client: {e}", exc_info=True)
        print(f"❌ Error: {e}")
        print("\nFor troubleshooting:")
        print("1. Ensure all MCP servers are properly installed")
        print("2. Check that your OpenAI API key is valid")
        print("3. Verify server paths are correct")
    finally:
        print("🧹 Cleaning up resources...")
        try:
            await client.cleanup()
        except Exception as cleanup_error:
            logger.error(f"Error during cleanup: {cleanup_error}")

if __name__ == "__main__":
    # Check if help is requested without arguments
    if len(sys.argv) == 1:
        print_usage()
        sys.exit(0)
    
    asyncio.run(main()) 