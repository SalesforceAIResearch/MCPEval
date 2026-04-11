"""Backend routes for multi-turn simulation pipeline."""

import json
import os
import shlex
import tempfile
from pathlib import Path

from flask import Blueprint, jsonify, request
from .task_utils import build_server_specs, validate_servers


def create_simulation_routes(config, job_manager):
    """Create simulation route handlers."""
    simulation_bp = Blueprint('simulation', __name__)

    @simulation_bp.route('/api/simulate', methods=['POST'])
    def run_simulation():
        """Run multi-turn user simulation."""
        try:
            data = request.get_json()

            servers = data.get('servers', [])
            if not validate_servers(servers):
                return jsonify({'error': 'At least one server is required'}), 400

            simulator_model = data.get('simulator_model', {})
            agent_model = data.get('agent_model', {})
            if not simulator_model or not agent_model:
                return jsonify({'error': 'Both simulator_model and agent_model configs are required'}), 400

            # Optional params
            scenarios_file = data.get('scenarios_file', '')
            tasks_file = data.get('tasks_file', '')
            output = data.get('output', 'multiturn_results.jsonl')
            num_scenarios = data.get('num_scenarios', -1)
            max_turns = data.get('max_turns', 5)
            max_agent_steps = data.get('max_agent_steps', 10)
            scenario_type = data.get('scenario_type', 'standard')

            # Write temp model config files
            sim_config_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
            json.dump(simulator_model, sim_config_file, indent=2)
            sim_config_file.close()

            agent_config_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
            json.dump(agent_model, agent_config_file, indent=2)
            agent_config_file.close()

            # Build CLI command
            cmd_parts = ['mcp-eval', 'simulate']

            server_specs = build_server_specs(servers)
            if server_specs:
                cmd_parts.extend(['--servers'] + server_specs)

            cmd_parts.extend([
                '--simulator-model-config', shlex.quote(sim_config_file.name),
                '--agent-model-config', shlex.quote(agent_config_file.name),
                '--output', shlex.quote(output),
                '--max-turns', str(max_turns),
                '--max-agent-steps', str(max_agent_steps),
                '--scenario-type', shlex.quote(scenario_type),
            ])

            if scenarios_file:
                cmd_parts.extend(['--scenarios-file', shlex.quote(scenarios_file)])
            if tasks_file:
                cmd_parts.extend(['--tasks-file', shlex.quote(tasks_file)])
            if num_scenarios > 0:
                cmd_parts.extend(['--num-scenarios', str(num_scenarios)])

            cmd = ' '.join(cmd_parts)

            job_id = job_manager.create_job(
                "Multi-Turn Simulation",
                f"Simulate {num_scenarios if num_scenarios > 0 else 'all'} scenarios",
                "simulate",
            )
            result = job_manager.run_job_async(job_id, cmd)
            result['job_id'] = job_id
            return jsonify(result)

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @simulation_bp.route('/api/generate-scenarios', methods=['POST'])
    def generate_scenarios():
        """Generate multi-turn scenarios."""
        try:
            data = request.get_json()

            servers = data.get('servers', [])
            tasks_file = data.get('tasks_file', '')
            model_config = data.get('model_config', {})
            output = data.get('output', 'scenarios.jsonl')
            num_scenarios = data.get('num_scenarios', -1)
            max_turns = data.get('max_turns', 5)
            scenario_type = data.get('scenario_type', 'standard')

            cmd_parts = ['mcp-eval', 'generate-scenarios']

            if servers:
                server_specs = build_server_specs(servers)
                if server_specs:
                    cmd_parts.extend(['--servers'] + server_specs)

            cmd_parts.extend([
                '--output', shlex.quote(output),
                '--max-turns', str(max_turns),
                '--scenario-type', shlex.quote(scenario_type),
            ])

            if tasks_file:
                cmd_parts.extend(['--tasks-file', shlex.quote(tasks_file)])
            if num_scenarios > 0:
                cmd_parts.extend(['--num-scenarios', str(num_scenarios)])

            # Model config
            if model_config:
                config_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
                json.dump(model_config, config_file, indent=2)
                config_file.close()
                cmd_parts.extend(['--model-config', shlex.quote(config_file.name)])

            cmd = ' '.join(cmd_parts)

            job_id = job_manager.create_job(
                "Scenario Generation",
                f"Generate {num_scenarios if num_scenarios > 0 else ''} scenarios",
                "generate-scenarios",
            )
            result = job_manager.run_job_async(job_id, cmd)
            result['job_id'] = job_id
            return jsonify(result)

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @simulation_bp.route('/api/evaluate-multiturn', methods=['POST'])
    def evaluate_multiturn():
        """Evaluate multi-turn conversation results."""
        try:
            data = request.get_json()

            input_file = data.get('input', '')
            if not input_file:
                return jsonify({'error': 'input file is required'}), 400

            model_config = data.get('model_config', {})
            model = data.get('model', 'gpt-4o')
            output = data.get('output', 'multiturn_evaluation.jsonl')
            num_samples = data.get('num_samples', -1)
            resume = data.get('resume', False)

            cmd_parts = [
                'mcp-eval', 'evaluate-multiturn',
                '--input', shlex.quote(input_file),
                '--output', shlex.quote(output),
                '--model', shlex.quote(model),
            ]

            if num_samples > 0:
                cmd_parts.extend(['--num-samples', str(num_samples)])
            if resume:
                cmd_parts.append('--resume')

            if model_config:
                config_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
                json.dump(model_config, config_file, indent=2)
                config_file.close()
                cmd_parts.extend(['--model-config', shlex.quote(config_file.name)])

            cmd = ' '.join(cmd_parts)

            job_id = job_manager.create_job(
                "Multi-Turn Evaluation",
                f"Evaluate conversations from {input_file}",
                "evaluate-multiturn",
            )
            result = job_manager.run_job_async(job_id, cmd)
            result['job_id'] = job_id
            return jsonify(result)

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return simulation_bp
