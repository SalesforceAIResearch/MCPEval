#!/usr/bin/env python3
"""
User Simulation CLI Module

Runs multi-turn conversations between a user simulator LLM and an agent LLM
using MCP servers for tool execution. Outputs conversation data as JSONL.
"""
import os
import sys
import json
import asyncio
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

from mcpeval.models.llms import OpenAIWrapper
from mcpeval.commons.types import Task, MultiTurnScenario, Persona
from mcpeval.synthesis.utils import load_tasks_from_jsonl
from mcpeval.client.openai_client import OpenAIMCPClient
from mcpeval.simulation.user_simulator import UserSimulator
from mcpeval.simulation.conversation_orchestrator import ConversationOrchestrator
from mcpeval.simulation.scenario_generator import MultiTurnScenarioGenerator
from mcpeval.simulation.personas import (
    DEFAULT_PERSONAS,
    load_personas_from_file,
    get_random_persona,
)
from mcpeval.utils.cli import setup_colored_logging
from dotenv import load_dotenv

load_dotenv()
setup_colored_logging(level=logging.INFO)
logger = logging.getLogger(__name__)


def _load_model_config(config_path: str) -> Dict[str, Any]:
    """Load model configuration from a JSON file."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Model config file not found: {config_path}")
    with open(path, "r") as f:
        return json.load(f)


def _save_result_to_jsonl(result: Dict[str, Any], output_file: str) -> None:
    """Append a single result to a JSONL file."""
    with open(output_file, "a") as f:
        f.write(json.dumps(result) + "\n")


def _load_scenarios_from_jsonl(file_path: str) -> List[MultiTurnScenario]:
    """Load multi-turn scenarios from a JSONL file."""
    scenarios = []
    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            # Handle persona if present
            if "persona" in data and data["persona"] is not None:
                data["persona"] = Persona(**data["persona"])
            # Remove fields that are post-execution results
            for field in ["turns", "full_conversation"]:
                data.pop(field, None)
            # Remove tools - they'll be populated from MCP servers
            data.pop("tools", None)
            scenarios.append(MultiTurnScenario(**data))
    return scenarios


async def run_simulation(args):
    """Run the multi-turn user simulation."""
    try:
        # Load model configs
        simulator_config = _load_model_config(args.simulator_model_config)
        agent_config = _load_model_config(args.agent_model_config)

        logger.info(f"Simulator model: {simulator_config.get('model', 'unknown')}")
        logger.info(f"Agent model: {agent_config.get('model', 'unknown')}")

        # Load personas
        persona_pool = DEFAULT_PERSONAS
        if hasattr(args, "persona_file") and args.persona_file:
            persona_pool = load_personas_from_file(args.persona_file)
            logger.info(f"Loaded {len(persona_pool)} custom personas")

        # Create output directory
        output_dir = os.path.dirname(args.output)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Connect to MCP servers
        api_key = agent_config.get("api_key") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key is required")

        base_url = agent_config.get("base_url")
        client_kwargs = {
            "model": agent_config.get("model", "gpt-4o"),
            "system_prompt": "You are a helpful assistant.",
            "api_key": api_key,
        }
        if base_url:
            client_kwargs["base_url"] = base_url

        client = OpenAIMCPClient(**client_kwargs)

        # Connect to servers
        if hasattr(args, "server_paths") and args.server_paths:
            server_paths = args.server_paths
            server_args_list = args.server_args_list
            server_envs = getattr(args, "server_env_list", [])
        else:
            server_paths = [args.server]
            server_args_list = [getattr(args, "server_args", [])]
            server_envs = [getattr(args, "server_env", None)]

        await client.connect_to_multiple_servers(
            server_paths, server_args_list, server_envs
        )
        logger.info(f"Connected to {len(server_paths)} MCP servers")

        # Get available tools
        tools = await client.get_all_tools()
        tool_name_to_session = client.tool_name_to_session
        logger.info(f"Available tools: {[t.name for t in tools]}")

        # Create LLM wrappers
        simulator_llm = OpenAIWrapper(model_config=simulator_config)
        agent_llm = OpenAIWrapper(model_config=agent_config)

        # Load or generate scenarios
        scenarios: List[MultiTurnScenario] = []

        if hasattr(args, "scenarios_file") and args.scenarios_file:
            # Load pre-generated scenarios
            scenarios = _load_scenarios_from_jsonl(args.scenarios_file)
            # Attach tools to scenarios
            for s in scenarios:
                s.tools = tools
            logger.info(f"Loaded {len(scenarios)} scenarios from {args.scenarios_file}")

        elif hasattr(args, "tasks_file") and args.tasks_file:
            # Convert existing tasks to scenarios
            tasks = load_tasks_from_jsonl(args.tasks_file)
            if args.num_scenarios > 0:
                tasks = tasks[: args.num_scenarios]
            logger.info(f"Converting {len(tasks)} tasks to multi-turn scenarios")

            # Attach tools to tasks if they don't have them
            for task in tasks:
                if not task.tools:
                    task.tools = tools

            generator = MultiTurnScenarioGenerator(
                llm=simulator_llm, persona_pool=persona_pool
            )
            scenarios = generator.convert_tasks_batch(
                tasks=tasks,
                scenario_type=args.scenario_type,
                max_turns=args.max_turns,
            )

        else:
            # Generate scenarios from scratch
            num = args.num_scenarios if args.num_scenarios > 0 else 10
            logger.info(f"Generating {num} scenarios from scratch")

            generator = MultiTurnScenarioGenerator(
                llm=simulator_llm, persona_pool=persona_pool
            )
            scenarios = generator.generate_batch(
                tools=tools,
                num_scenarios=num,
                scenario_type=args.scenario_type,
                max_turns=args.max_turns,
            )

        if not scenarios:
            logger.error("No scenarios to simulate")
            return False

        logger.info(f"Running simulation with {len(scenarios)} scenarios")

        # Check for already completed scenarios (resume support)
        already_done = set()
        if os.path.exists(args.output):
            with open(args.output, "r") as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        already_done.add(data.get("scenario_id"))
            logger.info(f"Found {len(already_done)} already completed scenarios")

        # Run simulations
        total_start = time.time()
        completed = 0

        for i, scenario in enumerate(scenarios):
            if scenario.id in already_done:
                logger.info(
                    f"Skipping scenario {i + 1}/{len(scenarios)}: {scenario.id} (already done)"
                )
                continue

            logger.info(
                f"\n{'='*60}\n"
                f"Scenario {i + 1}/{len(scenarios)}: {scenario.name}\n"
                f"Type: {scenario.scenario_type} | "
                f"Persona: {scenario.persona.name if scenario.persona else 'N/A'} | "
                f"Max turns: {scenario.max_turns}\n"
                f"{'='*60}"
            )

            # Create user simulator with scenario's persona
            user_sim = UserSimulator(llm=simulator_llm, persona=scenario.persona)

            # Create orchestrator
            orchestrator = ConversationOrchestrator(
                user_simulator=user_sim,
                agent_llm=agent_llm,
                tool_name_to_session=tool_name_to_session,
                tools=tools,
                max_agent_steps_per_turn=getattr(args, "max_agent_steps", 10),
            )

            try:
                result = await orchestrator.run_conversation(scenario)
                result["model"] = agent_config.get("model", "unknown")

                # Save incrementally
                _save_result_to_jsonl(result, args.output)
                completed += 1

                logger.info(
                    f"Completed scenario {i + 1}/{len(scenarios)}: "
                    f"{result['num_turns']} turns, "
                    f"success={result['overall_success']}"
                )

            except Exception as e:
                logger.error(f"Error in scenario {i + 1}/{len(scenarios)}: {e}")
                error_result = {
                    "scenario_id": scenario.id,
                    "scenario_name": scenario.name,
                    "scenario_type": scenario.scenario_type,
                    "error": str(e),
                    "overall_success": False,
                    "model": agent_config.get("model", "unknown"),
                }
                _save_result_to_jsonl(error_result, args.output)

        total_elapsed = time.time() - total_start

        # Cleanup
        await client.cleanup()

        # Print summary
        logger.info(
            f"\nSimulation complete:\n"
            f"  Total scenarios: {len(scenarios)}\n"
            f"  Completed: {completed}\n"
            f"  Skipped (already done): {len(already_done)}\n"
            f"  Total time: {total_elapsed:.2f}s\n"
            f"  Output: {args.output}"
        )

        return True

    except Exception as e:
        logger.exception(f"Error in simulation: {e}")
        raise


def main(args):
    """Main entry point for the simulation CLI."""
    try:
        success = asyncio.run(run_simulation(args))
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Simulation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Simulation failed: {e}")
        sys.exit(1)
