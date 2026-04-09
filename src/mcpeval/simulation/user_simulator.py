"""
LLM-powered User Simulator for multi-turn evaluation.

Generates realistic user messages based on a persona, scenario, and conversation history.
"""

import logging
from typing import List, Dict, Any, Optional

from mcpeval.models.llms import OpenAIWrapper
from mcpeval.commons.types import Persona, MultiTurnScenario, ToolDefinition
from mcpeval.commons.prompts import (
    SCENARIO_TYPE_INSTRUCTIONS,
    user_simulator_system_prompt,
    user_simulator_followup_prompt,
    user_simulator_end_check_prompt,
)

logger = logging.getLogger(__name__)


def _format_tool_descriptions(tools: List[ToolDefinition]) -> str:
    """Format tools as human-readable descriptions for the user simulator."""
    if not tools:
        return "No tools available."
    descriptions = []
    for tool in tools:
        desc = getattr(tool, "description", "") or ""
        descriptions.append(f"- {tool.name}: {desc}")
    return "\n".join(descriptions)


def _format_conversation_summary(messages: List[Dict[str, Any]]) -> str:
    """Format conversation history as a readable summary."""
    lines = []
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        if role == "system":
            continue
        if role == "tool":
            tool_name = msg.get("name", "unknown_tool")
            # Truncate long tool results
            result_text = str(content)[:500]
            lines.append(f"[Tool Result ({tool_name})]: {result_text}")
        elif role == "assistant":
            tool_calls = msg.get("tool_calls", [])
            if tool_calls:
                for tc in tool_calls:
                    if isinstance(tc, dict) and "function" in tc:
                        fn_name = tc["function"].get("name", "?")
                        fn_args = tc["function"].get("arguments", "{}")
                        lines.append(f"Assistant [called {fn_name}({fn_args})]")
            if content:
                lines.append(f"Assistant: {content}")
        elif role == "user":
            lines.append(f"User: {content}")
    return "\n".join(lines)


class UserSimulator:
    """LLM-powered user simulator that generates realistic user messages.

    Uses a separate LLM instance to role-play as a user with a given persona,
    generating initial requests and follow-up messages for multi-turn conversations.
    """

    def __init__(
        self,
        llm: OpenAIWrapper,
        persona: Optional[Persona] = None,
    ):
        """
        Args:
            llm: OpenAIWrapper instance for generating user messages.
            persona: Optional persona to role-play. If None, uses a generic user.
        """
        self.llm = llm
        self.persona = persona

    def _get_persona_description(self) -> str:
        if self.persona:
            parts = [self.persona.description]
            if self.persona.communication_style:
                parts.append(
                    f"Communication style: {self.persona.communication_style}"
                )
            if self.persona.expertise_level:
                parts.append(f"Expertise level: {self.persona.expertise_level}")
            return " | ".join(parts)
        return "A typical user with moderate technical knowledge."

    def generate_initial_message(
        self,
        scenario: MultiTurnScenario,
        available_tools: List[ToolDefinition],
    ) -> str:
        """Generate the first user message to kick off the conversation.

        Args:
            scenario: The multi-turn scenario defining the goal and context.
            available_tools: Tools the assistant has access to (shown as descriptions).

        Returns:
            The initial user message text.
        """
        scenario_type_instructions = SCENARIO_TYPE_INSTRUCTIONS.get(
            scenario.scenario_type,
            SCENARIO_TYPE_INSTRUCTIONS["standard"],
        )

        system_msg = user_simulator_system_prompt.format(
            persona_description=self._get_persona_description(),
            scenario_goal=scenario.goal,
            scenario_description=scenario.description,
            tool_descriptions=_format_tool_descriptions(available_tools),
            scenario_type_instructions=scenario_type_instructions,
        )

        user_msg = "Generate your first message to the assistant."
        if scenario.initial_context:
            user_msg += f"\n\nAdditional context you know: {scenario.initial_context}"

        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ]

        response = self.llm.chat_completion(messages=messages)
        content = response["choices"][0]["message"].get("content", "")

        logger.debug(f"UserSimulator initial message: {content[:200]}")
        return content.strip()

    def generate_followup_message(
        self,
        scenario: MultiTurnScenario,
        conversation_history: List[Dict[str, Any]],
        turn_number: int,
        available_tools: List[ToolDefinition],
    ) -> str:
        """Generate a follow-up user message based on conversation history.

        Args:
            scenario: The multi-turn scenario.
            conversation_history: Full conversation so far (system + user + assistant + tool messages).
            turn_number: Current turn number (1-indexed).
            available_tools: Tools the assistant has access to.

        Returns:
            The follow-up user message text.
        """
        scenario_type_instructions = SCENARIO_TYPE_INSTRUCTIONS.get(
            scenario.scenario_type,
            SCENARIO_TYPE_INSTRUCTIONS["standard"],
        )

        system_msg = user_simulator_system_prompt.format(
            persona_description=self._get_persona_description(),
            scenario_goal=scenario.goal,
            scenario_description=scenario.description,
            tool_descriptions=_format_tool_descriptions(available_tools),
            scenario_type_instructions=scenario_type_instructions,
        )

        followup_prompt = user_simulator_followup_prompt.format(
            scenario_goal=scenario.goal,
            turn_number=turn_number,
            persona_description=self._get_persona_description(),
        )

        # Build messages: system prompt + conversation summary + followup instruction
        conv_summary = _format_conversation_summary(conversation_history)
        messages = [
            {"role": "system", "content": system_msg},
            {
                "role": "user",
                "content": f"Here is the conversation so far:\n\n{conv_summary}\n\n{followup_prompt}",
            },
        ]

        response = self.llm.chat_completion(messages=messages)
        content = response["choices"][0]["message"].get("content", "")

        logger.debug(f"UserSimulator followup (turn {turn_number}): {content[:200]}")
        return content.strip()

    def should_end_conversation(
        self,
        scenario: MultiTurnScenario,
        conversation_history: List[Dict[str, Any]],
        turn_number: int,
    ) -> bool:
        """Determine if the simulated user should end the conversation.

        Args:
            scenario: The multi-turn scenario.
            conversation_history: Full conversation so far.
            turn_number: Current turn number.

        Returns:
            True if the conversation should end.
        """
        # Hard cap: always end at max_turns
        if turn_number > scenario.max_turns:
            return True

        conv_summary = _format_conversation_summary(conversation_history)
        prompt = user_simulator_end_check_prompt.format(
            scenario_goal=scenario.goal,
            conversation_summary=conv_summary,
        )

        messages = [
            {
                "role": "system",
                "content": "You determine whether a user's goal has been accomplished in a conversation. Respond with ONLY 'yes' or 'no'.",
            },
            {"role": "user", "content": prompt},
        ]

        response = self.llm.chat_completion(messages=messages)
        content = response["choices"][0]["message"].get("content", "").strip().lower()

        is_done = content.startswith("yes")
        logger.debug(
            f"UserSimulator end check (turn {turn_number}): {content} -> end={is_done}"
        )
        return is_done
