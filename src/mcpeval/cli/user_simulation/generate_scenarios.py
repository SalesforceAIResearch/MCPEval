#!/usr/bin/env python3
"""
Scenario Generation CLI Module

Generates multi-turn scenarios (from scratch or by converting existing tasks)
and saves them as JSONL without running the actual simulation.
"""
import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any

from mcpeval.models.llms import OpenAIWrapper
from mcpeval.commons.types import Task, MultiTurnScenario
from mcpeval.synthesis.utils import load_tasks_from_jsonl
from mcpeval.client.openai_client import OpenAIMCPClient
from mcpeval.simulation.scenario_generator import MultiTurnScenarioGenerator
from mcpeval.simulation.personas import DEFAULT_PERSONAS, load_personas_from_file
from mcpeval.utils.cli import setup_colored_logging
from dotenv import load_dotenv

load_dotenv()
setup_colored_logging(level=logging.INFO)
logger = logging.getLogger(__name__)


def _save_scenario_to_jsonl(scenario: MultiTurnScenario, output_file: str) -> None:
    """Append a scenario to a JSONL file."""
    data = {
        "id": scenario.id,
        "name": scenario.name,
        "description": scenario.description,
        "goal": scenario.goal,
        "persona": scenario.persona.model_dump() if scenario.persona else None,
        "scenario_type": scenario.scenario_type,
        "max_turns": scenario.max_turns,
        "initial_context": scenario.initial_context,
    }
    with open(output_file, "a") as f:
        f.write(json.dumps(data) + "\n")


async def run_scenario_generation(args):
    """Run scenario generation."""
    try:
        # Load model config
        model_config = {}
        if hasattr(args, "model_config") and args.model_config:
            config_path = Path(args.model_config)
            if not config_path.exists():
                logger.error(f"Model config file not found: {args.model_config}")
                return False
            with open(config_path, "r") as f:
                model_config = json.load(f)

        # Load personas
        persona_pool = DEFAULT_PERSONAS
        if hasattr(args, "persona_file") and args.persona_file:
            persona_pool = load_personas_from_file(args.persona_file)

        # Create output directory
        output_dir = os.path.dirname(args.output)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Clear output file if it exists
        if os.path.exists(args.output):
            os.remove(args.output)

        # Create LLM wrapper
        llm = OpenAIWrapper(model_config=model_config)

        # Create scenario generator
        generator = MultiTurnScenarioGenerator(llm=llm, persona_pool=persona_pool)

        if hasattr(args, "tasks_file") and args.tasks_file:
            # Convert existing tasks
            tasks = load_tasks_from_jsonl(args.tasks_file)
            if args.num_scenarios > 0:
                tasks = tasks[: args.num_scenarios]
            logger.info(f"Converting {len(tasks)} tasks to multi-turn scenarios")

            # If tasks need tools from MCP server, connect
            if hasattr(args, "server_paths") and args.server_paths:
                api_key = model_config.get("api_key") or os.getenv("OPENAI_API_KEY")
                client = OpenAIMCPClient(
                    model=model_config.get("model", "gpt-4o"),
                    system_prompt="helper",
                    api_key=api_key,
                    base_url=model_config.get("base_url"),
                )
                await client.connect_to_multiple_servers(
                    args.server_paths,
                    args.server_args_list,
                    getattr(args, "server_env_list", []),
                )
                tools = await client.get_all_tools()
                for task in tasks:
                    if not task.tools:
                        task.tools = tools

            scenarios = generator.convert_tasks_batch(
                tasks=tasks,
                scenario_type=args.scenario_type,
                max_turns=args.max_turns,
            )
        else:
            # Generate from scratch - need MCP server for tools
            if not (hasattr(args, "server_paths") and args.server_paths) and not (
                hasattr(args, "server") and args.server
            ):
                logger.error(
                    "Either --tasks-file or --servers must be provided for scenario generation"
                )
                return False

            api_key = model_config.get("api_key") or os.getenv("OPENAI_API_KEY")
            base_url = model_config.get("base_url")
            client_kwargs = {
                "model": model_config.get("model", "gpt-4o"),
                "system_prompt": "helper",
                "api_key": api_key,
            }
            if base_url:
                client_kwargs["base_url"] = base_url

            client = OpenAIMCPClient(**client_kwargs)

            if hasattr(args, "server_paths") and args.server_paths:
                await client.connect_to_multiple_servers(
                    args.server_paths,
                    args.server_args_list,
                    getattr(args, "server_env_list", []),
                )
            else:
                server_args = getattr(args, "server_args", [])
                server_env = getattr(args, "server_env", None)
                await client.connect_to_server(args.server, server_args, server_env)

            tools = await client.get_all_tools()
            num = args.num_scenarios if args.num_scenarios > 0 else 10

            scenarios = generator.generate_batch(
                tools=tools,
                num_scenarios=num,
                scenario_type=args.scenario_type,
                max_turns=args.max_turns,
            )

            await client.cleanup()

        # Save scenarios
        for scenario in scenarios:
            _save_scenario_to_jsonl(scenario, args.output)

        logger.info(
            f"Generated {len(scenarios)} scenarios, saved to {args.output}"
        )
        return True

    except Exception as e:
        logger.exception(f"Error in scenario generation: {e}")
        raise


def main(args):
    """Main entry point for scenario generation CLI."""
    try:
        success = asyncio.run(run_scenario_generation(args))
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Scenario generation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Scenario generation failed: {e}")
        sys.exit(1)
