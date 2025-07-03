# MCP Eval LLM - Development Guide

This guide covers the complete development setup and workflow for the MCP Evaluation Framework, including both CLI and web interface components.

## Project Architecture

```
mcp-eval-llm/
├── src/mcp_eval_llm/        # Core CLI evaluation framework
│   ├── cli/                 # Command-line interface commands
│   ├── evaluators/          # Model evaluation logic
│   └── utils/               # Shared utilities
├── frontend/                # React web UI
│   ├── src/components/      # React components
│   ├── src/pages/           # Page components
│   └── public/              # Static assets
├── backend/                 # Flask API server
│   ├── app.py               # Main API application
│   └── pyproject.toml       # Backend dependencies
├── benchmarks/              # Evaluation benchmarks
├── examples/                # Usage examples
└── docs/                    # Documentation
```

## Quick Setup

### Option 1: Automated Setup (Recommended)
```bash
# Clone and enter the project
git clone <repository-url>
cd mcp-eval-llm

# Run the unified setup script
./setup.sh
```

### Option 2: Manual Setup

#### 1. Core Project Setup
```bash
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install main project dependencies (includes backend API)
uv sync
uv sync --extra dev
```

#### 2. Backend API Setup
```bash
# Dependencies already installed with main project
cd backend
cp .env.example .env  # Configure as needed
```

#### 3. Frontend Setup
```bash
cd frontend
npm install  # or yarn install / pnpm install
npm run type-check  # Verify TypeScript
npm run lint  # Check code quality
```

## Development Workflow

### Running the Complete Application

1. **Start Backend API** (Terminal 1):
   ```bash
   cd backend
   uv run python app.py
   # API available at http://localhost:22358
   ```

2. **Start Frontend UI** (Terminal 2):
   ```bash
   cd frontend
   npm start
   # UI available at http://localhost:22359
   ```

3. **Access the Application**:
   - Web UI: http://localhost:22359
   - API Documentation: http://localhost:22358/api/health
   - Direct CLI: `uv run mcp-eval --help`

### CLI Development

#### Running CLI Commands
```bash
# Generate evaluation tasks
uv run python -m mcp_eval_llm.cli generate-tasks \
  --server filesystem \
  --model-name gpt-4 \
  --num-tasks 10 \
  --output tasks.jsonl

# Verify tasks
uv run python -m mcp_eval_llm.cli verify-tasks \
  --input tasks.jsonl \
  --server filesystem

# Run evaluation
uv run python -m mcp_eval_llm.cli evaluate \
  --task-file tasks.jsonl \
  --model-name gpt-4 \
  --output-dir results/
```

#### Adding New CLI Commands
1. Create new command file in `src/mcp_eval_llm/cli/`
2. Import and register in `src/mcp_eval_llm/cli/__init__.py`
3. Add corresponding API endpoint in `backend/app.py`
4. Create frontend interface in appropriate page component

### Frontend Development

#### Component Structure
```
src/
├── components/
│   ├── Header.tsx           # Navigation header
│   └── Sidebar.tsx          # Navigation sidebar
├── pages/
│   ├── Dashboard.tsx        # Main dashboard
│   ├── TaskGenerator.tsx    # Task generation interface
│   ├── ModelEvaluator.tsx   # Model evaluation interface
│   └── ...                  # Other feature pages
└── App.tsx                  # Main application component
```

#### Adding New Features
1. Create new page component in `src/pages/`
2. Add route in `src/App.tsx`
3. Add navigation item in `src/components/Sidebar.tsx`
4. Create corresponding API endpoints in backend

#### Available Scripts
```bash
npm start             # Development server
npm run dev           # Alias for npm start
npm run build         # Production build
npm run preview       # Test production build locally
npm test              # Run tests
npm run lint          # Lint and fix code
npm run format        # Format code with Prettier
npm run type-check    # TypeScript type checking
npm run analyze       # Bundle size analysis
```

### Backend API Development

#### API Structure
- **Core Operations**: Task generation, verification, evaluation
- **Data Processing**: Format conversion, data splitting
- **File Management**: Upload, download, file listing
- **Job Management**: Progress tracking for long-running operations

#### Adding New Endpoints
1. Add route handler function in `backend/app.py`
2. Update `backend/pyproject.toml` if new dependencies needed
3. Add API documentation in `backend/README.md`
4. Create frontend integration

#### Running Tests
```bash
cd backend
uv run pytest tests/
```

## Package Management with UV

### Installing Dependencies
```bash
# Add a new dependency
uv add package-name

# Add development dependency
uv add --dev package-name

# Install from pyproject.toml
uv sync

# Update dependencies
uv lock --upgrade
```

### Managing Environments
```bash
# Activate project environment
uv shell

# Run commands in environment
uv run python script.py
uv run pytest

# Show environment info
uv pip list
```

## Code Quality

### Formatting and Linting
```bash
# Format code
uv run black src/ backend/
uv run isort src/ backend/

# Lint code
uv run flake8 src/ backend/
uv run mypy src/ backend/

# Run all quality checks
uv run pre-commit run --all-files
```

### Testing

#### Backend Tests
```bash
cd backend
uv run pytest tests/ -v --cov=app
```

#### Frontend Tests
```bash
cd frontend
npm test
```

#### Integration Tests
```bash
# Start backend and frontend, then run:
uv run pytest tests/integration/ -v
```

## Configuration

### Environment Variables

#### Backend (.env)
```bash
FLASK_ENV=development
FLASK_DEBUG=true
FLASK_PORT=22358
CORS_ORIGINS=http://localhost:22359
```

#### Frontend (.env.local)
```bash
REACT_APP_API_URL=http://localhost:22358
REACT_APP_VERSION=1.0.0
```

### API Keys
Store sensitive API keys in `.env` files:
```bash
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
```

## Deployment

### Development Deployment
```bash
# Backend
cd backend
uv run gunicorn app:app --bind 0.0.0.0:22358

# Frontend
cd frontend
npm run build
npx serve -s build -l 3000
```

### Production Considerations
- Use production WSGI server (gunicorn, uvicorn)
- Configure environment variables
- Set up reverse proxy (nginx)
- Enable HTTPS
- Configure logging and monitoring

## Troubleshooting

### Common Issues

#### Port Conflicts
```bash
# Check what's using a port
lsof -i :22358
lsof -i :22359

# Kill process if needed
kill -9 <PID>
```

#### Permission Errors
```bash
# Ensure correct permissions
chmod +x setup.sh frontend/setup.sh backend/setup.sh

# Check file ownership
ls -la uploads/
```

#### Module Import Errors
```bash
# Reinstall project in development mode
uv sync --reinstall

# Check Python path
uv run python -c "import sys; print(sys.path)"
```

#### API Connection Issues
- Verify backend is running on correct port
- Check CORS configuration
- Confirm frontend proxy settings in `package.json`

### Debug Mode

#### Backend Debug
```bash
cd backend
FLASK_DEBUG=1 uv run python app.py
```

#### Frontend Debug
```bash
cd frontend
REACT_APP_DEBUG=1 npm start
```

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Make changes following code quality standards
4. Add tests for new functionality
5. Update documentation
6. Submit pull request

### Code Style
- Python: Follow PEP 8, use black and isort
- TypeScript/React: Follow Prettier and ESLint rules
- Commit messages: Use conventional commits format

## Support

- **Documentation**: Check `docs/` directory
- **Issues**: Create GitHub issue for bugs/feature requests
- **Discussions**: Use GitHub discussions for questions 