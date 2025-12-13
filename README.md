# Azure MCP Retrieval Server

A Model Context Protocol (MCP) server that provides document search and Q&A capabilities using Azure AI Search and Azure OpenAI.

## Prerequisites

- [Azure Developer CLI (azd)](https://aka.ms/install-azd)
- [Azure CLI](https://docs.microsoft.com/cli/azure/install-azure-cli)
- Python 3.11+
- [Docker](https://docs.docker.com/get-docker/) (for local container testing)

## Quick Start (GitHub Codespaces)

This project is optimized for GitHub Codespaces. Simply open in Codespaces and the devcontainer will automatically:
- Install Azure Developer CLI
- Install Python dependencies
- Set up the development environment

### 1. Local Development

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the MCP server locally with STDIO (for MCP clients)
MCP_TRANSPORT=stdio python src/main.py

# Or run with HTTP mode (for testing HTTP endpoints)
MCP_TRANSPORT=http python src/main.py
# Then visit: http://localhost:8000/health

# Or use VS Code tasks (press Ctrl+Shift+P → "Tasks: Run Task"):
# - "Run MCP Server (Local/STDIO)" - for MCP client testing
# - "Run MCP Server (HTTP)" - for HTTP endpoint testing
# - "Test with MCP Inspector" - opens MCP Inspector GUI
```

### 2. Test with MCP Inspector

```bash
npx @modelcontextprotocol/inspector python src/main.py
```

### 3. Deploy to Azure

```bash
# Login to Azure
azd auth login

# Provision infrastructure and deploy
azd up

# Just deploy code changes
azd deploy
```

## Available Tools

- `greet(name)` - A simple greeting tool to test the server

## Project Structure

```
azure-mcp-retrieval/
├── .devcontainer/          # GitHub Codespaces configuration
├── src/                    # Python source code
│   └── main.py            # MCP server entry point
├── infra/                  # Azure infrastructure (Bicep)
│   ├── main.bicep         # Main infrastructure template
│   ├── resources.bicep    # Azure resources definition
│   └── main.parameters.json
├── Dockerfile             # Container image definition
├── azure.yaml             # Azure Developer CLI configuration
└── requirements.txt       # Python dependencies
```

## Azure Resources

This project deploys:
- **Azure Container Apps**: Hosts the MCP server with scale-to-zero
- **Azure Container Registry**: Stores Docker images
- **Azure AI Search**: Vector database for document retrieval (to be configured)
- **Azure OpenAI**: Embeddings and chat completions (to be configured)
- **Log Analytics**: Monitoring and diagnostics

## Development Status

🚧 **In Development** - Currently implementing basic features iteratively.

## Next Steps

- Add Azure AI Search integration
- Implement document retrieval tools
- Add authentication layer
- Configure Azure OpenAI deployments

## Resources

- [Azure Developer CLI Documentation](https://learn.microsoft.com/azure/developer/azure-developer-cli/)
- [Model Context Protocol Specification](https://spec.modelcontextprotocol.io/)
- [Azure AI Search Documentation](https://learn.microsoft.com/azure/search/)
