#!/usr/bin/env python3
"""
Multi-Server OpenAI MCP Client Example

This example demonstrates how to use the enhanced OpenAI MCP client
to connect to multiple MCP servers simultaneously and interact with
tools from all servers in a single chat session.

Usage:
    python client.py <server1> <server2> [server3] ...

Example:
    python client.py @modelcontextprotocol/server-sequential-thinking @openbnb/mcp-server-airbnb

Requirements:
    - OpenAI API key set in environment (OPENAI_API_KEY)
    - MCP servers installed and accessible
"""

import asyncio
import sys
import os
import logging

# Add the parent directories to the path so we can import our modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
src_dir = os.path.join(parent_dir, 'src')
sys.path.insert(0, src_dir)

from mcp_eval_llm.client.openai_client import OpenAIMCPClient

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
    print("  uv run client.py <server1> [server2] [server3] ...")
    print("  uv run client.py <server1:args> [server2:args] [server3:args] ...")
    print()
    print("Server Format:")
    print("  server_path              - Server with no arguments")
    print("  server_path:arg1,arg2    - Server with arguments (comma-separated)")
    print("  server_path:             - Server with empty arguments")
    print()
    print("Examples:")
    print("  # Servers without arguments")
    print("  uv run client.py @modelcontextprotocol/server-sequential-thinking @openbnb/mcp-server-airbnb")
    print()
    print("  # Server with arguments")
    print("  uv run client.py @modelcontextprotocol/server-sequential-thinking @openbnb/mcp-server-airbnb:--ignore-robots-txt")
    print()
    print("  # Multiple arguments")
    print("  uv run client.py @openbnb/mcp-server-airbnb:--ignore-robots-txt,--debug ../../mcp_servers/filesystem/server.py")
    print()
    print("  # Mixed servers (some with args, some without)")
    print("  uv run client.py @openbnb/mcp-server-airbnb:--ignore-robots-txt @modelcontextprotocol/server-sequential-thinking")
    print()
    print("Requirements:")
    print("  - Set OPENAI_API_KEY environment variable")
    print("  - Ensure MCP servers are installed and accessible")
    print()

async def main():
    """Main function to run the multi-server chat demo"""
    
    # Check for help flag
    if len(sys.argv) < 2 or sys.argv[1] in ['-h', '--help', 'help']:
        print_usage()
        sys.exit(0 if len(sys.argv) < 2 else 0)
    
    if len(sys.argv) < 3:
        print("❌ Error: At least 2 servers are required for multi-server demo")
        print_usage()
        sys.exit(1)
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key:")
        print("  export OPENAI_API_KEY='your-api-key-here'")
        sys.exit(1)
    
    # Parse server:args format
    server_configs = []
    for arg in sys.argv[1:]:
        if ':' in arg:
            # Format: server:arg1,arg2 or server: (empty args)
            server_path, args_str = arg.split(':', 1)
            if args_str:
                server_args = [arg.strip() for arg in args_str.split(',') if arg.strip()]
            else:
                server_args = []  # Explicitly empty
            server_configs.append((server_path, server_args, True))  # True = explicit args
        else:
            # Format: server (no args specified)
            server_configs.append((arg, [], False))  # False = no args
    
    server_paths = [config[0] for config in server_configs]
    
    print("🚀 Multi-Server OpenAI MCP Client Demo")
    print("=" * 50)
    print(f"📡 Connecting to {len(server_paths)} servers:")
    for i, (server_path, args, explicit) in enumerate(server_configs, 1):
        server_display = server_path.split('/')[-1] if '/' in server_path else server_path
        if explicit:
            args_display = f" (args: {args})" if args else " (no args)"
        else:
            args_display = " (no args)"
        print(f"  {i}. {server_display}{args_display}")
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
        
        # Prepare server arguments directly from command line parsing
        server_args_list = []
        for server_path, args, explicit in server_configs:
            server_args_list.append(args)
            if args:
                print(f"  🔧 Args for {server_path.split('/')[-1]}: {args}")
            else:
                print(f"  📝 No args for {server_path.split('/')[-1]}")
        
        server_mapping = await client.connect_to_multiple_servers(
            server_paths,
            server_args_list
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
    # Ensure we're running with Python 3.8+
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required")
        sys.exit(1)
    
    asyncio.run(main()) 