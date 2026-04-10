"""
Multi-Turn Conversation Evaluator.

Uses an LLM judge to evaluate multi-turn conversations across multiple dimensions:
clarification handling, context maintenance, tool usage efficiency, goal achievement,
and response quality.
"""

import json
import logging
from typing import Dict, List, Any, Optional

from mcpeval.models.llms import OpenAIWrapper
from mcpeval.commons.prompts import (
    multiturn_evaluation_system_prompt,
    multiturn_evaluation_user_prompt,
)
from mcpeval.utils.structured_output import parse_llm_json, LLMJsonParseError

logger = logging.getLogger(__name__)


def _format_conversation_for_eval(conversation: List[Dict[str, Any]]) -> str:
    """Format a conversation for evaluation display."""
    lines = []
    for msg in conversation:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        if role == "system":
            continue
        elif role == "user":
            lines.append(f"**User**: {content}")
        elif role == "assistant":
            tool_calls = msg.get("tool_calls", [])
            if tool_calls:
                for tc in tool_calls:
                    if isinstance(tc, dict) and "function" in tc:
                        fn_name = tc["function"].get("name", "?")
                        fn_args = tc["function"].get("arguments", "{}")
                        lines.append(f"**Assistant** [Tool Call: {fn_name}({fn_args})]")
            if content:
                lines.append(f"**Assistant**: {content}")
        elif role == "tool":
            tool_name = msg.get("name", "unknown")
            result_text = str(content)[:300]
            lines.append(f"**Tool Result** ({tool_name}): {result_text}")
    return "\n\n".join(lines)


def _format_tool_calls_summary(turns: List[Dict[str, Any]]) -> str:
    """Format a summary of tool calls across turns."""
    lines = []
    for turn in turns:
        turn_num = turn.get("turn_number", "?")
        tool_calls = turn.get("tool_calls_in_turn", [])
        if tool_calls:
            call_strs = []
            for tc in tool_calls:
                name = tc.get("tool_name", "?")
                params = tc.get("tool_parameters", {})
                call_strs.append(f"{name}({json.dumps(params)[:200]})")
            lines.append(f"Turn {turn_num}: {', '.join(call_strs)}")
        else:
            lines.append(f"Turn {turn_num}: (no tool calls)")
    return "\n".join(lines) if lines else "No tool calls recorded."


def _parse_eval_response(text: str) -> Dict[str, Any]:
    """Parse evaluation JSON from LLM response."""
    return parse_llm_json(text)


class MultiTurnEvaluator:
    """LLM-based judge for multi-turn conversation quality.

    Evaluates conversations on 5 dimensions (each 0-10):
    - clarification_handling
    - context_maintenance
    - tool_usage_efficiency
    - goal_achievement
    - response_quality
    """

    def __init__(self, llm: OpenAIWrapper):
        """
        Args:
            llm: OpenAIWrapper instance for the judge LLM.
        """
        self.llm = llm

    def evaluate_conversation(
        self,
        conversation_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Evaluate a completed multi-turn conversation.

        Args:
            conversation_result: The output from ConversationOrchestrator.run_conversation().

        Returns:
            Dict with scores, assessment, and per-turn notes.
        """
        scenario_name = conversation_result.get("scenario_name", "Unknown")
        scenario_goal = conversation_result.get("metadata", {}).get(
            "scenario_goal", "Unknown"
        )
        scenario_type = conversation_result.get("scenario_type", "standard")
        persona = conversation_result.get("persona", {})
        persona_desc = (
            f"{persona.get('name', 'Unknown')}: {persona.get('description', 'N/A')}"
            if persona
            else "No persona specified"
        )

        conversation = conversation_result.get("full_conversation", [])
        turns = conversation_result.get("turns", [])

        conv_text = _format_conversation_for_eval(conversation)
        tool_summary = _format_tool_calls_summary(turns)

        system_msg = multiturn_evaluation_system_prompt
        user_msg = multiturn_evaluation_user_prompt.format(
            scenario_name=scenario_name,
            scenario_goal=scenario_goal,
            scenario_type=scenario_type,
            persona_description=persona_desc,
            conversation=conv_text,
            tool_calls_summary=tool_summary,
        )

        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ]

        for attempt in range(3):
            try:
                response = self.llm.chat_completion(messages=messages)
                content = response["choices"][0]["message"].get("content", "")
                scores = _parse_eval_response(content)

                # Compute overall score as average
                dimension_scores = [
                    scores.get("clarification_handling", 0),
                    scores.get("context_maintenance", 0),
                    scores.get("tool_usage_efficiency", 0),
                    scores.get("goal_achievement", 0),
                    scores.get("response_quality", 0),
                ]
                scores["overall_score"] = round(
                    sum(dimension_scores) / len(dimension_scores), 2
                )

                # Attach scenario metadata
                scores["scenario_id"] = conversation_result.get("scenario_id")
                scores["scenario_name"] = scenario_name
                scores["scenario_type"] = scenario_type
                scores["num_turns"] = conversation_result.get("num_turns", 0)

                logger.info(
                    f"Evaluated '{scenario_name}': overall={scores['overall_score']}"
                )
                return scores

            except Exception as e:
                logger.warning(
                    f"Attempt {attempt + 1}/3 failed to evaluate conversation: {e}"
                )
                if attempt == 2:
                    logger.error(f"Failed to evaluate '{scenario_name}' after 3 attempts")
                    return {
                        "scenario_id": conversation_result.get("scenario_id"),
                        "scenario_name": scenario_name,
                        "error": str(e),
                        "overall_score": 0,
                    }

    def evaluate_batch(
        self,
        conversation_results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Evaluate a batch of conversations and compute aggregate metrics.

        Args:
            conversation_results: List of conversation results from the orchestrator.

        Returns:
            Dict with per-conversation scores and aggregate summary.
        """
        evaluations = []
        for i, result in enumerate(conversation_results):
            logger.info(
                f"Evaluating conversation {i + 1}/{len(conversation_results)}"
            )
            eval_result = self.evaluate_conversation(result)
            evaluations.append(eval_result)

        # Compute aggregate metrics
        valid_evals = [e for e in evaluations if "error" not in e]
        if valid_evals:
            dimensions = [
                "clarification_handling",
                "context_maintenance",
                "tool_usage_efficiency",
                "goal_achievement",
                "response_quality",
                "overall_score",
            ]
            summary = {}
            for dim in dimensions:
                values = [e.get(dim, 0) for e in valid_evals]
                summary[f"avg_{dim}"] = round(sum(values) / len(values), 2)
                summary[f"min_{dim}"] = min(values)
                summary[f"max_{dim}"] = max(values)

            summary["total_conversations"] = len(conversation_results)
            summary["successful_evaluations"] = len(valid_evals)
            summary["failed_evaluations"] = len(evaluations) - len(valid_evals)
        else:
            summary = {
                "total_conversations": len(conversation_results),
                "successful_evaluations": 0,
                "failed_evaluations": len(evaluations),
            }

        return {
            "evaluations": evaluations,
            "summary": summary,
        }
