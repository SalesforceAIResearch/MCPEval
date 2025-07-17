import json
from pathlib import Path
from flask import Blueprint, jsonify, request


def create_auto_routes(config, job_manager):
    """Create auto workflow route handlers"""
    auto_bp = Blueprint('auto', __name__)

    @auto_bp.route('/api/auto/run', methods=['POST'])
    def run_auto_workflow():
        """Run the automatic evaluation workflow"""
        try:
            data = request.get_json()
            
            # Extract parameters matching the auto CLI structure
            working_dir = data.get('working_dir', '')
            servers = data.get('servers', [])
            task_model = data.get('task_model', 'gpt-4.1-2025-04-14')
            eval_model_configs = data.get('eval_model_configs', [])
            num_tasks = data.get('num_tasks', 200)
            max_turns = data.get('max_turns', 30)
            
            # Optional prompt files
            task_generation_prompt = data.get('task_generation_prompt')
            task_verification_prompt = data.get('task_verification_prompt')
            evaluation_prompt = data.get('evaluation_prompt')
            
            # LLM Judge options
            enable_llm_judge = data.get('enable_llm_judge', False)
            llm_judge_model = data.get('llm_judge_model', 'gpt-4o')
            
            # Validate required fields
            if not working_dir:
                return jsonify({'error': 'Working directory is required'}), 400
            if not servers:
                return jsonify({'error': 'At least one server is required'}), 400
            if not eval_model_configs:
                return jsonify({'error': 'At least one model config is required'}), 400
            
            # Create job
            job_id = job_manager.create_job("Auto Workflow", f"Auto eval: {working_dir}", "auto")
            
            # Store additional metadata for this job
            job_manager.job_metadata[job_id].update({
                'working_dir': working_dir,
                'servers': servers,
                'eval_model_configs': eval_model_configs
            })
            
            # Build command using the correct CLI structure
            command = ['mcp-eval', 'auto']
            
            # Required arguments
            command.extend(['--servers'] + servers)
            command.extend(['--working-dir', working_dir])
            command.extend(['--task-model', task_model])
            command.extend(['--eval-model-configs'] + eval_model_configs)
            
            # Optional arguments
            command.extend(['--num-tasks', str(num_tasks)])
            command.extend(['--max-turns', str(max_turns)])
            
            # Optional prompt files
            if task_generation_prompt:
                command.extend(['--task-generation-prompt', task_generation_prompt])
            if task_verification_prompt:
                command.extend(['--task-verification-prompt', task_verification_prompt])
            if evaluation_prompt:
                command.extend(['--evaluation-prompt', evaluation_prompt])
            
            # LLM Judge options
            if enable_llm_judge:
                command.append('--enable-llm-judge')
                command.extend(['--llm-judge-model', llm_judge_model])
            
            # Convert command list to string for job manager
            command_str = ' '.join([f'"{arg}"' if ' ' in arg else arg for arg in command])
            
            # Run command asynchronously
            result = job_manager.run_job_async(job_id, command_str)
            result['job_id'] = job_id
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @auto_bp.route('/api/auto/config/validate', methods=['POST'])
    def validate_auto_config():
        """Validate auto workflow configuration"""
        try:
            data = request.get_json()
            
            working_dir = data.get('working_dir', '')
            servers = data.get('servers', [])
            eval_model_configs = data.get('eval_model_configs', [])
            task_generation_prompt = data.get('task_generation_prompt')
            task_verification_prompt = data.get('task_verification_prompt')
            evaluation_prompt = data.get('evaluation_prompt')
            
            errors = []
            warnings = []
            
            # Validate working directory
            if not working_dir:
                errors.append('Working directory is required')
            elif working_dir in ['', '.', '..', '/']:
                errors.append('Invalid working directory name')
            
            # Validate servers
            if not servers:
                errors.append('At least one server must be selected')
            else:
                root_dir = config.get('paths', {}).get('root_directory', '..')
                for server in servers:
                    # Handle server specifications with arguments/env vars
                    server_path = server.split(':')[0].split('^')[0]
                    if not server_path.startswith('@'):  # Local server file
                        full_server_path = Path(root_dir) / server_path
                        if not full_server_path.exists():
                            errors.append(f'Server file not found: {server_path}')
            
            # Validate model configs
            if not eval_model_configs:
                errors.append('At least one evaluation model config must be provided')
            else:
                root_dir = config.get('paths', {}).get('root_directory', '..')
                for model_config in eval_model_configs:
                    config_path = Path(root_dir) / model_config
                    if not config_path.exists():
                        errors.append(f'Model config file not found: {model_config}')
                    else:
                        try:
                            with open(config_path, 'r') as f:
                                config_data = json.load(f)
                                if 'model' not in config_data:
                                    warnings.append(f'Model config {model_config} missing "model" field')
                        except json.JSONDecodeError:
                            errors.append(f'Invalid JSON in model config: {model_config}')
                        except Exception as e:
                            warnings.append(f'Could not validate model config {model_config}: {str(e)}')
            
            # Validate optional prompt files
            root_dir = config.get('paths', {}).get('root_directory', '..')
            for prompt_file, prompt_name in [
                (task_generation_prompt, 'Task generation prompt'),
                (task_verification_prompt, 'Task verification prompt'),
                (evaluation_prompt, 'Evaluation prompt')
            ]:
                if prompt_file:
                    prompt_path = Path(root_dir) / prompt_file
                    if not prompt_path.exists():
                        warnings.append(f'{prompt_name} file not found: {prompt_file}')
                    else:
                        try:
                            with open(prompt_path, 'r') as f:
                                json.load(f)
                        except json.JSONDecodeError:
                            warnings.append(f'Invalid JSON in {prompt_name.lower()}: {prompt_file}')
            
            return jsonify({
                'valid': len(errors) == 0,
                'errors': errors,
                'warnings': warnings
            })
            
        except Exception as e:
            return jsonify({
                'valid': False,
                'errors': [str(e)],
                'warnings': []
            }), 500

    @auto_bp.route('/api/auto/config/save', methods=['POST'])
    def save_auto_config():
        """Save auto workflow configuration"""
        try:
            data = request.get_json()
            config_name = data.get('config_name', 'default')
            
            # Get root directory from config
            root_dir = config.get('paths', {}).get('root_directory', '..')
            configs_dir = Path(root_dir) / 'configs' / 'auto'
            configs_dir.mkdir(parents=True, exist_ok=True)
            
            config_file = configs_dir / f'{config_name}.json'
            
            # Save configuration with correct structure
            config_data = {
                'working_dir': data.get('working_dir', ''),
                'servers': data.get('servers', []),
                'task_model': data.get('task_model', 'gpt-4.1-2025-04-14'),
                'eval_model_configs': data.get('eval_model_configs', []),
                'num_tasks': data.get('num_tasks', 200),
                'max_turns': data.get('max_turns', 30),
                'task_generation_prompt': data.get('task_generation_prompt'),
                'task_verification_prompt': data.get('task_verification_prompt'),
                'evaluation_prompt': data.get('evaluation_prompt'),
                'enable_llm_judge': data.get('enable_llm_judge', False),
                'llm_judge_model': data.get('llm_judge_model', 'gpt-4o')
            }
            
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            return jsonify({
                'success': True,
                'config_name': config_name,
                'path': str(config_file.relative_to(Path(root_dir)))
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @auto_bp.route('/api/auto/config/load/<config_name>', methods=['GET'])
    def load_auto_config(config_name):
        """Load auto workflow configuration"""
        try:
            # Get root directory from config
            root_dir = config.get('paths', {}).get('root_directory', '..')
            config_file = Path(root_dir) / 'configs' / 'auto' / f'{config_name}.json'
            
            if not config_file.exists():
                return jsonify({'error': 'Configuration not found'}), 404
            
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            
            return jsonify(config_data)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @auto_bp.route('/api/auto/config/list', methods=['GET'])
    def list_auto_configs():
        """List available auto workflow configurations"""
        try:
            # Get root directory from config
            root_dir = config.get('paths', {}).get('root_directory', '..')
            configs_dir = Path(root_dir) / 'configs' / 'auto'
            
            configs = []
            if configs_dir.exists():
                for config_file in configs_dir.glob('*.json'):
                    configs.append({
                        'name': config_file.stem,
                        'path': str(config_file.relative_to(Path(root_dir))),
                        'modified': config_file.stat().st_mtime
                    })
            
            return jsonify({'configs': configs})
            
        except Exception as e:
            return jsonify({'configs': [], 'error': str(e)}), 500

    return auto_bp 