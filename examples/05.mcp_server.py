"""Minimal MCP server used by :mod:`examples.05.mcp_client`."""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Addition Server")


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers."""

    return a + b


if __name__ == "__main__":
    mcp.run()
