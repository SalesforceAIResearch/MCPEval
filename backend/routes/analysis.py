from flask import Blueprint, jsonify, request
from pathlib import Path
from datetime import datetime
import os
from typing import Dict, Any, Tuple, Optional


def create_analysis_routes(config, job_manager):
    """Create analysis route handlers with two clean APIs:
    1. Basic analysis - AI report without charts
    2. Comprehensive analysis - AI report with charts
    """
    analysis_bp = Blueprint('analysis', __name__)

    def _validate_request(data) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, str]]]:
        """Validate analysis request data"""
        results_dir = data.get('results_dir', '')
        ground_truth = data.get('ground_truth', '')
        model = data.get('model', config.get('defaults', {}).get('judge_model', 'gpt-4'))
        
        if not results_dir:
            return None, {'error': 'results_dir is required'}
        
        if not ground_truth:
            return None, {'error': 'ground_truth is required'}
        
        if not model:
            return None, {'error': 'model is required'}
            
        return {
            'results_dir': results_dir,
            'ground_truth': ground_truth,
            'model': model
        }, None

    def _prepare_paths(domain_name, model_name, analysis_type, custom_summary_filename='', custom_report_filename=''):
        """Prepare file paths for analysis outputs with timestamps"""
        # Get workspace root path
        workspace_path = Path(config.get('workspace', {}).get('root', 'workspace'))
        
        # Generate timestamp for unique file names
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create reports directory structure (for AI reports)
        reports_dir = workspace_path / 'data' / domain_name / 'reports'
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Create analysis directory structure (for analysis summary files)
        analysis_dir = workspace_path / 'data' / domain_name / 'analysis'
        analysis_dir.mkdir(parents=True, exist_ok=True)
        
        # Create charts directory for comprehensive analysis
        if analysis_type == 'comprehensive':
            charts_dir = reports_dir / 'charts'
            charts_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate file names - use custom names if provided, otherwise timestamps
        if custom_summary_filename:
            summary_file = analysis_dir / custom_summary_filename
        else:
            summary_file = analysis_dir / f"{model_name}_task_evaluation_summary_analysis_{timestamp}.json"
        
        if custom_report_filename:
            report_file = reports_dir / custom_report_filename
        else:
            if analysis_type == 'comprehensive':
                report_file = reports_dir / f"{model_name}_comprehensive_report_{timestamp}.md"
            else:
                report_file = reports_dir / f"{model_name}_basic_report_{timestamp}.md"
        
        return {
            'workspace_path': workspace_path,
            'reports_dir': reports_dir,
            'analysis_dir': analysis_dir,
            'summary_file': summary_file,
            'report_file': report_file,
            'timestamp': timestamp
        }

    @analysis_bp.route('/api/analyze-results/basic', methods=['POST'])
    def analyze_basic():
        """Generate basic AI report without charts"""
        try:
            data = request.get_json()
            validated_data, error = _validate_request(data)
            if error:
                return jsonify(error), 400
            
            # At this point, validated_data is guaranteed to be not None
            assert validated_data is not None
            
            # Extract domain from results_dir path
            results_path = validated_data['results_dir']
            domain_name = 'healthcare'  # Default fallback
            if 'data/' in results_path:
                path_parts = results_path.split('/')
                if 'data' in path_parts:
                    data_index = path_parts.index('data')
                    if data_index + 1 < len(path_parts):
                        domain_name = path_parts[data_index + 1]
            
            # Extract custom filenames from request
            custom_summary_filename = data.get('summary_filename', '')
            custom_report_filename = data.get('report_filename', '')
            
            # Prepare paths with timestamps
            paths = _prepare_paths(domain_name, validated_data['model'], 'basic', custom_summary_filename, custom_report_filename)
            
            # Prepare full file paths relative to workspace
            workspace_path = paths['workspace_path']
            results_full_path = workspace_path / validated_data['results_dir']
            ground_truth_full_path = workspace_path / validated_data['ground_truth']
            
            # Validate input files exist
            if not results_full_path.exists():
                return jsonify({'error': f'Results file not found: {results_full_path}'}), 400
            
            if not ground_truth_full_path.exists():
                return jsonify({'error': f'Ground truth file not found: {ground_truth_full_path}'}), 400
            
            # Create job for basic analysis
            job_id = job_manager.create_job(
                'basic_analysis',
                f"Basic analysis for {validated_data['model']} - {domain_name}",
                'analyze-basic'
            )
            
            # Store metadata
            job_manager.job_metadata[job_id].update({
                'domain_name': domain_name,
                'model': validated_data['model'],
                'analysis_type': 'basic',
                'output_files': {
                    'report': str(paths['report_file']),
                    'summary': str(paths['summary_file'])
                },
                'timestamp': paths['timestamp']
            })
            
            # Build command string
            cmd = ' '.join([
                'mcp-eval', 'analyze',
                '--predictions', f'"{results_full_path}"',
                '--ground-truth', f'"{ground_truth_full_path}"',
                '--generate-report',
                '--report-model', validated_data['model'],
                '--report-output', f'"{paths["report_file"]}"',
                '--analysis-output', f'"{paths["summary_file"]}"'
            ])
            
            # Run analysis in background
            result = job_manager.run_job_async(job_id, cmd)
            result.update({
                'job_id': job_id,
                'domain_name': domain_name,
                'output_files': {
                    'report': str(paths['report_file']),
                    'summary': str(paths['summary_file'])
                },
                'timestamp': paths['timestamp']
            })
            
            return jsonify(result), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @analysis_bp.route('/api/analyze-results/comprehensive', methods=['POST'])
    def analyze_comprehensive():
        """Generate comprehensive AI report with charts"""
        try:
            data = request.get_json()
            validated_data, error = _validate_request(data)
            if error:
                return jsonify(error), 400
            
            # At this point, validated_data is guaranteed to be not None
            assert validated_data is not None
            
            # Extract domain from results_dir path
            results_path = validated_data['results_dir']
            domain_name = 'healthcare'  # Default fallback
            if 'data/' in results_path:
                path_parts = results_path.split('/')
                if 'data' in path_parts:
                    data_index = path_parts.index('data')
                    if data_index + 1 < len(path_parts):
                        domain_name = path_parts[data_index + 1]
            
            # Extract custom filenames from request
            custom_summary_filename = data.get('summary_filename', '')
            custom_report_filename = data.get('report_filename', '')
            
            # Prepare paths with timestamps
            paths = _prepare_paths(domain_name, validated_data['model'], 'comprehensive', custom_summary_filename, custom_report_filename)
            
            # Prepare full file paths relative to workspace
            workspace_path = paths['workspace_path']
            results_full_path = workspace_path / validated_data['results_dir']
            ground_truth_full_path = workspace_path / validated_data['ground_truth']
            
            # Validate input files exist
            if not results_full_path.exists():
                return jsonify({'error': f'Results file not found: {results_full_path}'}), 400
            
            if not ground_truth_full_path.exists():
                return jsonify({'error': f'Ground truth file not found: {ground_truth_full_path}'}), 400
            
            # Create job for comprehensive analysis
            job_id = job_manager.create_job(
                'comprehensive_analysis',
                f"Comprehensive analysis with charts for {validated_data['model']} - {domain_name}",
                'analyze-comprehensive'
            )
            
            # Store metadata
            job_manager.job_metadata[job_id].update({
                'domain_name': domain_name,
                'model': validated_data['model'],
                'analysis_type': 'comprehensive',
                'output_files': {
                    'report': str(paths['report_file']),
                    'summary': str(paths['summary_file']),
                    'charts_directory': str(paths['reports_dir'] / 'charts')
                },
                'timestamp': paths['timestamp']
            })
            
            # Build command string for comprehensive analysis
            # Single command to generate summary, report, and charts all at once
            cmd = ' '.join([
                'mcp-eval', 'analyze',
                '--predictions', f'"{results_full_path}"',
                '--ground-truth', f'"{ground_truth_full_path}"',
                '--generate-report',
                '--include-charts',
                '--report-model', validated_data['model'],
                '--report-output', f'"{paths["report_file"]}"',
                '--analysis-output', f'"{paths["summary_file"]}"',
                '--chart-formats', 'html', 'png', 'svg'
            ])
            
            # Run analysis in background
            result = job_manager.run_job_async(job_id, cmd)
            result.update({
                'job_id': job_id,
                'domain_name': domain_name,
                'output_files': {
                    'report': str(paths['report_file']),
                    'summary': str(paths['summary_file']),
                    'charts_directory': str(paths['reports_dir'] / 'charts')
                },
                'timestamp': paths['timestamp']
            })
            
            return jsonify(result), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @analysis_bp.route('/api/jobs/<job_id>', methods=['GET'])
    def get_job_status(job_id):
        """Get job status"""
        try:
            job = job_manager.get_job_status(job_id)
            if not job:
                return jsonify({'error': 'Job not found'}), 404
            return jsonify(job), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @analysis_bp.route('/api/jobs/<job_id>/kill', methods=['POST'])
    def kill_job(job_id):
        """Kill a running job"""
        try:
            success = job_manager.kill_job(job_id)
            if success:
                return jsonify({'message': 'Job killed successfully'}), 200
            else:
                return jsonify({'error': 'Job not found or already completed'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return analysis_bp 