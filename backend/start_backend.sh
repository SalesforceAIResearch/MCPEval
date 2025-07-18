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
