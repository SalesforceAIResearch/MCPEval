import os
import tempfile
import shutil
from pathlib import Path
from flask import Blueprint, jsonify, request


def create_workspace_routes(config, job_manager):
    """Create workspace-related route handlers"""
    workspace_bp = Blueprint('workspace', __name__)

    @workspace_bp.route('/api/workspace/create', methods=['POST'])
    def create_workspace():
        """Create a new workspace"""
        try:
            data = request.get_json()
            workspace_name = data.get('name', '').strip()
            
            if not workspace_name:
                return jsonify({'error': 'Workspace name is required'}), 400
            
            # Create workspace directory
            root_dir = config.get('paths', {}).get('root_directory', '..')
            workspace_dir = Path(root_dir) / 'workspaces' / workspace_name
            
            if workspace_dir.exists():
                return jsonify({'error': 'Workspace already exists'}), 400
            
            workspace_dir.mkdir(parents=True, exist_ok=True)
            
            # Create basic structure
            (workspace_dir / 'data').mkdir(exist_ok=True)
            (workspace_dir / 'results').mkdir(exist_ok=True)
            (workspace_dir / 'logs').mkdir(exist_ok=True)
            
            return jsonify({
                'success': True,
                'workspace': workspace_name,
                'path': str(workspace_dir.relative_to(Path(root_dir)))
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @workspace_bp.route('/api/workspace/list', methods=['GET'])
    def list_workspaces():
        """List available workspaces"""
        try:
            root_dir = config.get('paths', {}).get('root_directory', '..')
            workspaces_dir = Path(root_dir) / 'workspaces'
            
            workspaces = []
            if workspaces_dir.exists():
                for workspace_dir in workspaces_dir.iterdir():
                    if workspace_dir.is_dir() and not workspace_dir.name.startswith('.'):
                        workspaces.append({
                            'name': workspace_dir.name,
                            'path': str(workspace_dir.relative_to(Path(root_dir))),
                            'created': workspace_dir.stat().st_ctime
                        })
            
            return jsonify({'workspaces': workspaces})
            
        except Exception as e:
            return jsonify({'workspaces': [], 'error': str(e)}), 500

    @workspace_bp.route('/api/workspace/<workspace_name>', methods=['DELETE'])
    def delete_workspace(workspace_name):
        """Delete a workspace"""
        try:
            root_dir = config.get('paths', {}).get('root_directory', '..')
            workspace_dir = Path(root_dir) / 'workspaces' / workspace_name
            
            if not workspace_dir.exists():
                return jsonify({'error': 'Workspace not found'}), 404
            
            # Security check: ensure we're only deleting from workspaces directory
            if not workspace_dir.is_relative_to(Path(root_dir) / 'workspaces'):
                return jsonify({'error': 'Access denied'}), 403
            
            shutil.rmtree(workspace_dir)
            return jsonify({'success': True, 'message': f'Workspace {workspace_name} deleted'})
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return workspace_bp 