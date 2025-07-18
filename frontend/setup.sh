#!/bin/bash

# Frontend Setup Script for MCP Eval UI
# This script sets up the React frontend with modern development tools

set -e

echo "🚀 Setting up MCP Eval UI Frontend..."

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

# Load Node.js environment (may already be available from main setup)
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"

# Check if Node.js is already available (from main setup)
if command -v node &> /dev/null && command -v npm &> /dev/null; then
    NODE_VERSION=$(node --version | cut -d'v' -f2)
    REQUIRED_VERSION="18.0.0"
    
    if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$NODE_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then
        echo "✅ Node.js $NODE_VERSION already available (from main setup)"
    else
        echo "⚠️  Node.js version $NODE_VERSION is too old. Required: $REQUIRED_VERSION+"
        echo "🔄 Installing Node.js 18..."
        install_nodejs
    fi
else
    echo "⚠️  Node.js not found. Installing Node.js environment..."
    
    # Check if nvm is installed
    if ! command -v nvm &> /dev/null; then
        echo "❌ nvm is not installed. Installing it now..."
        install_nvm
    fi
    
    # Install Node.js
    echo "❌ Node.js is not installed. Installing Node.js 18..."
    install_nodejs
fi

# Verify installation
echo "🔍 Verifying Node.js installation..."
node --version
npm --version

# Check for npm vs yarn vs pnpm
PACKAGE_MANAGER="npm"
if command -v yarn &> /dev/null; then
    PACKAGE_MANAGER="yarn"
    echo "📦 Using Yarn package manager"
elif command -v pnpm &> /dev/null; then
    PACKAGE_MANAGER="pnpm"
    echo "📦 Using pnpm package manager"
else
    echo "📦 Using npm package manager"
fi

# Install Node.js dependencies
echo "🔧 Installing frontend dependencies..."
case $PACKAGE_MANAGER in
    "yarn")
        yarn install
        ;;
    "pnpm")
        pnpm install
        ;;
    *)
        npm install
        ;;
esac

# Install additional dependencies for markdown viewer
echo "📝 Installing markdown viewer dependencies..."
case $PACKAGE_MANAGER in
    "yarn")
        yarn add react-markdown remark-gfm rehype-highlight
        ;;
    "pnpm")
        pnpm add react-markdown remark-gfm rehype-highlight
        ;;
    *)
        npm install react-markdown remark-gfm rehype-highlight
        ;;
esac

# Set up environment variables
if [ ! -f ".env.local" ]; then
    echo "⚙️  Setting up environment configuration..."
    cat > .env.local << EOF
# Frontend Environment Variables
REACT_APP_API_URL=http://localhost:22358
REACT_APP_VERSION=1.0.0
REACT_APP_ENVIRONMENT=development
GENERATE_SOURCEMAP=true
EOF
    echo "📝 Created .env.local with default configuration"
else
    echo "✅ Environment file already exists"
fi

# Run TypeScript type checking
echo "🔍 Running TypeScript type check..."
if ! npm run type-check; then
    echo "⚠️  TypeScript type errors found. Run 'npm run type-check' to see details."
fi

# Run linting
echo "🧹 Running code quality checks..."
if ! npm run lint; then
    echo "⚠️  Linting issues found. Run 'npm run lint' to fix automatically."
fi

# Check if build works
echo "🏗️  Testing production build..."
if npm run build > /dev/null 2>&1; then
    echo "✅ Production build successful"
    rm -rf build  # Clean up test build
else
    echo "⚠️  Production build failed. Check for errors with 'npm run build'"
fi

echo ""
echo "🎉 Frontend setup complete!"
echo ""
echo "📋 Available Commands:"
echo "  npm start         # Start development server"
echo "  npm run build     # Create production build"
echo "  npm test          # Run tests"
echo "  npm run lint      # Lint and fix code"
echo "  npm run format    # Format code with Prettier"
echo "  npm run type-check # Check TypeScript types"
echo ""
echo "🚀 Next steps:"
echo "  1. Start the development server: npm start"
echo "  2. Open http://localhost:22359 in your browser"
echo "  3. Make sure the backend API is running on http://localhost:22358"
echo ""
echo "💡 Pro tips:"
echo "  • Use 'npm run dev' as an alias for 'npm start'"
echo "  • Run 'npm run preview' to test production build locally"
echo "  • Check .env.local for environment configuration" 