# server.py
from mcp.server.fastmcp import FastMCP

# Create a basic MCP server
mcp = FastMCP("Demo")


# Add an addition tool
@mcp.tool()
def special_add(a: int, b: int) -> int:
    """A special addition tool that adds two numbers and doubles the result"""
    return (a + b) * 2

@mcp.tool()
def special_subtract(a: int, b: int) -> int:
    """A special subtraction tool that subtracts two numbers and halves the result"""
    return (a - b) / 2

@mcp.tool()
def special_multiply(a: int, b: int) -> int:
    """A special multiplication tool that multiplies two numbers and doubles the result"""
    return (a * b) * 2

@mcp.tool()
def special_divide(a: int, b: int) -> int:  
    """A special division tool that divides two numbers and halves the result"""
    return (a / b) / 2

@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"    

if __name__ == "__main__":
    import argparse
    import os
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Special Calculator MCP Server")
    parser.add_argument(
        "--transport", 
        choices=["stdio", "sse", "streamable-http"], 
        default="stdio",
        help="Transport protocol to use (default: stdio)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000,
        help="Port for HTTP transport (default: 8000)"
    )
    
    args = parser.parse_args()
    
    # Allow environment variables to override
    transport = os.environ.get("MCP_TRANSPORT", args.transport)
    port = int(os.environ.get("PORT", args.port))
    
    print(f"Starting MCP server with transport: {transport}")
    
    if transport == "streamable-http":
        # Note: FastMCP currently defaults to port 8000 for streamable-http transport
        actual_port = 8000  # FastMCP hardcoded default
        print(f"🚀 Starting Special Calculator MCP Server on HTTP")
        print(f"   Server URL: http://127.0.0.1:{actual_port}/mcp")
        print(f"   Available tools: special_add, special_subtract, special_multiply, special_divide")
        print(f"   Test with: uv run test_http_mcp.py")
        if port != 8000:
            print(f"   Note: --port {port} requested, but FastMCP uses port {actual_port}")
    
    # Initialize and run the server
    mcp.run(transport=transport)