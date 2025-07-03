#!/usr/bin/env python3
"""
LLM Judger Results Analyzer

This module provides analysis functionality for LLM judger results,
specifically for analyzing trajectory and completion score files.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict, Counter
import statistics

from mcp_eval_llm.utils.cli import Colors, colored_print, setup_colored_logging, load_json
from dotenv import load_dotenv

# Import OpenAI for report generation
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Load environment variables
load_dotenv()

# Set up logging
setup_colored_logging(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_score_files(trajectory_file: str, completion_file: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Load trajectory and completion score files."""
    try:
        trajectory_scores = load_json(trajectory_file)
        completion_scores = load_json(completion_file)
        
        colored_print(f"✅ Loaded {len(trajectory_scores)} trajectory scores", Colors.GREEN)
        colored_print(f"✅ Loaded {len(completion_scores)} completion scores", Colors.GREEN)
        
        return trajectory_scores, completion_scores
        
    except Exception as e:
        colored_print(f"❌ Error loading score files: {e}", Colors.RED)
        sys.exit(1)


def merge_score_data(trajectory_scores: List[Dict[str, Any]], 
                     completion_scores: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Merge trajectory and completion scores by task_id."""
    merged_data = {}
    
    # Index trajectory scores by task_id
    trajectory_map = {item['task_id']: item for item in trajectory_scores}
    
    # Index completion scores by task_id
    completion_map = {item['task_id']: item for item in completion_scores}
    
    # Find all unique task_ids
    all_task_ids = set(trajectory_map.keys()) | set(completion_map.keys())
    
    for task_id in all_task_ids:
        merged_data[task_id] = {
            'task_id': task_id,
            'task_name': '',
            'original_success': None,
            'trajectory': trajectory_map.get(task_id),
            'completion': completion_map.get(task_id)
        }
        
        # Get task name and original success from either source
        if trajectory_map.get(task_id):
            merged_data[task_id]['task_name'] = trajectory_map[task_id].get('task_name', '')
            merged_data[task_id]['original_success'] = trajectory_map[task_id].get('original_success')
        elif completion_map.get(task_id):
            merged_data[task_id]['task_name'] = completion_map[task_id].get('task_name', '')
            merged_data[task_id]['original_success'] = completion_map[task_id].get('original_success')
    
    return merged_data


def calculate_summary_statistics(merged_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate summary statistics for trajectory and completion scores."""
    stats = {
        'total_tasks': len(merged_data),
        'trajectory_stats': {},
        'completion_stats': {},
        'combined_stats': {},
        'task_coverage': {},
        'aspect_analysis': {}
    }
    
    # Collect scores
    trajectory_scores = []
    completion_scores = []
    combined_scores = []
    
    # Collect aspect scores
    trajectory_aspects = defaultdict(list)
    completion_aspects = defaultdict(list)
    
    tasks_with_both = 0
    tasks_with_trajectory_only = 0
    tasks_with_completion_only = 0
    
    for task_id, data in merged_data.items():
        has_trajectory = data['trajectory'] is not None
        has_completion = data['completion'] is not None
        
        if has_trajectory and has_completion:
            tasks_with_both += 1
        elif has_trajectory:
            tasks_with_trajectory_only += 1
        elif has_completion:
            tasks_with_completion_only += 1
        
        if has_trajectory:
            traj_score = data['trajectory']['trajectory_score']
            trajectory_scores.append(traj_score)
            
            # Collect aspect scores
            traj_aspects = data['trajectory'].get('trajectory_scores', {})
            for aspect, score in traj_aspects.items():
                trajectory_aspects[aspect].append(score)
        
        if has_completion:
            comp_score = data['completion']['completion_score']
            completion_scores.append(comp_score)
            
            # Collect aspect scores
            comp_aspects = data['completion'].get('completion_scores', {})
            for aspect, score in comp_aspects.items():
                completion_aspects[aspect].append(score)
        
        # Calculate combined score if both are available
        if has_trajectory and has_completion:
            combined_score = (data['trajectory']['trajectory_score'] + data['completion']['completion_score']) / 2
            combined_scores.append(combined_score)
    
    # Calculate trajectory statistics
    if trajectory_scores:
        stats['trajectory_stats'] = {
            'count': len(trajectory_scores),
            'mean': statistics.mean(trajectory_scores),
            'median': statistics.median(trajectory_scores),
            'std_dev': statistics.stdev(trajectory_scores) if len(trajectory_scores) > 1 else 0,
            'min': min(trajectory_scores),
            'max': max(trajectory_scores),
            'high_scores': sum(1 for s in trajectory_scores if s >= 0.8),
            'medium_scores': sum(1 for s in trajectory_scores if 0.5 <= s < 0.8),
            'low_scores': sum(1 for s in trajectory_scores if s < 0.5)
        }
    
    # Calculate completion statistics
    if completion_scores:
        stats['completion_stats'] = {
            'count': len(completion_scores),
            'mean': statistics.mean(completion_scores),
            'median': statistics.median(completion_scores),
            'std_dev': statistics.stdev(completion_scores) if len(completion_scores) > 1 else 0,
            'min': min(completion_scores),
            'max': max(completion_scores),
            'high_scores': sum(1 for s in completion_scores if s >= 0.8),
            'medium_scores': sum(1 for s in completion_scores if 0.5 <= s < 0.8),
            'low_scores': sum(1 for s in completion_scores if s < 0.5)
        }
    
    # Calculate combined statistics
    if combined_scores:
        stats['combined_stats'] = {
            'count': len(combined_scores),
            'mean': statistics.mean(combined_scores),
            'median': statistics.median(combined_scores),
            'std_dev': statistics.stdev(combined_scores) if len(combined_scores) > 1 else 0,
            'min': min(combined_scores),
            'max': max(combined_scores),
            'high_scores': sum(1 for s in combined_scores if s >= 0.8),
            'medium_scores': sum(1 for s in combined_scores if 0.5 <= s < 0.8),
            'low_scores': sum(1 for s in combined_scores if s < 0.5)
        }
    
    # Task coverage statistics
    stats['task_coverage'] = {
        'tasks_with_both_scores': tasks_with_both,
        'tasks_with_trajectory_only': tasks_with_trajectory_only,
        'tasks_with_completion_only': tasks_with_completion_only
    }
    
    # Aspect analysis
    stats['aspect_analysis']['trajectory'] = {}
    for aspect, scores in trajectory_aspects.items():
        if scores:
            stats['aspect_analysis']['trajectory'][aspect] = {
                'mean': statistics.mean(scores),
                'median': statistics.median(scores),
                'std_dev': statistics.stdev(scores) if len(scores) > 1 else 0,
                'min': min(scores),
                'max': max(scores)
            }
    
    stats['aspect_analysis']['completion'] = {}
    for aspect, scores in completion_aspects.items():
        if scores:
            stats['aspect_analysis']['completion'][aspect] = {
                'mean': statistics.mean(scores),
                'median': statistics.median(scores),
                'std_dev': statistics.stdev(scores) if len(scores) > 1 else 0,
                'min': min(scores),
                'max': max(scores)
            }
    
    return stats


def analyze_correlations(merged_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze correlations between trajectory and completion scores."""
    correlations = {
        'trajectory_completion_correlation': None,
        'original_success_correlation': {}
    }
    
    # Collect data for correlation analysis
    trajectory_scores = []
    completion_scores = []
    original_success_values = []
    
    for task_id, data in merged_data.items():
        if data['trajectory'] and data['completion']:
            traj_score = data['trajectory']['trajectory_score']
            comp_score = data['completion']['completion_score']
            
            trajectory_scores.append(traj_score)
            completion_scores.append(comp_score)
            
            # Original success correlation
            if data['original_success'] is not None:
                original_success_values.append((data['original_success'], traj_score, comp_score))
    
    # Calculate trajectory-completion correlation
    if len(trajectory_scores) > 1:
        try:
            correlation = statistics.correlation(trajectory_scores, completion_scores)
            correlations['trajectory_completion_correlation'] = correlation
        except statistics.StatisticsError:
            correlations['trajectory_completion_correlation'] = None
    
    # Analyze original success correlation
    if original_success_values:
        success_traj_scores = [traj for success, traj, comp in original_success_values if success]
        failure_traj_scores = [traj for success, traj, comp in original_success_values if not success]
        success_comp_scores = [comp for success, traj, comp in original_success_values if success]
        failure_comp_scores = [comp for success, traj, comp in original_success_values if not success]
        
        correlations['original_success_correlation'] = {
            'success_trajectory_mean': statistics.mean(success_traj_scores) if success_traj_scores else 0,
            'failure_trajectory_mean': statistics.mean(failure_traj_scores) if failure_traj_scores else 0,
            'success_completion_mean': statistics.mean(success_comp_scores) if success_comp_scores else 0,
            'failure_completion_mean': statistics.mean(failure_comp_scores) if failure_comp_scores else 0,
            'success_count': len(success_traj_scores),
            'failure_count': len(failure_traj_scores)
        }
    
    return correlations


def identify_patterns(merged_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Identify patterns in the scoring data."""
    patterns = {
        'high_performers': [],
        'low_performers': [],
        'trajectory_completion_gaps': [],
        'consistent_performers': [],
        'aspect_weaknesses': {
            'trajectory': defaultdict(list),
            'completion': defaultdict(list)
        }
    }
    
    for task_id, data in merged_data.items():
        task_name = data['task_name']
        
        # Identify high and low performers
        if data['trajectory'] and data['completion']:
            traj_score = data['trajectory']['trajectory_score']
            comp_score = data['completion']['completion_score']
            combined_score = (traj_score + comp_score) / 2
            
            if combined_score >= 0.9:
                patterns['high_performers'].append({
                    'task_id': task_id,
                    'task_name': task_name,
                    'trajectory_score': traj_score,
                    'completion_score': comp_score,
                    'combined_score': combined_score
                })
            elif combined_score <= 0.5:
                patterns['low_performers'].append({
                    'task_id': task_id,
                    'task_name': task_name,
                    'trajectory_score': traj_score,
                    'completion_score': comp_score,
                    'combined_score': combined_score
                })
            
            # Identify large gaps between trajectory and completion scores
            gap = abs(traj_score - comp_score)
            if gap >= 0.3:
                patterns['trajectory_completion_gaps'].append({
                    'task_id': task_id,
                    'task_name': task_name,
                    'trajectory_score': traj_score,
                    'completion_score': comp_score,
                    'gap': gap,
                    'gap_direction': 'trajectory_higher' if traj_score > comp_score else 'completion_higher'
                })
            
            # Identify consistent performers (both scores within 0.1 of each other)
            if gap <= 0.1 and combined_score >= 0.7:
                patterns['consistent_performers'].append({
                    'task_id': task_id,
                    'task_name': task_name,
                    'trajectory_score': traj_score,
                    'completion_score': comp_score,
                    'combined_score': combined_score
                })
        
        # Identify aspect weaknesses
        if data['trajectory']:
            traj_aspects = data['trajectory'].get('trajectory_scores', {})
            for aspect, score in traj_aspects.items():
                if score <= 0.6:
                    patterns['aspect_weaknesses']['trajectory'][aspect].append({
                        'task_id': task_id,
                        'task_name': task_name,
                        'score': score
                    })
        
        if data['completion']:
            comp_aspects = data['completion'].get('completion_scores', {})
            for aspect, score in comp_aspects.items():
                if score <= 0.6:
                    patterns['aspect_weaknesses']['completion'][aspect].append({
                        'task_id': task_id,
                        'task_name': task_name,
                        'score': score
                    })
    
    # Sort patterns by scores
    patterns['high_performers'].sort(key=lambda x: x['combined_score'], reverse=True)
    patterns['low_performers'].sort(key=lambda x: x['combined_score'])
    patterns['trajectory_completion_gaps'].sort(key=lambda x: x['gap'], reverse=True)
    patterns['consistent_performers'].sort(key=lambda x: x['combined_score'], reverse=True)
    
    return patterns


def generate_insights(stats: Dict[str, Any], correlations: Dict[str, Any], patterns: Dict[str, Any]) -> List[str]:
    """Generate actionable insights from the analysis."""
    insights = []
    
    # Overall performance insights
    if stats.get('combined_stats'):
        combined = stats['combined_stats']
        insights.append(f"Overall Performance: Average combined score of {combined['mean']:.3f} with {combined['high_scores']} high-performing tasks (≥0.8)")
    
    # Trajectory vs Completion comparison
    if stats.get('trajectory_stats') and stats.get('completion_stats'):
        traj_mean = stats['trajectory_stats']['mean']
        comp_mean = stats['completion_stats']['mean']
        
        if abs(traj_mean - comp_mean) > 0.05:
            better_aspect = "trajectory" if traj_mean > comp_mean else "completion"
            worse_aspect = "completion" if traj_mean > comp_mean else "trajectory"
            insights.append(f"Performance Gap: {better_aspect.title()} scores are significantly higher than {worse_aspect} scores ({traj_mean:.3f} vs {comp_mean:.3f})")
    
    # Correlation insights
    if correlations.get('trajectory_completion_correlation') is not None:
        corr = correlations['trajectory_completion_correlation']
        if corr > 0.7:
            insights.append(f"Strong Correlation: Trajectory and completion scores are highly correlated (r={corr:.3f})")
        elif corr < 0.3:
            insights.append(f"Weak Correlation: Trajectory and completion scores show weak correlation (r={corr:.3f}), suggesting different evaluation aspects")
    
    # Original success correlation insights
    if correlations.get('original_success_correlation'):
        osc = correlations['original_success_correlation']
        if osc['success_count'] > 0 and osc['failure_count'] > 0:
            success_avg = (osc['success_trajectory_mean'] + osc['success_completion_mean']) / 2
            failure_avg = (osc['failure_trajectory_mean'] + osc['failure_completion_mean']) / 2
            if success_avg - failure_avg > 0.2:
                insights.append(f"Success Alignment: Tasks marked as successful show significantly higher LLM judge scores ({success_avg:.3f} vs {failure_avg:.3f})")
    
    # Pattern insights
    if patterns['trajectory_completion_gaps']:
        gap_count = len(patterns['trajectory_completion_gaps'])
        insights.append(f"Score Inconsistency: {gap_count} tasks show large gaps (≥0.3) between trajectory and completion scores")
    
    if patterns['high_performers']:
        insights.append(f"Top Performers: {len(patterns['high_performers'])} tasks achieved excellent scores (≥0.9)")
    
    if patterns['low_performers']:
        insights.append(f"Improvement Needed: {len(patterns['low_performers'])} tasks scored poorly (≤0.5) and need attention")
    
    # Aspect-specific insights
    if stats.get('aspect_analysis'):
        # Find weakest trajectory aspects
        traj_aspects = stats['aspect_analysis'].get('trajectory', {})
        if traj_aspects:
            weakest_traj = min(traj_aspects.items(), key=lambda x: x[1]['mean'])
            insights.append(f"Weakest Trajectory Aspect: {weakest_traj[0]} (avg: {weakest_traj[1]['mean']:.3f})")
        
        # Find weakest completion aspects
        comp_aspects = stats['aspect_analysis'].get('completion', {})
        if comp_aspects:
            weakest_comp = min(comp_aspects.items(), key=lambda x: x[1]['mean'])
            insights.append(f"Weakest Completion Aspect: {weakest_comp[0]} (avg: {weakest_comp[1]['mean']:.3f})")
    
    return insights


def print_analysis_summary(stats: Dict[str, Any], correlations: Dict[str, Any], 
                          patterns: Dict[str, Any], insights: List[str]) -> None:
    """Print a comprehensive analysis summary."""
    colored_print("\n" + "="*80, Colors.CYAN)
    colored_print("LLM JUDGER RESULTS ANALYSIS", Colors.BRIGHT_CYAN, bold=True)
    colored_print("="*80, Colors.CYAN)
    
    # Basic statistics
    colored_print(f"\n📊 OVERVIEW:", Colors.BRIGHT_CYAN, bold=True)
    colored_print(f"Total tasks analyzed: {stats['total_tasks']}", Colors.WHITE)
    
    coverage = stats['task_coverage']
    colored_print(f"Tasks with both scores: {coverage['tasks_with_both_scores']}", Colors.GREEN)
    colored_print(f"Tasks with trajectory only: {coverage['tasks_with_trajectory_only']}", Colors.YELLOW)
    colored_print(f"Tasks with completion only: {coverage['tasks_with_completion_only']}", Colors.YELLOW)
    
    # Score statistics
    if stats.get('trajectory_stats'):
        colored_print(f"\n🛤️  TRAJECTORY SCORES:", Colors.BRIGHT_BLUE, bold=True)
        traj = stats['trajectory_stats']
        colored_print(f"Mean: {traj['mean']:.3f} ± {traj['std_dev']:.3f}", Colors.WHITE)
        colored_print(f"Range: {traj['min']:.3f} - {traj['max']:.3f}", Colors.WHITE)
        colored_print(f"Distribution: {traj['high_scores']} high (≥0.8), {traj['medium_scores']} medium (0.5-0.8), {traj['low_scores']} low (<0.5)", Colors.WHITE)
    
    if stats.get('completion_stats'):
        colored_print(f"\n✅ COMPLETION SCORES:", Colors.BRIGHT_GREEN, bold=True)
        comp = stats['completion_stats']
        colored_print(f"Mean: {comp['mean']:.3f} ± {comp['std_dev']:.3f}", Colors.WHITE)
        colored_print(f"Range: {comp['min']:.3f} - {comp['max']:.3f}", Colors.WHITE)
        colored_print(f"Distribution: {comp['high_scores']} high (≥0.8), {comp['medium_scores']} medium (0.5-0.8), {comp['low_scores']} low (<0.5)", Colors.WHITE)
    
    if stats.get('combined_stats'):
        colored_print(f"\n🎯 COMBINED SCORES:", Colors.BRIGHT_MAGENTA, bold=True)
        combined = stats['combined_stats']
        colored_print(f"Mean: {combined['mean']:.3f} ± {combined['std_dev']:.3f}", Colors.WHITE)
        colored_print(f"Range: {combined['min']:.3f} - {combined['max']:.3f}", Colors.WHITE)
        colored_print(f"Distribution: {combined['high_scores']} high (≥0.8), {combined['medium_scores']} medium (0.5-0.8), {combined['low_scores']} low (<0.5)", Colors.WHITE)
    
    # Correlation analysis
    colored_print(f"\n🔗 CORRELATIONS:", Colors.BRIGHT_YELLOW, bold=True)
    if correlations.get('trajectory_completion_correlation') is not None:
        corr = correlations['trajectory_completion_correlation']
        colored_print(f"Trajectory ↔ Completion: {corr:.3f}", Colors.WHITE)
    
    if correlations.get('original_success_correlation'):
        osc = correlations['original_success_correlation']
        if osc['success_count'] > 0 and osc['failure_count'] > 0:
            colored_print(f"Original Success Impact:", Colors.WHITE)
            colored_print(f"  Successful tasks avg: {(osc['success_trajectory_mean'] + osc['success_completion_mean'])/2:.3f}", Colors.GREEN)
            colored_print(f"  Failed tasks avg: {(osc['failure_trajectory_mean'] + osc['failure_completion_mean'])/2:.3f}", Colors.RED)
    
    # Aspect analysis
    if stats.get('aspect_analysis'):
        colored_print(f"\n🎭 ASPECT ANALYSIS:", Colors.BRIGHT_CYAN, bold=True)
        
        # Trajectory aspects
        traj_aspects = stats['aspect_analysis'].get('trajectory', {})
        if traj_aspects:
            colored_print(f"Trajectory aspects (avg scores):", Colors.BLUE)
            sorted_traj = sorted(traj_aspects.items(), key=lambda x: x[1]['mean'], reverse=True)
            for aspect, data in sorted_traj:
                color = Colors.GREEN if data['mean'] >= 0.8 else Colors.YELLOW if data['mean'] >= 0.6 else Colors.RED
                colored_print(f"  {aspect}: {data['mean']:.3f}", color)
        
        # Completion aspects
        comp_aspects = stats['aspect_analysis'].get('completion', {})
        if comp_aspects:
            colored_print(f"Completion aspects (avg scores):", Colors.GREEN)
            sorted_comp = sorted(comp_aspects.items(), key=lambda x: x[1]['mean'], reverse=True)
            for aspect, data in sorted_comp:
                color = Colors.GREEN if data['mean'] >= 0.8 else Colors.YELLOW if data['mean'] >= 0.6 else Colors.RED
                colored_print(f"  {aspect}: {data['mean']:.3f}", color)
    
    # Key patterns
    colored_print(f"\n🔍 KEY PATTERNS:", Colors.BRIGHT_MAGENTA, bold=True)
    colored_print(f"High performers (≥0.9): {len(patterns['high_performers'])}", Colors.GREEN)
    colored_print(f"Low performers (≤0.5): {len(patterns['low_performers'])}", Colors.RED)
    colored_print(f"Large score gaps (≥0.3): {len(patterns['trajectory_completion_gaps'])}", Colors.YELLOW)
    colored_print(f"Consistent performers: {len(patterns['consistent_performers'])}", Colors.CYAN)
    
    # Insights
    colored_print(f"\n💡 KEY INSIGHTS:", Colors.BRIGHT_WHITE, bold=True)
    for i, insight in enumerate(insights, 1):
        colored_print(f"{i}. {insight}", Colors.WHITE)


def save_analysis_results(stats: Dict[str, Any], correlations: Dict[str, Any], 
                         patterns: Dict[str, Any], insights: List[str], 
                         output_file: str) -> None:
    """Save analysis results to JSON file."""
    analysis_results = {
        'summary_statistics': stats,
        'correlations': correlations,
        'patterns': patterns,
        'insights': insights,
        'metadata': {
            'analysis_type': 'llm_judger_results',
            'version': '1.0'
        }
    }
    
    try:
        # Ensure output directory exists
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_results, f, indent=2, ensure_ascii=False)
            
        colored_print(f"✅ Analysis results saved to {output_file}", Colors.GREEN)
        
    except Exception as e:
        colored_print(f"❌ Error saving analysis results: {e}", Colors.RED)


def load_rubrics_content() -> str:
    """Load the rubrics.md content from the llm_judger directory."""
    rubrics_path = Path(__file__).parent / "rubrics.md"
    try:
        with open(rubrics_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Rubrics documentation not available."


def generate_ai_report(stats: Dict[str, Any], correlations: Dict[str, Any], 
                      patterns: Dict[str, Any], insights: List[str], 
                      model: str = "gpt-4o") -> str:
    """Generate an AI-powered performance report using OpenAI models."""
    if not OPENAI_AVAILABLE:
        raise ImportError("OpenAI package is not installed. Install it with: pip install openai")
    
    # Load rubrics content
    rubrics_content = load_rubrics_content()
    
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
        'summary_statistics': stats,
        'correlations': correlations,
        'patterns': patterns,
        'insights': insights
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
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=4000
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        raise Exception(f"Failed to generate AI report: {str(e)}")


def generate_report_from_analysis_file(analysis_file: str, model: str = "gpt-4o", output_file: str = None) -> str:
    """Generate an AI report directly from an analysis JSON file."""
    if not OPENAI_AVAILABLE:
        raise ImportError("OpenAI package is not installed. Install it with: pip install openai")
    
    # Load the analysis file
    try:
        with open(analysis_file, 'r', encoding='utf-8') as f:
            analysis_data = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Analysis file not found: {analysis_file}")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON format in analysis file: {analysis_file}")
    
    # Extract components from analysis data
    stats = analysis_data.get('summary_statistics', {})
    correlations = analysis_data.get('correlations', {})
    patterns = analysis_data.get('patterns', {})
    insights = analysis_data.get('insights', [])
    
    # Prepare output file path
    if output_file is None:
        base_name = os.path.splitext(analysis_file)[0]
        if base_name.endswith('_analysis'):
            base_name = base_name[:-9]  # Remove '_analysis' suffix
        output_file = f"{base_name}_ai_report.md"
    
    # Create directory if it doesn't exist (before API call)
    output_dir = os.path.dirname(output_file)
    if output_dir:  # Only create directory if it's not empty
        os.makedirs(output_dir, exist_ok=True)
    
    # Generate the report
    report_content = generate_ai_report(stats, correlations, patterns, insights, model)
    
    # Save the report
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    return output_file


def main(args):
    """Main entry point for LLM judger analysis."""
    # Set up logging based on verbosity
    if getattr(args, 'verbose', False):
        setup_colored_logging(level=logging.DEBUG)
    else:
        setup_colored_logging(level=logging.INFO)
    
    # Print banner
    colored_print("🧠 LLM Judger Results Analyzer", Colors.BRIGHT_CYAN, bold=True)
    colored_print("=" * 50, Colors.CYAN)
    
    # Validate that we have the required input files for analysis
    if not args.trajectory_file or not args.completion_file:
        colored_print("❌ Both --trajectory-file and --completion-file are required for analysis", Colors.RED)
        sys.exit(1)
    
    # Validate input files exist
    if not os.path.exists(args.trajectory_file):
        colored_print(f"❌ Trajectory file not found: {args.trajectory_file}", Colors.RED)
        sys.exit(1)
    
    if not os.path.exists(args.completion_file):
        colored_print(f"❌ Completion file not found: {args.completion_file}", Colors.RED)
        sys.exit(1)
    
    try:
        # Load score files
        colored_print("📂 Loading score files...", Colors.CYAN)
        trajectory_scores, completion_scores = load_score_files(args.trajectory_file, args.completion_file)
        
        # Merge data
        colored_print("🔗 Merging trajectory and completion data...", Colors.CYAN)
        merged_data = merge_score_data(trajectory_scores, completion_scores)
        
        # Calculate statistics
        colored_print("📊 Calculating summary statistics...", Colors.CYAN)
        stats = calculate_summary_statistics(merged_data)
        
        # Analyze correlations
        colored_print("🔗 Analyzing correlations...", Colors.CYAN)
        correlations = analyze_correlations(merged_data)
        
        # Identify patterns
        colored_print("🔍 Identifying patterns...", Colors.CYAN)
        patterns = identify_patterns(merged_data)
        
        # Generate insights
        colored_print("💡 Generating insights...", Colors.CYAN)
        insights = generate_insights(stats, correlations, patterns)
        
        # Print summary
        print_analysis_summary(stats, correlations, patterns, insights)
        
        # Determine output directory
        output_dir = getattr(args, 'output_dir', None)
        if output_dir is None:
            output_dir = os.path.dirname(args.trajectory_file)
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate base filename for outputs
        base_name = os.path.splitext(os.path.basename(args.trajectory_file))[0]
        if base_name.endswith('_trajectory_scores'):
            base_name = base_name[:-17]  # Remove '_trajectory_scores' suffix
        
        # Always save analysis results
        analysis_output = os.path.join(output_dir, f"{base_name}_llm_judger_analysis.json")
        colored_print(f"\n💾 Saving analysis results...", Colors.CYAN)
        save_analysis_results(stats, correlations, patterns, insights, analysis_output)
        
        # Generate AI report by default (unless disabled with --generate-report 0)
        generate_report = getattr(args, 'generate_report', 1)
        if generate_report == 1:
            colored_print(f"\n🤖 Generating AI performance report using {getattr(args, 'report_model', 'gpt-4o')}...", Colors.CYAN)
            try:
                # Prepare report output path
                report_output = os.path.join(output_dir, f"{base_name}_llm_judger_ai_report.md")
                
                # Generate the report
                report_content = generate_ai_report(
                    stats, correlations, patterns, insights, 
                    getattr(args, 'report_model', 'gpt-4o')
                )
                
                # Save report
                with open(report_output, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                
                colored_print(f"📄 AI performance report saved to: {report_output}", Colors.GREEN)
                
            except Exception as e:
                colored_print(f"❌ Failed to generate AI report: {str(e)}", Colors.RED)
                colored_print("💡 Make sure you have the OpenAI API key set and the openai package installed", Colors.DIM)
        else:
            colored_print(f"\n📋 AI report generation disabled (--generate-report 0)", Colors.DIM)
        
        colored_print(f"\n✅ Analysis completed successfully!", Colors.BRIGHT_GREEN, bold=True)
        
    except KeyboardInterrupt:
        colored_print("\n⚠️ Analysis interrupted by user", Colors.YELLOW)
        sys.exit(1)
    except Exception as e:
        colored_print(f"\n❌ Analysis failed: {e}", Colors.RED)
        if getattr(args, 'verbose', False):
            logger.exception("Detailed error information:")
        sys.exit(1)


if __name__ == "__main__":
    print("Please use the main CLI: python -m mcp_eval_llm.cli.main llm-judge-analyze --help")
    sys.exit(1)
