"""V1 API routes for evaluation runs and their results/scores."""

from flask import Blueprint, jsonify, request

from mcpeval.db.session import init_db, session_scope
from mcpeval.db import operations as ops


def create_runs_routes(db_path=None):
    bp = Blueprint("v1_runs", __name__, url_prefix="/api/v1")

    # Ensure tables exist
    init_db(db_path)

    # ------------------------------------------------------------------
    # Runs
    # ------------------------------------------------------------------

    @bp.route("/runs", methods=["GET"])
    def list_runs():
        """List evaluation runs, optionally filtered by model_name or status."""
        model_name = request.args.get("model_name")
        status = request.args.get("status")
        limit = request.args.get("limit", 50, type=int)
        offset = request.args.get("offset", 0, type=int)

        with session_scope(db_path) as s:
            runs = ops.list_runs(s, model_name=model_name, status=status, limit=limit, offset=offset)
            return jsonify([r.to_dict() for r in runs])

    @bp.route("/runs/<run_id>", methods=["GET"])
    def get_run(run_id):
        """Get details of a single evaluation run."""
        with session_scope(db_path) as s:
            run = ops.get_run(s, run_id)
            if not run:
                return jsonify({"error": "Run not found"}), 404
            return jsonify(run.to_dict())

    @bp.route("/runs", methods=["POST"])
    def create_run():
        """Create a new evaluation run."""
        data = request.get_json(force=True)
        model_name = data.get("model_name")
        if not model_name:
            return jsonify({"error": "model_name is required"}), 400

        with session_scope(db_path) as s:
            run = ops.create_run(
                s,
                model_name=model_name,
                model_config=data.get("model_config"),
                servers=data.get("servers"),
                num_tasks=data.get("num_tasks", 0),
                run_id=data.get("id"),
            )
            return jsonify(run.to_dict()), 201

    # ------------------------------------------------------------------
    # Task Results
    # ------------------------------------------------------------------

    @bp.route("/runs/<run_id>/results", methods=["GET"])
    def get_results(run_id):
        """Get per-task results for a run."""
        success = request.args.get("success")
        success_only = None
        if success == "true":
            success_only = True
        elif success == "false":
            success_only = False

        with session_scope(db_path) as s:
            run = ops.get_run(s, run_id)
            if not run:
                return jsonify({"error": "Run not found"}), 404
            results = ops.get_task_results(s, run_id, success_only=success_only)
            return jsonify([r.to_dict() for r in results])

    @bp.route("/runs/<run_id>/results", methods=["POST"])
    def add_result(run_id):
        """Add a task result to a run."""
        data = request.get_json(force=True)
        task_id = data.get("task_id")
        if not task_id:
            return jsonify({"error": "task_id is required"}), 400

        with session_scope(db_path) as s:
            run = ops.get_run(s, run_id)
            if not run:
                return jsonify({"error": "Run not found"}), 404
            result = ops.add_task_result(
                s,
                run_id=run_id,
                task_id=task_id,
                success=data.get("success", False),
                tool_calls=data.get("tool_calls"),
                final_response=data.get("final_response", ""),
                conversation=data.get("conversation"),
                error=data.get("error"),
                latency_ms=data.get("latency_ms", 0),
                input_tokens=data.get("input_tokens", 0),
                output_tokens=data.get("output_tokens", 0),
                task_name=data.get("task_name"),
                task_description=data.get("task_description"),
                task_goal=data.get("task_goal"),
            )
            return jsonify(result.to_dict()), 201

    # ------------------------------------------------------------------
    # Scores
    # ------------------------------------------------------------------

    @bp.route("/runs/<run_id>/scores", methods=["GET"])
    def get_scores(run_id):
        """Get static evaluation scores for a run."""
        match_type = request.args.get("match_type")

        with session_scope(db_path) as s:
            run = ops.get_run(s, run_id)
            if not run:
                return jsonify({"error": "Run not found"}), 404
            scores = ops.get_scores(s, run_id, match_type=match_type)

            # Aggregate mean scores
            if scores:
                avg = {
                    "tool_name_score": sum(sc.tool_name_score for sc in scores) / len(scores),
                    "param_match_score": sum(sc.param_match_score for sc in scores) / len(scores),
                    "order_score": sum(sc.order_score for sc in scores) / len(scores),
                    "overall_score": sum(sc.overall_score for sc in scores) / len(scores),
                }
            else:
                avg = {}

            return jsonify({
                "aggregate": avg,
                "per_task": [sc.to_dict() for sc in scores],
            })

    @bp.route("/runs/<run_id>/scores", methods=["POST"])
    def add_scores(run_id):
        """Add a score entry for a task in a run."""
        data = request.get_json(force=True)
        required = ["task_id", "match_type"]
        missing = [f for f in required if f not in data]
        if missing:
            return jsonify({"error": f"Missing fields: {missing}"}), 400

        with session_scope(db_path) as s:
            score = ops.add_score(
                s,
                run_id=run_id,
                task_id=data["task_id"],
                match_type=data["match_type"],
                tool_name_score=data.get("tool_name_score", 0.0),
                param_match_score=data.get("param_match_score", 0.0),
                order_score=data.get("order_score", 0.0),
                overall_score=data.get("overall_score", 0.0),
            )
            return jsonify(score.to_dict()), 201

    # ------------------------------------------------------------------
    # LLM Judge Scores
    # ------------------------------------------------------------------

    @bp.route("/runs/<run_id>/judge-scores", methods=["GET"])
    def get_judge_scores(run_id):
        """Get LLM judge scores for a run."""
        dimension = request.args.get("dimension")

        with session_scope(db_path) as s:
            run = ops.get_run(s, run_id)
            if not run:
                return jsonify({"error": "Run not found"}), 404
            scores = ops.get_llm_judge_scores(s, run_id, dimension=dimension)
            return jsonify([sc.to_dict() for sc in scores])

    # ------------------------------------------------------------------
    # Run completion
    # ------------------------------------------------------------------

    @bp.route("/runs/<run_id>/complete", methods=["POST"])
    def complete_run(run_id):
        """Mark a run as completed and compute aggregate stats."""
        data = request.get_json(silent=True) or {}
        status = data.get("status", "completed")

        with session_scope(db_path) as s:
            run = ops.get_run(s, run_id)
            if not run:
                return jsonify({"error": "Run not found"}), 404
            ops.complete_run(s, run_id, status=status)
            run = ops.get_run(s, run_id)
            return jsonify(run.to_dict())

    # ------------------------------------------------------------------
    # Compare
    # ------------------------------------------------------------------

    @bp.route("/runs/compare", methods=["POST"])
    def compare_runs():
        """Compare two or more runs statistically.

        Body: {"run_paths": ["path1.jsonl", "path2.jsonl"], "confidence": 0.95}
        """
        data = request.get_json(force=True)
        run_paths = data.get("run_paths", [])
        if len(run_paths) < 2:
            return jsonify({"error": "At least 2 run paths required"}), 400

        from mcpeval.stats.comparison import compare_results
        confidence = data.get("confidence", 0.95)

        try:
            report = compare_results(run_paths, confidence=confidence)
            return jsonify(report)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return bp
