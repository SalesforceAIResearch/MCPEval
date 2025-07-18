import os
import tempfile
import shutil
from pathlib import Path
from flask import Blueprint, jsonify, request, send_file
from werkzeug.utils import secure_filename
from utils.file_utils import list_servers, list_backend_files, list_files, list_directories, create_evaluation_pipeline_structure, list_model_configs, list_reports


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

    @files_bp.route('/api/reports', methods=['GET'])
    def reports():
        """List available report files"""
        try:
            result = list_reports(config)
            return jsonify(result)
        except Exception as e:
            return jsonify({'reports': [], 'error': str(e)}), 500

    @files_bp.route('/api/backend-files', methods=['GET'])
    def backend_files():
        """List backend files"""
        try:
            files = list_backend_files(config)
            return jsonify({'files': files})
        except Exception as e:
            return jsonify({'files': [], 'error': str(e)}), 500

    @files_bp.route('/api/model-configs', methods=['GET'])
    def model_configs():
        """List available model configuration files"""
        try:
            configs = list_model_configs(config)
            return jsonify({'configs': configs})
        except Exception as e:
            return jsonify({'configs': [], 'error': str(e)}), 500

    @files_bp.route('/api/directories', methods=['GET'])
    def directories():
        """List available directories"""
        try:
            directory = request.args.get('directory', '.')
            directories = list_directories(config, directory)
            return jsonify({'directories': directories})
        except Exception as e:
            return jsonify({'directories': [], 'error': str(e)}), 500

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

    @files_bp.route('/api/create-pipeline-structure', methods=['POST'])
    def create_pipeline_structure():
        """Create evaluation pipeline structure for a domain"""
        try:
            data = request.get_json()
            domain_name = data.get('domain_name', '').strip()
            
            if not domain_name:
                return jsonify({'error': 'Domain name is required'}), 400
            
            # Sanitize domain name
            import re
            domain_name = re.sub(r'[<>:"/\\|?*]', '_', domain_name)
            
            # Create the pipeline structure
            result = create_evaluation_pipeline_structure(config, domain_name)
            
            return jsonify({
                'success': True,
                'domain_name': result['domain_name'],
                'base_path': result['base_path'],
                'created_directories': result['created_directories']
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @files_bp.route('/api/files/delete', methods=['POST'])
    def delete_files():
        """Delete multiple files"""
        try:
            data = request.get_json()
            file_paths = data.get('filePaths', [])
            
            if not file_paths:
                return jsonify({'error': 'No files specified for deletion'}), 400
            
            # Get root directory from config
            root_dir = config.get('paths', {}).get('root_directory', '..')
            root_path = Path(root_dir)
            
            deleted_files = []
            errors = []
            
            for file_path in file_paths:
                try:
                    full_path = root_path / file_path
                    
                    # Security check: ensure the file is within the allowed directory
                    if not full_path.is_relative_to(root_path):
                        errors.append(f'Access denied for {file_path}')
                        continue
                    
                    if not full_path.exists():
                        errors.append(f'File not found: {file_path}')
                        continue
                    
                    full_path.unlink()
                    deleted_files.append(file_path)
                    
                except Exception as e:
                    errors.append(f'Error deleting {file_path}: {str(e)}')
            
            if errors and not deleted_files:
                return jsonify({'error': 'Failed to delete any files', 'details': errors}), 400
            
            result = {
                'success': True,
                'deleted_files': deleted_files,
                'deleted_count': len(deleted_files)
            }
            
            if errors:
                result['warnings'] = errors
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @files_bp.route('/api/files/merge', methods=['POST'])
    def merge_files():
        """Merge multiple files into a single file"""
        try:
            data = request.get_json()
            file_paths = data.get('filePaths', [])
            output_filename = data.get('outputFileName', '').strip()
            output_directory = data.get('outputDirectory', 'data').strip()
            
            if not file_paths:
                return jsonify({'error': 'No files specified for merging'}), 400
            
            if len(file_paths) < 2:
                return jsonify({'error': 'At least 2 files are required for merging'}), 400
            
            if not output_filename:
                return jsonify({'error': 'Output filename is required'}), 400
            
            # Get root directory from config
            root_dir = config.get('paths', {}).get('root_directory', '..')
            root_path = Path(root_dir)
            
            # Determine output path
            if output_directory:
                output_path = root_path / output_directory / output_filename
            else:
                output_path = root_path / output_filename
            
            # Security check for output path
            if not output_path.is_relative_to(root_path):
                return jsonify({'error': 'Invalid output directory'}), 403
            
            # Create output directory if it doesn't exist
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if output file already exists
            if output_path.exists():
                return jsonify({'error': f'Output file {output_filename} already exists'}), 409
            
            # Collect and validate input files
            input_files = []
            for file_path in file_paths:
                full_path = root_path / file_path
                
                # Security check: ensure the file is within the allowed directory
                if not full_path.is_relative_to(root_path):
                    return jsonify({'error': f'Access denied for {file_path}'}), 403
                
                if not full_path.exists():
                    return jsonify({'error': f'File not found: {file_path}'}), 404
                
                input_files.append(full_path)
            
            # Determine merge strategy based on file extension
            file_ext = output_path.suffix.lower()
            total_lines = 0
            
            with open(output_path, 'w', encoding='utf-8') as output_file:
                for i, input_file in enumerate(input_files):
                    try:
                        with open(input_file, 'r', encoding='utf-8') as f:
                            if file_ext == '.jsonl':
                                # For JSONL files, copy each line (preserving JSON structure)
                                for line in f:
                                    line = line.strip()
                                    if line:  # Skip empty lines
                                        output_file.write(line + '\n')
                                        total_lines += 1
                            else:
                                # For other files, copy content with separators
                                content = f.read().strip()
                                if content:
                                    if i > 0:
                                        output_file.write('\n\n')  # Add separator between files
                                    output_file.write(content)
                                    total_lines += content.count('\n') + 1
                    except Exception as e:
                        # Clean up partial output file
                        if output_path.exists():
                            output_path.unlink()
                        return jsonify({'error': f'Error reading {input_file.name}: {str(e)}'}), 500
            
            # Get output file size
            output_size = output_path.stat().st_size
            
            return jsonify({
                'success': True,
                'output_filename': output_filename,
                'output_path': str(output_path.relative_to(root_path)),
                'merged_files': file_paths,
                'merged_count': len(file_paths),
                'total_lines': total_lines,
                'output_size': output_size
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return files_bp 