import os
import re
from datetime import datetime
from pathlib import Path
from utils.file_utils import create_evaluation_pipeline_structure, get_recommended_output_path


def extract_server_name(server_path):
    """Extract a clean server name from the server path for folder organization"""
    if '/' in server_path:
        # Extract from path like 'mcp_servers/healthcare/server.py' -> 'healthcare'
        parts = server_path.split('/')
        if 'mcp_servers' in parts:
            idx = parts.index('mcp_servers')
            if idx + 1 < len(parts):
                return parts[idx + 1]
        # Fallback to second-to-last part if available
        if len(parts) >= 2:
            return parts[-2]
        return parts[-1].replace('.py', '')
    elif '@' in server_path:
        # Extract from npm package like '@openbnb/mcp-server-airbnb' -> 'airbnb'
        name = server_path.split('/')[-1]
        if name.startswith('mcp-server-'):
            return name[11:]  # Remove 'mcp-server-' prefix
        return name
    else:
        # Fallback for simple names
        return server_path.replace('.py', '').replace('-', '_')


def generate_output_path(config, servers, custom_folder_name=None, custom_filename=None):
    """Generate organized output path following evaluation pipeline structure"""
    if custom_folder_name:
        # Use user-provided folder name
        server_name = custom_folder_name.strip()
        # Sanitize folder name (remove invalid characters)
        server_name = re.sub(r'[<>:"/\\|?*]', '_', server_name)
    elif not servers:
        server_name = "unknown"
    elif len(servers) == 1:
        server_name = extract_server_name(servers[0].get('path', ''))
    else:
        # Multi-server: use first server name + "_multi"
        server_name = extract_server_name(servers[0].get('path', '')) + "_multi"
    
    # Create the evaluation pipeline structure
    pipeline_info = create_evaluation_pipeline_structure(config, server_name)
    
    # Create filename
    if custom_filename:
        # Use user-provided filename
        filename = custom_filename.strip()
        # Ensure it has .jsonl extension
        if not filename.endswith('.jsonl'):
            filename += '.jsonl'
    else:
        # Generate timestamp-based filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"evaluation_tasks_{timestamp}.jsonl"
    
    # Get the recommended path for task generation (stage 1)
    output_path = get_recommended_output_path(config, server_name, 'generate', filename)
    
    return Path(output_path), server_name


def build_server_specs(servers):
    """Build server specifications for CLI commands"""
    server_specs = []
    for server in servers:
        server_path = server.get('path', '').strip()
        if server_path:
            server_args = server.get('args', [])
            server_env = server.get('env', {})
            
            # Start with server path
            server_spec = server_path
            
            # Add arguments if present
            if server_args:
                server_spec += f":{','.join(server_args)}"
            
            # Add environment variables if present
            if server_env:
                env_parts = []
                for key, value in server_env.items():
                    env_parts.append(f"{key}={value}")
                server_spec += f"^{','.join(env_parts)}"
            
            server_specs.append(server_spec)
    return server_specs


def validate_servers(servers):
    """Validate server configuration"""
    return servers and any(s.get('path', '').strip() for s in servers)


def validate_required_field(value, field_name):
    """Validate required field and return error message if invalid"""
    if not value or not str(value).strip():
        return f'{field_name} is required'
    return None 