"""
Conversation Orchestrator for multi-turn user simulation.

Drives the turn-by-turn loop between a UserSimulator and an agent (LLMTaskExecutor),
producing multi-turn conversation data for evaluation.
"""

import time
import logging
from typing import Dict, List, Any, Optional

from mcpeval.models.llms import OpenAIWrapper
from mcpeval.eval.task_executor import LLMTaskExecutor
from mcpeval.commons.types import (
    Task,
    ToolCall,
    TurnResult,
    MultiTurnScenario,
    ToolDefinition,
)
from mcpeval.simulation.user_simulator import UserSimulator

logger = logging.getLogger(__name__)


class ConversationOrchestrator:
    """Drives multi-turn conversations between a user simulator and an agent.

    Each "turn" consists of:
    1. UserSimulator generates a user message
    2. Agent (via LLMTaskExecutor) processes the message with tool calls until it produces a text response
    3. The turn result is recorded

    The orchestrator accumulates the full conversation history across turns,
    passing it to both the user simulator and the agent.
    """

    def __init__(
        self,
        user_simulator: UserSimulator,
        agent_llm: OpenAIWrapper,
        tool_name_to_session: Dict[str, Any],
        tools: List[ToolDefinition],
        max_agent_steps_per_turn: int = 10,
        agent_system_message: Optional[str] = None,
    ):
        """
        Args:
            user_simulator: The LLM-powered user simulator.
            agent_llm: OpenAIWrapper for the agent under test.
            tool_name_to_session: Mapping from tool name to MCP session.
            tools: List of available tool definitions.
            max_agent_steps_per_turn: Max tool-call steps the agent can take per turn.
            agent_system_message: Optional custom system message for the agent.
        """
        self.user_simulator = user_simulator
        self.agent_executor = LLMTaskExecutor(agent_llm)
        self.tool_name_to_session = tool_name_to_session
        self.tools = tools
        self.max_agent_steps_per_turn = max_agent_steps_per_turn
        self.agent_system_message = (
            agent_system_message
            or "You are a helpful assistant completing tasks using tools. "
            "Use the provided tools to help the user accomplish their goals."
        )

    async def run_conversation(
        self,
        scenario: MultiTurnScenario,
    ) -> Dict[str, Any]:
        """Run a full multi-turn conversation for the given scenario.

        Args:
            scenario: The multi-turn scenario to execute.

        Returns:
            Dict containing scenario_id, turns, full_conversation, num_turns,
            overall_success, and metadata.
        """
        start_time = time.time()

        # Initialize conversation with system message
        messages = [{"role": "system", "content": self.agent_system_message}]
        turns: List[TurnResult] = []
        all_tool_calls: List[ToolCall] = []
        overall_success = True

        logger.info(
            f"Starting multi-turn conversation for scenario '{scenario.name}' "
            f"(max_turns={scenario.max_turns}, type={scenario.scenario_type})"
        )

        for turn_num in range(1, scenario.max_turns + 1):
            turn_start = time.time()

            # 1. Generate user message
            try:
                if turn_num == 1:
                    user_text = self.user_simulator.generate_initial_message(
                        scenario, self.tools
                    )
                else:
                    # Check if conversation should end
                    if self.user_simulator.should_end_conversation(
                        scenario, messages, turn_num
                    ):
                        logger.info(
                            f"User simulator decided to end conversation at turn {turn_num}"
                        )
                        break

                    user_text = self.user_simulator.generate_followup_message(
                        scenario, messages, turn_num, self.tools
                    )
            except Exception as e:
                logger.error(f"Error generating user message at turn {turn_num}: {e}")
                overall_success = False
                break

            logger.info(f"Turn {turn_num} - User: {user_text[:100]}...")

            # 2. Add user message to conversation
            messages.append({"role": "user", "content": user_text})

            # 3. Run agent via LLMTaskExecutor
            # Create a minimal Task object (execute_task requires it but we pass messages directly)
            dummy_task = Task(
                name=scenario.name,
                description=scenario.description,
                goal=scenario.goal,
            )

            try:
                success, result = await self.agent_executor.execute_task(
                    task=dummy_task,
                    tools=self.tools,
                    tool_name_to_session=self.tool_name_to_session,
                    messages=messages,  # Pass accumulated conversation
                    max_turns=self.max_agent_steps_per_turn,
                )
            except Exception as e:
                logger.error(f"Error in agent execution at turn {turn_num}: {e}")
                overall_success = False
                break

            # 4. Update messages from executor result (it mutates in-place but also returns)
            messages = result["conversation"]

            # 5. Collect tool calls from this turn
            turn_tool_calls = result.get("tool_calls", [])
            all_tool_calls.extend(turn_tool_calls)

            # 6. Extract agent messages added in this turn
            # (everything after the user message we added)
            agent_messages = []
            found_user = False
            for msg in reversed(messages):
                if msg.get("role") == "user" and msg.get("content") == user_text:
                    break
                agent_messages.insert(0, msg)

            # 7. Record the turn
            turn_result = TurnResult(
                turn_number=turn_num,
                user_message={"role": "user", "content": user_text},
                agent_messages=agent_messages,
                tool_calls_in_turn=turn_tool_calls,
                agent_final_response=result.get("final_response", ""),
            )
            turns.append(turn_result)

            turn_elapsed = time.time() - turn_start
            logger.info(
                f"Turn {turn_num} completed in {turn_elapsed:.2f}s "
                f"({len(turn_tool_calls)} tool calls, "
                f"response: {result.get('final_response', '')[:80]}...)"
            )

            if not success:
                logger.warning(f"Agent reported failure at turn {turn_num}")
                overall_success = False

        elapsed = time.time() - start_time

        # Serialize tool calls for output
        serialized_tool_calls = []
        for tc in all_tool_calls:
            if hasattr(tc, "model_dump"):
                serialized_tool_calls.append(tc.model_dump())
            elif hasattr(tc, "__dict__"):
                serialized_tool_calls.append(tc.__dict__)
            else:
                serialized_tool_calls.append(
                    {"tool_name": str(tc.tool_name), "tool_parameters": tc.tool_parameters}
                )

        # Serialize turn results
        serialized_turns = []
        for t in turns:
            turn_dict = {
                "turn_number": t.turn_number,
                "user_message": t.user_message,
                "agent_messages": t.agent_messages,
                "tool_calls_in_turn": [
                    tc.model_dump() if hasattr(tc, "model_dump") else tc.__dict__
                    for tc in t.tool_calls_in_turn
                ],
                "agent_final_response": t.agent_final_response,
            }
            serialized_turns.append(turn_dict)

        result = {
            "scenario_id": scenario.id,
            "scenario_name": scenario.name,
            "scenario_type": scenario.scenario_type,
            "persona": (
                scenario.persona.model_dump() if scenario.persona else None
            ),
            "num_turns": len(turns),
            "turns": serialized_turns,
            "full_conversation": messages,
            "all_tool_calls": serialized_tool_calls,
            "overall_success": overall_success,
            "metadata": {
                "elapsed_seconds": round(elapsed, 2),
                "max_turns": scenario.max_turns,
                "max_agent_steps_per_turn": self.max_agent_steps_per_turn,
                "scenario_goal": scenario.goal,
                "scenario_description": scenario.description,
            },
        }

        logger.info(
            f"Conversation completed: {len(turns)} turns, "
            f"{len(all_tool_calls)} total tool calls, "
            f"success={overall_success}, {elapsed:.2f}s"
        )

        return result
