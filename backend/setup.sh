#!/bin/bash

# Backend Setup Script for MCP Eval API
# This script sets up the Flask backend with uv package management

set -e

echo "🚀 Setting up MCP Eval API Backend..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Source the shell configuration to make uv available
    export PATH="$HOME/.local/bin:$PATH"
    
    if ! command -v uv &> /dev/null; then
        echo "❌ Failed to install uv. Please install manually: https://docs.astral.sh/uv/"
        exit 1
    fi
fi

echo "✅ uv package manager available"

# Backend dependencies are managed by the main project
echo "📦 Backend dependencies managed by main project's virtual environment"
echo "✅ Using shared virtual environment from project root"

# Set up environment variables
if [ ! -f ".env" ]; then
    echo "⚙️  Setting up environment configuration..."
    cp .env.example .env
    echo "📝 Created .env file from template. Please review and update as needed."
else
    echo "✅ Environment file already exists"
fi

# Create uploads directory
mkdir -p ../uploads
echo "📁 Created uploads directory"

echo "🎉 Backend setup complete!"
echo ""
echo "Next steps:"
echo "  1. Review and update .env file if needed"
echo "  2. Start the development server: uv run python app.py"
echo "  3. API will be available at http://localhost:22358"
echo "  4. View API health check: curl http://localhost:22358/api/health" 