"""
Chart templates and styling configuration for MCP evaluation visualization.
"""

import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any


# Color palette for consistent theming
MCP_COLORS = {
    "primary": "#2E86AB",  # Blue
    "secondary": "#A23B72",  # Purple
    "success": "#F18F01",  # Orange
    "warning": "#C73E1D",  # Red
    "info": "#4A90E2",  # Light Blue
    "muted": "#6C757D",  # Gray
    "light": "#F8F9FA",  # Light Gray
    "dark": "#343A40",  # Dark Gray
}

# Extended color palette for multiple series
EXTENDED_COLORS = [
    "#2E86AB",
    "#A23B72",
    "#F18F01",
    "#C73E1D",
    "#4A90E2",
    "#28A745",
    "#FFC107",
    "#17A2B8",
    "#6F42C1",
    "#E83E8C",
]


def get_base_layout() -> Dict[str, Any]:
    """Get base layout configuration for all charts."""
    return {
        "font": {"family": "Arial, sans-serif", "size": 12},
        "plot_bgcolor": "white",
        "paper_bgcolor": "white",
        "margin": {"l": 60, "r": 40, "t": 60, "b": 60},
        "showlegend": True,
        "legend": {
            "orientation": "h",
            "yanchor": "bottom",
            "y": -0.2,
            "xanchor": "center",
            "x": 0.5,
        },
        "hovermode": "closest",
    }


def get_radar_template() -> Dict[str, Any]:
    """Get template for radar charts."""
    layout = get_base_layout()
    layout.update(
        {
            "polar": {
                "radialaxis": {
                    "visible": True,
                    "range": [0, 1],
                    "tickformat": ".2f",
                    "gridcolor": "#E5E5E5",
                },
                "angularaxis": {"gridcolor": "#E5E5E5"},
            },
            "showlegend": True,
        }
    )
    return layout


def get_bar_template() -> Dict[str, Any]:
    """Get template for bar charts."""
    layout = get_base_layout()
    layout.update(
        {
            "xaxis": {"gridcolor": "#E5E5E5", "zeroline": False},
            "yaxis": {"gridcolor": "#E5E5E5", "zeroline": False},
            "bargap": 0.3,
            "bargroupgap": 0.1,
        }
    )
    return layout


def get_horizontal_bar_template() -> Dict[str, Any]:
    """Get template for horizontal bar charts."""
    layout = get_base_layout()
    layout.update(
        {
            "xaxis": {"gridcolor": "#E5E5E5", "zeroline": False},
            "yaxis": {"gridcolor": "#E5E5E5", "zeroline": False, "automargin": True},
            "bargap": 0.3,
            "height": None,  # Will be set dynamically based on data
        }
    )
    return layout


def get_donut_template() -> Dict[str, Any]:
    """Get template for donut/pie charts."""
    layout = get_base_layout()
    layout.update(
        {
            "showlegend": True,
            "legend": {
                "orientation": "v",
                "yanchor": "middle",
                "y": 0.5,
                "xanchor": "left",
                "x": 1.02,
            },
        }
    )
    return layout


def get_line_template() -> Dict[str, Any]:
    """Get template for line charts."""
    layout = get_base_layout()
    layout.update(
        {
            "xaxis": {"gridcolor": "#E5E5E5", "zeroline": False},
            "yaxis": {"gridcolor": "#E5E5E5", "zeroline": False},
        }
    )
    return layout


def get_stacked_bar_template() -> Dict[str, Any]:
    """Get template for stacked bar charts."""
    layout = get_base_layout()
    layout.update(
        {
            "barmode": "stack",
            "xaxis": {"gridcolor": "#E5E5E5", "zeroline": False},
            "yaxis": {"gridcolor": "#E5E5E5", "zeroline": False},
            "bargap": 0.3,
        }
    )
    return layout


def apply_theme(
    fig: go.Figure, title: str = None, width: int = 800, height: int = 600
) -> go.Figure:
    """Apply consistent theming to a figure."""
    if title:
        fig.update_layout(
            title={
                "text": title,
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 16, "color": MCP_COLORS["dark"]},
            }
        )

    fig.update_layout(width=width, height=height, font={"color": MCP_COLORS["dark"]})

    return fig


def get_success_failure_colors() -> Dict[str, str]:
    """Get colors for success/failure visualization."""
    return {
        "success": MCP_COLORS["success"],
        "failure": MCP_COLORS["warning"],
        "partial": MCP_COLORS["info"],
    }


def get_tool_colors(num_tools: int) -> list:
    """Get colors for tool-specific visualizations."""
    if num_tools <= len(EXTENDED_COLORS):
        return EXTENDED_COLORS[:num_tools]
    else:
        # Generate additional colors using plotly's color scale
        return px.colors.qualitative.Set3[:num_tools]
