"""Common CRUD operations for the MCPEval database."""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from mcpeval.db.models import EvaluationRun, TaskResult, Score, LLMJudgeScore, Job

logger = logging.getLogger(__name__)


# --- Evaluation Runs ---

def create_run(
    session: Session,
    model_name: str,
    model_config: Optional[Dict] = None,
    servers: Optional[List[str]] = None,
    num_tasks: int = 0,
    run_id: Optional[str] = None,
) -> EvaluationRun:
    """Create a new evaluation run."""
    run = EvaluationRun(
        id=run_id or str(uuid.uuid4()),
        model_name=model_name,
        num_tasks=num_tasks,
        status="running",
    )
    if model_config:
        run.set_model_config(model_config)
    if servers:
        run.set_servers(servers)
    session.add(run)
    session.flush()
    return run


def complete_run(session: Session, run_id: str, status: str = "completed"):
    """Mark a run as completed and update aggregate stats."""
    run = session.get(EvaluationRun, run_id)
    if not run:
        return
    run.status = status
    results = session.query(TaskResult).filter_by(run_id=run_id).all()
    run.success_count = sum(1 for r in results if r.success)
    run.fail_count = len(results) - run.success_count
    run.total_tokens = sum((r.input_tokens or 0) + (r.output_tokens or 0) for r in results)
    session.flush()


def get_run(session: Session, run_id: str) -> Optional[EvaluationRun]:
    return session.get(EvaluationRun, run_id)


def list_runs(
    session: Session,
    model_name: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[EvaluationRun]:
    q = session.query(EvaluationRun)
    if model_name:
        q = q.filter(EvaluationRun.model_name == model_name)
    if status:
        q = q.filter(EvaluationRun.status == status)
    return q.order_by(EvaluationRun.created_at.desc()).offset(offset).limit(limit).all()


# --- Task Results ---

def add_task_result(
    session: Session,
    run_id: str,
    task_id: str,
    success: bool,
    tool_calls: Optional[List] = None,
    final_response: str = "",
    conversation: Optional[List] = None,
    error: Optional[str] = None,
    latency_ms: int = 0,
    input_tokens: int = 0,
    output_tokens: int = 0,
    task_name: Optional[str] = None,
    task_description: Optional[str] = None,
    task_goal: Optional[str] = None,
) -> TaskResult:
    """Add a task result to a run."""
    result = TaskResult(
        run_id=run_id,
        task_id=task_id,
        success=success,
        final_response=final_response,
        error=error,
        latency_ms=latency_ms,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        task_name=task_name,
        task_description=task_description,
        task_goal=task_goal,
    )
    if tool_calls:
        result.set_tool_calls(tool_calls)
    if conversation:
        result.set_conversation(conversation)
    session.add(result)
    session.flush()
    return result


def get_task_results(
    session: Session,
    run_id: str,
    success_only: Optional[bool] = None,
) -> List[TaskResult]:
    q = session.query(TaskResult).filter_by(run_id=run_id)
    if success_only is True:
        q = q.filter(TaskResult.success == True)
    elif success_only is False:
        q = q.filter(TaskResult.success == False)
    return q.all()


# --- Scores ---

def add_score(
    session: Session,
    run_id: str,
    task_id: str,
    match_type: str,
    tool_name_score: float = 0.0,
    param_match_score: float = 0.0,
    order_score: float = 0.0,
    overall_score: float = 0.0,
) -> Score:
    score = Score(
        run_id=run_id,
        task_id=task_id,
        match_type=match_type,
        tool_name_score=tool_name_score,
        param_match_score=param_match_score,
        order_score=order_score,
        overall_score=overall_score,
    )
    session.add(score)
    session.flush()
    return score


def get_scores(
    session: Session,
    run_id: str,
    match_type: Optional[str] = None,
) -> List[Score]:
    q = session.query(Score).filter_by(run_id=run_id)
    if match_type:
        q = q.filter(Score.match_type == match_type)
    return q.all()


# --- LLM Judge Scores ---

def add_llm_judge_score(
    session: Session,
    run_id: str,
    task_id: str,
    judge_model: str,
    dimension: str,
    score: float,
    max_score: float = 10.0,
    comments: str = "",
) -> LLMJudgeScore:
    entry = LLMJudgeScore(
        run_id=run_id,
        task_id=task_id,
        judge_model=judge_model,
        dimension=dimension,
        score=score,
        max_score=max_score,
        comments=comments,
    )
    session.add(entry)
    session.flush()
    return entry


def get_llm_judge_scores(
    session: Session,
    run_id: str,
    dimension: Optional[str] = None,
) -> List[LLMJudgeScore]:
    q = session.query(LLMJudgeScore).filter_by(run_id=run_id)
    if dimension:
        q = q.filter(LLMJudgeScore.dimension == dimension)
    return q.all()


# --- Jobs ---

def create_job(
    session: Session,
    job_type: str,
    title: str,
    endpoint: str = "",
    job_id: Optional[str] = None,
) -> Job:
    job = Job(
        id=job_id or str(uuid.uuid4()),
        type=job_type,
        title=title,
        endpoint=endpoint,
        status="pending",
    )
    session.add(job)
    session.flush()
    return job


def update_job(
    session: Session,
    job_id: str,
    status: Optional[str] = None,
    progress: Optional[int] = None,
    log_line: Optional[str] = None,
):
    job = session.get(Job, job_id)
    if not job:
        return
    if status is not None:
        job.status = status
    if progress is not None:
        job.progress = progress
    if log_line is not None:
        job.append_log(log_line)
    job.updated_at = datetime.now(timezone.utc)
    session.flush()


def get_job(session: Session, job_id: str) -> Optional[Job]:
    return session.get(Job, job_id)


def get_recent_jobs(session: Session, limit: int = 10) -> List[Job]:
    return (
        session.query(Job)
        .order_by(Job.created_at.desc())
        .limit(limit)
        .all()
    )


# --- JSONL Import ---

def import_eval_results_jsonl(
    session: Session,
    jsonl_path: str,
    run_id: str,
    model_name: str,
    servers: Optional[List[str]] = None,
) -> EvaluationRun:
    """Import an existing JSONL results file into the database.

    Creates an EvaluationRun and TaskResult entries for each line.
    """
    import json as _json
    from pathlib import Path

    path = Path(jsonl_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {jsonl_path}")

    run = create_run(session, model_name=model_name, servers=servers, run_id=run_id)

    count = 0
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = _json.loads(line)
            task_meta = data.get("task", {})
            add_task_result(
                session,
                run_id=run.id,
                task_id=data.get("task_id", f"task_{count}"),
                success=data.get("success", False),
                tool_calls=data.get("tool_calls", []),
                final_response=data.get("final_response", ""),
                conversation=data.get("conversation", []),
                error=data.get("error"),
                task_name=task_meta.get("name"),
                task_description=task_meta.get("description"),
                task_goal=task_meta.get("goal"),
            )
            count += 1

    run.num_tasks = count
    complete_run(session, run.id)
    logger.info(f"Imported {count} task results into run {run.id}")
    return run
