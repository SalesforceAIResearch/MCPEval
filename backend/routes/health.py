from flask import Blueprint, jsonify
from datetime import datetime
import os


def create_health_routes(job_manager, mcp_client_manager):
    """Create health-related routes"""
    health_bp = Blueprint('health', __name__)
    
    @health_bp.route('/api/health')
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0',
            'services': {
                'job_manager': 'running',
                'mcp_client_manager': 'running'
            }
        })
    
    @health_bp.route('/api/status')
    def get_status():
        """Get system status"""
        return jsonify({
            'status': 'running',
            'timestamp': datetime.now().isoformat(),
            'uptime': 'N/A',  # Could implement uptime tracking
            'memory_usage': 'N/A',  # Could implement memory monitoring
            'active_jobs': len(job_manager.job_progress),
            'recent_activities': len(job_manager.get_recent_activities())
        })
    
    @health_bp.route('/api/recent-activities')
    def get_recent_activities():
        """Get recent job activities"""
        try:
            activities = job_manager.get_recent_activities()
            return jsonify({
                'success': True,
                'activities': activities,
                'total_count': len(activities),
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e),
                'activities': [],
                'total_count': 0
            }), 500
    
    return health_bp 