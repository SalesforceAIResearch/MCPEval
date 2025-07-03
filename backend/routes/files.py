import os
import tempfile
import shutil
from pathlib import Path
from flask import Blueprint, jsonify, request, send_file
from werkzeug.utils import secure_filename
from utils.file_utils import list_servers, list_backend_files, list_files


def create_files_routes(config, job_manager):
    """Create file-related route handlers"""
    files_bp = Blueprint('files', __name__)

    @files_bp.route('/api/servers', methods=['GET'])
    def servers():
        """List available MCP servers"""
        try:
            result = list_servers(config)
            return jsonify(result)
        except Exception as e:
            return jsonify({'servers': [], 'error': str(e)}), 500

    @files_bp.route('/api/backend-files', methods=['GET'])
    def backend_files():
        """List backend files"""
        try:
            files = list_backend_files(config)
            return jsonify({'files': files})
        except Exception as e:
            return jsonify({'files': [], 'error': str(e)}), 500

    @files_bp.route('/api/files', methods=['GET'])
    def files():
        """List available files"""
        try:
            directory = request.args.get('directory', '.')
            files = list_files(config, directory)
            return jsonify({'files': files})
        except Exception as e:
            return jsonify({'files': [], 'error': str(e)}), 500

    @files_bp.route('/api/download/<path:filename>', methods=['GET'])
    def download_file(filename):
        """Download a file"""
        try:
            # Get root directory from config
            root_dir = config.get('paths', {}).get('root_directory', '..')
            file_path = Path(root_dir) / filename
            
            # Security check: ensure the file is within the allowed directory
            if not file_path.is_relative_to(Path(root_dir)):
                return jsonify({'error': 'Access denied'}), 403
            
            if not file_path.exists():
                return jsonify({'error': 'File not found'}), 404
            
            return send_file(file_path, as_attachment=True)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @files_bp.route('/api/upload', methods=['POST'])
    def upload_file():
        """Upload a file"""
        try:
            if 'file' not in request.files:
                return jsonify({'error': 'No file provided'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            # Check file extension
            allowed_extensions = config.get('files', {}).get('allowed_extensions', ['.jsonl', '.json', '.txt', '.csv', '.yaml', '.yml'])
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in allowed_extensions:
                return jsonify({'error': f'File type {file_ext} not allowed. Allowed types: {", ".join(allowed_extensions)}'}), 400
            
            # Check file size (in MB)
            max_size = config.get('files', {}).get('max_upload_size', 100) * 1024 * 1024  # Convert MB to bytes
            file.seek(0, 2)  # Seek to end
            file_size = file.tell()
            file.seek(0)  # Reset to beginning
            
            if file_size > max_size:
                return jsonify({'error': f'File too large. Maximum size: {max_size // (1024 * 1024)}MB'}), 400
            
            # Save the file
            filename = secure_filename(file.filename)
            uploads_dir = Path(config.get('paths', {}).get('uploads_directory', '../uploads'))
            uploads_dir.mkdir(parents=True, exist_ok=True)
            
            file_path = uploads_dir / filename
            file.save(file_path)
            
            return jsonify({
                'success': True,
                'filename': filename,
                'path': str(file_path.relative_to(Path(config.get('paths', {}).get('root_directory', '..')))),
                'size': file_size
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @files_bp.route('/api/files/<path:filename>', methods=['DELETE'])
    def delete_file(filename):
        """Delete a file"""
        try:
            # Get root directory from config
            root_dir = config.get('paths', {}).get('root_directory', '..')
            file_path = Path(root_dir) / filename
            
            # Security check: ensure the file is within the allowed directory
            if not file_path.is_relative_to(Path(root_dir)):
                return jsonify({'error': 'Access denied'}), 403
            
            if not file_path.exists():
                return jsonify({'error': 'File not found'}), 404
            
            file_path.unlink()
            return jsonify({'success': True, 'message': f'File {filename} deleted successfully'})
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @files_bp.route('/api/file-content/<path:filename>', methods=['GET'])
    def get_file_content(filename):
        """Get file content for viewing"""
        try:
            # Get root directory from config
            root_dir = config.get('paths', {}).get('root_directory', '..')
            file_path = Path(root_dir) / filename
            
            # Security check: ensure the file is within the allowed directory
            if not file_path.is_relative_to(Path(root_dir)):
                return jsonify({'error': 'Access denied'}), 403
            
            if not file_path.exists():
                return jsonify({'error': 'File not found'}), 404
            
            # Read file content (limit to reasonable size)
            max_size = 1024 * 1024  # 1MB limit for viewing
            if file_path.stat().st_size > max_size:
                return jsonify({'error': f'File too large to view (max {max_size // 1024}KB)'}), 400
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return jsonify({'content': content, 'encoding': 'utf-8'})
            except UnicodeDecodeError:
                # Try binary mode for non-text files
                with open(file_path, 'rb') as f:
                    content = f.read()
                return jsonify({'content': content.hex(), 'encoding': 'binary'})
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return files_bp 