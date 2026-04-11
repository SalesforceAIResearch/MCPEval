"""
Synthesis module for generating synthetic datasets.

This module provides classes and utilities for generating synthetic datasets
for evaluating LLM tool use performance.
"""

# from .scenarios import Scenario, ScenarioLibrary  # TODO: scenarios module not implemented yet
# from .generator import ScenarioGenerator  # TODO: scenarios module not implemented yet
from .task_generator import TaskGenerator
from .tools import (
    ToolCallParameters,  # This is actually mcp.types.CallToolRequestParams
)
from .tools import ToolDefinition  # This is actually mcp.types.Tool
from .tools import (
    ToolCallResult,
    ToolLibrary,
    ToolParameter,
)

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
