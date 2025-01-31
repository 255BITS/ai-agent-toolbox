# Run the 05.mcp_client.py to test this
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Addition Server")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

