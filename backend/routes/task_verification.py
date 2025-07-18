from pathlib import Path
from flask import Blueprint, jsonify, request
from .task_utils import build_server_specs, validate_servers, validate_required_field


def create_task_verification_routes(config, job_manager):
    """Create task verification route handlers"""
    task_verification_bp = Blueprint('task_verification', __name__)

    @task_verification_bp.route('/api/verify-tasks', methods=['POST'])
    def verify_tasks():
        """Verify tasks using the CLI"""
        try:
            data = request.get_json()
            
            # Extract parameters from frontend
            servers = data.get('servers', [])
            domain_name = data.get('domain_name', '')
            tasks_filename = data.get('tasks_filename', '')
            output_filename = data.get('output_filename', '')
            model = data.get('model', 'gpt-4.1-2025-04-14')
            num_tasks = data.get('num_tasks', -1)
            api_key = data.get('api_key', None)
            
            # Validate required fields
            if not validate_servers(servers):
                return jsonify({'error': 'At least one server path is required'}), 400
            
            error = validate_required_field(domain_name, 'Domain name')
            if error:
                return jsonify({'error': error}), 400
            
            error = validate_required_field(tasks_filename, 'Tasks filename')
            if error:
                return jsonify({'error': error}), 400
            
            # Construct file paths following the organized structure
            workspace_path = Path(config.get('workspace', {}).get('root', 'workspace'))
            input_file = workspace_path / 'data' / domain_name / 'tasks' / tasks_filename
            
            # Determine output file path
            if output_filename:
                output_file = workspace_path / 'data' / domain_name / 'verified_tasks' / output_filename
            else:
                output_file = workspace_path / 'data' / domain_name / 'verified_tasks' / f"verified_{tasks_filename}"
            
            # Ensure the output directory exists
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Validate input file exists
            if not input_file.exists():
                return jsonify({'error': f'Input file not found: {input_file}'}), 400
            
            # Create job
            job_id = job_manager.create_job(
                "Task Verification", 
                f"Verify tasks in {domain_name}/{tasks_filename}", 
                "verify-tasks"
            )
            
            # Store additional metadata
            job_manager.job_metadata[job_id].update({
                'input_file': str(input_file),
                'output_file': str(output_file),
                'domain_name': domain_name,
                'num_tasks': num_tasks
            })
            
            # Build command using the correct CLI format
            cmd_parts = ['mcp-eval', 'verify-tasks']
            
            # Add servers - format each server with its arguments
            server_specs = build_server_specs(servers)
            if server_specs:
                cmd_parts.extend(['--servers'] + server_specs)
            
            # Add required parameters
            cmd_parts.extend([
                '--tasks-file', str(input_file),
                '--output', str(output_file),
                '--model', model,
                '--non-interactive'  # Always run in non-interactive mode from backend
            ])
            
            # Add optional parameters
            if num_tasks != -1:
                cmd_parts.extend(['--num-tasks', str(num_tasks)])
            
            if api_key:
                cmd_parts.extend(['--api-key', api_key])
            
            # Convert to shell command string
            command = ' '.join([f'"{part}"' if ' ' in part else part for part in cmd_parts])
            
            # Run command asynchronously
            result = job_manager.run_job_async(job_id, command)
            result['job_id'] = job_id
            result['input_file'] = str(input_file)
            result['output_file'] = str(output_file)
            result['domain_name'] = domain_name
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return task_verification_bp 