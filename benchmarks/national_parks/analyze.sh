# Define arguments

DOMAIN="national_parks"
# MODELS=("gpt-4.1-mini")
# MODELS=("gpt-4.1-mini" "gpt-4.1-nano" "gpt-4o" "gpt-4o-mini"  "o3" "o3-mini" "o4-mini")
# MODELS=("mistral_small_24b")
# MODELS=("qwen3_3b_a3b")
# MODELS=("qwen3_32b")
MODELS=("mistral_small_24b")
MAX_TURNS=30
REPORT_MODEL="gpt-4.1-2025-04-14"
JUDGE_MODEL="gpt-4o"
SERVERS="mcp-server-nationalparks^NPS_API_KEY=$NPS_API_KEY"
TASKS_FILE="data/${DOMAIN}/evaluation_tasks_verified.jsonl"
PROMPT_FILE="benchmarks/${DOMAIN}/evaluation_prompt.json"
RESULTS_DIR="benchmarks/${DOMAIN}/results"
REPORT_DIR="benchmarks/${DOMAIN}/report"
JUDGE_LOG="benchmarks/${DOMAIN}/logs/judge.log"
EVAL_LOG="benchmarks/${DOMAIN}/logs/evaluate.log"
ANALYSIS_LOG="benchmarks/${DOMAIN}/logs/analyze.log"
JUDGE_LOG="benchmarks/${DOMAIN}/logs/judge.log"

mkdir -p benchmarks/${DOMAIN}/results
mkdir -p benchmarks/${DOMAIN}/report
mkdir -p benchmarks/${DOMAIN}/logs


for model in "${MODELS[@]}"; do
    MODEL_CONFIG="benchmarks/${DOMAIN}/eval_models/${model}.json"
    OUTPUT="benchmarks/${DOMAIN}/results/${model}_task_evaluation.jsonl"
    REPORT_OUTPUT="benchmarks/${DOMAIN}/report/${model}_task_evaluation.md"
    TRAJECTORY_FILE="benchmarks/${DOMAIN}/results/${model}_task_evaluation_with_gpt-4o_trajectory.jsonl"
    COMPLETION_FILE="benchmarks/${DOMAIN}/results/${model}_task_evaluation_with_gpt-4o_completion.jsonl"
    echo "Analyzing ${model}..."
    mcp-eval analyze --predictions $OUTPUT --ground-truth $TASKS_FILE --generate-report --report-model $REPORT_MODEL --report-output $REPORT_OUTPUT
    mcp-eval judge-rubric --trajectory-file $TRAJECTORY_FILE \
    --completion-file $COMPLETION_FILE \
    --output-dir $REPORT_DIR
done


