#!/usr/bin/env python3
"""
Report Generation for LLM Judger Results

This module provides AI-powered report generation functionality for LLM judger results.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

from mcpeval.utils.cli import Colors, colored_print

# Import OpenAI for report generation
try:
    from openai import OpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def load_rubrics_content(rubrics_file: Optional[str] = None) -> str:
    """Load the rubrics content from a file.
    
    Args:
        rubrics_file: Path to custom rubrics file. If None, uses default rubrics.md
        
    Returns:
        String content of the rubrics file
    """
    if rubrics_file:
        rubrics_path = Path(rubrics_file)
    else:
        rubrics_path = Path(__file__).parent / "rubrics.md"
    
    try:
        with open(rubrics_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        if rubrics_file:
            raise FileNotFoundError(f"Custom rubrics file not found: {rubrics_file}")
        return "Rubrics documentation not available."


def generate_ai_report(
    stats: Dict[str, Any],
    correlations: Dict[str, Any],
    patterns: Dict[str, Any],
    insights: List[str],
    model: str = "gpt-4o",
    rubrics_file: Optional[str] = None,
) -> str:
    """Generate an AI-powered performance report using OpenAI models."""
    if not OPENAI_AVAILABLE:
        raise ImportError(
            "OpenAI package is not installed. Install it with: pip install openai"
        )

    # Load rubrics content
    rubrics_content = load_rubrics_content(rubrics_file)

    # Create OpenAI client
    client = OpenAI()

    # System prompt for LLM judger analysis with rubrics
    system_prompt = f"""You are an AI performance analyst specializing in LLM judger evaluation results. 

Use the following evaluation rubrics to understand the meaning and scoring criteria for each aspect:

{rubrics_content}

Generate a comprehensive performance report based on the provided LLM judger analysis data.

Your report should:
1. Provide an executive summary of the LLM judger performance
2. Include structured tables for key metrics and performance breakdowns
3. Highlight key strengths and weaknesses in both trajectory and completion evaluation
4. Identify specific areas for improvement based on the rubrics definitions
5. Explain the significance of the correlation metrics
6. Provide actionable recommendations for improving model performance
7. Analyze aspect-specific performance using the rubrics definitions (trajectory aspects like planning, efficiency, etc. and completion aspects like accuracy, completeness, etc.)

IMPORTANT: 
- Use the rubrics definitions to interpret what each score means (e.g., 0.956 for efficiency means "Very Good" performance with minor inefficiencies)
- Include well-formatted tables for:
  - Overall Performance Summary (trajectory vs completion vs combined scores)
  - Aspect Performance Breakdown (individual aspect scores with performance levels from rubrics)
  - Performance Distribution (high/medium/low score counts)
  - Top and Bottom Performers
  - Correlation Analysis Results
- Reference the specific rubrics criteria when making recommendations

Use markdown table format like this example:
| Aspect | Mean Score | Performance Level | Rubrics Interpretation | Improvement Needed |
|--------|------------|-------------------|----------------------|-------------------|
| planning | 0.969 | Excellent | Perfect task understanding, clear decomposition | Minimal |

Format the report in clear markdown with appropriate sections, emphasis, and well-structured tables.
Focus on actionable insights for improving both the model being evaluated and the evaluation process itself, using the rubrics as your guide for interpretation."""

    # Prepare analysis data for the prompt
    analysis_data = {
        "summary_statistics": stats,
        "correlations": correlations,
        "patterns": patterns,
        "insights": insights,
    }

    # User prompt with analysis results
    user_prompt = f"""Please analyze this LLM judger evaluation data and generate a performance report:

{json.dumps(analysis_data, indent=2)}"""

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

        report_content = response.choices[0].message.content
        if report_content is None:
            raise Exception("OpenAI API returned empty response")

        return report_content

    except Exception as e:
        raise Exception(f"Failed to generate AI report: {str(e)}")


def generate_report_from_analysis_file(
    analysis_file: str, model: str = "gpt-4o", output_file: Optional[str] = None, rubrics_file: Optional[str] = None
) -> str:
    """Generate an AI report directly from an analysis JSON file."""
    if not OPENAI_AVAILABLE:
        raise ImportError(
            "OpenAI package is not installed. Install it with: pip install openai"
        )

    # Load the analysis file
    try:
        with open(analysis_file, "r", encoding="utf-8") as f:
            analysis_data = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Analysis file not found: {analysis_file}")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON format in analysis file: {analysis_file}")

    # Extract components from analysis data
    stats = analysis_data.get("summary_statistics", {})
    correlations = analysis_data.get("correlations", {})
    patterns = analysis_data.get("patterns", {})
    insights = analysis_data.get("insights", [])

    # Prepare output file path
    if output_file is None:
        base_name = os.path.splitext(analysis_file)[0]
        if base_name.endswith("_analysis"):
            base_name = base_name[:-9]  # Remove '_analysis' suffix
        output_file = f"{base_name}_ai_report.md"

    # Create directory if it doesn't exist (before API call)
    output_dir = os.path.dirname(output_file)
    if output_dir:  # Only create directory if it's not empty
        os.makedirs(output_dir, exist_ok=True)

    # Generate the report
    report_content = generate_ai_report(stats, correlations, patterns, insights, model, rubrics_file)

    # Save the report
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report_content)

    return output_file


def save_ai_report(report_content: str, output_file: str) -> None:
    """Save AI report content to a file."""
    try:
        # Ensure output directory exists
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(report_content)

        colored_print(f"📄 AI performance report saved to: {output_file}", Colors.GREEN)

    except Exception as e:
        colored_print(f"❌ Error saving AI report: {e}", Colors.RED)
        raise
