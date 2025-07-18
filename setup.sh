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

# Function to install nvm
install_nvm() {
    echo "📦 Installing nvm (Node Version Manager)..."
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
    
    # Load nvm
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    [ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"
    
    echo "✅ nvm installed successfully"
}

# Function to install Node.js 18
install_nodejs() {
    echo "📦 Installing Node.js 18..."
    nvm install 18
    nvm use 18
    nvm alias default 18
    echo "✅ Node.js 18 installed and set as default"
}

# Install Node.js first (required for MCP servers)
echo "🔧 Setting up Node.js environment (required for MCP servers)..."

# Check if nvm is installed
if ! command -v nvm &> /dev/null; then
    # Try to load nvm if it exists but isn't in PATH
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    [ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"
    
    if ! command -v nvm &> /dev/null; then
        echo "❌ nvm is not installed. Installing it now..."
        install_nvm
    fi
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Installing Node.js 18..."
    install_nodejs
else
    # Check Node.js version
    NODE_VERSION=$(node --version | cut -d'v' -f2)
    REQUIRED_VERSION="18.0.0"

    if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$NODE_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then 
        echo "❌ Node.js version $NODE_VERSION is too old. Required: $REQUIRED_VERSION+"
        echo "🔄 Installing Node.js 18..."
        install_nodejs
    else
        echo "✅ Node.js version $NODE_VERSION is compatible"
    fi
fi

# Verify Node.js installation
echo "🔍 Verifying Node.js installation..."
node --version
npm --version
npx --version

# Export Node.js paths for the rest of the setup
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"

# Add Node.js to PATH for the rest of this script
if [ -d "$HOME/.nvm/versions/node" ]; then
    # Find the latest Node.js version and add it to PATH
    LATEST_NODE=$(ls -1 "$HOME/.nvm/versions/node" | sort -V | tail -n1)
    export PATH="$HOME/.nvm/versions/node/$LATEST_NODE/bin:$PATH"
    echo "✅ Node.js environment configured for setup"
fi

echo ""

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

# Setup Backend (now with Node.js environment available)
echo "🔧 Setting up Backend API..."
cd backend
chmod +x setup.sh
# Pass Node.js environment to backend setup
NVM_DIR="$NVM_DIR" PATH="$PATH" ./setup.sh
cd ..

echo ""

# Setup Frontend (Node.js already installed, but still run for npm dependencies)
echo "🎨 Setting up Frontend UI..."
cd frontend
chmod +x setup.sh
# Pass Node.js environment to frontend setup
NVM_DIR="$NVM_DIR" PATH="$PATH" ./setup.sh
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
echo ""
echo "🔧 For MCP servers to work properly, ensure Node.js is in PATH:"
echo "   export NVM_DIR=\"\$HOME/.nvm\""
echo "   [ -s \"\$NVM_DIR/nvm.sh\" ] && \\. \"\$NVM_DIR/nvm.sh\"" 