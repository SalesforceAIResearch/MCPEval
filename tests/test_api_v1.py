"""Tests for the v1 REST API routes."""

import json
import os
import sys

import pytest

# Add backend directory to path for imports
_backend_dir = os.path.join(os.path.dirname(__file__), "..", "backend")
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from mcpeval.db.session import init_db, reset_engine


@pytest.fixture(autouse=True)
def tmp_db(tmp_path):
    """Create a fresh database for each test."""
    reset_engine()
    db_path = str(tmp_path / "test_api.db")
    os.environ["MCPEVAL_DB_PATH"] = db_path
    init_db(db_path)
    yield db_path
    reset_engine()
    os.environ.pop("MCPEVAL_DB_PATH", None)


@pytest.fixture
def app(tmp_db):
    """Create a Flask test app with v1 routes registered."""
    from flask import Flask
    from routes.v1.leaderboard import create_leaderboard_routes
    from routes.v1.runs import create_runs_routes

    app = Flask(__name__)
    app.config["TESTING"] = True
    app.register_blueprint(create_runs_routes(tmp_db))
    app.register_blueprint(create_leaderboard_routes(tmp_db))
    return app


@pytest.fixture
def client(app):
    return app.test_client()


class TestRunsCRUD:
    def test_create_run(self, client):
        resp = client.post(
            "/api/v1/runs",
            json={
                "model_name": "gpt-4o",
                "servers": ["server_a.py"],
                "num_tasks": 10,
            },
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["model_name"] == "gpt-4o"
        assert data["num_tasks"] == 10
        assert "id" in data

    def test_create_run_missing_model_name(self, client):
        resp = client.post("/api/v1/runs", json={"servers": []})
        assert resp.status_code == 400

    def test_list_runs(self, client):
        client.post("/api/v1/runs", json={"model_name": "gpt-4o"})
        client.post("/api/v1/runs", json={"model_name": "gpt-3.5"})

        resp = client.get("/api/v1/runs")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) == 2

    def test_list_runs_filter(self, client):
        client.post("/api/v1/runs", json={"model_name": "gpt-4o"})
        client.post("/api/v1/runs", json={"model_name": "gpt-3.5"})

        resp = client.get("/api/v1/runs?model_name=gpt-4o")
        data = resp.get_json()
        assert len(data) == 1
        assert data[0]["model_name"] == "gpt-4o"

    def test_get_run_not_found(self, client):
        resp = client.get("/api/v1/runs/nonexistent")
        assert resp.status_code == 404

    def test_get_run_by_id(self, client):
        create_resp = client.post("/api/v1/runs", json={"model_name": "gpt-4o"})
        run_id = create_resp.get_json()["id"]

        resp = client.get(f"/api/v1/runs/{run_id}")
        assert resp.status_code == 200
        assert resp.get_json()["id"] == run_id


class TestResults:
    def test_add_and_get_results(self, client):
        run = client.post("/api/v1/runs", json={"model_name": "m"}).get_json()
        run_id = run["id"]

        # Add results
        client.post(
            f"/api/v1/runs/{run_id}/results",
            json={
                "task_id": "t1",
                "success": True,
                "final_response": "Done",
            },
        )
        client.post(
            f"/api/v1/runs/{run_id}/results",
            json={
                "task_id": "t2",
                "success": False,
                "error": "timeout",
            },
        )

        resp = client.get(f"/api/v1/runs/{run_id}/results")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) == 2

    def test_filter_results_by_success(self, client):
        run = client.post("/api/v1/runs", json={"model_name": "m"}).get_json()
        run_id = run["id"]

        client.post(
            f"/api/v1/runs/{run_id}/results", json={"task_id": "t1", "success": True}
        )
        client.post(
            f"/api/v1/runs/{run_id}/results", json={"task_id": "t2", "success": False}
        )

        passed = client.get(f"/api/v1/runs/{run_id}/results?success=true").get_json()
        assert len(passed) == 1
        assert passed[0]["task_id"] == "t1"


class TestScores:
    def test_add_and_get_scores(self, client):
        run = client.post("/api/v1/runs", json={"model_name": "m"}).get_json()
        run_id = run["id"]

        client.post(
            f"/api/v1/runs/{run_id}/scores",
            json={
                "task_id": "t1",
                "match_type": "strict",
                "overall_score": 0.85,
            },
        )

        resp = client.get(f"/api/v1/runs/{run_id}/scores")
        data = resp.get_json()
        assert data["aggregate"]["overall_score"] == pytest.approx(0.85)
        assert len(data["per_task"]) == 1

    def test_scores_missing_fields(self, client):
        run = client.post("/api/v1/runs", json={"model_name": "m"}).get_json()
        run_id = run["id"]

        resp = client.post(f"/api/v1/runs/{run_id}/scores", json={"task_id": "t1"})
        assert resp.status_code == 400


class TestComplete:
    def test_complete_run(self, client):
        run = client.post("/api/v1/runs", json={"model_name": "m"}).get_json()
        run_id = run["id"]

        client.post(
            f"/api/v1/runs/{run_id}/results", json={"task_id": "t1", "success": True}
        )
        client.post(
            f"/api/v1/runs/{run_id}/results", json={"task_id": "t2", "success": False}
        )

        resp = client.post(f"/api/v1/runs/{run_id}/complete", json={})
        data = resp.get_json()
        assert data["status"] == "completed"
        assert data["success_count"] == 1
        assert data["fail_count"] == 1


class TestLeaderboard:
    def test_empty_leaderboard(self, client):
        resp = client.get("/api/v1/leaderboard")
        assert resp.status_code == 200
        assert resp.get_json() == []

    def test_leaderboard_ranking(self, client):
        # Create two completed runs with different models
        for model, success_rate in [("gpt-4o", True), ("gpt-3.5", False)]:
            run = client.post("/api/v1/runs", json={"model_name": model}).get_json()
            run_id = run["id"]
            client.post(
                f"/api/v1/runs/{run_id}/results",
                json={
                    "task_id": "t1",
                    "success": success_rate,
                },
            )
            client.post(f"/api/v1/runs/{run_id}/complete", json={})

        resp = client.get("/api/v1/leaderboard")
        data = resp.get_json()
        assert len(data) == 2
        assert data[0]["model_name"] == "gpt-4o"  # ranked first (100% success)
        assert data[0]["rank"] == 1
        assert data[1]["model_name"] == "gpt-3.5"
