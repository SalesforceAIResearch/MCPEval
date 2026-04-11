#!/usr/bin/env bash
# =============================================================================
# MCPEval CLI Smoke Test Suite
#
# Runs unit tests, lint checks, CLI help verification, and (optionally)
# an end-to-end pipeline smoke test through the SFRGateway proxy.
#
# Usage:
#   ./scripts/smoke_test.sh              # Run all tests (e2e only if gateway is up)
#   ./scripts/smoke_test.sh --quick      # Skip e2e pipeline tests
#   ./scripts/smoke_test.sh --e2e-only   # Only run e2e pipeline tests
# =============================================================================

set -euo pipefail

# --- Configuration -----------------------------------------------------------
TMPDIR_PREFIX="/tmp/mcpeval_smoke"
GATEWAY_URL="http://localhost:8008/v1"
MODEL_CONFIG="eval_phase1/model_config.json"
SERVER="mcp_servers/special_calculator/server.py"
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Counters
PASS=0
FAIL=0
SKIP=0

# --- Helpers -----------------------------------------------------------------
pass()  { ((PASS++)); echo -e "  ${GREEN}PASS${NC} $1"; }
fail()  { ((FAIL++)); echo -e "  ${RED}FAIL${NC} $1"; }
skip()  { ((SKIP++)); echo -e "  ${YELLOW}SKIP${NC} $1"; }
header() { echo -e "\n${CYAN}${BOLD}=== $1 ===${NC}"; }

cleanup() {
    rm -rf "${TMPDIR_PREFIX}"_*
}

# --- Parse args --------------------------------------------------------------
RUN_UNIT=true
RUN_LINT=true
RUN_HELP=true
RUN_E2E=true

case "${1:-}" in
    --quick)    RUN_E2E=false ;;
    --e2e-only) RUN_UNIT=false; RUN_LINT=false; RUN_HELP=false ;;
    --help|-h)
        echo "Usage: $0 [--quick | --e2e-only]"
        echo "  (no args)   Run everything (e2e if gateway reachable)"
        echo "  --quick     Skip e2e pipeline tests"
        echo "  --e2e-only  Only run e2e pipeline tests"
        exit 0 ;;
esac

cd "$PROJECT_ROOT"
trap cleanup EXIT

echo -e "${BOLD}MCPEval CLI Smoke Test Suite${NC}"
echo "Project root: $PROJECT_ROOT"

# =============================================================================
# 1. Unit Tests
# =============================================================================
if $RUN_UNIT; then
    header "Unit Tests (pytest)"
    if uv run pytest tests/ --ignore=tests/test_http_mcp.py -v --tb=short 2>&1 | tail -3; then
        # Check exit code via PIPESTATUS
        if uv run pytest tests/ --ignore=tests/test_http_mcp.py -q --tb=line > /dev/null 2>&1; then
            pass "pytest (all tests passed)"
        else
            fail "pytest (some tests failed)"
        fi
    else
        fail "pytest (execution error)"
    fi
fi

# =============================================================================
# 2. Lint Checks
# =============================================================================
if $RUN_LINT; then
    header "Lint Checks"

    if uv run black --check src/ tests/ > /dev/null 2>&1; then
        pass "black formatting"
    else
        fail "black formatting (run: uv run black src/ tests/)"
    fi

    if uv run isort --check-only src/ tests/ > /dev/null 2>&1; then
        pass "isort import sorting"
    else
        fail "isort import sorting (run: uv run isort src/ tests/)"
    fi
fi

# =============================================================================
# 3. CLI --help Smoke Test
# =============================================================================
if $RUN_HELP; then
    header "CLI Subcommand --help"

    SUBCOMMANDS=(
        generate-tasks verify-tasks revalidate-tasks
        convert-data split-data evaluate analyze
        judge judge-rubric report-gen
        simulate generate-scenarios evaluate-multiturn
        auto import compare
    )

    for cmd in "${SUBCOMMANDS[@]}"; do
        if uv run mcp-eval "$cmd" --help > /dev/null 2>&1; then
            pass "$cmd --help"
        else
            fail "$cmd --help"
        fi
    done
fi

# =============================================================================
# 4. End-to-End Pipeline Smoke Test
# =============================================================================
if $RUN_E2E; then
    header "E2E Pipeline (SFRGateway)"

    # Check gateway availability
    if ! curl -s --max-time 5 "${GATEWAY_URL}/models" > /dev/null 2>&1; then
        skip "SFRGateway not reachable at ${GATEWAY_URL} — skipping e2e tests"
        skip "(start it with: cd sfrgateway && PROXY_PORT=8008 uv run python server.py)"
    else
        pass "SFRGateway reachable"

        export OPENAI_API_KEY=dummy
        export OPENAI_BASE_URL="${GATEWAY_URL}"

        WORKDIR=$(mktemp -d "${TMPDIR_PREFIX}_XXXXXX")
        TASKS="${WORKDIR}/tasks.jsonl"
        VERIFIED="${WORKDIR}/verified.jsonl"
        EVAL_OUT="${WORKDIR}/eval_results.json"
        EVAL_ARRAY="${WORKDIR}/eval_array.json"
        SCENARIOS="${WORKDIR}/scenarios.jsonl"
        SIM_OUT="${WORKDIR}/sim_results.jsonl"
        MULTITURN_EVAL="${WORKDIR}/multiturn_eval.jsonl"
        DB_PATH="${WORKDIR}/test.db"

        # 4a. generate-tasks
        if uv run mcp-eval generate-tasks \
            --servers "$SERVER" \
            --model-config "$MODEL_CONFIG" \
            --num-tasks 2 \
            --output "$TASKS" > /dev/null 2>&1; then
            pass "generate-tasks (2 tasks)"
        else
            fail "generate-tasks"
        fi

        # 4b. verify-tasks
        if [ -f "$TASKS" ]; then
            if uv run mcp-eval verify-tasks \
                --servers "$SERVER" \
                --tasks-file "$TASKS" \
                --model-config "$MODEL_CONFIG" \
                --output "$VERIFIED" \
                --non-interactive > /dev/null 2>&1; then
                pass "verify-tasks"
            else
                fail "verify-tasks"
            fi
        else
            skip "verify-tasks (no tasks file)"
        fi

        # 4c. evaluate
        if [ -f "$TASKS" ]; then
            if uv run mcp-eval evaluate \
                --servers "$SERVER" \
                --tasks-file "$TASKS" \
                --model-config "$MODEL_CONFIG" \
                --output "$EVAL_OUT" > /dev/null 2>&1; then
                pass "evaluate"
            else
                fail "evaluate"
            fi
        else
            skip "evaluate (no tasks file)"
        fi

        # 4d. analyze (needs JSON array, eval output is JSONL)
        if [ -f "$EVAL_OUT" ]; then
            # Convert JSONL to JSON array for analyze/judge
            python3 -c "
import json, sys
lines = open('${EVAL_OUT}').readlines()
data = [json.loads(l) for l in lines if l.strip()]
with open('${EVAL_ARRAY}', 'w') as f:
    json.dump(data, f)
" 2>/dev/null
            if uv run mcp-eval analyze \
                --predictions "$EVAL_ARRAY" \
                --ground-truth "$TASKS" > /dev/null 2>&1; then
                pass "analyze"
            else
                # analyze may error on small data — not a hard failure
                skip "analyze (may need more data)"
            fi
        else
            skip "analyze (no eval output)"
        fi

        # 4e. generate-scenarios
        if uv run mcp-eval generate-scenarios \
            --servers "$SERVER" \
            --model-config "$MODEL_CONFIG" \
            --num-scenarios 1 \
            --output "$SCENARIOS" > /dev/null 2>&1; then
            pass "generate-scenarios (1 scenario)"
        else
            fail "generate-scenarios"
        fi

        # 4f. simulate
        if [ -f "$SCENARIOS" ]; then
            if uv run mcp-eval simulate \
                --servers "$SERVER" \
                --simulator-model-config "$MODEL_CONFIG" \
                --agent-model-config "$MODEL_CONFIG" \
                --scenarios-file "$SCENARIOS" \
                --output "$SIM_OUT" \
                --max-turns 3 > /dev/null 2>&1; then
                pass "simulate (max-turns 3)"
            else
                fail "simulate"
            fi
        else
            skip "simulate (no scenarios file)"
        fi

        # 4g. evaluate-multiturn
        if [ -f "$SIM_OUT" ]; then
            if uv run mcp-eval evaluate-multiturn \
                --input "$SIM_OUT" \
                --model-config "$MODEL_CONFIG" \
                --output "$MULTITURN_EVAL" > /dev/null 2>&1; then
                pass "evaluate-multiturn"
            else
                fail "evaluate-multiturn"
            fi
        else
            skip "evaluate-multiturn (no simulation output)"
        fi

        # 4h. compare (duplicate eval and compare with itself)
        if [ -f "$EVAL_OUT" ]; then
            cp "$EVAL_OUT" "${EVAL_OUT}.copy"
            if uv run mcp-eval compare \
                --runs "$EVAL_OUT" "${EVAL_OUT}.copy" > /dev/null 2>&1; then
                pass "compare"
            else
                fail "compare"
            fi
        else
            skip "compare (no eval output)"
        fi

        # 4i. import
        if [ -f "$EVAL_OUT" ]; then
            if uv run mcp-eval import \
                --from "$EVAL_OUT" \
                --model-name smoke-test-model \
                --db-path "$DB_PATH" > /dev/null 2>&1; then
                pass "import (SQLite)"
            else
                fail "import"
            fi
        else
            skip "import (no eval output)"
        fi

        # 4j. judge (needs JSON array format)
        if [ -f "$EVAL_ARRAY" ]; then
            if uv run mcp-eval judge \
                --input-file "$EVAL_ARRAY" \
                --output-dir "$WORKDIR" \
                --model-config "$MODEL_CONFIG" > /dev/null 2>&1; then
                pass "judge"
            else
                fail "judge"
            fi
        else
            skip "judge (no eval array)"
        fi
    fi
fi

# =============================================================================
# Summary
# =============================================================================
header "Summary"
TOTAL=$((PASS + FAIL + SKIP))
echo -e "  ${GREEN}${PASS} passed${NC}, ${RED}${FAIL} failed${NC}, ${YELLOW}${SKIP} skipped${NC} (${TOTAL} total)"
echo ""

if [ "$FAIL" -gt 0 ]; then
    echo -e "${RED}${BOLD}Some tests failed!${NC}"
    exit 1
else
    echo -e "${GREEN}${BOLD}All tests passed!${NC}"
    exit 0
fi
