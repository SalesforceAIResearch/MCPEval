"""
DEPRECATED: The contents of this file have been moved to mcpeval.commons.types.
This file is kept for backward compatibility.
"""

# Keep this import for backward compatibility
from mcp.types import CallToolRequestParams as ToolCallParameters

# Re-export all the types from commons.types for backward compatibility
from ..commons.types import (
    ToolCallResult,
    ToolDefinition,
    ToolLibrary,
    ToolParameter,
    format_tools_for_prompt,
)
