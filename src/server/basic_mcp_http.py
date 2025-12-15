"""
Basic MCP Server with FastMCP (HTTP Streamable Transport)

Run locally:     uv run src/server/basic_mcp_http.py
Debug:           F5 in VS Code
MCP Inspector:   npx @modelcontextprotocol/inspector http://localhost:8000/mcp
"""

import logging
import os
from typing import Annotated

from dotenv import load_dotenv
from fastmcp import FastMCP

load_dotenv(override=True)

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("BasicMCP")

# Initialize the MCP server
mcp = FastMCP("Basic MCP Server")


@mcp.tool
async def hello(
    name: Annotated[str, "Name to greet"],
) -> str:
    """Say hello to someone."""
    logger.info(f"Hello called with name: {name}")
    return f"Hello, {name}! Welcome to the MCP Server."


@mcp.tool
async def echo(
    message: Annotated[str, "Message to echo back"],
) -> str:
    """Echo back the provided message."""
    logger.info(f"Echo called with message: {message}")
    return f"Echo: {message}"


@mcp.tool
async def add_numbers(
    a: Annotated[float, "First number"],
    b: Annotated[float, "Second number"],
) -> float:
    """Add two numbers together."""
    result = a + b
    logger.info(f"Add called: {a} + {b} = {result}")
    return result


@mcp.resource("resource://info")
async def get_server_info() -> str:
    """Get information about the MCP server."""
    return "Basic MCP Server v1.0.0 - HTTP Streamable Transport"


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    logger.info(f"Starting MCP Server on http://{host}:{port}/mcp")
    mcp.run(transport="streamable-http", host=host, port=port)
