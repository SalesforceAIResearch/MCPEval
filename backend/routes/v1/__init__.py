"""V1 resource-oriented REST API routes backed by the database."""

from flask import Blueprint

from routes.v1.runs import create_runs_routes
from routes.v1.leaderboard import create_leaderboard_routes


def create_v1_routes(db_path=None):
    """Create and register all v1 API route blueprints.

    Returns a list of blueprints to register with the app.
    """
    return [
        create_runs_routes(db_path),
        create_leaderboard_routes(db_path),
    ]
