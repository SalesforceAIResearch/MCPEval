#!/bin/bash

# Generate comprehensive reports with charts using the new sectioned approach
echo "🚀 Generating comprehensive travel assistant reports with sectioned charts..."

# Function to generate static evaluation report with sectioned charts
generate_sectioned_static_report() {
    local model=$1
    echo "📊 Processing static evaluation for $model (sectioned approach)..."
    
    # Check if static analysis file exists
    if [ -f "benchmarks/travel_assistant/results/${model}_mix_task_evaluation_summary_analysis.json" ]; then
        python -c "
import sys
sys.path.insert(0, 'src')
from mcpeval.cli.analyzer.analyze import generate_sectioned_report_from_summary
generate_sectioned_report_from_summary('benchmarks/travel_assistant/results/${model}_mix_task_evaluation_summary_analysis.json')
"
    else
        echo "⚠️  Static analysis file not found for $model, skipping..."
    fi
}

# Function to generate LLM judger report with charts (using existing approach for now)
generate_llm_judger_report() {
    local model=$1
    echo "🧠 Processing LLM judger analysis for $model..."
    
    # Check if LLM judger analysis file exists
    if [ -f "benchmarks/travel_assistant/report/${model}_mix_task_evaluation_trajectory_llm_judger_analysis.json" ]; then
        python -c "
import sys
sys.path.insert(0, 'src')
from mcpeval.cli.analyzer.analyze import generate_sectioned_report_from_summary
generate_sectioned_report_from_summary('benchmarks/travel_assistant/report/${model}_mix_task_evaluation_trajectory_llm_judger_analysis.json')
"
    else
        echo "⚠️  LLM judger analysis file not found for $model, skipping..."
    fi
}

# Function to process a single model
process_model() {
    local model=$1
    echo "🔄 Processing $model..."
    
    # Generate static evaluation report with sectioned charts
    generate_sectioned_static_report "$model"
    
    # Generate LLM judger report
    generate_llm_judger_report "$model"
    
    echo "✅ Completed reports for $model"
    echo ""
}

# Check if a specific model was provided as argument
if [ $# -eq 1 ]; then
    model=$1
    echo "🎯 Running for single model: $model"
    process_model "$model"
else
    # Generate reports for all models
    echo "🌟 Running for all models..."
    models=("gpt4o" "gpt4o-mini" "gpt4.1-mini" "gpt4.1-nano" "o3" "o3-mini" "o4-mini")

    for model in "${models[@]}"; do
        process_model "$model"
    done
fi

echo "🎉 Travel assistant reports with sectioned charts generated successfully!"
echo ""
echo "📁 Static evaluation reports: *_report_with_charts.md (sectioned approach)"
echo "🧠 LLM judger reports: *_llm_judger_report_with_charts.md" 