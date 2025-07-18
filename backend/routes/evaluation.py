import json
import tempfile
import os
from pathlib import Path
from flask import Blueprint, jsonify, request
from .task_utils import build_server_specs, validate_servers, validate_required_field


def create_evaluation_routes(config, job_manager):
    """Create evaluation route handlers"""
    evaluation_bp = Blueprint('evaluation', __name__)

    @evaluation_bp.route('/api/evaluate-model', methods=['POST'])
    def evaluate_model():
        """Evaluate a model using the CLI"""
        try:
            data = request.get_json()
            
            # Extract parameters
            tasks_file = data.get('tasks_file', '')
            model_config = data.get('model_config', '')
            output_dir = data.get('output_dir', 'results')
            max_concurrent = data.get('max_concurrent', config.get('defaults', {}).get('max_concurrent', 5))
            train_ratio = data.get('train_ratio', config.get('defaults', {}).get('train_ratio', 0.8))
            random_seed = data.get('random_seed', config.get('defaults', {}).get('random_seed', 42))
            
            # Validate required fields
            if not tasks_file or not model_config:
                return jsonify({'error': 'Tasks file and model config are required'}), 400
            
            # Create job
            job_id = job_manager.create_job("Model Evaluation", f"Evaluate model with {tasks_file}", "evaluate-model")
            
            # Build command using mcp-eval CLI
            command = f'mcp-eval evaluate'
            command += f' --tasks-file "{tasks_file}"'
            command += f' --model-config "{model_config}"'
            command += f' --output "{output_dir}"'
            command += f' --max-concurrent {max_concurrent}'
            command += f' --train-ratio {train_ratio}'
            command += f' --random-seed {random_seed}'
            
            # Run command asynchronously
            result = job_manager.run_job_async(job_id, command)
            result['job_id'] = job_id
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @evaluation_bp.route('/api/evaluate-models', methods=['POST'])
    def evaluate_models():
        """Evaluate multiple models using the CLI"""
        try:
            data = request.get_json()
            
            # Extract parameters from frontend
            servers = data.get('servers', [])
            domain_name = data.get('domain_name', '')
            tasks_filename = data.get('tasks_filename', '')
            output_filename = data.get('output_filename', '')
            models = data.get('models', [])
            max_turns = data.get('max_turns', 30)
            prompt_file = data.get('prompt_file', None)
            num_tasks = data.get('num_tasks', -1)
            
            # Validate required fields
            if not validate_servers(servers):
                return jsonify({'error': 'At least one server path is required'}), 400
            
            error = validate_required_field(domain_name, 'Domain name')
            if error:
                return jsonify({'error': error}), 400
            
            error = validate_required_field(tasks_filename, 'Tasks filename')
            if error:
                return jsonify({'error': error}), 400
            
            if not models or len(models) == 0:
                return jsonify({'error': 'At least one model configuration is required'}), 400
            
            # Construct file paths following the organized structure
            workspace_path = Path(config.get('workspace', {}).get('root', '../workspace'))
            
            # Create absolute paths for validation and directory creation
            input_file_abs = workspace_path / 'data' / domain_name / 'verified_tasks' / tasks_filename
            if output_filename:
                output_file_abs = workspace_path / 'data' / domain_name / 'evaluations' / output_filename
            else:
                output_file_abs = workspace_path / 'data' / domain_name / 'evaluations' / f"evaluation_results.jsonl"
            
            # Create relative paths for CLI commands (since CLI runs from workspace)
            input_file = Path('data') / domain_name / 'verified_tasks' / tasks_filename
            if output_filename:
                output_file = Path('data') / domain_name / 'evaluations' / output_filename
            else:
                output_file = Path('data') / domain_name / 'evaluations' / f"evaluation_results.jsonl"
            
            # Ensure the output directory exists
            output_file_abs.parent.mkdir(parents=True, exist_ok=True)
            
            # Validate input file exists
            if not input_file_abs.exists():
                return jsonify({'error': f'Input file not found: {input_file_abs}'}), 400
            
            # Create job
            model_names = [model.get('name', 'Unknown') for model in models]
            if len(models) == 1:
                title = f"Evaluate {model_names[0]} on {domain_name} tasks"
            else:
                title = f"Evaluate {len(models)} models on {domain_name} tasks"
            
            job_id = job_manager.create_job(
                "Model Evaluation", 
                title, 
                "evaluate-models"
            )
            
            # Store additional metadata
            job_manager.job_metadata[job_id].update({
                'input_file': str(input_file_abs),
                'output_path': str(output_file_abs),
                'domain_name': domain_name,
                'models': model_names,
                'num_models': len(models)
            })
            
            # Create temporary model config files for each model
            temp_configs = []
            
            try:
                for i, model in enumerate(models):
                    # Create temporary config file
                    temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
                    model_config_data = {
                        'model': model.get('model', 'gpt-4o'),
                        'temperature': model.get('temperature', 0.1),
                        'max_tokens': model.get('max_tokens', 4000),
                        'top_p': model.get('top_p', 0.95)
                    }
                    
                    # Add optional fields if provided
                    if model.get('api_key'):
                        model_config_data['api_key'] = model.get('api_key')
                    if model.get('base_url'):
                        model_config_data['base_url'] = model.get('base_url')
                    
                    json.dump(model_config_data, temp_config, indent=2)
                    temp_config.close()
                    temp_configs.append(temp_config.name)
                
                # Build a compound command that runs all model evaluations sequentially
                # This allows us to track progress through a single job
                commands = []
                
                for i, (model, temp_config_path) in enumerate(zip(models, temp_configs)):
                    model_name = model.get('name', f'model_{i+1}')
                    
                    # Create individual output file for this model
                    model_output_file = output_file.parent / f"{model_name}_evaluation.jsonl"
                    
                    # Build command using the correct CLI format for single evaluation
                    cmd_parts = ['mcp-eval', 'evaluate']
                    
                    # Add servers - format each server with its arguments (same as task generation/verification)
                    server_specs = build_server_specs(servers)
                    if server_specs:
                        cmd_parts.extend(['--servers'] + server_specs)
                    
                    # Add other parameters
                    cmd_parts.extend([
                        '--tasks-file', str(input_file),
                        '--model-config', temp_config_path,
                        '--output', str(model_output_file),
                        '--max-turns', str(max_turns)
                    ])
                    
                    # Add optional parameters
                    if num_tasks > 0:
                        cmd_parts.extend(['--num-tasks', str(num_tasks)])
                    
                    if prompt_file:
                        cmd_parts.extend(['--prompt-file', prompt_file])
                    
                    # Convert to shell command string
                    command = ' '.join([f'"{part}"' if ' ' in part else part for part in cmd_parts])
                    commands.append(f'echo "Starting evaluation for {model_name}..." && {command}')
                
                # Join all commands with && to run them sequentially
                full_command = ' && '.join(commands)
                
                # Add cleanup command to remove temporary config files
                cleanup_command = f'rm -f {" ".join(temp_configs)}'
                full_command += f' && {cleanup_command}'
                
                # Run command asynchronously
                result = job_manager.run_job_async(job_id, full_command)
                result['job_id'] = job_id
                result['input_file'] = str(input_file_abs)
                result['output_path'] = str(output_file_abs)
                result['domain_name'] = domain_name
                
                return jsonify(result)
                
            except Exception as e:
                # Clean up temp files if something goes wrong during setup
                for temp_config in temp_configs:
                    try:
                        os.unlink(temp_config)
                    except:
                        pass
                raise e
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return evaluation_bp 