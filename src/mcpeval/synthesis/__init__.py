"""
Synthesis module for generating synthetic datasets.

This module provides classes and utilities for generating synthetic datasets
for evaluating LLM tool use performance.
"""

from .tools import (
    ToolDefinition,  # This is actually mcp.types.Tool
    ToolParameter,
    ToolLibrary,
    ToolCallParameters,  # This is actually mcp.types.CallToolRequestParams
    ToolCallResult,
)

# from .scenarios import Scenario, ScenarioLibrary  # TODO: scenarios module not implemented yet
# from .generator import ScenarioGenerator  # TODO: scenarios module not implemented yet
from .task_generator import TaskGenerator

__all__ = [
    "ToolDefinition",
    "ToolParameter",
    "ToolLibrary",
    "ToolCallParameters",
    "ToolCallResult",
    # 'Scenario',
    # 'ScenarioLibrary',
    # 'ScenarioGenerator',
    "TaskGenerator",
]
