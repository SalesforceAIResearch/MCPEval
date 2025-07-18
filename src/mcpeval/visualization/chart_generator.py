"""
Chart generator for MCP evaluation results visualization.
"""

import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, List, Tuple, Optional
import os
from pathlib import Path

from .chart_templates import (
    get_radar_template,
    get_bar_template,
    get_horizontal_bar_template,
    get_donut_template,
    get_line_template,
    get_stacked_bar_template,
    apply_theme,
    get_success_failure_colors,
    get_tool_colors,
    MCP_COLORS,
    EXTENDED_COLORS,
)


class ChartGenerator:
    """Generate various chart types from MCP evaluation analysis data."""

    def __init__(self, analysis_data: Dict[str, Any]):
        """Initialize with analysis data from summary_analysis.json."""
        self.data = analysis_data
        self.summary = analysis_data.get("summary", {})
        self.tool_usage = analysis_data.get("tool_usage", {})
        self.parameter_mismatches = analysis_data.get("parameter_mismatches", {})
        self.success_patterns = analysis_data.get("success_patterns", {})

    def create_performance_radar_chart(self) -> go.Figure:
        """Create radar chart showing overall performance metrics."""
        exact_match = self.summary.get("exact_match", {})
        flexible_match = self.summary.get("flexible_match", {})

        categories = ["Name Match", "Param Match", "Order Match", "Overall Score"]

        exact_values = [
            exact_match.get("average_name_match_score", 0),
            exact_match.get("average_param_match_score", 0),
            exact_match.get("average_order_match_score", 0),
            exact_match.get("average_overall_score", 0),
        ]

        flexible_values = [
            flexible_match.get("average_name_match_score", 0),
            flexible_match.get("average_param_match_score", 0),
            flexible_match.get("average_order_match_score", 0),
            flexible_match.get("average_overall_score", 0),
        ]

        fig = go.Figure()

        # Add exact match trace
        fig.add_trace(
            go.Scatterpolar(
                r=exact_values,
                theta=categories,
                fill="toself",
                name="Exact Match",
                line_color=MCP_COLORS["warning"],
                fillcolor=f"rgba({int(MCP_COLORS['warning'][1:3], 16)}, {int(MCP_COLORS['warning'][3:5], 16)}, {int(MCP_COLORS['warning'][5:7], 16)}, 0.3)",
            )
        )

        # Add flexible match trace
        fig.add_trace(
            go.Scatterpolar(
                r=flexible_values,
                theta=categories,
                fill="toself",
                name="Flexible Match",
                line_color=MCP_COLORS["success"],
                fillcolor=f"rgba({int(MCP_COLORS['success'][1:3], 16)}, {int(MCP_COLORS['success'][3:5], 16)}, {int(MCP_COLORS['success'][5:7], 16)}, 0.3)",
            )
        )

        fig.update_layout(get_radar_template())
        return apply_theme(fig, "Performance Metrics Comparison", 700, 500)

    def create_success_rate_comparison(self) -> go.Figure:
        """Create bar chart comparing exact vs flexible success rates."""
        exact_success = self.summary.get("exact_match", {}).get(
            "tasks_with_complete_success", 0
        )
        flexible_success = self.summary.get("flexible_match", {}).get(
            "tasks_with_complete_success", 0
        )
        total_tasks = self.summary.get("total_tasks", 1)

        categories = ["Exact Match", "Flexible Match"]
        success_counts = [exact_success, flexible_success]
        success_rates = [s / total_tasks * 100 for s in success_counts]

        fig = go.Figure()

        # Add bars with custom colors
        colors = [MCP_COLORS["warning"], MCP_COLORS["success"]]

        fig.add_trace(
            go.Bar(
                x=categories,
                y=success_rates,
                text=[
                    f"{count}/{total_tasks}<br>({rate:.1f}%)"
                    for count, rate in zip(success_counts, success_rates)
                ],
                textposition="auto",
                marker_color=colors,
                name="Success Rate",
            )
        )

        fig.update_layout(get_bar_template())
        fig.update_layout(
            yaxis_title="Success Rate (%)",
            yaxis=dict(range=[0, max(success_rates) * 1.1]),
        )

        return apply_theme(fig, "Success Rate: Exact vs Flexible Matching", 600, 400)

    def create_tool_usage_comparison(self) -> go.Figure:
        """Create grouped bar chart comparing expected vs actual tool usage."""
        ground_truth_tools = self.tool_usage.get("ground_truth_tools", {})
        prediction_tools = self.tool_usage.get("prediction_tools", {})

        tools = list(ground_truth_tools.keys())
        expected_counts = [ground_truth_tools.get(tool, 0) for tool in tools]
        actual_counts = [prediction_tools.get(tool, 0) for tool in tools]

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                name="Expected",
                x=tools,
                y=expected_counts,
                marker_color=MCP_COLORS["primary"],
            )
        )

        fig.add_trace(
            go.Bar(
                name="Actual",
                x=tools,
                y=actual_counts,
                marker_color=MCP_COLORS["secondary"],
            )
        )

        fig.update_layout(get_bar_template())
        fig.update_layout(
            yaxis_title="Tool Usage Count", xaxis_title="Tools", xaxis_tickangle=-45
        )

        return apply_theme(fig, "Tool Usage: Expected vs Actual", 800, 500)

    def create_parameter_mismatch_chart(self) -> go.Figure:
        """Create horizontal bar chart showing parameter mismatches."""
        # Flatten parameter mismatches and get top issues
        all_mismatches = []
        for tool, params in self.parameter_mismatches.items():
            for param, count in params.items():
                all_mismatches.append((f"{tool}.{param}", count))

        # Sort by count and take top 15
        all_mismatches.sort(key=lambda x: x[1], reverse=True)
        top_mismatches = all_mismatches[:15]

        if not top_mismatches:
            # Create empty chart if no data
            fig = go.Figure()
            fig.add_annotation(
                text="No parameter mismatches found",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=16, color=MCP_COLORS["muted"]),
            )
            return apply_theme(fig, "Parameter Mismatches", 800, 400)

        params, counts = zip(*top_mismatches)

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                y=list(params),
                x=list(counts),
                orientation="h",
                marker_color=MCP_COLORS["warning"],
                text=list(counts),
                textposition="auto",
            )
        )

        template = get_horizontal_bar_template()
        template["height"] = max(400, len(top_mismatches) * 25)
        fig.update_layout(template)

        fig.update_layout(
            xaxis_title="Mismatch Count",
            yaxis_title="Tool.Parameter",
            yaxis=dict(automargin=True),
        )

        return apply_theme(
            fig, "Most Common Parameter Mismatches", 800, template["height"]
        )

    def create_success_by_tool_count_chart(self) -> go.Figure:
        """Create stacked bar chart showing success/failure by tool count."""
        flexible_data = self.success_patterns.get("by_tool_count", {}).get(
            "flexible", {}
        )
        success_data = flexible_data.get("success", {})
        failure_data = flexible_data.get("failure", {})

        # Get all tool counts
        all_counts = set(success_data.keys()) | set(failure_data.keys())
        tool_counts = sorted([int(c) for c in all_counts])

        success_values = [success_data.get(str(c), 0) for c in tool_counts]
        failure_values = [failure_data.get(str(c), 0) for c in tool_counts]

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                name="Success",
                x=[f"{c} tools" for c in tool_counts],
                y=success_values,
                marker_color=MCP_COLORS["success"],
            )
        )

        fig.add_trace(
            go.Bar(
                name="Failure",
                x=[f"{c} tools" for c in tool_counts],
                y=failure_values,
                marker_color=MCP_COLORS["warning"],
            )
        )

        fig.update_layout(get_stacked_bar_template())
        fig.update_layout(yaxis_title="Number of Tasks", xaxis_title="Tool Count")

        return apply_theme(fig, "Success Rate by Tool Count", 700, 500)

    def create_tool_specific_success_charts(self) -> List[go.Figure]:
        """Create individual donut charts for each tool's success rate."""
        by_tool_data = self.success_patterns.get("by_tool", {})
        figures = []

        for tool_name, tool_data in by_tool_data.items():
            success_rate = tool_data.get("success_rate", 0)
            successful_tasks = tool_data.get("successful_tasks", 0)
            total_tasks = tool_data.get("total_tasks", 1)
            failed_tasks = total_tasks - successful_tasks

            # Create donut chart
            fig = go.Figure(
                data=[
                    go.Pie(
                        labels=["Success", "Failure"],
                        values=[successful_tasks, failed_tasks],
                        hole=0.3,
                        marker_colors=[MCP_COLORS["success"], MCP_COLORS["warning"]],
                        textinfo="label+percent",
                        textposition="outside",
                    )
                ]
            )

            fig.update_layout(get_donut_template())

            title = f"{tool_name.replace('_', ' ').title()}<br>Success Rate: {success_rate:.1%} ({successful_tasks}/{total_tasks})"
            fig = apply_theme(fig, title, 400, 400)
            figures.append(fig)

        return figures

    def create_model_comparison_chart(
        self, comparison_data: Dict[str, Dict[str, Any]]
    ) -> go.Figure:
        """Create line chart comparing multiple models (if data available)."""
        models = list(comparison_data.keys())

        # Extract overall scores for each model
        exact_scores = []
        flexible_scores = []

        for model in models:
            model_data = comparison_data[model]
            exact_scores.append(
                model_data.get("summary", {})
                .get("exact_match", {})
                .get("average_overall_score", 0)
            )
            flexible_scores.append(
                model_data.get("summary", {})
                .get("flexible_match", {})
                .get("average_overall_score", 0)
            )

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=models,
                y=exact_scores,
                mode="lines+markers",
                name="Exact Match",
                line=dict(color=MCP_COLORS["warning"], width=3),
                marker=dict(size=8),
            )
        )

        fig.add_trace(
            go.Scatter(
                x=models,
                y=flexible_scores,
                mode="lines+markers",
                name="Flexible Match",
                line=dict(color=MCP_COLORS["success"], width=3),
                marker=dict(size=8),
            )
        )

        fig.update_layout(get_line_template())
        fig.update_layout(
            yaxis_title="Overall Score", xaxis_title="Models", yaxis=dict(range=[0, 1])
        )

        return apply_theme(fig, "Model Performance Comparison", 800, 500)

    def save_chart(
        self, fig: go.Figure, output_path: str, formats: List[str] = ["html", "png"]
    ) -> Dict[str, str]:
        """Save chart in multiple formats."""
        saved_files = {}
        base_path = Path(output_path)

        # Ensure output directory exists
        base_path.parent.mkdir(parents=True, exist_ok=True)

        for fmt in formats:
            if fmt == "html":
                file_path = f"{base_path}.html"
                fig.write_html(file_path, include_plotlyjs="cdn")
                saved_files["html"] = file_path
            elif fmt == "png":
                file_path = f"{base_path}.png"
                fig.write_image(
                    file_path, width=fig.layout.width, height=fig.layout.height, scale=2
                )
                saved_files["png"] = file_path
            elif fmt == "svg":
                file_path = f"{base_path}.svg"
                fig.write_image(file_path, format="svg")
                saved_files["svg"] = file_path

        return saved_files

    def generate_all_charts(
        self,
        output_dir: str,
        formats: List[str] = ["html", "png"],
        model_name: str = None,
    ) -> Dict[str, Dict[str, str]]:
        """Generate all charts and save them."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        saved_charts = {}

        # Use model name as prefix if provided
        prefix = f"{model_name}_" if model_name else ""

        # 1. Performance radar chart
        radar_fig = self.create_performance_radar_chart()
        saved_charts["performance_radar"] = self.save_chart(
            radar_fig, output_path / f"{prefix}performance_radar", formats
        )

        # 2. Success rate comparison
        success_fig = self.create_success_rate_comparison()
        saved_charts["success_comparison"] = self.save_chart(
            success_fig, output_path / f"{prefix}success_comparison", formats
        )

        # 3. Tool usage comparison
        tool_usage_fig = self.create_tool_usage_comparison()
        saved_charts["tool_usage"] = self.save_chart(
            tool_usage_fig, output_path / f"{prefix}tool_usage_comparison", formats
        )

        # 4. Parameter mismatches
        param_fig = self.create_parameter_mismatch_chart()
        saved_charts["parameter_mismatches"] = self.save_chart(
            param_fig, output_path / f"{prefix}parameter_mismatches", formats
        )

        # 5. Success by tool count
        tool_count_fig = self.create_success_by_tool_count_chart()
        saved_charts["success_by_tool_count"] = self.save_chart(
            tool_count_fig, output_path / f"{prefix}success_by_tool_count", formats
        )

        # 6. Tool-specific success charts
        tool_success_figs = self.create_tool_specific_success_charts()
        for i, fig in enumerate(tool_success_figs):
            tool_name = list(self.success_patterns.get("by_tool", {}).keys())[i]
            saved_charts[f"tool_success_{tool_name}"] = self.save_chart(
                fig, output_path / f"{prefix}tool_success_{tool_name}", formats
            )

        return saved_charts

    def create_llm_judger_trajectory_aspects_chart(
        self, data: Dict[str, Any], model_name: str
    ) -> str:
        """Create radar chart for LLM judger trajectory aspects."""
        aspects = (
            data.get("summary_statistics", {})
            .get("aspect_analysis", {})
            .get("trajectory", {})
        )

        if not aspects:
            return ""

        aspect_names = list(aspects.keys())
        mean_scores = [aspects[aspect]["mean"] for aspect in aspect_names]

        # Create radar chart
        fig = go.Figure()

        fig.add_trace(
            go.Scatterpolar(
                r=mean_scores,
                theta=aspect_names,
                fill="toself",
                name=f"{model_name} Trajectory Aspects",
                line=dict(color=MCP_COLORS["primary"], width=3),
                fillcolor=f"rgba({int(MCP_COLORS['primary'][1:3], 16)}, {int(MCP_COLORS['primary'][3:5], 16)}, {int(MCP_COLORS['primary'][5:7], 16)}, 0.3)",
            )
        )

        fig.update_layout(get_radar_template())
        fig.update_layout(
            title=dict(
                text=f"LLM Judger - Trajectory Aspects Performance<br><sub>{model_name}</sub>",
                x=0.5,
                font=dict(size=16, color=MCP_COLORS["dark"]),
            ),
            polar=dict(
                radialaxis=dict(
                    visible=True, range=[0, 1], tickmode="linear", tick0=0, dtick=0.2
                )
            ),
        )

        return apply_theme(
            fig, f"LLM Judger - Trajectory Aspects Performance - {model_name}", 600, 500
        )

    def create_llm_judger_completion_aspects_chart(
        self, data: Dict[str, Any], model_name: str
    ) -> str:
        """Create bar chart for LLM judger completion aspects."""
        aspects = (
            data.get("summary_statistics", {})
            .get("aspect_analysis", {})
            .get("completion", {})
        )

        if not aspects:
            return ""

        aspect_names = list(aspects.keys())
        mean_scores = [aspects[aspect]["mean"] for aspect in aspect_names]
        std_devs = [aspects[aspect]["std_dev"] for aspect in aspect_names]

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=aspect_names,
                y=mean_scores,
                error_y=dict(type="data", array=std_devs),
                name="Mean Score",
                marker=dict(
                    color=MCP_COLORS["primary"],
                    line=dict(color=MCP_COLORS["secondary"], width=1),
                ),
            )
        )

        fig.update_layout(get_bar_template())
        fig.update_layout(
            yaxis_title="Score",
            xaxis_title="Completion Aspects",
            yaxis=dict(range=[0, 1]),
        )

        return apply_theme(
            fig, f"LLM Judger - Completion Aspects Performance - {model_name}", 700, 500
        )

    def create_llm_judger_score_distribution_chart(
        self, data: Dict[str, Any], model_name: str
    ) -> str:
        """Create histogram showing distribution of LLM judger scores."""
        summary_stats = data.get("summary_statistics", {})

        trajectory_stats = summary_stats.get("trajectory_stats", {})
        completion_stats = summary_stats.get("completion_stats", {})
        combined_stats = summary_stats.get("combined_stats", {})

        if not all([trajectory_stats, completion_stats, combined_stats]):
            return ""

        # Create score distribution data
        categories = ["Trajectory", "Completion", "Combined"]
        means = [
            trajectory_stats.get("mean", 0),
            completion_stats.get("mean", 0),
            combined_stats.get("mean", 0),
        ]
        std_devs = [
            trajectory_stats.get("std_dev", 0),
            completion_stats.get("std_dev", 0),
            combined_stats.get("std_dev", 0),
        ]

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=categories,
                y=means,
                error_y=dict(type="data", array=std_devs),
                name="Mean Score",
                marker=dict(
                    color=[
                        MCP_COLORS["primary"],
                        MCP_COLORS["secondary"],
                        MCP_COLORS["info"],
                    ],
                    line=dict(color=MCP_COLORS["dark"], width=1),
                ),
                text=[f"{mean:.3f}" for mean in means],
                textposition="auto",
            )
        )

        fig.update_layout(get_bar_template())
        fig.update_layout(
            yaxis_title="Score", xaxis_title="Score Type", yaxis=dict(range=[0, 1])
        )

        return apply_theme(
            fig, f"LLM Judger - Score Distribution - {model_name}", 600, 500
        )

    def create_llm_judger_high_performers_chart(
        self, data: Dict[str, Any], model_name: str
    ) -> str:
        """Create chart showing top performing tasks from LLM judger analysis."""
        high_performers = data.get("patterns", {}).get("high_performers", [])

        if not high_performers or len(high_performers) < 5:
            return ""

        # Take top 10 performers
        top_performers = high_performers[:10]

        task_names = [
            (
                task.get("task_name", "Unknown")[:40] + "..."
                if len(task.get("task_name", "")) > 40
                else task.get("task_name", "Unknown")
            )
            for task in top_performers
        ]
        trajectory_scores = [task.get("trajectory_score", 0) for task in top_performers]
        completion_scores = [task.get("completion_score", 0) for task in top_performers]
        combined_scores = [task.get("combined_score", 0) for task in top_performers]

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                name="Trajectory Score",
                x=task_names,
                y=trajectory_scores,
                marker=dict(color=MCP_COLORS["primary"]),
            )
        )

        fig.add_trace(
            go.Bar(
                name="Completion Score",
                x=task_names,
                y=completion_scores,
                marker=dict(color=MCP_COLORS["secondary"]),
            )
        )

        fig.add_trace(
            go.Bar(
                name="Combined Score",
                x=task_names,
                y=combined_scores,
                marker=dict(color=MCP_COLORS["info"]),
            )
        )

        fig.update_layout(get_bar_template())
        fig.update_layout(
            yaxis_title="Score",
            xaxis_title="Tasks",
            xaxis_tickangle=-45,
            yaxis=dict(range=[0, 1]),
            barmode="group",
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
        )

        return apply_theme(
            fig, f"LLM Judger - Top 10 Performing Tasks - {model_name}", 1000, 600
        )

    def generate_llm_judger_charts(
        self, data: Dict[str, Any], model_name: str, output_dir: str
    ) -> List[str]:
        """Generate all LLM judger analysis charts."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        charts = []

        # Use model name as prefix
        prefix = f"{model_name}_"

        # Generate LLM judger specific charts
        chart_methods_and_names = [
            (
                self.create_llm_judger_trajectory_aspects_chart,
                "llm_judger_trajectory_aspects",
            ),
            (
                self.create_llm_judger_completion_aspects_chart,
                "llm_judger_completion_aspects",
            ),
            (
                self.create_llm_judger_score_distribution_chart,
                "llm_judger_score_distribution",
            ),
            (
                self.create_llm_judger_high_performers_chart,
                "llm_judger_high_performers",
            ),
        ]

        for method, chart_name in chart_methods_and_names:
            try:
                chart_fig = method(data, model_name)
                if chart_fig:
                    # Save the chart
                    saved_files = self.save_chart(
                        chart_fig,
                        output_path / f"{prefix}{chart_name}",
                        ["html", "png"],
                    )
                    if "html" in saved_files:
                        charts.append(saved_files["html"])
            except Exception as e:
                print(f"Error generating chart with {method.__name__}: {e}")

        return charts
