"""
Visualization module for MCP evaluation results.

This module provides chart generation and report enhancement capabilities
for MCP evaluation analysis data.
"""

from .chart_generator import ChartGenerator
from .chart_templates import (
    MCP_COLORS,
    EXTENDED_COLORS,
    get_base_layout,
    get_radar_template,
    get_bar_template,
    get_horizontal_bar_template,
    get_donut_template,
    get_line_template,
    get_stacked_bar_template,
    apply_theme,
    get_success_failure_colors,
    get_tool_colors,
)
from .report_enhancer import ReportEnhancer, enhance_report_with_charts

__all__ = [
    "ChartGenerator",
    "ReportEnhancer",
    "enhance_report_with_charts",
    "MCP_COLORS",
    "EXTENDED_COLORS",
    "get_base_layout",
    "get_radar_template",
    "get_bar_template",
    "get_horizontal_bar_template",
    "get_donut_template",
    "get_line_template",
    "get_stacked_bar_template",
    "apply_theme",
    "get_success_failure_colors",
    "get_tool_colors",
]
