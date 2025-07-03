#!/bin/bash

# MCP Eval LLM - Complete Setup Script
# This script sets up both frontend and backend components

set -e

echo "🚀 Setting up MCP Eval LLM Project..."
echo ""

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

# Install main project dependencies using uv
echo "📦 Setting up main project..."
if ! command -v uv &> /dev/null; then
    echo "Installing uv package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

echo "Installing main project dependencies (includes backend API)..."
uv sync

echo "Installing development dependencies..."
uv sync --extra dev

echo "Setting up mcp-eval CLI command..."
export PATH="$PWD/.venv/bin:$PATH"

echo "✅ Main project setup complete"
echo "✅ mcp-eval CLI command is now available"
echo ""

# Setup Backend
echo "🔧 Setting up Backend API..."
cd backend
chmod +x setup.sh
./setup.sh
cd ..

echo ""

# Setup Frontend
echo "🎨 Setting up Frontend UI..."
cd frontend
chmod +x setup.sh
./setup.sh
cd ..

echo ""
echo "🎉 Complete setup finished!"
echo ""
echo "📋 Quick Start Guide:"
echo ""
echo "🔧 MCP Eval CLI Usage:"
echo "   mcp-eval --help                    # Show all available commands"
echo "   mcp-eval auto --help               # Show auto evaluation options"
echo "   ./benchmarks/special_calculator/auto.sh  # Run special calculator evaluation"
echo ""
echo "1. Start the backend API:"
echo "   cd backend && uv run python app.py"
echo ""
echo "2. Start the frontend (in a new terminal):"
echo "   cd frontend && npm start"
echo ""
echo "3. Access the application:"
echo "   • Frontend: http://localhost:22359"
echo "   • Backend API: http://localhost:22358"
echo "   • API Health Check: curl http://localhost:22358/api/health"
echo ""
echo "📖 Documentation:"
echo "   • Backend API: backend/README.md"
echo "   • Frontend UI: frontend/README.md"
echo "   • Main Project: README.md"
echo ""
echo "💡 To make mcp-eval available in new terminals, run:"
echo "   export PATH=\"\$PWD/.venv/bin:\$PATH\"" 