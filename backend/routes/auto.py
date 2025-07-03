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
            
            # Extract parameters
            workspace = data.get('workspace', 'default')
            servers = data.get('servers', [])
            model_configs = data.get('model_configs', [])
            num_tasks = data.get('num_tasks', 10)
            max_concurrent = data.get('max_concurrent', 3)
            
            # Validate required fields
            if not servers or not model_configs:
                return jsonify({'error': 'Servers and model configs are required'}), 400
            
            # Create job
            job_id = job_manager.create_job("Auto Workflow", f"Auto eval: {workspace}", "auto")
            
            # Store additional metadata for this job
            job_manager.job_metadata[job_id].update({
                'workspace': workspace,
                'servers': servers
            })
            
            # Build command - using the auto CLI module
            command = f'uv run python -m mcp_eval_llm.cli.auto.auto'
            command += f' --workspace "{workspace}"'
            command += f' --servers {" ".join([f"{s}" for s in servers])}'
            command += f' --model-configs {" ".join([f"{mc}" for mc in model_configs])}'
            command += f' --num-tasks {num_tasks}'
            command += f' --max-concurrent {max_concurrent}'
            
            # Run command asynchronously
            result = job_manager.run_job_async(job_id, command)
            result['job_id'] = job_id
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @auto_bp.route('/api/auto/config/validate', methods=['POST'])
    def validate_auto_config():
        """Validate auto workflow configuration"""
        try:
            data = request.get_json()
            
            workspace = data.get('workspace', '')
            servers = data.get('servers', [])
            model_configs = data.get('model_configs', [])
            
            errors = []
            warnings = []
            
            # Validate workspace
            if not workspace:
                errors.append('Workspace name is required')
            elif workspace in ['', '.', '..', '/']:
                errors.append('Invalid workspace name')
            
            # Validate servers
            if not servers:
                errors.append('At least one server must be selected')
            else:
                root_dir = config.get('paths', {}).get('root_directory', '..')
                for server in servers:
                    server_path = Path(root_dir) / server
                    if not server_path.exists():
                        errors.append(f'Server file not found: {server}')
            
            # Validate model configs
            if not model_configs:
                errors.append('At least one model config must be provided')
            else:
                root_dir = config.get('paths', {}).get('root_directory', '..')
                for model_config in model_configs:
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
            
            # Save configuration
            config_data = {
                'workspace': data.get('workspace', ''),
                'servers': data.get('servers', []),
                'model_configs': data.get('model_configs', []),
                'num_tasks': data.get('num_tasks', 10),
                'max_concurrent': data.get('max_concurrent', 3)
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