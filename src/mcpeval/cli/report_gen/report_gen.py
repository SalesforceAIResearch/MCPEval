#!/usr/bin/env python
"""
Report Generation CLI for generating AI-powered evaluation reports.
Supports tool usage reports, LLM judge reports, and comprehensive reports.
"""

import json
import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from mcpeval.utils.cli import Colors, colored_print

# Import report generation functions
from ..analyzer.report_generator import (
    generate_report_from_summary as generate_tool_report,
)
from ..llm_judger.report_generator import (
    generate_report_from_analysis_file as generate_llm_judge_report,
)

# Import OpenAI for comprehensive report generation
try:
    from openai import OpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Import visualization components
try:
    from mcpeval.visualization.chart_generator import ChartGenerator
    from mcpeval.visualization.report_enhancer import ReportEnhancer

    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False


def _load_rubrics_and_metrics() -> dict:
    """Load evaluation rubrics and metrics from their respective files."""
    current_dir = Path(__file__).parent
    rubrics_path = current_dir.parent / "llm_judger" / "rubrics.md"
    metrics_path = current_dir.parent / "analyzer" / "metrics.md"

    rubrics_content = ""
    metrics_content = ""

    try:
        if rubrics_path.exists():
            with open(rubrics_path, "r", encoding="utf-8") as f:
                rubrics_content = f.read()
    except Exception as e:
        colored_print(f"Warning: Could not load rubrics: {e}", Colors.YELLOW)

    try:
        if metrics_path.exists():
            with open(metrics_path, "r", encoding="utf-8") as f:
                metrics_content = f.read()
    except Exception as e:
        colored_print(f"Warning: Could not load metrics: {e}", Colors.YELLOW)

    return {"rubrics": rubrics_content, "metrics": metrics_content}


def detect_file_type(file_path: str) -> str:
    """Detect the type of analysis file based on its structure."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Check for LLM judge analysis structure
        if all(
            key in data for key in ["summary_statistics", "correlations", "patterns"]
        ):
            return "llm_judge"

        # Check for tool analysis structure
        if "summary" in data and "tool_usage" in data:
            return "tool_analysis"

        # Check for alternative tool analysis structure
        if "parameter_mismatches" in data and "success_patterns" in data:
            return "tool_analysis"

        return "unknown"

    except Exception as e:
        colored_print(f"❌ Error detecting file type for {file_path}: {e}", Colors.RED)
        return "unknown"


def _load_json_file(file_path: str):
    """Load JSON data from file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _determine_model_name(tool_file: str, llm_judge_file: str, model_name: str) -> str:
    """Determine model name from files or use provided name."""
    if model_name:
        return model_name

    # Extract from first available file
    file_path = tool_file or llm_judge_file
    return Path(file_path).stem.split("_")[0] if file_path else "model"


def _determine_output_file(
    tool_file: str, llm_judge_file: str, output_file: str, model_name: str
) -> Path:
    """Determine output file path."""
    if output_file:
        return Path(output_file)

    # Use directory from first available file
    base_dir = (
        Path(tool_file or llm_judge_file).parent
        if (tool_file or llm_judge_file)
        else Path.cwd()
    )
    return base_dir / f"{model_name}_comprehensive_report.md"


def _generate_charts(tool_data, llm_judge_data, model_name: str, output_file: Path):
    """Generate charts for the report."""
    if not VISUALIZATION_AVAILABLE:
        return {}

    charts_dir = output_file.parent / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)
    all_charts = {}

    # Generate static/tool evaluation charts
    if tool_data:
        try:
            chart_generator = ChartGenerator(tool_data)
            static_charts = chart_generator.generate_all_charts(
                str(charts_dir), ["html", "png"], model_name
            )
            chart_paths = [
                file_dict["html"]
                for file_dict in static_charts.values()
                if "html" in file_dict
            ]
            all_charts["static"] = chart_paths
            colored_print(
                f"Generated {len(chart_paths)} static evaluation charts", Colors.GREEN
            )
        except Exception as e:
            colored_print(
                f"Warning: Error generating static charts: {e}", Colors.YELLOW
            )

    # Generate LLM judge charts
    if llm_judge_data:
        try:
            chart_generator = ChartGenerator({})
            llm_judger_charts = chart_generator.generate_llm_judger_charts(
                llm_judge_data, model_name, str(charts_dir)
            )
            all_charts["llm_judger"] = llm_judger_charts
            colored_print(
                f"Generated {len(llm_judger_charts)} LLM judger charts", Colors.GREEN
            )
        except Exception as e:
            colored_print(
                f"Warning: Error generating LLM judge charts: {e}", Colors.YELLOW
            )

    return all_charts


def _enhance_report_with_charts(output_file: Path, all_charts: dict):
    """Enhance report with generated charts."""
    if not all_charts:
        return

    with open(output_file, "r") as f:
        content = f.read()

    enhancer = ReportEnhancer()
    enhanced_content = content

    # Enhance with static charts
    if "static" in all_charts:
        enhanced_content = (
            enhancer.enhance_ai_report_with_integrated_comprehensive_charts(
                enhanced_content, all_charts, use_png=True
            )
        )

    # Enhance with LLM judge charts
    if "llm_judger" in all_charts:
        enhanced_content = enhancer.enhance_llm_judger_report_with_charts(
            enhanced_content, all_charts, use_png=True
        )

    with open(output_file, "w") as f:
        f.write(enhanced_content)

    total_charts = sum(len(charts) for charts in all_charts.values())
    colored_print(f"✨ Enhanced report with {total_charts} charts", Colors.GREEN)


def generate_comprehensive_report(
    tool_file: str = None,
    llm_judge_file: str = None,
    model_name: str = None,
    output_file: str = None,
    model: str = "gpt-4o",
    include_charts: bool = True,
) -> str:
    """Generate a comprehensive report combining tool usage and LLM judge analysis."""
    if not OPENAI_AVAILABLE:
        raise ImportError(
            "OpenAI package is not installed. Install it with: pip install openai"
        )

    # Load evaluation framework
    framework = _load_rubrics_and_metrics()

    # Load data
    tool_data = _load_json_file(tool_file) if tool_file else None
    llm_judge_data = _load_json_file(llm_judge_file) if llm_judge_file else None

    # Determine output parameters
    model_name = _determine_model_name(tool_file, llm_judge_file, model_name)
    output_file = _determine_output_file(
        tool_file, llm_judge_file, output_file, model_name
    )
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Generate report using OpenAI
    client = OpenAI()

    # Enhanced system prompt with rubrics and metrics
    system_prompt = f"""You are an AI performance analyst specializing in comprehensive LLM evaluation. You have access to detailed evaluation rubrics and metrics frameworks.

## EVALUATION FRAMEWORK

### LLM Judge Evaluation Rubrics:
{framework['rubrics']}

### Tool Usage Evaluation Metrics:
{framework['metrics']}

## TASK
Generate a comprehensive performance report that combines tool usage analysis and LLM judge evaluation results using the above frameworks.

## REPORT STRUCTURE

Your report should include:

### 1. Executive Summary
- Overall performance assessment using the rubric scoring scale (0.0-1.0)
- Key strengths and weaknesses identified
- High-level recommendations

### 2. Tool Usage Analysis (if available)
- **Strict vs Flexible Matching Performance**: Analyze success rates using both approaches
- **Parameter Accuracy**: Review parameter mismatch patterns and success rates
- **Tool Selection Effectiveness**: Evaluate tool success rates and combination patterns
- **Efficiency Metrics**: Analyze tool count vs success rate relationships
- **Error Patterns**: Identify missing tools, extra tools, and systematic issues

### 3. LLM Judge Analysis (if available)
Based on the trajectory evaluation aspects, analyze:
- **Planning Quality**: Task understanding and decomposition effectiveness
- **Execution Flow**: Logical sequence and action structure
- **Tool Selection**: Appropriateness of chosen tools for each step
- **Tool Usage**: Parameter correctness and result interpretation
- **Adaptability**: Error handling and context management
- **Efficiency**: Optimization and resource utilization
- **Context Awareness**: Constraint awareness and state tracking

Based on task completion aspects, analyze:
- **Requirement Coverage**: Completeness against task specifications
- **Accuracy**: Factual correctness and analysis quality
- **Completeness**: Thoroughness and detail level
- **Usefulness**: Practical value and applicability

### 4. Integrated Analysis
- **Correlation Analysis**: How tool usage patterns relate to LLM judge scores
- **Performance Consistency**: Areas where both evaluations agree/disagree
- **Bottleneck Identification**: Critical failure points across both dimensions
- **Strength Amplification**: Areas where good tool usage enhances trajectory quality

### 5. Detailed Findings
- **Quantitative Metrics**: Present key numerical findings with proper context
- **Qualitative Insights**: Behavioral patterns and execution characteristics
- **Comparative Analysis**: Performance relative to evaluation thresholds

### 6. Actionable Recommendations
- **Immediate Improvements**: High-impact, low-effort fixes
- **Strategic Enhancements**: Longer-term development priorities
- **Training Focus Areas**: Specific capabilities to develop
- **Evaluation Insights**: Lessons for future assessments

## FORMATTING REQUIREMENTS
- Use clear markdown formatting with proper headers
- Include well-structured tables for quantitative data
- Use bullet points for key insights
- Provide specific examples where relevant
- Reference the rubric scoring scale (0.0-1.0) throughout
- Include confidence indicators for assessments

## ANALYSIS PRINCIPLES
- Base conclusions on evidence from the provided data
- Use the established rubrics and metrics as your evaluation framework
- Provide balanced assessment of strengths and weaknesses
- Focus on actionable insights that can drive improvement
- Maintain consistency with the scoring scales and definitions provided"""

    combined_data = {
        "tool_analysis": tool_data,
        "llm_judge_analysis": llm_judge_data,
        "model_name": model_name,
    }

    user_prompt = f"""Please analyze this combined evaluation data and generate a comprehensive performance report using the provided rubrics and metrics framework:

{json.dumps(combined_data, indent=2)}"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=8000,
        )

        # Save the report
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(response.choices[0].message.content)

        # Generate and add charts
        if include_charts:
            colored_print(
                "📊 Generating charts for comprehensive report...", Colors.CYAN
            )
            all_charts = _generate_charts(
                tool_data, llm_judge_data, model_name, output_file
            )
            _enhance_report_with_charts(output_file, all_charts)

        return str(output_file)

    except Exception as e:
        raise Exception(f"Failed to generate comprehensive report: {str(e)}")


def _validate_input_files(tool_file: str, llm_judge_file: str):
    """Validate input files exist and are accessible."""
    if not tool_file and not llm_judge_file:
        colored_print(
            "❌ At least one input file (--tool-analysis-file or --llm-judge-file) is required",
            Colors.RED,
        )
        sys.exit(1)

    for file_path, file_type in [
        (tool_file, "Tool analysis"),
        (llm_judge_file, "LLM judge analysis"),
    ]:
        if file_path and not os.path.exists(file_path):
            colored_print(f"❌ {file_type} file not found: {file_path}", Colors.RED)
            sys.exit(1)


def main(args):
    """Main entry point for report generation CLI."""
    colored_print("📄 AI Report Generator", Colors.BRIGHT_CYAN, bold=True)
    colored_print("=" * 50, Colors.CYAN)

    # Validate input files
    _validate_input_files(args.tool_analysis_file, args.llm_judge_file)

    # Determine chart inclusion
    include_charts = not args.no_charts

    try:
        if args.tool_analysis_file and args.llm_judge_file:
            # Generate comprehensive report
            colored_print(
                "🔄 Generating comprehensive report combining both analyses...",
                Colors.CYAN,
            )
            output_file = generate_comprehensive_report(
                tool_file=args.tool_analysis_file,
                llm_judge_file=args.llm_judge_file,
                model_name=args.model_name,
                output_file=args.output_file,
                model=args.model,
                include_charts=include_charts,
            )
            colored_print(
                f"✅ Comprehensive report generated: {output_file}", Colors.GREEN
            )

        elif args.tool_analysis_file:
            # Generate tool usage report
            colored_print("🔧 Generating tool usage report...", Colors.CYAN)

            file_type = detect_file_type(args.tool_analysis_file)
            if file_type != "tool_analysis":
                colored_print(
                    f"⚠️ File may not be a tool analysis file: {args.tool_analysis_file}",
                    Colors.YELLOW,
                )

            output_file = generate_tool_report(
                summary_file=args.tool_analysis_file,
                model=args.model,
                output_file=args.output_file,
                include_charts=include_charts,
                model_name=args.model_name,
                analysis_files={"static": args.tool_analysis_file},
                analysis_type="static",
            )
            colored_print(
                f"✅ Tool usage report generated: {output_file}", Colors.GREEN
            )

        elif args.llm_judge_file:
            # Generate LLM judge report
            colored_print("🧠 Generating LLM judge report...", Colors.CYAN)

            file_type = detect_file_type(args.llm_judge_file)
            if file_type != "llm_judge":
                colored_print(
                    f"⚠️ File may not be an LLM judge analysis file: {args.llm_judge_file}",
                    Colors.YELLOW,
                )

            output_file = generate_llm_judge_report(
                analysis_file=args.llm_judge_file,
                model=args.model,
                output_file=args.output_file,
            )
            colored_print(f"✅ LLM judge report generated: {output_file}", Colors.GREEN)

        colored_print(
            f"\n✅ Report generation completed successfully!",
            Colors.BRIGHT_GREEN,
            bold=True,
        )

    except KeyboardInterrupt:
        colored_print("\n⚠️ Report generation interrupted by user", Colors.YELLOW)
        sys.exit(1)
    except Exception as e:
        colored_print(f"\n❌ Report generation failed: {e}", Colors.RED)
        if getattr(args, "verbose", False):
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    print("Please use the main CLI: mcp-eval report-gen --help")
    sys.exit(1)
