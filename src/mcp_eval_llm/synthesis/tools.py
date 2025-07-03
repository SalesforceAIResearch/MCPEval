"""
DEPRECATED: The contents of this file have been moved to mcp_eval_llm.commons.types.
This file is kept for backward compatibility.
"""

# Re-export all the types from commons.types for backward compatibility
from ..commons.types import (
    ToolDefinition,
    ToolParameter,
    ToolCallResult,
    ToolLibrary,
    format_tools_for_prompt
)

# Keep this import for backward compatibility
from mcp.types import CallToolRequestParams as ToolCallParameters