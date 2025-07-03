# MCPEval - Backend API

Flask-based REST API server that provides a web interface to the MCPEval CLI commands.

## Features

- **REST API Endpoints** for all CLI commands
- **Real-time Job Tracking** with progress monitoring
- **File Upload/Download** capabilities
- **CORS Support** for frontend integration
- **System Monitoring** and health checks
- **Asynchronous Task Processing**

## Installation

### Prerequisites

- Python 3.8+
- [uv](https://docs.astral.sh/uv/) package manager

### Setup

1. **Install uv (if not already installed):**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Backend dependencies are included in main project:**
   ```bash
   # From project root
   uv sync --extra dev
   ```

3. **Set up environment variables (optional):**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## Running the Server

### Development Mode
```bash
uv run python app.py
```
The server will start on `http://localhost:22358` with debug mode enabled.

### Production Mode
```bash
uv run gunicorn --bind 0.0.0.0:22358 --workers 4 app:app
```

## API Endpoints

### Core Operations
- `POST /api/generate-tasks` - Generate evaluation tasks
- `POST /api/verify-tasks` - Verify tasks against servers
- `POST /api/evaluate` - Run model evaluations
- `POST /api/analyze` - Analyze results vs ground truth
- `POST /api/judge` - LLM-powered evaluation
- `POST /api/judge-rubric` - Analyze LLM judgments

### Data Processing
- `POST /api/convert-data` - Convert data formats
- `POST /api/split-data` - Split datasets

### File Management
- `POST /api/upload` - Upload files
- `GET /api/download/<filename>` - Download files
- `GET /api/files` - List available files

### System Information
- `GET /api/health` - Health check
- `GET /api/servers` - List available MCP servers
- `GET /api/models` - List available models
- `GET /api/system-info` - System metrics

### Job Management
- `GET /api/job-status/<job_id>` - Get job progress and logs

## Example Usage

### Generate Tasks
```bash
curl -X POST http://localhost:22358/api/generate-tasks \
  -H "Content-Type: application/json" \
  -d '{
    "servers": ["filesystem", "brave-search"],
    "model_name": "gpt-4",
    "num_tasks": 10,
    "output_path": "generated_tasks.jsonl"
  }'
```

### Check Job Status
```bash
curl http://localhost:22358/api/job-status/{job_id}
```

## Configuration

### Backend Configuration File

The backend can be configured using a `backend.yaml` file placed in the same directory as `app.py`. If this file doesn't exist, the application will use default settings.

**Example `backend.yaml`:**
```yaml
# Application settings
app:
  debug: true
  host: "0.0.0.0"
  port: 22358

# Directory paths (relative to the config file)
paths:
  root_directory: ".."
  uploads_directory: "../uploads"
  temp_directory: "/tmp"
  logs_directory: "../logs"

# Default settings for task generation and evaluation
defaults:
  generation_model: "gpt-4"
  judge_model: "gpt-4"
  num_tasks: 10
  max_concurrent: 5
  train_ratio: 0.8
  random_seed: 42

# Environment variables to set for CLI commands
environment:
  PYTHONPATH: "${root_directory}/src"
  # OPENAI_API_KEY: "your-key-here"
  # ANTHROPIC_API_KEY: "your-key-here"
```

**Key Configuration Options:**
- **`paths.root_directory`**: Working directory for CLI commands (should point to project root)
- **`app.host`** and **`app.port`**: Server binding configuration
- **`defaults`**: Default values used in API endpoints when parameters aren't provided
- **`environment`**: Environment variables set when running CLI commands

The configuration supports variable substitution using `${variable_name}` syntax.

### Project Dependencies

The backend shares dependencies with the main project. Make sure the main project is properly set up:

```bash
# From project root
uv sync --extra dev
```

## Development

### Running Tests
```bash
uv run pytest tests/
```

### Code Formatting
```bash
uv run black app.py
uv run isort app.py
uv run flake8 app.py
```

### Project Structure
```
backend/
├── app.py              # Main Flask application
├── README.md          # This file
├── .env.example       # Environment variables template
├── setup.sh           # Backend setup script
└── tests/             # Test files

Note: Dependencies are managed in the main project's pyproject.toml
```

## Error Handling

The API returns JSON error responses:

```json
{
  "error": "Error description",
  "status": "failed"
}
```

Common HTTP status codes:
- `200` - Success
- `400` - Bad Request (invalid parameters)
- `404` - Not Found (job/file not found)
- `500` - Internal Server Error

## Security Considerations

- CORS is enabled for frontend integration
- File uploads are restricted to safe directories
- CLI commands run with current user permissions
- No authentication implemented (add as needed)

## Troubleshooting

### Port Already in Use
```bash
# Find process using port 22358
lsof -i :22358
# Kill process if needed
kill -9 <PID>
```

### Permission Errors
Ensure the backend has read/write access to:
- Upload directory (`../uploads`)
- Output directories
- MCP evaluation CLI modules

### Module Import Errors
Make sure the main project is installed:
```bash
cd ..
pip install -e .
``` 