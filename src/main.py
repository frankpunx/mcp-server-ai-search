"""
Azure MCP Retrieval Server
Provides document search and Q&A capabilities via Model Context Protocol
"""
import os
from mcp.server.fastmcp import FastMCP
from starlette.responses import JSONResponse
from starlette.requests import Request

# Initialize MCP server
mcp = FastMCP("azure-retrieval-server")

# ==================== MCP Tools ====================


@mcp.tool()
async def greet(name: str = "World") -> str:
    """
    A simple greeting tool to test the MCP server.

    Args:
        name: The name to greet (default: "World")

    Returns:
        A friendly greeting message
    """
    return f"Hello, {name}! Welcome to the Azure MCP Retrieval Server."

# ==================== Health Check ====================


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request):
    """Health check endpoint for Azure Container Apps"""
    return JSONResponse({"status": "healthy", "service": "azure-retrieval-server"})

# ==================== Server Entry Point ====================

if __name__ == "__main__":
    # Default to STDIO for local development
    # Set MCP_TRANSPORT=http for Azure deployment
    transport_mode = os.getenv("MCP_TRANSPORT", "stdio").lower()

    if transport_mode == "http":
        # HTTP mode for Azure deployment
        print("🌐 Starting MCP server in HTTP mode (Azure)...")
        mcp.run(transport="streamable-http")
    else:
        # STDIO mode for local development with Inspector
        print("🚀 Starting MCP server...")
        mcp.run(transport="stdio")
