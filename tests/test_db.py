"""Tests for the database layer (models, session, operations)."""

import json
import os
import tempfile

import pytest

from mcpeval.db import operations as ops
from mcpeval.db.models import Base, EvaluationRun, Job, LLMJudgeScore, Score, TaskResult
from mcpeval.db.session import (
    get_engine,
    get_session,
    init_db,
    reset_engine,
    session_scope,
)


@pytest.fixture(autouse=True)
def tmp_db(tmp_path):
    """Create a fresh in-memory-like temp database for each test."""
    reset_engine()
    db_path = str(tmp_path / "test.db")
    os.environ["MCPEVAL_DB_PATH"] = db_path
    init_db(db_path)
    yield db_path
    reset_engine()
    os.environ.pop("MCPEVAL_DB_PATH", None)


class TestModels:
    def test_evaluation_run_json_fields(self, tmp_db):
        with session_scope(tmp_db) as s:
            run = EvaluationRun(id="run-1", model_name="gpt-4o", status="running")
            run.set_model_config({"temperature": 0.1})
            run.set_servers(["server_a.py", "server_b.py"])
            s.add(run)

        with session_scope(tmp_db) as s:
            run = s.get(EvaluationRun, "run-1")
            assert run.get_model_config() == {"temperature": 0.1}
            assert run.get_servers() == ["server_a.py", "server_b.py"]

    def test_evaluation_run_to_dict(self, tmp_db):
        with session_scope(tmp_db) as s:
            run = EvaluationRun(id="run-2", model_name="gpt-4o")
            s.add(run)

        with session_scope(tmp_db) as s:
            run = s.get(EvaluationRun, "run-2")
            d = run.to_dict()
            assert d["id"] == "run-2"
            assert d["model_name"] == "gpt-4o"

    def test_task_result_json_fields(self, tmp_db):
        with session_scope(tmp_db) as s:
            run = EvaluationRun(id="run-3", model_name="m")
            s.add(run)
            tr = TaskResult(run_id="run-3", task_id="t1", success=True)
            tr.set_tool_calls([{"tool_name": "search", "tool_parameters": {}}])
            tr.set_conversation([{"role": "user", "content": "hi"}])
            s.add(tr)

        with session_scope(tmp_db) as s:
            tr = s.query(TaskResult).filter_by(task_id="t1").first()
            assert tr.get_tool_calls()[0]["tool_name"] == "search"
            assert tr.get_conversation()[0]["role"] == "user"

    def test_job_append_log(self, tmp_db):
        with session_scope(tmp_db) as s:
            job = Job(id="j1", type="eval", title="Test job")
            job.append_log("line 1")
            job.append_log("line 2")
            s.add(job)

        with session_scope(tmp_db) as s:
            job = s.get(Job, "j1")
            logs = job.get_logs()
            assert logs == ["line 1", "line 2"]


class TestOperations:
    def test_create_and_get_run(self, tmp_db):
        with session_scope(tmp_db) as s:
            run = ops.create_run(s, model_name="gpt-4o", num_tasks=10, run_id="r1")
            assert run.id == "r1"

        with session_scope(tmp_db) as s:
            fetched = ops.get_run(s, "r1")
            assert fetched.model_name == "gpt-4o"
            assert fetched.num_tasks == 10

    def test_list_runs_filters(self, tmp_db):
        with session_scope(tmp_db) as s:
            ops.create_run(s, model_name="gpt-4o", run_id="r1")
            ops.create_run(s, model_name="gpt-3.5", run_id="r2")

        with session_scope(tmp_db) as s:
            all_runs = ops.list_runs(s)
            assert len(all_runs) == 2

            filtered = ops.list_runs(s, model_name="gpt-4o")
            assert len(filtered) == 1
            assert filtered[0].id == "r1"

    def test_add_and_get_task_results(self, tmp_db):
        with session_scope(tmp_db) as s:
            ops.create_run(s, model_name="m", run_id="r1")
            ops.add_task_result(s, run_id="r1", task_id="t1", success=True)
            ops.add_task_result(
                s, run_id="r1", task_id="t2", success=False, error="timeout"
            )

        with session_scope(tmp_db) as s:
            all_results = ops.get_task_results(s, "r1")
            assert len(all_results) == 2

            passed = ops.get_task_results(s, "r1", success_only=True)
            assert len(passed) == 1
            assert passed[0].task_id == "t1"

            failed = ops.get_task_results(s, "r1", success_only=False)
            assert len(failed) == 1
            assert failed[0].error == "timeout"

    def test_complete_run_aggregates(self, tmp_db):
        with session_scope(tmp_db) as s:
            ops.create_run(s, model_name="m", run_id="r1")
            ops.add_task_result(
                s,
                run_id="r1",
                task_id="t1",
                success=True,
                input_tokens=100,
                output_tokens=50,
            )
            ops.add_task_result(
                s,
                run_id="r1",
                task_id="t2",
                success=False,
                input_tokens=200,
                output_tokens=100,
            )
            ops.complete_run(s, "r1")

        with session_scope(tmp_db) as s:
            run = ops.get_run(s, "r1")
            assert run.status == "completed"
            assert run.success_count == 1
            assert run.fail_count == 1
            assert run.total_tokens == 450

    def test_scores(self, tmp_db):
        with session_scope(tmp_db) as s:
            ops.create_run(s, model_name="m", run_id="r1")
            ops.add_score(
                s, run_id="r1", task_id="t1", match_type="strict", overall_score=0.85
            )
            ops.add_score(
                s, run_id="r1", task_id="t1", match_type="flexible", overall_score=0.95
            )

        with session_scope(tmp_db) as s:
            strict = ops.get_scores(s, "r1", match_type="strict")
            assert len(strict) == 1
            assert strict[0].overall_score == 0.85

            all_scores = ops.get_scores(s, "r1")
            assert len(all_scores) == 2

    def test_llm_judge_scores(self, tmp_db):
        with session_scope(tmp_db) as s:
            ops.create_run(s, model_name="m", run_id="r1")
            ops.add_llm_judge_score(
                s,
                run_id="r1",
                task_id="t1",
                judge_model="gpt-4o",
                dimension="trajectory",
                score=8.5,
                comments="Good",
            )

        with session_scope(tmp_db) as s:
            scores = ops.get_llm_judge_scores(s, "r1")
            assert len(scores) == 1
            assert scores[0].score == 8.5
            assert scores[0].dimension == "trajectory"

    def test_job_crud(self, tmp_db):
        with session_scope(tmp_db) as s:
            job = ops.create_job(
                s, job_type="eval", title="Run eval", endpoint="/api/eval"
            )
            job_id = job.id

        with session_scope(tmp_db) as s:
            ops.update_job(s, job_id, status="running", progress=50, log_line="halfway")

        with session_scope(tmp_db) as s:
            job = ops.get_job(s, job_id)
            assert job.status == "running"
            assert job.progress == 50
            assert "halfway" in job.get_logs()

    def test_recent_jobs(self, tmp_db):
        with session_scope(tmp_db) as s:
            for i in range(15):
                ops.create_job(s, job_type="eval", title=f"Job {i}")

        with session_scope(tmp_db) as s:
            recent = ops.get_recent_jobs(s, limit=10)
            assert len(recent) == 10

    def test_import_jsonl(self, tmp_db, tmp_path):
        # Create a sample JSONL file
        jsonl_path = str(tmp_path / "results.jsonl")
        with open(jsonl_path, "w") as f:
            for i in range(3):
                record = {
                    "task_id": f"task_{i}",
                    "success": i % 2 == 0,
                    "tool_calls": [{"tool_name": "search", "tool_parameters": {}}],
                    "final_response": f"Response {i}",
                    "conversation": [{"role": "user", "content": f"Q{i}"}],
                    "task": {
                        "name": f"Task {i}",
                        "description": f"Desc {i}",
                        "goal": f"Goal {i}",
                    },
                }
                f.write(json.dumps(record) + "\n")

        with session_scope(tmp_db) as s:
            run = ops.import_eval_results_jsonl(
                s, jsonl_path, run_id="import-1", model_name="gpt-4o"
            )

        with session_scope(tmp_db) as s:
            run = ops.get_run(s, "import-1")
            assert run.num_tasks == 3
            assert run.success_count == 2  # tasks 0 and 2
            assert run.fail_count == 1

            results = ops.get_task_results(s, "import-1")
            assert len(results) == 3
            assert results[0].task_name == "Task 0"
