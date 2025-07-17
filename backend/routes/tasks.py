from flask import Blueprint
from .task_generation import create_task_generation_routes
from .task_verification import create_task_verification_routes
from .evaluation import create_evaluation_routes
from .analysis import create_analysis_routes
from .jobs import create_jobs_routes


def create_tasks_routes(config, job_manager):
    """Create task-related route handlers by combining all sub-modules"""
    tasks_bp = Blueprint('tasks', __name__)

    # Create sub-module blueprints
    task_generation_bp = create_task_generation_routes(config, job_manager)
    task_verification_bp = create_task_verification_routes(config, job_manager)
    evaluation_bp = create_evaluation_routes(config, job_manager)
    analysis_bp = create_analysis_routes(config, job_manager)
    jobs_bp = create_jobs_routes(job_manager)

    # Register all routes to the main blueprint
    tasks_bp.register_blueprint(task_generation_bp)
    tasks_bp.register_blueprint(task_verification_bp)
    tasks_bp.register_blueprint(evaluation_bp)
    tasks_bp.register_blueprint(analysis_bp)
    tasks_bp.register_blueprint(jobs_bp)

    return tasks_bp 