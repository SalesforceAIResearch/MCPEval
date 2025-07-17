import os
import yaml
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def load_config(config_path=None):
    """Load configuration from yaml file"""
    if config_path is None:
        config_path = Path(__file__).parent.parent / 'backend.yaml'
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
    
    # Handle workspace variable substitution in paths first
    if 'workspace' in config and 'paths' in config:
        workspace_root = config['workspace'].get('root', '.')
        # Resolve workspace root relative to config directory
        if not os.path.isabs(workspace_root):
            workspace_root = str(config_path.parent / workspace_root)
        
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
    
    # Resolve remaining relative paths
    config_dir = config_path.parent
    for key, value in config.get('paths', {}).items():
        if isinstance(value, str) and not os.path.isabs(value):
            config['paths'][key] = str(config_dir / value)
    
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