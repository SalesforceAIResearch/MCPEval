"""
Multi-Turn Scenario Generator.

Generates multi-turn conversation scenarios from scratch or by converting existing
single-turn tasks into multi-turn scenarios.
"""

import json
import logging
from typing import List, Dict, Any, Optional

from mcpeval.models.llms import OpenAIWrapper
from mcpeval.commons.types import (
    Task,
    Persona,
    MultiTurnScenario,
    ToolDefinition,
    format_tools_for_prompt,
)
from mcpeval.commons.prompts import (
    SCENARIO_TYPE_INSTRUCTIONS,
    multiturn_scenario_generation_system_prompt,
    multiturn_scenario_generation_user_prompt,
    multiturn_task_conversion_system_prompt,
    multiturn_task_conversion_user_prompt,
)
from mcpeval.simulation.personas import DEFAULT_PERSONAS, get_random_persona
from mcpeval.utils.structured_output import parse_llm_json, LLMJsonParseError

logger = logging.getLogger(__name__)


class MultiTurnScenarioGenerator:
    """Generates multi-turn conversation scenarios.

    Supports two modes:
    1. Generate from scratch: Given tools, use LLM to create multi-turn scenarios
    2. Convert existing tasks: Transform single-turn Task objects into MultiTurnScenario
    """

    def __init__(
        self,
        llm: OpenAIWrapper,
        persona_pool: Optional[List[Persona]] = None,
    ):
        """
        Args:
            llm: OpenAIWrapper instance for scenario generation.
            persona_pool: Pool of personas to assign. Uses defaults if None.
        """
        self.llm = llm
        self.persona_pool = persona_pool if persona_pool is not None else DEFAULT_PERSONAS

    def generate_scenario(
        self,
        tools: List[ToolDefinition],
        scenario_type: str = "standard",
        persona: Optional[Persona] = None,
        existing_scenarios: Optional[List[str]] = None,
        max_turns: int = 5,
    ) -> MultiTurnScenario:
        """Generate a new multi-turn scenario from scratch.

        Args:
            tools: Available tool definitions.
            scenario_type: Type of scenario to generate.
            persona: Optional specific persona. Random if None.
            existing_scenarios: List of existing scenario descriptions to avoid duplicates.
            max_turns: Maximum turns for the scenario.

        Returns:
            A new MultiTurnScenario object.
        """
        if persona is None:
            persona = get_random_persona(self.persona_pool)

        type_instructions = SCENARIO_TYPE_INSTRUCTIONS.get(
            scenario_type, SCENARIO_TYPE_INSTRUCTIONS["standard"]
        )

        system_msg = multiturn_scenario_generation_system_prompt.format(
            scenario_type_instructions=type_instructions,
            scenario_type=scenario_type,
        )

        formatted_tools = format_tools_for_prompt(tools)
        existing = "\n".join(existing_scenarios) if existing_scenarios else "None yet."

        user_msg = multiturn_scenario_generation_user_prompt.format(
            formatted_tools=formatted_tools,
            existing_scenarios=existing,
        )

        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ]

        for attempt in range(3):
            try:
                response = self.llm.chat_completion(messages=messages)
                content = response["choices"][0]["message"].get("content", "")
                data = parse_llm_json(content)

                scenario = MultiTurnScenario(
                    name=data["name"],
                    description=data["description"],
                    goal=data["goal"],
                    persona=persona,
                    tools=tools,
                    scenario_type=data.get("scenario_type", scenario_type),
                    max_turns=data.get("max_turns", max_turns),
                    initial_context=data.get("initial_context"),
                )

                logger.info(f"Generated scenario: {scenario.name}")
                return scenario

            except Exception as e:
                logger.warning(
                    f"Attempt {attempt + 1}/3 failed to generate scenario: {e}"
                )
                if attempt == 2:
                    raise ValueError(
                        f"Failed to generate scenario after 3 attempts: {e}"
                    )

    def convert_task_to_scenario(
        self,
        task: Task,
        scenario_type: str = "standard",
        persona: Optional[Persona] = None,
        max_turns: int = 5,
    ) -> MultiTurnScenario:
        """Convert an existing single-turn task into a multi-turn scenario.

        Uses LLM to restructure the task so information is revealed across
        multiple conversation turns rather than all at once.

        Args:
            task: The single-turn Task to convert.
            scenario_type: Type of multi-turn scenario to create.
            persona: Optional specific persona. Random if None.
            max_turns: Maximum turns for the scenario.

        Returns:
            A new MultiTurnScenario derived from the task.
        """
        if persona is None:
            persona = get_random_persona(self.persona_pool)

        type_instructions = SCENARIO_TYPE_INSTRUCTIONS.get(
            scenario_type, SCENARIO_TYPE_INSTRUCTIONS["standard"]
        )

        system_msg = multiturn_task_conversion_system_prompt.format(
            scenario_type_instructions=type_instructions,
            scenario_type=scenario_type,
            max_turns=max_turns,
        )

        formatted_tools = (
            format_tools_for_prompt(task.tools) if task.tools else "No tools specified."
        )

        user_msg = multiturn_task_conversion_user_prompt.format(
            task_name=task.name,
            task_description=task.description,
            task_goal=task.goal,
            formatted_tools=formatted_tools,
        )

        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ]

        for attempt in range(3):
            try:
                response = self.llm.chat_completion(messages=messages)
                content = response["choices"][0]["message"].get("content", "")
                data = parse_llm_json(content)

                scenario = MultiTurnScenario(
                    name=data.get("name", task.name),
                    description=data.get("description", task.description),
                    goal=data.get("goal", task.goal),
                    persona=persona,
                    tools=task.tools,
                    scenario_type=data.get("scenario_type", scenario_type),
                    max_turns=data.get("max_turns", max_turns),
                    initial_context=data.get("initial_context"),
                )

                logger.info(
                    f"Converted task '{task.name}' to scenario: {scenario.name}"
                )
                return scenario

            except Exception as e:
                logger.warning(
                    f"Attempt {attempt + 1}/3 failed to convert task: {e}"
                )
                if attempt == 2:
                    raise ValueError(
                        f"Failed to convert task '{task.name}' after 3 attempts: {e}"
                    )

    def generate_batch(
        self,
        tools: List[ToolDefinition],
        num_scenarios: int,
        scenario_type: str = "standard",
        max_turns: int = 5,
    ) -> List[MultiTurnScenario]:
        """Generate multiple scenarios, tracking existing ones to avoid duplicates.

        Args:
            tools: Available tool definitions.
            num_scenarios: Number of scenarios to generate.
            scenario_type: Type of scenario to generate.
            max_turns: Maximum turns per scenario.

        Returns:
            List of generated MultiTurnScenario objects.
        """
        scenarios = []
        existing_descriptions = []

        for i in range(num_scenarios):
            try:
                persona = get_random_persona(self.persona_pool)
                scenario = self.generate_scenario(
                    tools=tools,
                    scenario_type=scenario_type,
                    persona=persona,
                    existing_scenarios=existing_descriptions,
                    max_turns=max_turns,
                )
                scenarios.append(scenario)
                existing_descriptions.append(
                    f"- {scenario.name}: {scenario.description[:200]}"
                )
                logger.info(
                    f"Generated scenario {i + 1}/{num_scenarios}: {scenario.name}"
                )
            except Exception as e:
                logger.error(f"Failed to generate scenario {i + 1}/{num_scenarios}: {e}")

        return scenarios

    def convert_tasks_batch(
        self,
        tasks: List[Task],
        scenario_type: str = "standard",
        max_turns: int = 5,
    ) -> List[MultiTurnScenario]:
        """Convert a batch of tasks to multi-turn scenarios.

        Args:
            tasks: List of single-turn Task objects to convert.
            scenario_type: Type of multi-turn scenario to create.
            max_turns: Maximum turns per scenario.

        Returns:
            List of converted MultiTurnScenario objects.
        """
        scenarios = []
        for i, task in enumerate(tasks):
            try:
                persona = get_random_persona(self.persona_pool)
                scenario = self.convert_task_to_scenario(
                    task=task,
                    scenario_type=scenario_type,
                    persona=persona,
                    max_turns=max_turns,
                )
                scenarios.append(scenario)
                logger.info(
                    f"Converted task {i + 1}/{len(tasks)}: {task.name} -> {scenario.name}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to convert task {i + 1}/{len(tasks)} '{task.name}': {e}"
                )

        return scenarios
