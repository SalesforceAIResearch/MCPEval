Run the MCPEval test suite. Accept an optional argument: `quick` (skip e2e), `e2e` (e2e only), or blank (run all).

## What to do

Run `scripts/smoke_test.sh` with the appropriate flag based on the argument:
- No argument or `all`: `./scripts/smoke_test.sh`
- `quick`: `./scripts/smoke_test.sh --quick`
- `e2e` or `e2e-only`: `./scripts/smoke_test.sh --e2e-only`

After the script finishes, summarize the results in a table showing pass/fail/skip for each test category.

## Interpreting failures

If tests fail, diagnose them:

- **pytest failures**: Read the failing test output and identify the root cause. Check if it's a code change regression or a test environment issue.
- **black/isort failures**: Run `uv run black src/ tests/` and `uv run isort src/ tests/` to auto-fix formatting. Show the user what changed.
- **CLI --help failures**: The subcommand likely has an import error. Run `uv run mcp-eval <cmd> --help` directly and read the traceback.
- **E2E failures**: Check if the SFRGateway is running (`curl -s http://localhost:8008/v1/models`). If it is, run the failing command manually with full output to see the error.

## Key gotchas learned from testing

- `analyze` and `judge` expect JSON arrays, not JSONL — the smoke test auto-converts
- `import` uses `--from` (not `--input`)
- `convert-data` has no `--output-format` flag
- `revalidate-tasks` needs verified tasks with tool_calls data to do real work
- E2E tests need `OPENAI_API_KEY=dummy OPENAI_BASE_URL=http://localhost:8008/v1`
- Model config: `eval_phase1/model_config.json`
- Simplest server for testing: `mcp_servers/special_calculator/server.py`

$ARGUMENTS
