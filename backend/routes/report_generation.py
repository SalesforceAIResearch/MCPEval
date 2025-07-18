from flask import Blueprint, jsonify, request
from pathlib import Path
from .task_utils import generate_output_path, validate_servers, extract_server_name


def create_report_generation_routes(config, job_manager):
    """Create report generation route handlers"""
    report_generation_bp = Blueprint('report_generation', __name__)

    @report_generation_bp.route('/api/generate-report', methods=['POST'])
    def generate_report():
        """Generate AI-powered evaluation reports using the CLI"""
        try:
            data = request.get_json()
            
            # Extract parameters from frontend
            tool_analysis_file = data.get('tool_analysis_file', None)
            llm_judge_file = data.get('llm_judge_file', None)
            output_file = data.get('output_file', None)
            model_name = data.get('model_name', None)
            model = data.get('model', 'gpt-4o')
            include_charts = data.get('include_charts', True)
            api_key = data.get('api_key', None)
            output_folder_name = data.get('output_folder_name', None)
            
            # Validate required fields - at least one analysis file is required
            if not tool_analysis_file and not llm_judge_file:
                return jsonify({'error': 'At least one analysis file (tool analysis or LLM judge) is required'}), 400
            
            # Validate file paths exist
            workspace_root = config.get('workspace', {}).get('root', '../workspace')
            if tool_analysis_file:
                tool_file_path = Path(workspace_root) / tool_analysis_file
                if not tool_file_path.exists():
                    return jsonify({'error': f'Tool analysis file not found: {tool_analysis_file}'}), 400
            
            if llm_judge_file:
                judge_file_path = Path(workspace_root) / llm_judge_file
                if not judge_file_path.exists():
                    return jsonify({'error': f'LLM judge file not found: {llm_judge_file}'}), 400
            
            # Determine report type and output file name
            if tool_analysis_file and llm_judge_file:
                report_type = "Comprehensive Report"
                if not model_name:
                    # Extract model name from one of the files
                    model_name = Path(tool_analysis_file).stem.split('_')[0]
                default_output = f"{model_name}_comprehensive_report.md"
            elif tool_analysis_file:
                report_type = "Tool Usage Report"
                if not model_name:
                    model_name = Path(tool_analysis_file).stem.split('_')[0]
                default_output = f"{model_name}_tool_usage_report.md"
            else:  # llm_judge_file only
                report_type = "LLM Judge Report"
                if not model_name:
                    model_name = Path(llm_judge_file).stem.split('_')[0]
                default_output = f"{model_name}_llm_judge_report.md"
            
            # Generate output path
            if not output_file:
                if tool_analysis_file:
                    base_dir = Path(tool_analysis_file).parent
                elif llm_judge_file:
                    base_dir = Path(llm_judge_file).parent
                else:
                    base_dir = Path("reports")
                output_file = str(base_dir / default_output)
            
            # Ensure the output directory exists
            output_path = Path(workspace_root) / output_file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create job
            job_id = job_manager.create_job(
                "Report Generation", 
                f"Generate {report_type} for {model_name}", 
                "generate-report"
            )
            
            # Store additional metadata
            job_manager.job_metadata[job_id].update({
                'output_path': str(output_path),
                'model_name': model_name,
                'report_type': report_type,
                'tool_analysis_file': tool_analysis_file,
                'llm_judge_file': llm_judge_file
            })
            
            # Build command using the correct CLI format
            cmd_parts = ['mcp-eval', 'report-gen']
            
            # Add analysis files
            if tool_analysis_file:
                cmd_parts.extend(['--tool-analysis-file', tool_analysis_file])
            
            if llm_judge_file:
                cmd_parts.extend(['--llm-judge-file', llm_judge_file])
            
            # Add output file
            cmd_parts.extend(['--output-file', output_file])
            
            # Add model for AI generation
            cmd_parts.extend(['--model', model])
            
            # Add chart option
            if include_charts:
                cmd_parts.append('--include-charts')
            else:
                cmd_parts.append('--no-charts')
            
            # Add API key if provided
            if api_key:
                cmd_parts.extend(['--api-key', api_key])
            
            # Convert to shell command string
            command = ' '.join([f'"{part}"' if ' ' in part else part for part in cmd_parts])
            
            # Run command asynchronously
            result = job_manager.run_job_async(job_id, command)
            result['job_id'] = job_id
            result['output_path'] = str(output_path)
            result['model_name'] = model_name
            result['report_type'] = report_type
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @report_generation_bp.route('/api/detect-analysis-files', methods=['POST'])
    def detect_analysis_files():
        """List all files in a directory"""
        try:
            data = request.get_json()
            directory = data.get('directory', '')
            
            if not directory:
                return jsonify({'error': 'Directory path is required'}), 400
            
            workspace_root = config.get('workspace', {}).get('root', '../workspace')
            search_path = Path(workspace_root) / directory
            
            if not search_path.exists() or not search_path.is_dir():
                return jsonify({'error': f'Directory not found: {directory}'}), 400
            
            # List all files in the directory
            files = []
            for file_path in search_path.iterdir():
                if file_path.is_file():
                    relative_path = str(file_path.relative_to(Path(workspace_root)))
                    files.append({
                        'path': relative_path,
                        'name': file_path.name,
                        'size': file_path.stat().st_size,
                        'extension': file_path.suffix
                    })
            
            # Sort files by name
            files.sort(key=lambda x: x['name'])
            
            return jsonify({
                'directory': directory,
                'files': files,
                'total_files': len(files)
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return report_generation_bp 