from flask import Blueprint, jsonify, request
from pathlib import Path


def create_llm_judge_routes(config, job_manager):
    """Create LLM judge route handlers"""
    llm_judge_bp = Blueprint('llm_judge', __name__)

    @llm_judge_bp.route('/api/llm-judge', methods=['POST'])
    def llm_judge():
        """Run LLM judge using the CLI"""
        try:
            data = request.get_json()
            
            # Extract parameters from frontend
            input_file = data.get('input_file', None)
            output_dir = data.get('output_dir', None)
            model = data.get('model', 'gpt-4o')
            resume = data.get('resume', False)
            api_key = data.get('api_key', None)
            
            # Validate required fields
            if not input_file:
                return jsonify({'error': 'Input file is required'}), 400
            
            if not output_dir:
                return jsonify({'error': 'Output directory is required'}), 400
            
            # Create job
            input_path = Path(input_file)
            job_id = job_manager.create_job(
                "LLM Judge", 
                f"Judge evaluation for {input_path.name}", 
                "llm-judge"
            )
            
            # Store additional metadata
            workspace_root = config.get('workspace', {}).get('root', '../workspace')
            full_output_dir = Path(workspace_root) / output_dir
            job_manager.job_metadata[job_id].update({
                'input_file': input_file,
                'output_dir': str(full_output_dir),
                'model': model
            })
            
            # Build command using the correct CLI format
            cmd_parts = ['mcp-eval', 'judge']
            
            # Add required parameters
            cmd_parts.extend([
                '--input-file', input_file,
                '--output-dir', output_dir,
                '--model', model
            ])
            
            # Add optional parameters
            if resume:
                cmd_parts.append('--resume')
            
            if api_key:
                cmd_parts.extend(['--api-key', api_key])
            
            # Convert to shell command string
            command = ' '.join([f'"{part}"' if ' ' in part else part for part in cmd_parts])
            
            # Run command asynchronously
            result = job_manager.run_job_async(job_id, command)
            result['job_id'] = job_id
            result['output_dir'] = str(full_output_dir)
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @llm_judge_bp.route('/api/llm-judge-rubric', methods=['POST'])
    def llm_judge_rubric():
        """Run LLM judge rubric analysis using the CLI"""
        try:
            data = request.get_json()
            
            # Extract parameters from frontend
            trajectory_file = data.get('trajectory_file', None)
            completion_file = data.get('completion_file', None)
            output_dir = data.get('output_dir', None)
            api_key = data.get('api_key', None)
            
            # Validate required fields
            if not trajectory_file:
                return jsonify({'error': 'Trajectory file is required'}), 400
            
            if not completion_file:
                return jsonify({'error': 'Completion file is required'}), 400
                
            if not output_dir:
                return jsonify({'error': 'Output directory is required'}), 400
            
            # Create job
            trajectory_path = Path(trajectory_file)
            job_id = job_manager.create_job(
                "LLM Judge Rubric", 
                f"Rubric analysis for {trajectory_path.name}", 
                "llm-judge-rubric"
            )
            
            # Store additional metadata
            workspace_root = config.get('workspace', {}).get('root', '../workspace')
            full_output_dir = Path(workspace_root) / output_dir
            job_manager.job_metadata[job_id].update({
                'trajectory_file': trajectory_file,
                'completion_file': completion_file,
                'output_dir': str(full_output_dir)
            })
            
            # Build command using the correct CLI format
            cmd_parts = ['mcp-eval', 'judge-rubric']
            
            # Add required parameters
            cmd_parts.extend([
                '--trajectory-file', trajectory_file,
                '--completion-file', completion_file,
                '--output-dir', output_dir
            ])
            
            # Add optional parameters
            if api_key:
                cmd_parts.extend(['--api-key', api_key])
            
            # Convert to shell command string
            command = ' '.join([f'"{part}"' if ' ' in part else part for part in cmd_parts])
            
            # Run command asynchronously
            result = job_manager.run_job_async(job_id, command)
            result['job_id'] = job_id
            result['output_dir'] = str(full_output_dir)
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return llm_judge_bp 