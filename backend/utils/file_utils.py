import os
from datetime import datetime
from pathlib import Path


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


def list_servers(config):
    """List available MCP servers"""
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
    config_dir = Path(__file__).parent.parent  # backend directory
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
                            config_dir = Path(__file__).parent.parent  # backend directory
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
                            config_dir = Path(__file__).parent.parent  # backend directory
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
    
    return {
        'servers': servers,
        'debug_info': debug_info
    }


def list_backend_files(config):
    """List backend files"""
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
                        config_dir = Path(__file__).parent.parent  # backend directory
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
                        config_dir = Path(__file__).parent.parent  # backend directory
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
    
    return files


def list_files(config, directory='.'):
    """List available files"""
    root_dir = config.get('paths', {}).get('root_directory', '..')
    base_path = Path(root_dir) / directory
    
    if not base_path.exists():
        raise FileNotFoundError('Directory not found')
    
    files = []
    for item in base_path.iterdir():
        if item.is_file() and not item.name.startswith('.'):
            files.append({
                'name': item.name,
                'path': str(item.relative_to(Path(root_dir))),
                'size': item.stat().st_size,
                'modified': datetime.fromtimestamp(item.stat().st_mtime).isoformat()
            })
    
    return files 