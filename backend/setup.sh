#!/bin/bash

# Backend Setup Script for MCP Eval API
# This script sets up the Flask backend with uv package management

set -e

echo "🚀 Setting up MCP Eval API Backend..."

# Ensure Node.js environment is available (passed from main setup)
if [ ! -z "$NVM_DIR" ]; then
    echo "✅ Using Node.js environment from main setup"
    export NVM_DIR="$NVM_DIR"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    [ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"
else
    echo "⚠️  Node.js environment not passed from main setup, trying to load..."
    # Try to load nvm if it exists
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    [ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"
fi

# Verify Node.js is available for MCP servers
if command -v node &> /dev/null && command -v npx &> /dev/null; then
    echo "✅ Node.js and npx available for MCP servers"
    echo "   Node.js: $(node --version)"
    echo "   npx: $(npx --version)"
else
    echo "⚠️  Node.js/npx not found. MCP npm servers may not work properly."
    echo "   Make sure to run the main setup.sh script first."
fi

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
PROJECT_ROOT=$(dirname $PWD)
echo currently in $PWD
echo copying environment template in $PROJECT_ROOT
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo "⚙️  Setting up environment configuration in $PROJECT_ROOT ..."
    cp $PROJECT_ROOT/.env.template $PROJECT_ROOT/.env
    echo "📝 Created .env file from template. Please review and update as needed."
else
    echo "✅ Environment file already exists"
fi

# Create uploads directory
mkdir -p ../uploads
echo "📁 Created uploads directory"

# Create a startup script that ensures Node.js is in PATH
echo "📝 Creating backend startup script with Node.js environment..."
cat > start_backend.sh << 'EOF'
#!/bin/bash

# Backend startup script with Node.js environment
# This ensures the backend server can find npx for MCP servers

# Load Node.js environment
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"

# Add Node.js to PATH if available
if [ -d "$HOME/.nvm/versions/node" ]; then
    LATEST_NODE=$(ls -1 "$HOME/.nvm/versions/node" | sort -V | tail -n1)
    export PATH="$HOME/.nvm/versions/node/$LATEST_NODE/bin:$PATH"
fi

# Verify Node.js environment
echo "🔍 Backend Node.js environment:"
echo "   Node.js: $(node --version 2>/dev/null || echo 'Not found')"
echo "   npx: $(npx --version 2>/dev/null || echo 'Not found')"
echo "   PATH includes: $(echo $PATH | tr ':' '\n' | grep -E '(nvm|node)' | head -3 | tr '\n' ' ')"

# Start the backend server
echo "🚀 Starting MCP Eval Backend Server..."
uv run python app.py
EOF

chmod +x start_backend.sh
echo "✅ Created start_backend.sh script"

echo "🎉 Backend setup complete!"
echo ""
echo "Next steps:"
echo "  1. Review and update .env file if needed"
echo "  2. Start the development server:"
echo "     Option A: ./start_backend.sh  (recommended - includes Node.js environment)"
echo "     Option B: uv run python app.py (may not find npx for MCP servers)"
echo "  3. API will be available at http://localhost:22358"
echo "  4. View API health check: curl http://localhost:22358/api/health"
echo ""
echo "🔧 For MCP servers to work properly:"
echo "   - Use ./start_backend.sh to start the server"
echo "   - This ensures npx is available for npm-based MCP servers" 
