from flask import Blueprint, jsonify, request
from pathlib import Path
from .task_utils import generate_output_path, build_server_specs, validate_servers, extract_server_name


def create_task_generation_routes(config, job_manager):
    """Create task generation route handlers"""
    task_generation_bp = Blueprint('task_generation', __name__)

    @task_generation_bp.route('/api/generate-tasks', methods=['POST'])
    def generate_tasks():
        """Generate tasks using the CLI"""
        try:
            data = request.get_json()
            
            # Extract parameters from frontend
            servers = data.get('servers', [])
            num_tasks = data.get('num_tasks', 10)
            existing_files = data.get('existing_files', [])
            prompt_file = data.get('prompt_file', None)
            model = data.get('model', 'gpt-4.1-2025-04-14')
            temperature = data.get('temperature', 0.2)
            max_tokens = data.get('max_tokens', 2000)
            top_p = data.get('top_p', 0.95)
            api_key = data.get('api_key', None)
            output_folder_name = data.get('output_folder_name', None)
            output_file_name = data.get('output_file_name', None)
            
            # Validate required fields
            if not validate_servers(servers):
                return jsonify({'error': 'At least one server path is required'}), 400
            
            # Generate organized output path (use custom name if provided)
            output_path, server_name = generate_output_path(config, servers, output_folder_name, output_file_name)
            
            # Ensure the directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create job
            server_names = [extract_server_name(s.get('path', '')) for s in servers if s.get('path')]
            job_id = job_manager.create_job(
                "Task Generation", 
                f"Generate {num_tasks} tasks for {', '.join(server_names[:2])}{'...' if len(server_names) > 2 else ''}", 
                "generate-tasks"
            )
            
            # Store additional metadata
            workspace_root = config.get('workspace', {}).get('root', '../workspace')
            full_output_path = Path(workspace_root) / output_path
            job_manager.job_metadata[job_id].update({
                'output_path': str(full_output_path),
                'server_name': server_name,
                'num_tasks': num_tasks
            })
            
            # Build command using the correct CLI format
            cmd_parts = ['mcp-eval', 'generate-tasks']
            
            # Add servers - format each server with its arguments
            server_specs = build_server_specs(servers)
            if server_specs:
                cmd_parts.extend(['--servers'] + server_specs)
            
            # Add other parameters
            cmd_parts.extend([
                '--output', str(output_path),
                '--num-tasks', str(num_tasks),
                '--model', model,
                '--temperature', str(temperature),
                '--max-tokens', str(max_tokens),
                '--top-p', str(top_p)
            ])
            
            # Add optional parameters
            if existing_files:
                cmd_parts.extend(['--existing-files'] + existing_files)
            
            if prompt_file:
                cmd_parts.extend(['--prompt-file', prompt_file])
            
            if api_key:
                cmd_parts.extend(['--api-key', api_key])
            
            # Convert to shell command string
            command = ' '.join([f'"{part}"' if ' ' in part else part for part in cmd_parts])
            
            # Run command asynchronously
            result = job_manager.run_job_async(job_id, command)
            result['job_id'] = job_id
            result['output_path'] = str(full_output_path)
            result['server_name'] = server_name
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return task_generation_bp 