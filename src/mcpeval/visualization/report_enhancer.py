"""
Report enhancer for integrating charts with AI-generated reports.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

from .chart_generator import ChartGenerator

# Import OpenAI for section text generation
try:
    from openai import OpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class ReportEnhancer:
    """Enhance existing AI reports with generated charts."""

    def __init__(self, analysis_data: Dict[str, Any] = None):
        """Initialize with optional analysis data."""
        self.analysis_data = analysis_data
        if analysis_data:
            self.chart_generator = ChartGenerator(analysis_data)
        else:
            self.chart_generator = None

    def generate_charts_for_report(
        self,
        output_dir: str,
        formats: List[str] = ["html", "png"],
        model_name: str = None,
    ) -> Dict[str, Dict[str, str]]:
        """Generate all charts needed for report enhancement."""
        charts_dir = Path(output_dir) / "charts"
        return self.chart_generator.generate_all_charts(
            str(charts_dir), formats, model_name
        )

    def create_chart_references_markdown(
        self,
        saved_charts: Dict[str, Dict[str, str]],
        base_url: str = "",
        use_png: bool = True,
    ) -> str:
        """Create markdown references for charts to be included in reports."""
        markdown_content = []

        # Chart sections in logical order
        chart_sections = [
            (
                "performance_radar",
                "Performance Overview",
                "Overall performance metrics comparison between exact and flexible matching.",
            ),
            (
                "success_comparison",
                "Success Rate Analysis",
                "Comparison of success rates between exact and flexible matching approaches.",
            ),
            (
                "tool_usage",
                "Tool Usage Analysis",
                "Comparison of expected vs actual tool usage patterns.",
            ),
            (
                "parameter_mismatches",
                "Parameter Issues",
                "Most common parameter mismatches that cause evaluation failures.",
            ),
            (
                "success_by_tool_count",
                "Complexity Analysis",
                "Success rates by task complexity (number of tools required).",
            ),
        ]

        for chart_key, title, description in chart_sections:
            if chart_key in saved_charts:
                chart_files = saved_charts[chart_key]

                markdown_content.append(f"### {title}")
                markdown_content.append(f"{description}")
                markdown_content.append("")

                # Use PNG images for better report integration
                if use_png and "png" in chart_files:
                    png_path = Path(chart_files["png"]).name
                    markdown_content.append(f"![{title}]({base_url}charts/{png_path})")
                    markdown_content.append("")
                elif "html" in chart_files:
                    # Fallback to HTML if PNG not available
                    html_path = Path(chart_files["html"]).name
                    markdown_content.append(
                        f'<iframe src="{base_url}charts/{html_path}" width="100%" height="600" frameborder="0"></iframe>'
                    )
                    markdown_content.append("")

                markdown_content.append("---")
                markdown_content.append("")

        # Add tool-specific charts
        tool_charts = {
            k: v for k, v in saved_charts.items() if k.startswith("tool_success_")
        }
        if tool_charts:
            markdown_content.append("### Tool-Specific Performance")
            markdown_content.append("Individual success rates for each tool.")
            markdown_content.append("")

            # Create a grid layout for tool charts using PNG images
            tool_names = [k.replace("tool_success_", "") for k in tool_charts.keys()]
            for i, (chart_key, tool_name) in enumerate(
                zip(tool_charts.keys(), tool_names)
            ):
                chart_files = tool_charts[chart_key]

                # Start new row every 2 charts
                if i % 2 == 0:
                    markdown_content.append(
                        '<div style="display: flex; flex-wrap: wrap; gap: 20px;">'
                    )

                markdown_content.append('<div style="flex: 1; min-width: 300px;">')

                if use_png and "png" in chart_files:
                    png_path = Path(chart_files["png"]).name
                    markdown_content.append(
                        f"![{tool_name.replace('_', ' ').title()} Success Rate]({base_url}charts/{png_path})"
                    )
                elif "html" in chart_files:
                    html_path = Path(chart_files["html"]).name
                    markdown_content.append(
                        f'<iframe src="{base_url}charts/{html_path}" width="100%" height="450" frameborder="0"></iframe>'
                    )

                markdown_content.append("</div>")

                # Close row every 2 charts or at the end
                if i % 2 == 1 or i == len(tool_charts) - 1:
                    markdown_content.append("</div>")
                    markdown_content.append("")

        return "\n".join(markdown_content)

    def enhance_ai_report(
        self,
        original_report: str,
        saved_charts: Dict[str, Dict[str, str]],
        base_url: str = "",
    ) -> str:
        """Enhance an existing AI-generated report by inserting charts."""
        # Create chart references
        chart_markdown = self.create_chart_references_markdown(saved_charts, base_url)

        # Find a good insertion point in the report
        # Look for common section headers where we can insert charts
        insertion_patterns = [
            "## Performance Analysis",
            "## Detailed Analysis",
            "## Analysis Results",
            "## Results",
            "## Performance Metrics",
        ]

        # Try to find a good insertion point
        insertion_point = -1
        for pattern in insertion_patterns:
            if pattern in original_report:
                insertion_point = original_report.find(pattern)
                break

        if insertion_point == -1:
            # If no good insertion point found, append to the end
            enhanced_report = (
                original_report + "\n\n## Visual Analysis\n\n" + chart_markdown
            )
        else:
            # Insert charts before the found section
            enhanced_report = (
                original_report[:insertion_point]
                + "## Visual Analysis\n\n"
                + chart_markdown
                + "\n\n"
                + original_report[insertion_point:]
            )

        return enhanced_report

    def create_chart_summary_table(
        self, saved_charts: Dict[str, Dict[str, str]]
    ) -> str:
        """Create a summary table of all generated charts."""
        table_rows = []
        table_rows.append("| Chart | Description | HTML | PNG |")
        table_rows.append("|-------|-------------|------|-----|")

        chart_descriptions = {
            "performance_radar": "Performance metrics radar chart",
            "success_comparison": "Success rate comparison bar chart",
            "tool_usage": "Tool usage comparison chart",
            "parameter_mismatches": "Parameter mismatch analysis",
            "success_by_tool_count": "Success rate by complexity",
        }

        for chart_key, chart_files in saved_charts.items():
            if chart_key.startswith("tool_success_"):
                tool_name = (
                    chart_key.replace("tool_success_", "").replace("_", " ").title()
                )
                description = f"{tool_name} success rate"
            else:
                description = chart_descriptions.get(
                    chart_key, chart_key.replace("_", " ").title()
                )

            html_link = (
                f"[View]({Path(chart_files.get('html', '')).name})"
                if "html" in chart_files
                else "N/A"
            )
            png_link = (
                f"[Download]({Path(chart_files.get('png', '')).name})"
                if "png" in chart_files
                else "N/A"
            )

            table_rows.append(
                f"| {description} | Interactive visualization | {html_link} | {png_link} |"
            )

        return "\n".join(table_rows)

    def generate_standalone_chart_report(
        self, output_dir: str, title: str = "MCP Evaluation Charts"
    ) -> str:
        """Generate a standalone report with just charts and minimal text."""
        # Generate charts
        saved_charts = self.generate_charts_for_report(output_dir)

        # Create standalone report
        report_content = []
        report_content.append(f"# {title}")
        report_content.append("")
        report_content.append(
            "This report provides visual analysis of the MCP evaluation results."
        )
        report_content.append("")

        # Add chart summary table
        report_content.append("## Chart Index")
        report_content.append("")
        report_content.append(self.create_chart_summary_table(saved_charts))
        report_content.append("")

        # Add all charts
        chart_markdown = self.create_chart_references_markdown(saved_charts)
        report_content.append(chart_markdown)

        # Add metadata
        report_content.append("---")
        report_content.append("")
        report_content.append("## Metadata")
        report_content.append("")
        report_content.append(
            f"- Total tasks: {self.analysis_data.get('summary', {}).get('total_tasks', 'N/A')}"
        )
        report_content.append(
            f"- Exact match success: {self.analysis_data.get('summary', {}).get('exact_match', {}).get('tasks_with_complete_success', 'N/A')}"
        )
        report_content.append(
            f"- Flexible match success: {self.analysis_data.get('summary', {}).get('flexible_match', {}).get('tasks_with_complete_success', 'N/A')}"
        )
        report_content.append("")
        report_content.append("Generated using MCP-Eval-LLM visualization system.")

        # Save report
        report_path = Path(output_dir) / "charts_report.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(report_content))

        return str(report_path)

    def enhance_ai_report_with_integrated_comprehensive_charts(
        self,
        report_content: str,
        all_charts: Dict[str, List[str]],
        use_png: bool = True,
    ) -> str:
        """Enhance AI report by integrating charts from all analysis types into relevant sections."""
        if "static" not in all_charts:
            return report_content

        lines = report_content.split("\n")
        enhanced_lines = []

        # Track which charts have been inserted to prevent duplicates
        inserted_charts = set()

        i = 0
        while i < len(lines):
            line = lines[i]
            enhanced_lines.append(line)

            # 1. Insert performance radar chart after average overall score table
            if (
                "| Average Overall Score" in line
                and "performance_radar" not in inserted_charts
            ):

                for chart_path in all_charts["static"]:
                    if "performance_radar" in chart_path:
                        chart_ref = self._get_chart_reference(chart_path, use_png)
                        enhanced_lines.extend(
                            ["", "**Performance Overview:**", chart_ref, ""]
                        )
                        inserted_charts.add("performance_radar")
                        break

            # 2. Insert success comparison chart after flexible matching success mention
            elif (
                "Flexible Matching Success" in line
                or "flexible matching" in line.lower()
            ) and "success_comparison" not in inserted_charts:

                for chart_path in all_charts["static"]:
                    if "success_comparison" in chart_path:
                        chart_ref = self._get_chart_reference(chart_path, use_png)
                        enhanced_lines.extend(
                            ["", "**Success Rate Comparison:**", chart_ref, ""]
                        )
                        inserted_charts.add("success_comparison")
                        break

            # 3. Insert task complexity chart after the complexity table (look for the last row pattern)
            elif (
                ("| 9" in line or "| 8" in line)
                and "0%" in line
                and "success_by_tool_count" not in inserted_charts
            ):

                for chart_path in all_charts["static"]:
                    if "success_by_tool_count" in chart_path:
                        chart_ref = self._get_chart_reference(chart_path, use_png)
                        enhanced_lines.extend(
                            ["", "**Success Rate by Task Complexity:**", chart_ref, ""]
                        )
                        inserted_charts.add("success_by_tool_count")
                        break

            # 4. Insert tool-specific charts after the tool performance table (look for Clinical Trials Search or last tool)
            elif (
                ("Clinical Trials Search" in line or "Health Topics Search" in line)
                and "|" in line
                and "%" in line
                and "tool_specific_charts" not in inserted_charts
            ):

                enhanced_lines.extend(["", "**Individual Tool Performance:**", ""])
                for chart_path in all_charts["static"]:
                    if "tool_success_" in chart_path:
                        chart_ref = self._get_chart_reference(chart_path, use_png)
                        enhanced_lines.extend([chart_ref, ""])

                inserted_charts.add("tool_specific_charts")

            # 5. Insert parameter mismatch chart after "Parameter Mismatches" section header
            elif (
                (
                    "Parameter Mismatches" in line
                    or "parameter mismatches" in line.lower()
                )
                and line.strip().startswith("#")
                and "parameter_mismatches" not in inserted_charts
            ):

                for chart_path in all_charts["static"]:
                    if "parameter_mismatch" in chart_path:
                        chart_ref = self._get_chart_reference(chart_path, use_png)
                        enhanced_lines.extend(
                            ["", "**Parameter Mismatch Analysis:**", chart_ref, ""]
                        )
                        inserted_charts.add("parameter_mismatches")
                        break

            # 6. Insert tool usage chart after "Tool Usage Analysis:" mention
            elif (
                "Tool Usage Analysis" in line
                and "tool_usage_comparison" not in inserted_charts
            ):

                for chart_path in all_charts["static"]:
                    if "tool_usage_comparison" in chart_path:
                        chart_ref = self._get_chart_reference(chart_path, use_png)
                        enhanced_lines.extend(["", chart_ref, ""])
                        inserted_charts.add("tool_usage_comparison")
                        break

            i += 1

        return "\n".join(enhanced_lines)

    def enhance_llm_judger_report_with_charts(
        self,
        report_content: str,
        all_charts: Dict[str, List[str]],
        use_png: bool = True,
    ) -> str:
        """Enhance LLM judger report by integrating LLM judger charts into relevant sections."""
        if "llm_judger" not in all_charts:
            return report_content

        lines = report_content.split("\n")
        enhanced_lines = []

        # Track which charts have been inserted to prevent duplicates
        inserted_charts = set()

        i = 0
        while i < len(lines):
            line = lines[i]
            enhanced_lines.append(line)

            # 1. Insert completion aspects chart after executive summary
            if (
                ("Executive Summary" in line or "executive summary" in line.lower())
                and line.strip().startswith("#")
                and "completion_aspects" not in inserted_charts
            ):

                # Look for the end of executive summary section
                j = i + 1
                while j < len(lines) and not lines[j].strip().startswith("##"):
                    enhanced_lines.append(lines[j])
                    j += 1

                for chart_path in all_charts["llm_judger"]:
                    if "completion_aspects" in chart_path:
                        chart_ref = self._get_chart_reference(chart_path, use_png)
                        enhanced_lines.extend(
                            ["", "**Completion Quality Analysis:**", chart_ref, ""]
                        )
                        inserted_charts.add("completion_aspects")
                        break

                # Skip the processed lines
                i = j - 1

            # 2. Insert score distribution chart after performance metrics
            elif (
                "High-Performing Tasks" in line or "Excellent" in line
            ) and "score_distribution" not in inserted_charts:

                for chart_path in all_charts["llm_judger"]:
                    if "score_distribution" in chart_path:
                        chart_ref = self._get_chart_reference(chart_path, use_png)
                        enhanced_lines.extend(
                            ["", "**Score Distribution Analysis:**", chart_ref, ""]
                        )
                        inserted_charts.add("score_distribution")
                        break

            # 3. Insert trajectory aspects chart after trajectory score mention
            elif (
                "trajectory" in line.lower() and "score" in line.lower()
            ) and "trajectory_aspects" not in inserted_charts:

                for chart_path in all_charts["llm_judger"]:
                    if "trajectory_aspects" in chart_path:
                        chart_ref = self._get_chart_reference(chart_path, use_png)
                        enhanced_lines.extend(
                            ["", "**Trajectory Analysis Performance:**", chart_ref, ""]
                        )
                        inserted_charts.add("trajectory_aspects")
                        break

            # 4. Insert high performers chart after actionable recommendations
            elif (
                (
                    "Actionable Recommendations" in line
                    or "actionable recommendations" in line.lower()
                )
                and line.strip().startswith("#")
                and "high_performers" not in inserted_charts
            ):

                # Look for the end of recommendations section
                j = i + 1
                while j < len(lines) and not lines[j].strip().startswith("#"):
                    enhanced_lines.append(lines[j])
                    j += 1

                for chart_path in all_charts["llm_judger"]:
                    if "high_performers" in chart_path:
                        chart_ref = self._get_chart_reference(chart_path, use_png)
                        enhanced_lines.extend(
                            ["", "**Top Performing Tasks:**", chart_ref, ""]
                        )
                        inserted_charts.add("high_performers")
                        break

                # Skip the processed lines
                i = j - 1

            i += 1

        return "\n".join(enhanced_lines)

    def detect_analysis_files(
        self, report_dir: Path, model_name: str
    ) -> Dict[str, str]:
        """Detect available analysis files for a model."""
        analysis_files = {}

        # Check for static evaluation analysis
        static_file = (
            report_dir / f"{model_name}_mix_task_evaluation_summary_analysis.json"
        )
        if static_file.exists():
            analysis_files["static"] = str(static_file)

        # Check for LLM judger analysis
        llm_judger_file = (
            report_dir
            / f"{model_name}_mix_task_evaluation_trajectory_llm_judger_analysis.json"
        )
        if llm_judger_file.exists():
            analysis_files["llm_judger"] = str(llm_judger_file)

        return analysis_files

    def generate_comprehensive_charts(
        self, analysis_files: Dict[str, str], model_name: str, output_dir: str
    ) -> Dict[str, List[str]]:
        """Generate charts for all available analysis types."""
        all_charts = {}

        # Ensure charts are saved in charts/ subdirectory
        charts_dir = Path(output_dir) / "charts"
        charts_dir.mkdir(parents=True, exist_ok=True)

        # Generate static evaluation charts
        if "static" in analysis_files:
            try:
                with open(analysis_files["static"], "r") as f:
                    static_data = json.load(f)

                # Create chart generator for static data
                static_chart_generator = ChartGenerator(static_data)
                static_charts = static_chart_generator.generate_all_charts(
                    str(charts_dir), ["html", "png"], model_name
                )

                # Convert to list of file paths
                chart_paths = []
                for chart_name, file_dict in static_charts.items():
                    if "html" in file_dict:
                        chart_paths.append(file_dict["html"])

                all_charts["static"] = chart_paths
                print(
                    f"Generated {len(chart_paths)} static evaluation charts for {model_name}"
                )
            except Exception as e:
                print(f"Error generating static charts for {model_name}: {e}")
                all_charts["static"] = []

        # Generate LLM judger charts
        if "llm_judger" in analysis_files:
            try:
                with open(analysis_files["llm_judger"], "r") as f:
                    llm_judger_data = json.load(f)

                # Create a temporary chart generator for LLM judger data
                temp_chart_generator = ChartGenerator(
                    {}
                )  # Empty data since we'll call specific methods
                llm_judger_charts = temp_chart_generator.generate_llm_judger_charts(
                    llm_judger_data, model_name, str(charts_dir)
                )
                all_charts["llm_judger"] = llm_judger_charts
                print(
                    f"Generated {len(llm_judger_charts)} LLM judger charts for {model_name}"
                )
            except Exception as e:
                print(f"Error generating LLM judger charts for {model_name}: {e}")
                all_charts["llm_judger"] = []

        return all_charts

    def _get_chart_reference(self, chart_path: str, use_png: bool = True) -> str:
        """Get appropriate chart reference (PNG or HTML iframe)."""
        chart_path_obj = Path(chart_path)
        chart_filename = chart_path_obj.name

        if use_png:
            png_filename = chart_filename.replace(".html", ".png")
            png_path = chart_path_obj.parent / png_filename
            if png_path.exists():
                chart_name = chart_path_obj.stem
                return f"![{chart_name}](./charts/{png_filename})"
            else:
                return f"<iframe src='./charts/{chart_filename}' width='100%' height='500px'></iframe>"
        else:
            return f"<iframe src='./charts/{chart_filename}' width='100%' height='500px'></iframe>"

    def generate_sectioned_report_with_charts(
        self, analysis_file: str, model_name: str, output_dir: str
    ) -> str:
        """Generate a sectioned report with perfectly aligned charts based on metrics.md structure."""

        # Load analysis data
        with open(analysis_file, "r") as f:
            analysis_data = json.load(f)

        # Define section structure based on metrics.md
        REPORT_SECTIONS = [
            {
                "title": "Executive Summary",
                "json_paths": ["summary"],
                "charts": [],
                "prompt": """Create an executive summary that provides a high-level overview of the model's performance. 
                Include key findings, overall success rates, and main strengths/weaknesses.""",
            },
            {
                "title": "Core Performance Metrics",
                "json_paths": [
                    "summary.exact_match",
                    "summary.flexible_match",
                    "summary.weights",
                    "summary.thresholds",
                ],
                "charts": ["performance_radar", "success_comparison"],
                "prompt": """Analyze the core performance metrics including strict vs flexible matching results.
                Create tables showing the comparison between exact and flexible matching scores.
                Explain what each score means and highlight key differences.""",
            },
            {
                "title": "Task Complexity Analysis",
                "json_paths": ["success_patterns.by_tool_count"],
                "charts": ["success_by_tool_count"],
                "prompt": """Analyze how performance varies by task complexity (number of tools required).
                Create a table showing success rates by tool count for both strict and flexible matching.
                Explain the trend and identify optimal complexity ranges.""",
            },
            {
                "title": "Individual Tool Performance",
                "json_paths": ["success_patterns.by_tool", "tool_usage"],
                "charts": ["tool_success_*"],
                "prompt": """Analyze the performance of individual tools.
                Create a table showing success rates, successful tasks, and total tasks for each tool.
                Identify which tools the model struggles with most.""",
            },
            {
                "title": "Tool Combination Patterns",
                "json_paths": ["success_patterns.by_tool_combination"],
                "charts": [],
                "prompt": """Analyze success rates for specific tool combinations.
                Show the most successful and problematic tool combinations.
                Focus on combinations that appear frequently (≥5 times).""",
            },
            {
                "title": "Parameter Mismatch Analysis",
                "json_paths": ["parameter_mismatches"],
                "charts": ["parameter_mismatches"],
                "prompt": """Analyze which specific parameters are most commonly incorrect.
                Create a table showing tool names, parameter names, and mismatch counts.
                Identify systematic parameter prediction errors.""",
            },
            {
                "title": "Areas for Improvement & Recommendations",
                "json_paths": ["summary", "parameter_mismatches", "success_patterns"],
                "charts": [],
                "prompt": """Based on all the analysis, provide specific areas for improvement and actionable recommendations.
                Reference the performance indicators from the metrics documentation.
                Provide concrete steps for addressing identified issues.""",
            },
        ]

        # Generate report content
        report_sections = []
        charts_dir = Path(output_dir) / "charts"
        charts_dir.mkdir(parents=True, exist_ok=True)

        for section_config in REPORT_SECTIONS:
            # Extract relevant data for this section
            section_data = self._extract_section_data(
                analysis_data, section_config["json_paths"]
            )

            # Generate text for this section
            section_text = self._generate_section_text(
                section_data, section_config["prompt"]
            )

            # Generate charts for this section
            section_charts = self._generate_section_charts(
                section_data,
                section_config["charts"],
                model_name,
                str(charts_dir),
                analysis_data,
            )

            # Combine section
            section_content = [f"## {section_config['title']}", "", section_text]

            # Add charts if any
            if section_charts:
                section_content.extend(["", "### Visualizations"])
                for chart_path in section_charts:
                    chart_name = Path(chart_path).stem
                    chart_filename = Path(chart_path).name
                    section_content.extend(
                        [
                            f"**{chart_name.replace('_', ' ').title()}:**",
                            f"![{chart_name}](./charts/{chart_filename})",
                            "",
                        ]
                    )

            section_content.extend(["", "---", ""])
            report_sections.extend(section_content)

        return "\n".join(report_sections)

    def _extract_section_data(
        self, analysis_data: Dict[str, Any], json_paths: List[str]
    ) -> Dict[str, Any]:
        """Extract specific data subset for a report section."""
        section_data = {}

        for path in json_paths:
            if not path:  # Skip empty paths
                continue

            keys = path.split(".")
            value = analysis_data

            try:
                for key in keys:
                    value = value[key]
                section_data[path] = value
            except (KeyError, TypeError):
                # Path doesn't exist in data, skip it
                continue

        return section_data

    def _generate_section_text(self, section_data: Dict[str, Any], prompt: str) -> str:
        """Generate text for a specific section using GPT."""
        if not OPENAI_AVAILABLE:
            return f"Section analysis not available (OpenAI not installed)\n\nData: {json.dumps(section_data, indent=2)}"

        try:
            client = OpenAI()

            # Load metrics documentation for context
            metrics_content = self._load_metrics_content()

            system_prompt = f"""You are analyzing MCP model evaluation data. Use this metrics documentation for context:

{metrics_content}

Generate a clear, well-structured analysis section. Use markdown formatting including tables where appropriate.
Focus only on the specific data provided for this section.

IMPORTANT: 
- Do NOT include section headers (like # or ##) as they will be added separately
- Start directly with the content analysis
- Use only subsection headers (### or ####) if needed for organization within your content
- Generate clean markdown without any section-level headers"""

            user_prompt = f"""{prompt}

Data to analyze:
{json.dumps(section_data, indent=2)}"""

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=1500,
            )

            return response.choices[0].message.content

        except Exception as e:
            return f"Error generating section text: {str(e)}\n\nData: {json.dumps(section_data, indent=2)}"

    def _generate_section_charts(
        self,
        section_data: Dict[str, Any],
        chart_types: List[str],
        model_name: str,
        charts_dir: str,
        full_analysis_data: Dict[str, Any],
    ) -> List[str]:
        """Generate charts for a specific section."""
        if not chart_types:
            return []

        generated_charts = []

        try:
            # Create a chart generator with the FULL analysis data, not just section data
            temp_generator = ChartGenerator(full_analysis_data)

            for chart_type in chart_types:
                if chart_type == "performance_radar":
                    fig = temp_generator.create_performance_radar_chart()
                    chart_path = temp_generator.save_chart(
                        fig, f"{charts_dir}/{model_name}_performance_radar", ["png"]
                    )["png"]
                elif chart_type == "success_comparison":
                    fig = temp_generator.create_success_rate_comparison()
                    chart_path = temp_generator.save_chart(
                        fig, f"{charts_dir}/{model_name}_success_comparison", ["png"]
                    )["png"]
                elif chart_type == "success_by_tool_count":
                    fig = temp_generator.create_success_by_tool_count_chart()
                    chart_path = temp_generator.save_chart(
                        fig, f"{charts_dir}/{model_name}_success_by_tool_count", ["png"]
                    )["png"]
                elif chart_type == "parameter_mismatches":
                    fig = temp_generator.create_parameter_mismatch_chart()
                    chart_path = temp_generator.save_chart(
                        fig, f"{charts_dir}/{model_name}_parameter_mismatches", ["png"]
                    )["png"]
                elif chart_type.startswith("tool_success_"):
                    # Generate all individual tool charts
                    tool_figs = temp_generator.create_tool_specific_success_charts()
                    for i, fig in enumerate(tool_figs):
                        chart_path = temp_generator.save_chart(
                            fig, f"{charts_dir}/{model_name}_tool_specific_{i}", ["png"]
                        )["png"]
                        generated_charts.append(chart_path)
                    continue
                else:
                    continue

                if chart_path:
                    generated_charts.append(chart_path)

        except Exception as e:
            print(f"Error generating charts for section: {e}")
            import traceback

            traceback.print_exc()

        return generated_charts

    def _load_metrics_content(self) -> str:
        """Load the metrics.md content for context."""
        try:
            metrics_path = (
                Path(__file__).parent.parent / "cli" / "analyzer" / "metrics.md"
            )
            with open(metrics_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return "Metrics documentation not available."


def enhance_report_with_charts(
    analysis_file: str,
    original_report_file: str,
    output_dir: str,
    enhanced_report_file: str = None,
) -> Dict[str, str]:
    """
    Convenience function to enhance an existing report with charts.

    Args:
        analysis_file: Path to the summary analysis JSON file
        original_report_file: Path to the original AI-generated report
        output_dir: Directory to save charts and enhanced report
        enhanced_report_file: Path for enhanced report (optional)

    Returns:
        Dictionary with paths to generated files
    """
    # Load analysis data
    with open(analysis_file, "r", encoding="utf-8") as f:
        analysis_data = json.load(f)

    # Load original report
    with open(original_report_file, "r", encoding="utf-8") as f:
        original_report = f.read()

    # Create enhancer and generate charts
    enhancer = ReportEnhancer(analysis_data)
    saved_charts = enhancer.generate_charts_for_report(output_dir)

    # Enhance the report
    enhanced_report = enhancer.enhance_ai_report(original_report, saved_charts)

    # Save enhanced report
    if enhanced_report_file is None:
        base_name = Path(original_report_file).stem
        enhanced_report_file = Path(output_dir) / f"{base_name}_with_charts.md"

    with open(enhanced_report_file, "w", encoding="utf-8") as f:
        f.write(enhanced_report)

    return {
        "enhanced_report": str(enhanced_report_file),
        "charts_directory": str(Path(output_dir) / "charts"),
        "chart_files": saved_charts,
    }
