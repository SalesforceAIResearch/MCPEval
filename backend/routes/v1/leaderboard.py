"""V1 API routes for the model leaderboard."""

from flask import Blueprint, jsonify, request

from mcpeval.db.session import init_db, session_scope
from mcpeval.db.models import EvaluationRun


def create_leaderboard_routes(db_path=None):
    bp = Blueprint("v1_leaderboard", __name__, url_prefix="/api/v1")

    init_db(db_path)

    @bp.route("/leaderboard", methods=["GET"])
    def leaderboard():
        """Cross-run model rankings.

        Returns models ranked by average success rate across all completed runs.
        Optionally filter by server or date range via query params.
        """
        with session_scope(db_path) as s:
            runs = (
                s.query(EvaluationRun)
                .filter(EvaluationRun.status == "completed")
                .all()
            )

            # Group by model name
            model_stats: dict = {}
            for run in runs:
                name = run.model_name
                if name not in model_stats:
                    model_stats[name] = {
                        "model_name": name,
                        "runs": 0,
                        "total_tasks": 0,
                        "total_pass": 0,
                        "total_fail": 0,
                        "total_tokens": 0,
                        "total_cost": 0.0,
                    }
                st = model_stats[name]
                st["runs"] += 1
                st["total_tasks"] += run.num_tasks or 0
                st["total_pass"] += run.success_count or 0
                st["total_fail"] += run.fail_count or 0
                st["total_tokens"] += run.total_tokens or 0
                st["total_cost"] += run.total_cost or 0.0

            # Compute success rates and sort
            entries = []
            for st in model_stats.values():
                total = st["total_pass"] + st["total_fail"]
                st["success_rate"] = round(st["total_pass"] / total, 4) if total > 0 else 0.0
                entries.append(st)

            entries.sort(key=lambda e: e["success_rate"], reverse=True)

            # Add rank
            for i, entry in enumerate(entries, 1):
                entry["rank"] = i

            return jsonify(entries)

    return bp
