import os
import json
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


def list_model_configs(config):
    """List available model configuration files"""
    # Get root directory from config
    root_dir = config.get('paths', {}).get('root_directory', '..')
    
    # Common locations for model configs
    potential_locations = [
        Path(root_dir) / 'benchmarks',
        Path(root_dir) / 'eval_models',
        Path(root_dir) / 'model_configs',
        Path(root_dir) / 'configs' / 'models'
    ]
    
    model_configs = []
    
    # Search through all potential locations
    for base_dir in potential_locations:
        if base_dir.exists():
            # Search recursively for JSON files that look like model configs
            for json_file in base_dir.rglob('*.json'):
                if json_file.is_file() and not json_file.name.startswith('.'):
                    try:
                        # Try to read and validate it's a model config
                        with open(json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            
                        # Check if it looks like a model config
                        if 'model' in data or 'models' in data:
                            # Calculate relative path
                            try:
                                relative_path = str(json_file.relative_to(Path(root_dir)))
                            except ValueError:
                                # If file is not under configured root, use project root as fallback
                                config_dir = Path(__file__).parent.parent  # backend directory
                                project_root = config_dir.parent  # project root
                                try:
                                    relative_path = str(json_file.relative_to(project_root))
                                except ValueError:
                                    relative_path = str(json_file)
                            
                            # Extract model information
                            model_name = data.get('model', 'Unknown')
                            if 'models' in data and isinstance(data['models'], list) and data['models']:
                                model_name = data['models'][0].get('model', model_name)
                            
                            model_info = {
                                'name': json_file.name,
                                'path': relative_path,
                                'model': model_name,
                                'description': f"Model config for {model_name}",
                                'size': json_file.stat().st_size,
                                'modified': datetime.fromtimestamp(json_file.stat().st_mtime).isoformat()
                            }
                            
                            # Add additional config details if available
                            if 'temperature' in data:
                                model_info['temperature'] = data['temperature']
                            if 'max_tokens' in data:
                                model_info['max_tokens'] = data['max_tokens']
                            
                            model_configs.append(model_info)
                    except Exception as e:
                        # Skip files that can't be read or aren't valid JSON
                        continue
    
    # Remove duplicates based on path
    seen_paths = set()
    unique_configs = []
    for config in model_configs:
        if config['path'] not in seen_paths:
            seen_paths.add(config['path'])
            unique_configs.append(config)
    
    # Sort by name
    unique_configs.sort(key=lambda x: x['name'])
    
    return unique_configs


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


def list_directories(config, directory='.'):
    """List available directories"""
    root_dir = config.get('paths', {}).get('root_directory', '..')
    base_path = Path(root_dir) / directory
    
    if not base_path.exists():
        raise FileNotFoundError('Directory not found')
    
    directories = []
    for item in base_path.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            # Calculate directory statistics
            file_count = 0
            total_size = 0
            last_modified = None
            
            try:
                for file_item in item.iterdir():
                    if file_item.is_file() and not file_item.name.startswith('.'):
                        file_count += 1
                        total_size += file_item.stat().st_size
                        file_modified = datetime.fromtimestamp(file_item.stat().st_mtime)
                        if last_modified is None or file_modified > last_modified:
                            last_modified = file_modified
            except (OSError, PermissionError):
                # If we can't read the directory, set defaults
                file_count = 0
                total_size = 0
                last_modified = datetime.fromtimestamp(item.stat().st_mtime)
            
            directories.append({
                'name': item.name,
                'path': str(item.relative_to(Path(root_dir))),
                'fileCount': file_count,
                'totalSize': total_size,
                'lastModified': last_modified.isoformat() if last_modified else None
            })
    
    return directories


def create_evaluation_pipeline_structure(config, domain_name: str):
    """Create the recommended directory structure for evaluation pipeline"""
    workspace_root = config.get('workspace', {}).get('root', '../workspace')
    base_path = Path(workspace_root) / 'data' / domain_name
    
    # Define the pipeline stages with cleaner names
    stages = {
        'tasks': 'Generated tasks',
        'verified_tasks': 'Verified and approved tasks',
        'evaluations': 'Model evaluation results', 
        'judging': 'LLM judge scoring',
        'reports': 'Analysis reports and summaries',
        'analysis': 'Comparative analysis and charts'
    }
    
    created_dirs = []
    for stage_name, description in stages.items():
        stage_path = base_path / stage_name
        try:
            stage_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append({
                'path': str(stage_path),
                'name': stage_name,
                'description': description
            })
        except Exception as e:
            print(f"Warning: Could not create directory {stage_path}: {e}")
    
    return {
        'domain_name': domain_name,
        'base_path': str(base_path),
        'created_directories': created_dirs
    }


def get_recommended_output_path(config, domain_name: str, stage: str, filename: str):
    """Get the recommended output path following the evaluation pipeline structure"""
    workspace_root = config.get('workspace', {}).get('root', '../workspace')
    
    # Map operation types to stages with cleaner names
    stage_mapping = {
        'generate': 'tasks',
        'verify': 'verified_tasks', 
        'evaluate': 'evaluations',
        'judge': 'judging',
        'analyze': 'reports',
        'compare': 'analysis'
    }
    
    stage_dir = stage_mapping.get(stage, 'tasks')
    
    # Create the full absolute path for directory creation
    full_output_path = Path(workspace_root) / 'data' / domain_name / stage_dir / filename
    
    # Ensure the directory exists
    full_output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Return relative path from workspace root (since CLI runs from workspace)
    relative_path = Path('data') / domain_name / stage_dir / filename
    return str(relative_path)


def list_reports(config):
    """List available report files"""
    # Get root directory from config
    root_dir = config.get('paths', {}).get('root_directory', '..')
    
    # Common locations for report files
    potential_locations = [
        Path(root_dir) / 'benchmarks',
        Path(root_dir) / 'data',
        Path(root_dir) / 'workspace' / 'data',
        Path(root_dir) / 'reports'
    ]
    
    reports = []
    
    # Search through all potential locations
    for base_dir in potential_locations:
        if base_dir.exists():
            # Search recursively for report files
            for report_file in base_dir.rglob('*'):
                if report_file.is_file() and not report_file.name.startswith('.'):
                    # Look for report-like files
                    if (report_file.suffix.lower() in ['.md', '.json', '.html', '.txt'] and
                        ('report' in report_file.name.lower() or 
                         'analysis' in report_file.name.lower() or
                         'summary' in report_file.name.lower() or
                         'judger' in report_file.name.lower() or
                         report_file.parent.name in ['report', 'reports', 'analysis', 'judging'])):
                        
                        try:
                            # Calculate relative path
                            try:
                                relative_path = str(report_file.relative_to(Path(root_dir)))
                            except ValueError:
                                # If file is not under configured root, use project root as fallback
                                config_dir = Path(__file__).parent.parent  # backend directory
                                project_root = config_dir.parent  # project root
                                try:
                                    relative_path = str(report_file.relative_to(project_root))
                                except ValueError:
                                    relative_path = str(report_file)
                            
                            # Extract domain/benchmark name from path
                            path_parts = report_file.parts
                            domain = None
                            
                            # Try to extract domain from path structure
                            for i, part in enumerate(path_parts):
                                if part in ['benchmarks', 'data'] and i + 1 < len(path_parts):
                                    domain = path_parts[i + 1]
                                    break
                            
                            # Determine report type based on file name and location
                            report_type = 'report'
                            if 'analysis' in report_file.name.lower():
                                report_type = 'analysis'
                            elif 'summary' in report_file.name.lower():
                                report_type = 'summary'
                            elif 'judger' in report_file.name.lower():
                                report_type = 'judging'
                            elif report_file.suffix.lower() == '.json':
                                report_type = 'data'
                            elif report_file.suffix.lower() == '.html':
                                report_type = 'chart'
                            
                            # Try to read a preview of the content
                            preview = None
                            if report_file.suffix.lower() == '.md':
                                try:
                                    with open(report_file, 'r', encoding='utf-8') as f:
                                        content = f.read()
                                        # Extract first few lines as preview
                                        lines = content.split('\n')
                                        preview_lines = []
                                        for line in lines[:10]:
                                            if line.strip() and not line.startswith('#'):
                                                preview_lines.append(line.strip())
                                                if len(preview_lines) >= 3:
                                                    break
                                        if preview_lines:
                                            preview = ' '.join(preview_lines)[:200] + '...'
                                except Exception:
                                    pass
                            elif report_file.suffix.lower() == '.json':
                                try:
                                    with open(report_file, 'r', encoding='utf-8') as f:
                                        data = json.load(f)
                                        if isinstance(data, dict):
                                            # Create a summary of the JSON structure
                                            keys = list(data.keys())[:5]
                                            preview = f"JSON data with keys: {', '.join(keys)}"
                                            if len(data.keys()) > 5:
                                                preview += f" and {len(data.keys()) - 5} more"
                                except Exception:
                                    pass
                            
                            report_info = {
                                'name': report_file.name,
                                'path': relative_path,
                                'domain': domain or 'unknown',
                                'type': report_type,
                                'extension': report_file.suffix.lower(),
                                'size': report_file.stat().st_size,
                                'modified': datetime.fromtimestamp(report_file.stat().st_mtime).isoformat(),
                                'preview': preview
                            }
                            
                            reports.append(report_info)
                        except Exception as e:
                            # Skip files that can't be read
                            continue
    
    # Remove duplicates based on path
    seen_paths = set()
    unique_reports = []
    for report in reports:
        if report['path'] not in seen_paths:
            seen_paths.add(report['path'])
            unique_reports.append(report)
    
    # Sort by domain, then by type, then by name
    unique_reports.sort(key=lambda x: (x['domain'], x['type'], x['name']))
    
    # Add debug information about search paths
    debug_info = {
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
        'reports': unique_reports,
        'debug_info': debug_info
    } 