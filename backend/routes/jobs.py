from flask import Blueprint, jsonify, request


def create_jobs_routes(job_manager):
    """Create job management route handlers"""
    jobs_bp = Blueprint('jobs', __name__)

    @jobs_bp.route('/api/job/<job_id>', methods=['GET'])
    def get_job_status(job_id):
        """Get job status and progress"""
        try:
            status = job_manager.get_job_status(job_id)
            if status is None:
                return jsonify({'error': 'Job not found'}), 404
            return jsonify(status)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @jobs_bp.route('/api/job/<job_id>/kill', methods=['POST'])
    def kill_job(job_id):
        """Kill a running job"""
        try:
            success = job_manager.kill_job(job_id)
            if success:
                return jsonify({'message': 'Job killed successfully'})
            else:
                return jsonify({'error': 'Job not found or already completed'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return jobs_bp 