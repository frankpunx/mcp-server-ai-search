#!/bin/bash

# Post-create script for GitHub Codespaces
echo "🚀 Setting up Azure MCP Retrieval Server development environment..."

# Install Azure Developer CLI
echo "📦 Installing Azure Developer CLI..."
curl -fsSL https://aka.ms/install-azd.sh | bash -s -- --version stable

# Create Python virtual environment
echo "🐍 Creating Python virtual environment..."
python -m venv .venv

# Install Python dependencies in venv
echo "📦 Installing Python dependencies..."
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

# Install MCP Inspector for testing (optional but useful)
echo "🔍 Installing MCP Inspector..."
npm install -g @modelcontextprotocol/inspector

# Configure bash to auto-activate venv
echo "" >> ~/.bashrc
echo "# Auto-activate Python venv" >> ~/.bashrc
echo "if [ -f /workspaces/mcp-server-ai-search/.venv/bin/activate ]; then" >> ~/.bashrc
echo "    source /workspaces/mcp-server-ai-search/.venv/bin/activate" >> ~/.bashrc
echo "fi" >> ~/.bashrc

echo "✅ Setup complete!"
echo ""
echo "📚 Quick Start:"
echo "  1. Activate venv: source .venv/bin/activate"
echo "  2. Run 'python src/main.py' to start the MCP server locally"
echo "  3. Run 'azd auth login' to authenticate with Azure"
echo "  4. Run 'azd up' to deploy to Azure"
echo "  5. Run 'npx @modelcontextprotocol/inspector python src/main.py' to test with MCP Inspector"
echo ""
echo "💡 The venv will be automatically activated in new terminal sessions."
