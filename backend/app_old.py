from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import subprocess
import json
import os
import threading
import time
from datetime import datetime
import tempfile
import shutil
from pathlib import Path
import uuid
import yaml
import argparse
import asyncio
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load configuration
def load_config(config_path=None):
    """Load configuration from yaml file"""
    if config_path is None:
        config_path = Path(__file__).parent / 'backend.yaml'
    else:
        config_path = Path(config_path)
    
    # Default configuration as fallback
    default_config = {
        'app': {'debug': True, 'host': '0.0.0.0', 'port': 22358},
        'paths': {'root_directory': '..', 'uploads_directory': '../uploads', 'temp_directory': '/tmp', 'logs_directory': '../logs'},
        'defaults': {'generation_model': 'gpt-4', 'judge_model': 'gpt-4', 'num_tasks': 10, 'max_concurrent': 5, 'train_ratio': 0.8, 'random_seed': 42},
        'jobs': {'max_concurrent_jobs': 3, 'cleanup_interval': 3600, 'max_retention': 86400},
        'files': {'max_upload_size': 100, 'allowed_extensions': ['.jsonl', '.json', '.txt', '.csv', '.yaml', '.yml']},
        'environment': {'PYTHONPATH': '${root_directory}/src'}
    }
    
    if not config_path.exists():
        print(f"Warning: Configuration file not found at {config_path}")
        print("Using default configuration. Consider creating a config file for custom settings.")
        config = default_config
    else:
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Merge with defaults to ensure all required keys exist
            for section, defaults in default_config.items():
                if section not in config:
                    config[section] = defaults
                elif isinstance(defaults, dict):
                    for key, default_value in defaults.items():
                        if key not in config[section]:
                            config[section][key] = default_value
                            
            print(f"Configuration loaded successfully from {config_path}")
        except Exception as e:
            print(f"Error loading configuration from {config_path}: {e}")
            print("Using default configuration.")
            config = default_config
    
    # Resolve relative paths
    config_dir = config_path.parent
    for key, value in config.get('paths', {}).items():
        if isinstance(value, str) and not os.path.isabs(value):
            config['paths'][key] = str(config_dir / value)
    
    # Handle workspace variable substitution in paths
    if 'workspace' in config and 'paths' in config:
        workspace_root = config['workspace'].get('root', '.')
        # Resolve workspace root relative to config directory
        if not os.path.isabs(workspace_root):
            workspace_root = str(config_dir / workspace_root)
        
        # Create workspace root directory if it doesn't exist
        workspace_root_path = Path(workspace_root)
        try:
            workspace_root_path.mkdir(parents=True, exist_ok=True)
            print(f"Workspace root directory ensured: {workspace_root}")
        except Exception as e:
            print(f"Warning: Could not create workspace root directory {workspace_root}: {e}")
        
        # Update the workspace root in config to use the resolved absolute path
        config['workspace']['root'] = workspace_root
        
        # Substitute workspace variables in paths
        for key, value in config['paths'].items():
            if isinstance(value, str) and '${workspace.root}' in value:
                config['paths'][key] = value.replace('${workspace.root}', workspace_root)
    
    # Set environment variables
    for key, value in config.get('environment', {}).items():
        if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
            # Handle variable substitution like ${root_directory}
            var_name = value[2:-1]
            if var_name in config.get('paths', {}):
                value = config['paths'][var_name]
        os.environ[key] = str(value)
    
    return config

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='MCP Eval LLM Backend Server',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python app.py                           # Use default backend.yaml
  python app.py --config my_config.yaml  # Use custom config file
  uv run app.py --config production.yaml # Run with uv and custom config
        """
    )
    
    parser.add_argument(
        '--config', '-c',
        type=str,
        help='Path to configuration YAML file (default: backend.yaml in the same directory as app.py)'
    )
    
    return parser.parse_args()

# Parse command line arguments
args = parse_args()

# Load configuration at startup
config = load_config(args.config)

app = Flask(__name__)
CORS(app)

# Store for tracking job progress
job_progress = {}
job_logs = {}
job_metadata = {}  # Store additional job information like type, title, etc.

# Global MCP client instance
mcp_client = None

def run_cli_command(command, job_id=None, capture_output=True):
    """Run a CLI command and optionally track progress"""
    try:
        if job_id:
            job_progress[job_id] = {'status': 'running', 'progress': 0}
            job_logs[job_id] = []

        # Get root directory from config
        root_dir = config.get('paths', {}).get('root_directory', '..')

        # Run the command
        if capture_output:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=root_dir)
            output = result.stdout
            error = result.stderr
            
            if job_id:
                if result.returncode == 0:
                    job_progress[job_id] = {'status': 'completed', 'progress': 100}
                    job_logs[job_id].append(f"Command completed successfully: {output}")
                else:
                    job_progress[job_id] = {'status': 'failed', 'progress': 100}
                    job_logs[job_id].append(f"Command failed: {error}")
            
            return {
                'success': result.returncode == 0,
                'output': output,
                'error': error,
                'returncode': result.returncode
            }
        else:
            # For long-running commands, run in background but wait for completion
            result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=root_dir)
            output = result.stdout
            error = result.stderr
            
            if job_id:
                if result.returncode == 0:
                    job_progress[job_id] = {'status': 'completed', 'progress': 100}
                    job_logs[job_id].append("Command completed successfully")
                    if output:
                        job_logs[job_id].append(f"Output: {output}")
                else:
                    job_progress[job_id] = {'status': 'failed', 'progress': 100}
                    job_logs[job_id].append(f"Command failed with exit code {result.returncode}")
                    if error:
                        job_logs[job_id].append(f"Error: {error}")
            
            return {
                'success': result.returncode == 0,
                'output': output,
                'error': error,
                'returncode': result.returncode
            }
    
    except Exception as e:
        if job_id:
            job_progress[job_id] = {'status': 'failed', 'progress': 100}
            job_logs[job_id].append(f"Error: {str(e)}")
        return {'success': False, 'error': str(e)}

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/api/mcp/status', methods=['GET'])
def mcp_status():
    """Get MCP client status"""
    global mcp_client
    
    try:
        if mcp_client:
            # Check if we can get tools from the client
            def get_tools():
                async def _get_tools():
                    return await mcp_client.get_all_tools()
                return run_async_function(_get_tools)
            
            tools = get_tools()
            tool_count = len(tools)
            
            return jsonify({
                'connected': True,
                'tool_count': tool_count,
                'tools': [{'name': tool.name, 'description': tool.description} for tool in tools[:5]]  # First 5 tools
            })
        else:
            return jsonify({'connected': False, 'tool_count': 0, 'tools': []})
            
    except Exception as e:
        return jsonify({'connected': False, 'error': str(e), 'tool_count': 0, 'tools': []})

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration settings"""
    # Return a safe version of the config (without sensitive data)
    safe_config = {
        'app': config.get('app', {}),
        'workspace': config.get('workspace', {}),
        'defaults': config.get('defaults', {}),
        'jobs': config.get('jobs', {}),
        'files': config.get('files', {}),
        'paths': config.get('paths', {})
    }
    return jsonify(safe_config)

@app.route('/api/workspace', methods=['GET'])
def get_workspace_info():
    """Get workspace configuration and status"""
    try:
        workspace_config = config.get('workspace', {})
        paths_config = config.get('paths', {})
        
        # Check which directories exist
        directory_status = {}
        workspace_directories = [
            'mcp_servers_directory',
            'data_directory', 
            'results_directory',
            'uploads_directory',
            'config_directory',
            'logs_directory',
            'auto_workspaces_directory'
        ]
        
        for dir_key in workspace_directories:
            dir_path = paths_config.get(dir_key)
            if dir_path:
                directory_status[dir_key] = {
                    'path': dir_path,
                    'exists': Path(dir_path).exists(),
                    'is_directory': Path(dir_path).is_dir() if Path(dir_path).exists() else False
                }
        
        workspace_info = {
            'workspace_config': workspace_config,
            'directory_status': directory_status,
            'root_directory': paths_config.get('root_directory'),
            'initialized': all(status['exists'] for status in directory_status.values())
        }
        
        return jsonify(workspace_info)
        
    except Exception as e:
        return jsonify({'error': f'Failed to get workspace info: {str(e)}'}), 500

@app.route('/api/workspace/initialize', methods=['POST'])
def initialize_workspace():
    """Initialize workspace directory structure"""
    try:
        paths_config = config.get('paths', {})
        
        # Create workspace directories
        workspace_directories = [
            'data_directory', 
            'results_directory',
            'uploads_directory',
            'config_directory',
            'logs_directory',
            'auto_workspaces_directory'
        ]
        
        created_directories = []
        for dir_key in workspace_directories:
            dir_path = paths_config.get(dir_key)
            if dir_path:
                Path(dir_path).mkdir(parents=True, exist_ok=True)
                created_directories.append({
                    'name': dir_key,
                    'path': dir_path,
                    'created': True
                })
        
        return jsonify({
            'success': True,
            'message': 'Workspace directories initialized successfully',
            'created_directories': created_directories
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to initialize workspace: {str(e)}'}), 500

@app.route('/api/generate-tasks', methods=['POST'])
def generate_tasks():
    """Generate evaluation tasks"""
    data = request.json
    job_id = str(uuid.uuid4())
    
    # Extract parameters with config defaults
    servers = data.get('servers', [])
    model_name = data.get('model_name', config.get('defaults', {}).get('generation_model', 'gpt-4'))
    num_tasks = data.get('num_tasks', config.get('defaults', {}).get('num_tasks', 10))
    output_path = data.get('output_path', 'generated_tasks.jsonl')
    
    # Store job metadata
    job_metadata[job_id] = {
        "type": "Task Generation",
        "title": f"Generate {num_tasks} tasks for {', '.join(servers)}",
        "endpoint": "generate-tasks"
    }
    
    # Build command
    server_args = ' '.join([f'--server {server}' for server in servers])
    command = f'python -m mcp_eval_llm.cli generate-tasks {server_args} --model-name {model_name} --num-tasks {num_tasks} --output {output_path}'
    
    # Run command in background
    def run_task():
        result = run_cli_command(command, job_id)
        job_progress[job_id].update(result)
    
    threading.Thread(target=run_task).start()
    
    return jsonify({'job_id': job_id, 'status': 'started'})

@app.route('/api/verify-tasks', methods=['POST'])
def verify_tasks():
    """Verify evaluation tasks"""
    data = request.json
    job_id = str(uuid.uuid4())
    
    input_path = data.get('input_path', 'tasks.jsonl')
    servers = data.get('servers', [])
    
    # Store job metadata
    job_metadata[job_id] = {
        "type": "Task Verification",
        "title": f"Verify tasks in {input_path}",
        "endpoint": "verify-tasks"
    }
    
    server_args = ' '.join([f'--server {server}' for server in servers])
    command = f'python -m mcp_eval_llm.cli verify-tasks --input {input_path} {server_args}'
    
    def run_task():
        result = run_cli_command(command, job_id)
        job_progress[job_id].update(result)
    
    threading.Thread(target=run_task).start()
    
    return jsonify({'job_id': job_id, 'status': 'started'})

@app.route('/api/evaluate', methods=['POST'])
def evaluate():
    """Run model evaluation"""
    data = request.json
    job_id = str(uuid.uuid4())
    
    task_file = data.get('task_file', 'tasks.jsonl')
    model_names = data.get('model_names', ['gpt-4'])
    output_dir = data.get('output_dir', 'evaluation_results')
    max_concurrent = data.get('max_concurrent', config.get('defaults', {}).get('max_concurrent', 5))
    
    # Store job metadata
    job_metadata[job_id] = {
        "type": "Model Evaluation",
        "title": f"Evaluate {', '.join(model_names)} on {task_file}",
        "endpoint": "evaluate"
    }
    
    model_args = ' '.join([f'--model-name {model}' for model in model_names])
    command = f'python -m mcp_eval_llm.cli evaluate --task-file {task_file} {model_args} --output-dir {output_dir} --max-concurrent {max_concurrent}'
    
    def run_task():
        result = run_cli_command(command, job_id)
        job_progress[job_id].update(result)
    
    threading.Thread(target=run_task).start()
    
    return jsonify({'job_id': job_id, 'status': 'started'})

@app.route('/api/convert-data', methods=['POST'])
def convert_data():
    """Convert data format"""
    data = request.json
    job_id = str(uuid.uuid4())
    
    input_file = data.get('input_file')
    output_file = data.get('output_file')
    format_type = data.get('format', 'xlam')
    
    # Store job metadata
    job_metadata[job_id] = {
        "type": "Data Processing",
        "title": f"Convert {input_file} to {format_type.upper()}",
        "endpoint": "convert-data"
    }
    
    command = f'python -m mcp_eval_llm.cli convert-data --input {input_file} --output {output_file} --format {format_type}'
    
    def run_task():
        result = run_cli_command(command, job_id)
        job_progress[job_id].update(result)
    
    threading.Thread(target=run_task).start()
    
    return jsonify({'job_id': job_id, 'status': 'started'})

@app.route('/api/split-data', methods=['POST'])
def split_data():
    """Split data into train/test sets"""
    data = request.json
    job_id = str(uuid.uuid4())
    
    input_file = data.get('input_file')
    output_dir = data.get('output_dir', 'split_data')
    train_ratio = data.get('train_ratio', config.get('defaults', {}).get('train_ratio', 0.8))
    random_seed = data.get('random_seed', config.get('defaults', {}).get('random_seed', 42))
    
    # Store job metadata
    job_metadata[job_id] = {
        "type": "Data Processing",
        "title": f"Split {input_file} ({train_ratio:.0%} train)",
        "endpoint": "split-data"
    }
    
    command = f'python -m mcp_eval_llm.cli split-data --input {input_file} --output-dir {output_dir} --train-ratio {train_ratio} --random-seed {random_seed}'
    
    def run_task():
        result = run_cli_command(command, job_id)
        job_progress[job_id].update(result)
    
    threading.Thread(target=run_task).start()
    
    return jsonify({'job_id': job_id, 'status': 'started'})

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Analyze results against ground truth"""
    data = request.json
    job_id = str(uuid.uuid4())
    
    results_file = data.get('results_file')
    ground_truth_file = data.get('ground_truth_file')
    output_file = data.get('output_file', 'analysis_results.json')
    
    # Store job metadata
    job_metadata[job_id] = {
        "type": "Analysis",
        "title": f"Analyze {results_file} vs ground truth",
        "endpoint": "analyze"
    }
    
    command = f'python -m mcp_eval_llm.cli analyze --results {results_file} --ground-truth {ground_truth_file} --output {output_file}'
    
    def run_task():
        result = run_cli_command(command, job_id)
        job_progress[job_id].update(result)
    
    threading.Thread(target=run_task).start()
    
    return jsonify({'job_id': job_id, 'status': 'started'})

@app.route('/api/judge', methods=['POST'])
def judge():
    """Run LLM judgment"""
    data = request.json
    job_id = str(uuid.uuid4())
    
    results_file = data.get('results_file')
    judge_model = data.get('judge_model', config.get('defaults', {}).get('judge_model', 'gpt-4'))
    output_file = data.get('output_file', 'judge_results.json')
    
    # Store job metadata
    job_metadata[job_id] = {
        "type": "LLM Judging",
        "title": f"Judge evaluation with {judge_model}",
        "endpoint": "judge"
    }
    
    command = f'python -m mcp_eval_llm.cli judge --results {results_file} --judge-model {judge_model} --output {output_file}'
    
    def run_task():
        result = run_cli_command(command, job_id)
        job_progress[job_id].update(result)
    
    threading.Thread(target=run_task).start()
    
    return jsonify({'job_id': job_id, 'status': 'started'})

@app.route('/api/judge-rubric', methods=['POST'])
def judge_rubric():
    """Analyze LLM judgment results"""
    data = request.json
    job_id = str(uuid.uuid4())
    
    judge_file = data.get('judge_file')
    output_file = data.get('output_file', 'rubric_analysis.json')
    
    # Store job metadata
    job_metadata[job_id] = {
        "type": "Rubric Analysis",
        "title": f"Analyze judging rubric",
        "endpoint": "judge-rubric"
    }
    
    command = f'python -m mcp_eval_llm.cli judge-rubric --input {judge_file} --output {output_file}'
    
    def run_task():
        result = run_cli_command(command, job_id)
        job_progress[job_id].update(result)
    
    threading.Thread(target=run_task).start()
    
    return jsonify({'job_id': job_id, 'status': 'started'})

@app.route('/api/job-status/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get job status and progress"""
    if job_id not in job_progress:
        return jsonify({'error': 'Job not found'}), 404
    
    response = {
        'job_id': job_id,
        'progress': job_progress[job_id],
        'logs': job_logs.get(job_id, [])
    }
    
    # Add workspace information for auto jobs
    if job_id in job_metadata:
        metadata = job_metadata[job_id]
        if metadata.get('endpoint') == 'auto':
            response['workspace'] = metadata.get('workspace')
            response['servers'] = metadata.get('servers')
    
    return jsonify(response)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload a file"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Save file to configured uploads directory
    uploads_dir = Path(config.get('paths', {}).get('uploads_directory', '../uploads'))
    uploads_dir.mkdir(exist_ok=True)
    
    file_path = uploads_dir / file.filename
    file.save(file_path)
    
    return jsonify({'filename': file.filename, 'path': str(file_path)})

@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    """Download a file"""
    root_dir = config.get('paths', {}).get('root_directory', '..')
    file_path = Path(root_dir) / filename
    
    if not file_path.exists():
        return jsonify({'error': 'File not found'}), 404
    
    return send_file(file_path, as_attachment=True)

@app.route('/api/files', methods=['GET'])
def list_files():
    """List available files"""
    directory = request.args.get('dir', '.')
    root_dir = config.get('paths', {}).get('root_directory', '..')
    base_path = Path(root_dir) / directory
    
    if not base_path.exists():
        return jsonify({'error': 'Directory not found'}), 404
    
    files = []
    for item in base_path.iterdir():
        if item.is_file() and not item.name.startswith('.'):
            files.append({
                'name': item.name,
                'path': str(item.relative_to(Path(root_dir))),
                'size': item.stat().st_size,
                'modified': datetime.fromtimestamp(item.stat().st_mtime).isoformat()
            })
    
    return jsonify({'files': files})

@app.route('/api/servers', methods=['GET'])
def list_servers():
    """List available MCP servers"""
    try:
        # Get MCP servers directory from config
        servers_dir_path = config.get('paths', {}).get('mcp_servers_directory')
        root_dir = config.get('paths', {}).get('root_directory', '..')
        
        # Fallback to original location if mcp_servers_directory is not configured
        if servers_dir_path:
            servers_dir = Path(servers_dir_path)
        else:
            servers_dir = Path(root_dir) / 'mcp_servers'
        
        servers = []
        
        # Check multiple potential locations for MCP servers
        potential_locations = [servers_dir]
        
        # Also check the original location relative to the config file
        config_dir = Path(__file__).parent  # backend directory
        original_location = config_dir.parent / 'mcp_servers'  # project_root/mcp_servers
        if original_location != servers_dir and original_location.exists():
            potential_locations.append(original_location)
        
        found_servers = False
        for check_dir in potential_locations:
            if check_dir.exists() and any(check_dir.iterdir()):
                servers_dir = check_dir
                found_servers = True
                break
        
        if found_servers:
            # Scan for server directories
            for server_dir in servers_dir.iterdir():
                if server_dir.is_dir() and not server_dir.name.startswith('.'):
                    server_py = server_dir / 'server.py'
                    if server_py.exists():
                        # Read the server file to extract basic info
                        try:
                            with open(server_py, 'r', encoding='utf-8') as f:
                                content = f.read()
                                
                            # Calculate relative path - use project root as base
                            try:
                                # Try to get relative path from configured root
                                relative_path = str(server_py.relative_to(Path(root_dir)))
                            except ValueError:
                                # If file is not under configured root, use project root as fallback
                                config_dir = Path(__file__).parent  # backend directory
                                project_root = config_dir.parent  # project root
                                try:
                                    relative_path = str(server_py.relative_to(project_root))
                                except ValueError:
                                    # If still fails, just use the absolute path
                                    relative_path = str(server_py)
                            
                            # Extract basic information
                            server_info = {
                                'name': server_dir.name,
                                'path': relative_path,
                                'description': extract_server_description(content),
                                'tools': extract_server_tools(content),
                                'size': server_py.stat().st_size,
                                'modified': datetime.fromtimestamp(server_py.stat().st_mtime).isoformat()
                            }
                            servers.append(server_info)
                        except Exception as e:
                            # Calculate relative path for error case too
                            try:
                                relative_path = str(server_py.relative_to(Path(root_dir)))
                            except ValueError:
                                config_dir = Path(__file__).parent  # backend directory
                                project_root = config_dir.parent  # project root
                                try:
                                    relative_path = str(server_py.relative_to(project_root))
                                except ValueError:
                                    relative_path = str(server_py)
                            
                            # If we can't read the file, still include basic info
                            servers.append({
                                'name': server_dir.name,
                                'path': relative_path,
                                'description': 'Unable to read server description',
                                'tools': [],
                                'size': 0,
                                'modified': None,
                                'error': str(e)
                            })
        
        # Add debug information about search paths
        debug_info = {
            'configured_path': servers_dir_path,
            'used_path': str(servers_dir) if found_servers else None,
            'searched_locations': [str(loc) for loc in potential_locations],
            'locations_status': [
                {
                    'path': str(loc),
                    'exists': loc.exists(),
                    'has_content': any(loc.iterdir()) if loc.exists() else False
                }
                for loc in potential_locations
            ]
        }
        
        return jsonify({
            'servers': servers,
            'debug_info': debug_info
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to list servers: {str(e)}'}), 500

def extract_server_description(content):
    """Extract description from server file content"""
    # Look for common description patterns
    lines = content.split('\n')
    for i, line in enumerate(lines):
        # Look for FastMCP initialization with description
        if 'FastMCP(' in line and ('"' in line or "'" in line):
            # Extract the description from the FastMCP constructor
            start = line.find('"') + 1 if '"' in line else line.find("'") + 1
            end = line.rfind('"') if '"' in line else line.rfind("'")
            if start > 0 and end > start:
                return line[start:end]
        
        # Look for module docstring
        if i < 10 and line.strip().startswith('"""') and line.strip().endswith('"""') and len(line.strip()) > 6:
            return line.strip()[3:-3]
        elif i < 10 and line.strip().startswith('"""'):
            # Multi-line docstring
            for j in range(i + 1, min(i + 5, len(lines))):
                if lines[j].strip().endswith('"""'):
                    return ' '.join(lines[i:j+1]).replace('"""', '').strip()
    
    return 'MCP Server'

def extract_server_tools(content):
    """Extract tool names from server file content"""
    tools = []
    lines = content.split('\n')
    
    for line in lines:
        # Look for @mcp_tool() decorator
        if '@mcp_tool(' in line or '@mcp.tool(' in line:
            continue
        # Look for function definitions after decorators
        if line.strip().startswith('def ') and '(' in line:
            func_name = line.strip().split('def ')[1].split('(')[0]
            # Skip private functions and common non-tool functions
            if not func_name.startswith('_') and func_name not in ['startup', 'shutdown', 'main']:
                tools.append(func_name)
    
    return tools[:10]  # Limit to first 10 tools

@app.route('/api/backend-files', methods=['GET'])
def list_backend_files():
    """List backend files"""
    try:
        # Get root directory from config
        root_dir = config.get('paths', {}).get('root_directory', '..')
        backend_dir = Path(root_dir) / 'backend'
        
        files = []
        
        if backend_dir.exists():
            # Scan for files in backend directory
            for file_path in backend_dir.iterdir():
                if file_path.is_file() and not file_path.name.startswith('.'):
                    try:
                        # Calculate relative path with fallback
                        try:
                            relative_path = str(file_path.relative_to(Path(root_dir)))
                        except ValueError:
                            # If file is not under configured root, use project root as fallback
                            config_dir = Path(__file__).parent  # backend directory
                            project_root = config_dir.parent  # project root
                            try:
                                relative_path = str(file_path.relative_to(project_root))
                            except ValueError:
                                # If still fails, just use the absolute path
                                relative_path = str(file_path)
                        
                        # Get file info
                        file_info = {
                            'name': file_path.name,
                            'path': relative_path,
                            'extension': file_path.suffix,
                            'size': file_path.stat().st_size,
                            'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                            'type': get_file_type(file_path)
                        }
                        
                        # Add description based on file type
                        file_info['description'] = get_file_description(file_path)
                        
                        files.append(file_info)
                    except Exception as e:
                        # Calculate relative path for error case too
                        try:
                            relative_path = str(file_path.relative_to(Path(root_dir)))
                        except ValueError:
                            config_dir = Path(__file__).parent  # backend directory
                            project_root = config_dir.parent  # project root
                            try:
                                relative_path = str(file_path.relative_to(project_root))
                            except ValueError:
                                relative_path = str(file_path)
                        
                        # If we can't read the file, still include basic info
                        files.append({
                            'name': file_path.name,
                            'path': relative_path,
                            'extension': file_path.suffix,
                            'size': 0,
                            'modified': None,
                            'type': 'unknown',
                            'description': 'Unable to read file',
                            'error': str(e)
                        })
        
        # Sort files by name
        files.sort(key=lambda x: x['name'])
        
        return jsonify({'files': files})
        
    except Exception as e:
        return jsonify({'error': f'Failed to list backend files: {str(e)}'}), 500

def get_file_type(file_path):
    """Determine file type based on extension"""
    extension = file_path.suffix.lower()
    type_mapping = {
        '.py': 'python',
        '.yaml': 'yaml',
        '.yml': 'yaml', 
        '.json': 'json',
        '.md': 'markdown',
        '.txt': 'text',
        '.sh': 'shell',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.html': 'html',
        '.css': 'css',
        '.sql': 'sql'
    }
    return type_mapping.get(extension, 'file')

def get_file_description(file_path):
    """Get description for backend files"""
    file_descriptions = {
        'app.py': 'Main Flask backend application server',
        'backend.yaml': 'Backend configuration file',
        'backend.production.yaml': 'Production backend configuration',
        'README.md': 'Backend documentation and setup instructions',
        'setup.sh': 'Backend setup and installation script'
    }
    
    return file_descriptions.get(file_path.name, f'{get_file_type(file_path).title()} file')

@app.route('/api/models', methods=['GET'])
def list_models():
    """List available models"""
    models = [
        {'name': 'gpt-4', 'provider': 'OpenAI', 'description': 'GPT-4 (recommended)'},
        {'name': 'gpt-3.5-turbo', 'provider': 'OpenAI', 'description': 'GPT-3.5 Turbo'},
        {'name': 'claude-3-opus', 'provider': 'Anthropic', 'description': 'Claude 3 Opus'},
        {'name': 'claude-3-sonnet', 'provider': 'Anthropic', 'description': 'Claude 3 Sonnet'},
        {'name': 'claude-3-haiku', 'provider': 'Anthropic', 'description': 'Claude 3 Haiku'}
    ]
    return jsonify({'models': models})

@app.route('/api/recent-activities', methods=['GET'])
def get_recent_activities():
    """Get recent job activities"""
    activities = []
    
    # Convert job_progress to activity format
    for job_id, job_data in job_progress.items():
        # Get metadata if available, otherwise use defaults
        metadata = job_metadata.get(job_id, {})
        activity_type = metadata.get("type", "Unknown Task")
        title = metadata.get("title", f"Job {job_id[:8]}")
        
        # Calculate relative timestamp
        timestamp = "Just now"  # Default since we don't store creation time
        
        activity = {
            'id': job_id,
            'type': activity_type,
            'title': title,
            'status': job_data.get('status', 'unknown'),
            'progress': job_data.get('progress', 0),
            'timestamp': timestamp
        }
        
        activities.append(activity)
    
    # Sort by most recent first (for now, just reverse order)
    activities.reverse()
    
    # Limit to last 10 activities
    activities = activities[:10]
    
    return jsonify({'activities': activities})

@app.route('/api/system-info', methods=['GET'])
def system_info():
    """Get system information and metrics"""
    try:
        # Get basic system info
        import psutil
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return jsonify({
            'cpu_usage': cpu_percent,
            'memory_usage': memory.percent,
            'memory_total': memory.total,
            'memory_available': memory.available,
            'disk_usage': (disk.used / disk.total) * 100,
            'disk_total': disk.total,
            'disk_free': disk.free,
            'timestamp': datetime.now().isoformat()
        })
    except ImportError:
        # Fallback if psutil is not available
        return jsonify({
            'cpu_usage': 45,
            'memory_usage': 60,
            'disk_usage': 75,
            'timestamp': datetime.now().isoformat()
                })
    
    return jsonify({'activities': activities})

@app.route('/api/auto', methods=['POST'])
def auto_workflow():
    """Run complete auto evaluation workflow with automatic workspace creation"""
    data = request.json
    job_id = str(uuid.uuid4())
    
    # Extract parameters
    servers = data.get('servers', [])
    if not servers:
        return jsonify({'error': 'At least one server must be specified'}), 400
    
    # Create workspace name with server names and timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    server_names = []
    for server in servers:
        # Extract server name from path (e.g., 'mcp_servers/healthcare/server.py' -> 'healthcare')
        if '/' in server:
            server_name = server.split('/')[-2]  # Get parent directory name
        else:
            server_name = server.split('@')[-1].split('/')[0] if '@' in server else server
        server_names.append(server_name)
    
    workspace_name = f"{'_'.join(server_names)}_{timestamp}"
    
    # Create workspace path under root directory
    root_dir = config.get('paths', {}).get('root_directory', '..')
    workspace_path = Path(root_dir) / 'auto_workspaces' / workspace_name
    
    # Extract other parameters with defaults
    task_model = data.get('task_model', config.get('defaults', {}).get('generation_model', 'gpt-4.1-2025-04-14'))
    eval_model_configs = data.get('eval_model_configs', [])
    num_tasks = data.get('num_tasks', config.get('defaults', {}).get('num_tasks', 50))
    max_turns = data.get('max_turns', 30)
    enable_llm_judge = data.get('enable_llm_judge', False)
    llm_judge_model = data.get('llm_judge_model', config.get('defaults', {}).get('judge_model', 'gpt-4o'))
    
    # Optional prompt files
    task_generation_prompt = data.get('task_generation_prompt')
    task_verification_prompt = data.get('task_verification_prompt')
    evaluation_prompt = data.get('evaluation_prompt')
    
    # Store job metadata
    job_metadata[job_id] = {
        "type": "Auto Workflow",
        "title": f"Auto evaluation for {', '.join(server_names)}",
        "endpoint": "auto",
        "workspace": str(workspace_path),
        "servers": servers
    }
    
    # Build command - fix server argument format
    cmd_parts = ['python', '-m', 'mcp_eval_llm.cli.main', 'auto']
    
    # Add servers (multiple servers should be passed as separate arguments)
    cmd_parts.append('--servers')
    cmd_parts.extend(servers)
    
    # Add other required arguments
    cmd_parts.extend([
        '--working-dir', str(workspace_path),
        '--task-model', task_model,
        '--num-tasks', str(num_tasks),
        '--max-turns', str(max_turns)
    ])
    
    if eval_model_configs:
        cmd_parts.append('--eval-model-configs')
        cmd_parts.extend(eval_model_configs)
    
    if enable_llm_judge:
        cmd_parts.extend([
            '--enable-llm-judge',
            '--llm-judge-model', llm_judge_model
        ])
    
    if task_generation_prompt:
        cmd_parts.extend(['--task-generation-prompt', task_generation_prompt])
    
    if task_verification_prompt:
        cmd_parts.extend(['--task-verification-prompt', task_verification_prompt])
    
    if evaluation_prompt:
        cmd_parts.extend(['--evaluation-prompt', evaluation_prompt])
    
    # Convert to shell command string
    command = ' '.join([f'"{part}"' if ' ' in part else part for part in cmd_parts])
    
    # Run command in background
    def run_task():
        # Initialize progress tracking
        job_progress[job_id] = {'status': 'running', 'progress': 0}
        job_logs[job_id] = [f"Starting auto workflow for {', '.join(servers)}"]
        job_logs[job_id].append(f"Workspace: {workspace_path}")
        
        try:
            # Create the workspace directory
            workspace_path.mkdir(parents=True, exist_ok=True)
            job_logs[job_id].append("✓ Workspace directory created")
            job_progress[job_id]['progress'] = 5
            
            # Run the auto workflow command
            result = run_cli_command(command, job_id, capture_output=False)
            
            if result.get('success', False):
                job_progress[job_id]['status'] = 'completed'
                job_progress[job_id]['progress'] = 100
                job_logs[job_id].append("🎉 Auto workflow completed successfully!")
                job_logs[job_id].append(f"Results available at: {workspace_path}")
            else:
                job_progress[job_id]['status'] = 'failed'
                job_progress[job_id]['progress'] = 100
                job_logs[job_id].append(f"❌ Auto workflow failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            job_progress[job_id]['status'] = 'failed' 
            job_progress[job_id]['progress'] = 100
            job_logs[job_id].append(f"❌ Error during auto workflow: {str(e)}")
    
    threading.Thread(target=run_task).start()
    
    return jsonify({
        'job_id': job_id, 
        'status': 'started',
        'workspace': str(workspace_path),
        'servers': servers
    })

@app.route('/api/workspaces', methods=['GET'])
def list_workspaces():
    """List all auto-generated workspaces"""
    try:
        root_dir = config.get('paths', {}).get('root_directory', '..')
        workspaces_dir = Path(root_dir) / 'auto_workspaces'
        
        if not workspaces_dir.exists():
            return jsonify({'workspaces': []})
        
        workspaces = []
        for workspace_path in workspaces_dir.iterdir():
            if workspace_path.is_dir():
                # Parse workspace name to extract info
                workspace_name = workspace_path.name
                parts = workspace_name.split('_')
                
                # Last part should be timestamp (YYYYMMDD_HHMMSS format)
                if len(parts) >= 2:
                    timestamp_str = '_'.join(parts[-2:])  # Get last two parts for YYYYMMDD_HHMMSS
                    try:
                        timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                        servers = '_'.join(parts[:-2])  # Everything except last two parts
                    except ValueError:
                        # Fallback if timestamp parsing fails
                        timestamp = datetime.fromtimestamp(workspace_path.stat().st_mtime)
                        servers = workspace_name
                else:
                    timestamp = datetime.fromtimestamp(workspace_path.stat().st_mtime)
                    servers = workspace_name
                
                # Check if workspace has results
                results_dir = workspace_path / 'results'
                report_dir = workspace_path / 'report'
                has_results = results_dir.exists() and any(results_dir.iterdir())
                has_reports = report_dir.exists() and any(report_dir.iterdir())
                
                # Determine status
                status = 'completed' if has_results or has_reports else 'in_progress'
                
                workspace_info = {
                    'name': workspace_name,
                    'path': str(workspace_path),
                    'servers': servers,
                    'created': timestamp.isoformat(),
                    'status': status,
                    'has_results': has_results,
                    'has_reports': has_reports
                }
                workspaces.append(workspace_info)
        
        # Sort by creation time (newest first)
        workspaces.sort(key=lambda x: x['created'], reverse=True)
        
        return jsonify({'workspaces': workspaces})
        
    except Exception as e:
        return jsonify({'error': f'Failed to list workspaces: {str(e)}'}), 500

@app.route('/api/workspaces/<workspace_name>', methods=['GET'])
def get_workspace_details(workspace_name):
    """Get detailed information about a specific workspace"""
    try:
        root_dir = config.get('paths', {}).get('root_directory', '..')
        workspace_path = Path(root_dir) / 'auto_workspaces' / workspace_name
        
        if not workspace_path.exists():
            return jsonify({'error': 'Workspace not found'}), 404
        
        # Get workspace basic info
        parts = workspace_name.split('_')
        if len(parts) >= 2:
            timestamp_str = '_'.join(parts[-2:])  # Get last two parts for YYYYMMDD_HHMMSS
            try:
                timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                servers = '_'.join(parts[:-2])  # Everything except last two parts
            except ValueError:
                timestamp = datetime.fromtimestamp(workspace_path.stat().st_mtime)
                servers = workspace_name
        else:
            timestamp = datetime.fromtimestamp(workspace_path.stat().st_mtime)
            servers = workspace_name
        
        # Scan directory structure
        structure = {}
        subdirs = ['data', 'results', 'report', 'logs']
        
        for subdir in subdirs:
            subdir_path = workspace_path / subdir
            if subdir_path.exists():
                files = []
                for file_path in subdir_path.iterdir():
                    if file_path.is_file():
                        files.append({
                            'name': file_path.name,
                            'size': file_path.stat().st_size,
                            'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                        })
                structure[subdir] = files
            else:
                structure[subdir] = []
        
        # Get logs if available
        logs = []
        logs_dir = workspace_path / 'logs'
        if logs_dir.exists():
            for log_file in logs_dir.glob('*.log'):
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        log_content = f.read()
                        logs.append({
                            'name': log_file.name,
                            'content': log_content[-1000:] if len(log_content) > 1000 else log_content  # Last 1000 chars
                        })
                except Exception as e:
                    logs.append({
                        'name': log_file.name,
                        'content': f'Error reading log: {str(e)}'
                    })
        
        workspace_details = {
            'name': workspace_name,
            'path': str(workspace_path),
            'servers': servers,
            'created': timestamp.isoformat(),
            'structure': structure,
            'logs': logs
        }
        
        return jsonify(workspace_details)
        
    except Exception as e:
        return jsonify({'error': f'Failed to get workspace details: {str(e)}'}), 500

@app.route('/api/workspaces/<workspace_name>/files/<path:file_path>', methods=['GET'])
def download_workspace_file(workspace_name, file_path):
    """Download a file from a workspace"""
    try:
        root_dir = config.get('paths', {}).get('root_directory', '..')
        workspace_path = Path(root_dir) / 'auto_workspaces' / workspace_name
        full_file_path = workspace_path / file_path
        
        # Security check - ensure file is within workspace
        if not str(full_file_path.resolve()).startswith(str(workspace_path.resolve())):
            return jsonify({'error': 'Access denied'}), 403
        
        if not full_file_path.exists():
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(full_file_path, as_attachment=True)
        
    except Exception as e:
        return jsonify({'error': f'Failed to download file: {str(e)}'}), 500

# MCP Client API endpoints
def run_async_function(async_func):
    """Helper function to run async functions in Flask routes"""
    try:
        # Always use asyncio.run for consistency and proper cleanup
        # This ensures a fresh event loop for each call
        return asyncio.run(async_func())
    except Exception as e:
        print(f"Error in run_async_function: {e}")
        import traceback
        traceback.print_exc()
        raise e

@app.route('/api/mcp/connect', methods=['POST'])
def mcp_connect():
    """Connect to multiple MCP servers"""
    global mcp_client
    
    try:
        data = request.get_json()
        servers = data.get('servers', [])
        server_args = data.get('server_args', [])
        llm_config = data.get('llm_config', {})
        
        if not servers:
            return jsonify({'success': False, 'error': 'No servers provided'}), 400
        
        # Import required modules
        import sys
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        src_dir = os.path.join(parent_dir, 'src')
        sys.path.insert(0, src_dir)
        
        from mcp_eval_llm.client.openai_client import OpenAIMCPClient
        
        # Resolve server paths to absolute paths relative to project root
        resolved_servers = []
        for server_path in servers:
            if os.path.isabs(server_path):
                resolved_servers.append(server_path)
            else:
                # Resolve relative to project root (parent_dir), not backend directory
                absolute_path = os.path.join(parent_dir, server_path)
                resolved_servers.append(absolute_path)
        
        print(f"Original server paths: {servers}")
        print(f"Resolved server paths: {resolved_servers}")
        print(f"Server args: {server_args}")
        print(f"LLM config: {llm_config}")
        
        def connect_servers():
            async def _connect():
                try:
                    # Create a new client instance
                    system_prompt = llm_config.get('systemPrompt', 'You are a helpful AI assistant with access to various tools through MCP servers.')
                    
                    # Set OpenAI API key - check config first, then environment
                    api_key = llm_config.get('apiKey')
                    if api_key and api_key.strip() and api_key != 'test-key':
                        os.environ['OPENAI_API_KEY'] = api_key
                        print("Using API key from config")
                    elif os.environ.get('OPENAI_API_KEY'):
                        print("Using API key from environment")
                    else:
                        print("Warning: No valid API key provided in config and OPENAI_API_KEY not set in environment")
                    
                    print(f"Creating OpenAI client with model: {llm_config.get('model', 'gpt-4o')}")
                    client = OpenAIMCPClient(
                        model=llm_config.get('model', 'gpt-4o'),
                        system_prompt=system_prompt
                    )
                    
                    # Prepare server_args_list to match the number of servers
                    if not server_args:
                        server_args_list = [[] for _ in resolved_servers]
                    elif len(server_args) != len(resolved_servers):
                        # If server_args length doesn't match servers, pad with empty lists
                        server_args_list = server_args[:len(resolved_servers)]
                        while len(server_args_list) < len(resolved_servers):
                            server_args_list.append([])
                    else:
                        server_args_list = server_args
                    
                    print(f"Calling connect_to_multiple_servers with:")
                    print(f"  servers: {resolved_servers}")
                    print(f"  server_args_list: {server_args_list}")
                    
                    # Connect to multiple servers using resolved paths
                    server_mapping = await client.connect_to_multiple_servers(resolved_servers, server_args_list)
                    print(f"Server mapping result: {list(server_mapping.keys())}")
                    
                    return client, server_mapping
                    
                except Exception as e:
                    print(f"Error in _connect: {e}")
                    import traceback
                    traceback.print_exc()
                    raise
            
            return run_async_function(_connect)
        
        mcp_client, server_mapping = connect_servers()
        
        # Count connected servers and available tools
        connected_count = len([info for info in server_mapping.values() if info])
        total_tools = sum(len(info.get('tools', [])) for info in server_mapping.values() if info)
        
        print(f"Connection result: {connected_count} servers, {total_tools} tools")
        
        # Convert server mapping to JSON serializable format
        # Use original server paths as keys for the frontend
        serializable_mapping = {}
        for i, (resolved_path, info) in enumerate(server_mapping.items()):
            original_path = servers[i] if i < len(servers) else resolved_path
            tools_data = []
            if info and 'tools' in info:
                for tool in info['tools']:
                    tools_data.append({
                        'name': tool.name,
                        'description': tool.description,
                        'inputSchema': tool.inputSchema
                    })
            serializable_mapping[original_path] = {
                'tools': tools_data,
                'connected': bool(info)
            }
        
        return jsonify({
            'success': True,
            'connected_count': connected_count,
            'total_tools': total_tools,
            'server_mapping': serializable_mapping
        })
        
    except Exception as e:
        import traceback
        print("Full traceback:")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/mcp/disconnect', methods=['POST'])
def mcp_disconnect():
    """Disconnect from MCP servers"""
    global mcp_client
    
    try:
        if mcp_client:
            try:
                def cleanup():
                    async def _cleanup():
                        print("Starting MCP client cleanup...")
                        await mcp_client.cleanup()
                        print("MCP client cleanup completed")
                    return run_async_function(_cleanup)
                
                cleanup()
                print("Setting mcp_client to None")
                mcp_client = None
            except Exception as cleanup_error:
                print(f"Error during cleanup: {cleanup_error}")
                # Still set client to None even if cleanup fails
                mcp_client = None
        
        return jsonify({'success': True, 'message': 'Disconnected from all servers'})
        
    except Exception as e:
        print(f"Error in disconnect: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/mcp/chat', methods=['POST'])
def mcp_chat():
    """Send a message to the MCP client"""
    global mcp_client
    
    try:
        if not mcp_client:
            return jsonify({'success': False, 'error': 'No MCP client connected'}), 400
        
        # Quick health check of the client
        try:
            if not hasattr(mcp_client, 'server_mapping') or not mcp_client.server_mapping:
                return jsonify({'success': False, 'error': 'MCP client connection appears to be broken'}), 400
        except Exception as e:
            print(f"MCP client health check failed: {e}")
            return jsonify({'success': False, 'error': 'MCP client connection is invalid'}), 400
        
        data = request.get_json()
        message = data.get('message', '')
        
        if not message:
            return jsonify({'success': False, 'error': 'No message provided'}), 400
        
        def send_message():
            async def _send():
                try:
                    print(f"Processing message: {message}")
                    # Use the process_query method from the OpenAIMCPClient
                    response_content = await mcp_client.process_query(message)
                    print(f"Response received: {response_content[:200]}...")  # First 200 chars
                    return response_content
                except Exception as e:
                    print(f"Error in process_query: {e}")
                    import traceback
                    traceback.print_exc()
                    raise
            
            return run_async_function(_send)
        
        response_content = send_message()
        
        return jsonify({
            'success': True,
            'response': response_content,
            'tool_calls': [],  # Tool calls are handled internally by process_query
            'tool_results': []  # Tool results are also handled internally
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    # Use configuration for app settings
    app_config = config.get('app', {})
    debug = app_config.get('debug', True)
    host = app_config.get('host', '0.0.0.0')
    port = app_config.get('port', 22358)
    
    print(f"Starting MCP Eval LLM Backend...")
    
    # Show which config file is being used
    config_file = args.config if args.config else "backend.yaml (default)"
    print(f"Configuration: {config_file}")
    
    # Show workspace information
    workspace_info = config.get('workspace', {})
    paths_info = config.get('paths', {})
    
    print(f"Workspace root: {workspace_info.get('root', 'Not configured')}")
    print(f"Root directory: {paths_info.get('root_directory', '..')}")
    print(f"Server: {host}:{port}")
    print(f"Debug mode: {debug}")
    
    # Show key workspace directories
    key_dirs = ['mcp_servers_directory', 'data_directory', 'results_directory', 'uploads_directory']
    print("\nWorkspace directories:")
    for dir_key in key_dirs:
        dir_path = paths_info.get(dir_key, 'Not configured')
        exists = "✓" if Path(dir_path).exists() else "✗"
        print(f"  {exists} {dir_key.replace('_directory', '')}: {dir_path}")
    
    app.run(debug=debug, host=host, port=port) 