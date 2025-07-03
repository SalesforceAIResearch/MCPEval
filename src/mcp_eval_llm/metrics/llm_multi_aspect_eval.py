from __future__ import annotations

"""Multi-aspect LLM judge for AI agent execution trajectory evaluation.

This evaluator asks a large-language model to grade an AI agent's execution 
trajectory on a given task. The trajectory includes the full conversation flow:
system message, user task, agent reasoning, tool calls, tool responses, and 
final agent response.

The evaluator provides separate evaluation methods for:
1. **Trajectory Quality** - How well the agent navigates the task execution (including tool usage)
2. **Task Completion** - How well the final outcome addresses the original task

Each method returns individual scores for detailed analysis.

Returned JSON schema requested from the judge LLM (default):

```
{
  "trajectory": {
    "planning": float,              # 0-1 – task decomposition and approach
    "execution_flow": float,        # 0-1 – logical sequence of actions
    "tool_selection": float,        # 0-1 – appropriate tools chosen
    "tool_usage": float,           # 0-1 – correct parameters and interpretation
    "error_handling": float,        # 0-1 – recovery from issues/errors
    "efficiency": float            # 0-1 – optimal use of tools and steps
  },
  "task_completion": {
    "requirement_coverage": float,  # addresses all task requirements
    "accuracy": float,             # correctness of information/analysis
    "completeness": float,         # thoroughness of response
    "usefulness": float           # practical value to user
  },
  "overall": float,               # optional – judge may return, else evaluator computes average
  "comments": str                 # short explanation / feedback
}
```
"""

from dataclasses import dataclass, field
import json
import logging
import os
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator
from dotenv import load_dotenv

from mcp_eval_llm.models.llms import OpenAIWrapper

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result objects
# ---------------------------------------------------------------------------

class TrajectoryScores(BaseModel):
    planning: float = Field(..., ge=0.0, le=1.0)
    execution_flow: float = Field(..., ge=0.0, le=1.0)
    tool_selection: float = Field(..., ge=0.0, le=1.0)
    tool_usage: float = Field(..., ge=0.0, le=1.0)
    adaptability: float = Field(..., ge=0.0, le=1.0)
    efficiency: float = Field(..., ge=0.0, le=1.0)
    context_awareness: float = Field(..., ge=0.0, le=1.0)

    @model_validator(mode='after')
    def _check_values(self):  # noqa: D401 – custom validator
        for field_name, value in self.model_dump().items():
            if not (0.0 <= value <= 1.0):
                raise ValueError(f"Field {field_name} must be between 0 and 1, got {value}")
        return self


class TaskCompletionScores(BaseModel):
    requirement_coverage: float = Field(..., ge=0.0, le=1.0)
    accuracy: float = Field(..., ge=0.0, le=1.0)
    completeness: float = Field(..., ge=0.0, le=1.0)
    usefulness: float = Field(..., ge=0.0, le=1.0)

    @model_validator(mode='after')
    def _check_values(self):  # noqa: D401
        for field_name, value in self.model_dump().items():
            if not (0.0 <= value <= 1.0):
                raise ValueError(f"Field {field_name} must be between 0 and 1, got {value}")
        return self


class TrajectoryEvaluationResult(BaseModel):
    """Result from trajectory evaluation."""
    scores: TrajectoryScores
    overall_score: float = Field(..., ge=0.0, le=1.0)
    comments: str
    raw_response: Dict[str, Any]


class TaskCompletionEvaluationResult(BaseModel):
    """Result from task completion evaluation."""
    scores: TaskCompletionScores
    overall_score: float = Field(..., ge=0.0, le=1.0)
    comments: str
    raw_response: Dict[str, Any]


# ---------------------------------------------------------------------------
# Evaluator
# ---------------------------------------------------------------------------

DEFAULT_TRAJECTORY_KEYS = [
    "planning",
    "execution_flow", 
    "tool_selection",
    "tool_usage",
    "adaptability",
    "efficiency",
    "context_awareness",
]
DEFAULT_TASK_COMPLETION_KEYS = [
    "requirement_coverage",
    "accuracy",
    "completeness", 
    "usefulness",
]


@dataclass
class MultiAspectLLMJudger:
    """LLM evaluator that grades AI agent execution trajectory."""

    model: str = "gpt-4o"
    trajectory_keys: List[str] = field(default_factory=lambda: DEFAULT_TRAJECTORY_KEYS)
    task_completion_keys: List[str] = field(default_factory=lambda: DEFAULT_TASK_COMPLETION_KEYS)
    chat_kwargs: Dict[str, Any] = field(default_factory=dict)
    include_conversation: bool = True  # include full trajectory for context
    trajectory_prompt_template: Optional[str] = None  # custom trajectory evaluation prompt
    task_completion_prompt_template: Optional[str] = None  # custom task completion evaluation prompt
    model_config: Optional[Dict[str, Any]] = None  # model configuration for OpenAI client

    def __post_init__(self):
        # Pass model_config to OpenAIWrapper if provided
        if self.model_config:
            self.llm = OpenAIWrapper(model=self.model, model_config=self.model_config)
        else:
            self.llm = OpenAIWrapper(model=self.model)

    @classmethod
    def with_custom_prompts(
        cls,
        trajectory_prompt: Optional[str] = None,
        task_completion_prompt: Optional[str] = None,
        **kwargs
    ) -> "MultiAspectLLMJudger":
        """Create an evaluator with custom prompt templates.
        
        Args:
            trajectory_prompt: Custom prompt for trajectory evaluation
            task_completion_prompt: Custom prompt for task completion evaluation
            **kwargs: Other arguments passed to the constructor
            
        Returns:
            MultiAspectLLMJudger instance with custom prompts
        """
        return cls(
            trajectory_prompt_template=trajectory_prompt,
            task_completion_prompt_template=task_completion_prompt,
            **kwargs
        )

    # ------------------------------------------------------------------
    # Prompt construction
    # ------------------------------------------------------------------

    def _build_trajectory_prompt(self) -> str:
        """Build prompt template specifically for trajectory evaluation."""
        if self.trajectory_prompt_template is not None:
            return self.trajectory_prompt_template
        
        return (
            "You are evaluating the execution trajectory of an AI agent. Focus on HOW the agent "
            "approached and executed the task, including all tool interactions.\n\n"
            "**TRAJECTORY EVALUATION CRITERIA:**\n"
            "- planning: How well did the agent understand and decompose the task? (0.0-1.0)\n"
            "- execution_flow: Was the sequence of actions logical and well-structured? (0.0-1.0)\n"
            "- tool_selection: Were the right tools chosen for each step? (0.0-1.0)\n"
            "- tool_usage: Were tool parameters correct and results properly interpreted? (0.0-1.0)\n"
            "- adaptability: How well did the agent handle errors, unexpected results, changing contexts, and alternative paths? "
            "Score 1.0 if no errors occurred and execution was smooth, or if errors/changes were handled excellently, "
            "0.8-0.9 if minor issues were handled well, 0.5-0.7 if some problems occurred but were adequately addressed, "
            "0.0-0.4 if errors or changes were poorly handled. (0.0-1.0)\n"
            "- efficiency: Did the agent use an optimal approach without unnecessary steps? (0.0-1.0)\n"
            "- context_awareness: Did the agent maintain awareness of relevant context, constraints, and environmental state throughout execution? (0.0-1.0)\n\n"
            "Analyze the complete conversation flow from start to finish. Look for:\n"
            "- Clear task understanding\n"
            "- Logical step progression\n"
            "- Appropriate tool selection and usage\n"
            "- Correct parameter formatting and values\n"
            "- Proper interpretation of tool responses\n"
            "- Effective integration of tool results\n"
            "- Recovery from any issues\n\n"
            "**IMPORTANT**: For adaptability, if the execution was smooth with no errors or changes needed, "
            "this indicates good robustness and should receive a high score (0.9-1.0). "
            "Only give low scores if actual errors or unexpected situations occurred and were handled poorly.\n\n"
            "Respond ONLY with JSON:\n"
            "{\n"
            "  \"planning\": float,\n"
            "  \"execution_flow\": float,\n"
            "  \"tool_selection\": float,\n"
            "  \"tool_usage\": float,\n"
            "  \"adaptability\": float,\n"
            "  \"efficiency\": float,\n"
            "  \"context_awareness\": float,\n"
            "  \"comments\": \"Brief explanation\"\n"
            "}"
        )

    def _build_task_completion_prompt(self) -> str:
        """Build prompt template specifically for task completion evaluation."""
        if self.task_completion_prompt_template is not None:
            return self.task_completion_prompt_template
        
        return (
            "You are evaluating how well an AI agent completed the assigned task. "
            "Focus on the final outcome and how well it addresses the original requirements.\n\n"
            "**TASK COMPLETION EVALUATION CRITERIA:**\n"
            "- requirement_coverage: Did the agent address all aspects of the task? (0.0-1.0)\n"
            "- accuracy: Is the information and analysis factually correct? (0.0-1.0)\n"
            "- completeness: Is the response thorough and comprehensive? (0.0-1.0)\n"
            "- usefulness: Is the final result practically valuable to the user? (0.0-1.0)\n\n"
            "Compare the final response against:\n"
            "- Original task requirements\n"
            "- Expected deliverables\n"
            "- Quality of information provided\n"
            "- Practical utility for the user\n\n"
            "Respond ONLY with JSON:\n"
            "{\n"
            "  \"requirement_coverage\": float,\n"
            "  \"accuracy\": float,\n"
            "  \"completeness\": float,\n"
            "  \"usefulness\": float,\n"
            "  \"comments\": \"Brief explanation\"\n"
            "}"
        )

    # ------------------------------------------------------------------
    # Evaluation Methods
    # ------------------------------------------------------------------

    def evaluate_trajectory(
        self,
        task: Dict[str, Any],
        execution_trajectory: List[Dict[str, Any]],
        expected_approach: Optional[str] = None,
        expected_tool_calls: Optional[List[Dict[str, Any]]] = None,
        **chat_kwargs
    ) -> TrajectoryEvaluationResult:
        """Evaluate execution trajectory quality including tool usage."""
        user_parts = [
            "Task description:\n" + (task.get("description") or task.get("goal") or ""),
            "Execution trajectory (complete conversation):\n" + json.dumps(execution_trajectory, ensure_ascii=False, indent=2)
        ]
        
        if expected_approach:
            user_parts.append("Expected approach:\n" + expected_approach)
            
        if expected_tool_calls:
            user_parts.append("Expected tool calls:\n" + json.dumps(expected_tool_calls, ensure_ascii=False, indent=2))

        messages = [
            {"role": "system", "content": self._build_trajectory_prompt()},
            {"role": "user", "content": "\n\n".join(user_parts)}
        ]

        try:
            response = self.llm.chat_completion(messages, **{**self.chat_kwargs, **chat_kwargs})
            content = response["choices"][0]["message"]["content"]
            # Clean the JSON response
            cleaned_content = clean_json_response(content)
            raw_response = json.loads(cleaned_content)
            
            # Extract scores
            trajectory_scores = {k: float(raw_response.get(k, 0.0)) for k in self.trajectory_keys}
            overall_score = sum(trajectory_scores.values()) / len(trajectory_scores) if trajectory_scores else 0.0
            comments = raw_response.get("comments", "")
            
            return TrajectoryEvaluationResult(
                scores=TrajectoryScores(**trajectory_scores),
                overall_score=overall_score,
                comments=comments,
                raw_response=raw_response
            )
            
        except Exception as exc:
            logger.error("Trajectory evaluation failed – %s", exc)
            # Debug: print the actual response content
            try:
                content = response["choices"][0]["message"]["content"]
                logger.error("LLM response content: %r", content)
            except:
                logger.error("Could not extract response content")
            zero_scores = {k: 0.0 for k in self.trajectory_keys}
            return TrajectoryEvaluationResult(
                scores=TrajectoryScores(**zero_scores),
                overall_score=0.0,
                comments=f"Error: {exc}",
                raw_response={}
            )

    def evaluate_task_completion(
        self,
        task: Dict[str, Any],
        final_response: str,
        execution_trajectory: Optional[List[Dict[str, Any]]] = None,
        ground_truth_answer: Optional[str] = None,
        **chat_kwargs
    ) -> TaskCompletionEvaluationResult:
        """Evaluate task completion quality."""
        user_parts = [
            "Task description:\n" + (task.get("description") or task.get("goal") or ""),
            "Agent's final response:\n" + final_response
        ]
        
        if execution_trajectory and self.include_conversation:
            user_parts.append("Full execution trajectory:\n" + json.dumps(execution_trajectory, ensure_ascii=False, indent=2))
        
        if ground_truth_answer:
            user_parts.append("Expected answer:\n" + ground_truth_answer)

        messages = [
            {"role": "system", "content": self._build_task_completion_prompt()},
            {"role": "user", "content": "\n\n".join(user_parts)}
        ]

        try:
            response = self.llm.chat_completion(messages, **{**self.chat_kwargs, **chat_kwargs})
            content = response["choices"][0]["message"]["content"]
            # Clean the JSON response
            cleaned_content = clean_json_response(content)
            raw_response = json.loads(cleaned_content)
            
            # Extract scores
            task_completion_scores = {k: float(raw_response.get(k, 0.0)) for k in self.task_completion_keys}
            overall_score = sum(task_completion_scores.values()) / len(task_completion_scores) if task_completion_scores else 0.0
            comments = raw_response.get("comments", "")
            
            return TaskCompletionEvaluationResult(
                scores=TaskCompletionScores(**task_completion_scores),
                overall_score=overall_score,
                comments=comments,
                raw_response=raw_response
            )
            
        except Exception as exc:
            logger.error("Task completion evaluation failed – %s", exc)
            # Debug: print the actual response content
            try:
                content = response["choices"][0]["message"]["content"]
                logger.error("LLM response content: %r", content)
            except:
                logger.error("Could not extract response content")
            zero_scores = {k: 0.0 for k in self.task_completion_keys}
            return TaskCompletionEvaluationResult(
                scores=TaskCompletionScores(**zero_scores),
                overall_score=0.0,
                comments=f"Error: {exc}",
                raw_response={}
            )


def clean_json_response(content: str) -> str:
    """Clean JSON response by removing markdown code blocks if present."""
    content = content.strip()
    
    # Remove markdown code blocks
    if content.startswith('```json'):
        content = content[7:]  # Remove ```json
    elif content.startswith('```'):
        content = content[3:]   # Remove ```
    
    if content.endswith('```'):
        content = content[:-3]  # Remove trailing ```
    
    return content.strip() 