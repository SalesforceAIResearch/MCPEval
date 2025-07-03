import json
from pathlib import Path
from flask import Blueprint, jsonify, request


def create_tasks_routes(config, job_manager):
    """Create task-related route handlers"""
    tasks_bp = Blueprint('tasks', __name__)

    @tasks_bp.route('/api/generate-tasks', methods=['POST'])
    def generate_tasks():
        """Generate tasks using the CLI"""
        try:
            data = request.get_json()
            
            # Extract parameters
            config_path = data.get('config', '')
            dataset_name = data.get('dataset', '')
            model = data.get('model', config.get('defaults', {}).get('generation_model', 'gpt-4'))
            num_tasks = data.get('num_tasks', config.get('defaults', {}).get('num_tasks', 10))
            output_file = data.get('output_file', f'{dataset_name}_tasks.jsonl')
            temperature = data.get('temperature', 0.8)
            max_tokens = data.get('max_tokens', 2000)
            
            # Validate required fields
            if not config_path or not dataset_name:
                return jsonify({'error': 'Config path and dataset name are required'}), 400
            
            # Create job
            job_id = job_manager.create_job("Task Generation", f"Generate {num_tasks} tasks for {dataset_name}", "generate-tasks")
            
            # Build command
            command = f'uv run python -m mcp_eval_llm.cli.mcp_task_generator.generate'
            command += f' --config "{config_path}"'
            command += f' --dataset-name "{dataset_name}"'
            command += f' --model "{model}"'
            command += f' --num-tasks {num_tasks}'
            command += f' --output-file "{output_file}"'
            command += f' --temperature {temperature}'
            command += f' --max-tokens {max_tokens}'
            
            # Run command asynchronously
            result = job_manager.run_job_async(job_id, command)
            result['job_id'] = job_id
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @tasks_bp.route('/api/verify-tasks', methods=['POST'])
    def verify_tasks():
        """Verify tasks using the CLI"""
        try:
            data = request.get_json()
            
            # Extract parameters
            input_file = data.get('input_file', '')
            config_path = data.get('config', '')
            model = data.get('model', config.get('defaults', {}).get('judge_model', 'gpt-4'))
            output_file = data.get('output_file', input_file.replace('.jsonl', '_verified.jsonl'))
            max_concurrent = data.get('max_concurrent', config.get('defaults', {}).get('max_concurrent', 5))
            
            # Validate required fields
            if not input_file or not config_path:
                return jsonify({'error': 'Input file and config path are required'}), 400
            
            # Create job
            job_id = job_manager.create_job("Task Verification", f"Verify tasks in {input_file}", "verify-tasks")
            
            # Build command
            command = f'uv run python -m mcp_eval_llm.cli.mcp_task_verifier.verify'
            command += f' --input-file "{input_file}"'
            command += f' --config "{config_path}"'
            command += f' --model "{model}"'
            command += f' --output-file "{output_file}"'
            command += f' --max-concurrent {max_concurrent}'
            
            # Run command asynchronously
            result = job_manager.run_job_async(job_id, command)
            result['job_id'] = job_id
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @tasks_bp.route('/api/evaluate-model', methods=['POST'])
    def evaluate_model():
        """Evaluate a model using the CLI"""
        try:
            data = request.get_json()
            
            # Extract parameters
            tasks_file = data.get('tasks_file', '')
            model_config = data.get('model_config', '')
            output_dir = data.get('output_dir', 'results')
            max_concurrent = data.get('max_concurrent', config.get('defaults', {}).get('max_concurrent', 5))
            train_ratio = data.get('train_ratio', config.get('defaults', {}).get('train_ratio', 0.8))
            random_seed = data.get('random_seed', config.get('defaults', {}).get('random_seed', 42))
            
            # Validate required fields
            if not tasks_file or not model_config:
                return jsonify({'error': 'Tasks file and model config are required'}), 400
            
            # Create job
            job_id = job_manager.create_job("Model Evaluation", f"Evaluate model with {tasks_file}", "evaluate-model")
            
            # Build command
            command = f'uv run python -m mcp_eval_llm.cli.mcp_model_evaluator.evaluate'
            command += f' --tasks-file "{tasks_file}"'
            command += f' --model-config "{model_config}"'
            command += f' --output-dir "{output_dir}"'
            command += f' --max-concurrent {max_concurrent}'
            command += f' --train-ratio {train_ratio}'
            command += f' --random-seed {random_seed}'
            
            # Run command asynchronously
            result = job_manager.run_job_async(job_id, command)
            result['job_id'] = job_id
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @tasks_bp.route('/api/analyze-results', methods=['POST'])
    def analyze_results():
        """Analyze evaluation results using the CLI"""
        try:
            data = request.get_json()
            
            # Extract parameters
            results_dir = data.get('results_dir', '')
            model = data.get('model', config.get('defaults', {}).get('judge_model', 'gpt-4'))
            output_file = data.get('output_file', 'analysis_report.md')
            
            # Validate required fields
            if not results_dir:
                return jsonify({'error': 'Results directory is required'}), 400
            
            # Create job
            job_id = job_manager.create_job("Results Analysis", f"Analyze results in {results_dir}", "analyze-results")
            
            # Build command
            command = f'uv run python -m mcp_eval_llm.cli.analyzer.analyze'
            command += f' --results-dir "{results_dir}"'
            command += f' --model "{model}"'
            command += f' --output-file "{output_file}"'
            
            # Run command asynchronously
            result = job_manager.run_job_async(job_id, command)
            result['job_id'] = job_id
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @tasks_bp.route('/api/job/<job_id>', methods=['GET'])
    def get_job_status(job_id):
        """Get job status and progress"""
        try:
            status = job_manager.get_job_status(job_id)
            if status is None:
                return jsonify({'error': 'Job not found'}), 404
            return jsonify(status)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return tasks_bp 