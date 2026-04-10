"""SQLAlchemy ORM models for MCPEval persistent storage."""

import json
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Boolean,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class EvaluationRun(Base):
    """A single evaluation run (one model against a task set)."""

    __tablename__ = "evaluation_runs"

    id = Column(String, primary_key=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    status = Column(String, default="running")  # running, completed, failed
    model_name = Column(String, nullable=False)
    model_config = Column(Text, default="{}")  # JSON blob
    servers = Column(Text, default="[]")  # JSON list of server paths
    task_file_hash = Column(String, nullable=True)
    num_tasks = Column(Integer, default=0)
    config_snapshot = Column(Text, default="{}")  # full config JSON

    # Aggregated stats (populated on completion)
    success_count = Column(Integer, default=0)
    fail_count = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)

    task_results = relationship(
        "TaskResult", back_populates="run", cascade="all, delete-orphan"
    )
    scores = relationship(
        "Score", back_populates="run", cascade="all, delete-orphan"
    )
    llm_judge_scores = relationship(
        "LLMJudgeScore", back_populates="run", cascade="all, delete-orphan"
    )

    def set_model_config(self, config: dict):
        self.model_config = json.dumps(config)

    def get_model_config(self) -> dict:
        return json.loads(self.model_config) if self.model_config else {}

    def set_servers(self, servers: list):
        self.servers = json.dumps(servers)

    def get_servers(self) -> list:
        return json.loads(self.servers) if self.servers else []

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "status": self.status,
            "model_name": self.model_name,
            "model_config": self.get_model_config(),
            "servers": self.get_servers(),
            "num_tasks": self.num_tasks,
            "success_count": self.success_count,
            "fail_count": self.fail_count,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
        }


class TaskResult(Base):
    """Result of evaluating a single task within a run."""

    __tablename__ = "task_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, ForeignKey("evaluation_runs.id"), nullable=False, index=True)
    task_id = Column(String, nullable=False, index=True)
    success = Column(Boolean, default=False)
    tool_calls = Column(Text, default="[]")  # JSON list
    final_response = Column(Text, default="")
    conversation = Column(Text, default="[]")  # JSON list
    error = Column(Text, nullable=True)
    latency_ms = Column(Integer, default=0)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)

    # Task metadata
    task_name = Column(String, nullable=True)
    task_description = Column(Text, nullable=True)
    task_goal = Column(Text, nullable=True)

    run = relationship("EvaluationRun", back_populates="task_results")

    def set_tool_calls(self, calls: list):
        self.tool_calls = json.dumps(calls)

    def get_tool_calls(self) -> list:
        return json.loads(self.tool_calls) if self.tool_calls else []

    def set_conversation(self, conv: list):
        self.conversation = json.dumps(conv)

    def get_conversation(self) -> list:
        return json.loads(self.conversation) if self.conversation else []

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "run_id": self.run_id,
            "task_id": self.task_id,
            "success": self.success,
            "tool_calls": self.get_tool_calls(),
            "final_response": self.final_response,
            "conversation": self.get_conversation(),
            "error": self.error,
            "latency_ms": self.latency_ms,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "task_name": self.task_name,
            "task_description": self.task_description,
            "task_goal": self.task_goal,
        }


class Score(Base):
    """Static evaluation scores for a task result."""

    __tablename__ = "scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, ForeignKey("evaluation_runs.id"), nullable=False, index=True)
    task_id = Column(String, nullable=False, index=True)
    match_type = Column(String, nullable=False)  # "strict" or "flexible"
    tool_name_score = Column(Float, default=0.0)
    param_match_score = Column(Float, default=0.0)
    order_score = Column(Float, default=0.0)
    overall_score = Column(Float, default=0.0)

    run = relationship("EvaluationRun", back_populates="scores")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "run_id": self.run_id,
            "task_id": self.task_id,
            "match_type": self.match_type,
            "tool_name_score": self.tool_name_score,
            "param_match_score": self.param_match_score,
            "order_score": self.order_score,
            "overall_score": self.overall_score,
        }


class LLMJudgeScore(Base):
    """LLM judge scores for a task result (multi-aspect evaluation)."""

    __tablename__ = "llm_judge_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, ForeignKey("evaluation_runs.id"), nullable=False, index=True)
    task_id = Column(String, nullable=False, index=True)
    judge_model = Column(String, nullable=False)
    dimension = Column(String, nullable=False)  # e.g. "trajectory", "completion"
    score = Column(Float, default=0.0)
    max_score = Column(Float, default=10.0)
    comments = Column(Text, default="")

    run = relationship("EvaluationRun", back_populates="llm_judge_scores")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "run_id": self.run_id,
            "task_id": self.task_id,
            "judge_model": self.judge_model,
            "dimension": self.dimension,
            "score": self.score,
            "max_score": self.max_score,
            "comments": self.comments,
        }


class Job(Base):
    """Backend job tracking (replaces in-memory JobManager storage)."""

    __tablename__ = "jobs"

    id = Column(String, primary_key=True)
    type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    endpoint = Column(String, nullable=True)
    status = Column(String, default="pending")  # pending, running, completed, failed, cancelled
    progress = Column(Integer, default=0)
    command = Column(Text, nullable=True)
    logs = Column(Text, default="[]")  # JSON list of log lines
    metadata_json = Column(Text, default="{}")  # extra metadata
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    def append_log(self, line: str):
        logs = json.loads(self.logs) if self.logs else []
        logs.append(line)
        self.logs = json.dumps(logs)

    def get_logs(self) -> list:
        return json.loads(self.logs) if self.logs else []

    def set_metadata(self, data: dict):
        self.metadata_json = json.dumps(data)

    def get_metadata(self) -> dict:
        return json.loads(self.metadata_json) if self.metadata_json else {}

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "endpoint": self.endpoint,
            "status": self.status,
            "progress": self.progress,
            "command": self.command,
            "logs": self.get_logs(),
            "metadata": self.get_metadata(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
