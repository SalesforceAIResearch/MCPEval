#!/usr/bin/env python
"""
Report generation module for creating AI-powered evaluation reports.
This module contains all the report generation and visualization logic.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any
import sys

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from .tool_analysis import load_metrics_content

# Import OpenAI for report generation
try:
    from openai import OpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Import visualization components
try:
    from mcpeval.visualization import (
        ChartGenerator,
        ReportEnhancer,
        enhance_report_with_charts,
    )

    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # dotenv is optional, continue without it
    pass


def generate_ai_report(analysis: Dict[str, Any], model: str = "gpt-4o") -> str:
    """Generate an AI-powered performance report using OpenAI models."""
    if not OPENAI_AVAILABLE:
        raise ImportError(
            "OpenAI package is not installed. Install it with: pip install openai"
        )

    # Load metrics content
    metrics_content = load_metrics_content()

    # Create OpenAI client
    client = OpenAI()

    # System prompt with metrics content
    system_prompt = f"""Given the metric documentation content:

{metrics_content}

Generate a comprehensive model performance report based on the provided analysis data. 

Your report should:
1. Provide an executive summary of the model's performance
2. Include structured tables for key metrics and performance breakdowns
3. Highlight key strengths and weaknesses 
4. Identify specific areas for improvement
5. Explain the significance of the metrics in plain language
6. Provide actionable recommendations
7. Use the metric definitions from the documentation to give context

IMPORTANT: Include well-formatted tables for:
- Performance by Task Complexity (number of tools vs success rate)
- Tool-Specific Performance (individual tool success rates)
- Top Tool Combinations (with success rates)
- Parameter Mismatches (most common parameter errors)

Use markdown table format like this example:
| Tool | Success Rate | Successful Tasks | Total Tasks |
|------|--------------|------------------|-------------|
| tool_name | 85.0% | 17/20 | 20 |

Format the report in clear markdown with appropriate sections, emphasis, and well-structured tables."""

    # User prompt with analysis results
    user_prompt = f"""Please analyze this model evaluation data and generate a performance report:

{json.dumps(analysis, indent=2)}"""

    try:
        # Generate the report
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=4000,
        )

        return response.choices[0].message.content

    except Exception as e:
        raise Exception(f"Failed to generate AI report: {str(e)}")


def generate_report_from_summary(
    summary_file: str,
    model: str = "gpt-4o",
    output_file: str = None,
    include_charts: bool = False,
    model_name: str = None,
    analysis_files: Dict[str, str] = None,
    analysis_type: str = "static",
) -> str:
    """Generate an AI report directly from a summary analysis JSON file.

    Args:
        summary_file: Path to the summary analysis JSON file
        model: OpenAI model to use for report generation
        output_file: Path for output report file (auto-generated if None)
        include_charts: Whether to generate and include charts
        model_name: Name of the model being analyzed (extracted from filename if None)
        analysis_files: Dict mapping analysis types to file paths (e.g., {'static': '/path/to/static.json'})
        analysis_type: Type of analysis ('static' or 'llm_judger')
    """
    if not OPENAI_AVAILABLE:
        raise ImportError(
            "OpenAI package is not installed. Install it with: pip install openai"
        )

    # Load the summary analysis file
    try:
        with open(summary_file, "r", encoding="utf-8") as f:
            analysis = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Summary file not found: {summary_file}")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON format in summary file: {summary_file}")

    # Use provided model name or extract from filename
    if model_name is None:
        # Simple extraction from filename as fallback
        model_name = Path(summary_file).stem.split("_")[0]

    # Prepare output file path
    if output_file is None:
        summary_path = Path(summary_file)
        if analysis_type == "llm_judger":
            output_file = summary_path.parent / f"{model_name}_llm_judger_ai_report.md"
        else:
            output_file = summary_path.parent / f"{model_name}_ai_report.md"
    else:
        output_file = Path(output_file).resolve()

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Generate AI report
    report_content = generate_ai_report(analysis, model)

    # Save initial report
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report_content)

    # Generate charts if requested and available
    if include_charts:
        if not VISUALIZATION_AVAILABLE:
            print(
                "⚠️  Chart generation requested but visualization dependencies not available"
            )
            print("💡 Install plotly with: pip install plotly")
        elif analysis_files:
            print(f"📊 Generating comprehensive charts...")
            try:
                from mcpeval.visualization.report_enhancer import ReportEnhancer

                # Initialize report enhancer
                enhancer = ReportEnhancer()
                output_dir = str(output_file.parent)

                # Generate charts using provided analysis files
                all_charts = enhancer.generate_comprehensive_charts(
                    analysis_files, model_name, output_dir
                )

                # Count total charts generated
                total_charts = sum(len(charts) for charts in all_charts.values())
                print(f"Generated {total_charts} charts for {model_name}")

                # Enhance report with charts if report was generated
                if output_file and Path(output_file).exists():
                    # Read the AI report content
                    with open(output_file, "r") as f:
                        report_content = f.read()

                    # Choose enhancement method based on analysis type
                    if analysis_type == "llm_judger":
                        enhanced_content = (
                            enhancer.enhance_llm_judger_report_with_charts(
                                report_content, all_charts, use_png=True
                            )
                        )
                    else:
                        enhanced_content = enhancer.enhance_ai_report_with_integrated_comprehensive_charts(
                            report_content, all_charts, use_png=True
                        )

                    # Write enhanced report
                    with open(output_file, "w") as f:
                        f.write(enhanced_content)

                    print(
                        f"✨ Enhanced report with {total_charts} charts: {output_file}"
                    )
                else:
                    print(
                        f"📊 Generated {total_charts} charts (no AI report to enhance)"
                    )

            except ImportError as e:
                print(f"Chart generation dependencies not available: {e}")
                print("Install with: pip install plotly kaleido")
            except Exception as e:
                print(f"Error generating charts: {e}")
                import traceback

                traceback.print_exc()

    return str(output_file)


def generate_sectioned_report_from_summary(
    summary_file: str,
    model: str = "gpt-4o",
    output_file: str = None,
    model_name: str = None,
    analysis_type: str = "static",
) -> str:
    """Generate a sectioned report with perfectly aligned charts using metrics.md structure.

    Args:
        summary_file: Path to the summary analysis JSON file
        model: OpenAI model to use for report generation
        output_file: Path for output report file (auto-generated if None)
        model_name: Name of the model being analyzed (extracted from filename if None)
        analysis_type: Type of analysis ('static' or 'llm_judger')
    """
    if not OPENAI_AVAILABLE:
        raise ImportError(
            "OpenAI package is not installed. Install it with: pip install openai"
        )

    if not VISUALIZATION_AVAILABLE:
        raise ImportError(
            "Visualization dependencies not available. Install with: pip install plotly kaleido"
        )

    # Use provided model name or extract from filename
    if model_name is None:
        # Simple extraction from filename as fallback
        model_name = Path(summary_file).stem.split("_")[0]

    # Prepare output file path
    if output_file is None:
        summary_path = Path(summary_file)
        if analysis_type == "llm_judger":
            output_file = (
                summary_path.parent / f"{model_name}_llm_judger_report_with_charts.md"
            )
        else:
            output_file = summary_path.parent / f"{model_name}_report_with_charts.md"
    else:
        output_file = Path(output_file).resolve()

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Generate sectioned report with charts
    from mcpeval.visualization.report_enhancer import ReportEnhancer

    enhancer = ReportEnhancer()

    # Handle different analysis types
    if analysis_type == "llm_judger":
        # For LLM judger files, we need a different approach since the data structure is different
        # For now, fall back to the regular report generation with charts
        print(
            "⚠️  LLM judger sectioned reports not yet implemented. Using standard report generation..."
        )
        return generate_report_from_summary(
            summary_file,
            model,
            str(output_file),
            include_charts=True,
            model_name=model_name,
            analysis_files={analysis_type: summary_file},
            analysis_type=analysis_type,
        )
    else:
        # Use sectioned approach for static evaluation files
        report_content = enhancer.generate_sectioned_report_with_charts(
            summary_file, model_name, str(output_file.parent)
        )

        # Save the report
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(report_content)

        print(f"📄 Sectioned report with aligned charts saved to: {output_file}")
        return str(output_file)
