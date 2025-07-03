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
    # Initialize and run the server
    mcp.run(transport='stdio')