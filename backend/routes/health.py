from flask import Blueprint, jsonify


def create_health_routes(job_manager, mcp_client_manager):
    """Create health and status route handlers"""
    health_bp = Blueprint('health', __name__)

    @health_bp.route('/api/health', methods=['GET'])
    def health():
        """Health check endpoint"""
        return jsonify({'status': 'healthy', 'service': 'MCP Eval LLM Backend'})

    @health_bp.route('/api/status', methods=['GET'])
    def status():
        """Status endpoint with system information"""
        try:
            # Get recent activities from job manager
            activities = job_manager.get_recent_activities()
            
            # Get MCP client status
            mcp_status = mcp_client_manager.get_status()
            
            # Basic system status
            system_status = {
                'status': 'healthy',
                'service': 'MCP Eval LLM Backend',
                'timestamp': job_manager.job_progress.get('timestamp', 'N/A'),
                'recent_activities': activities,
                'mcp_connection': mcp_status
            }
            
            return jsonify(system_status)
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'service': 'MCP Eval LLM Backend',
                'error': str(e),
                'recent_activities': [],
                'mcp_connection': {'connected': False, 'error': str(e)}
            }), 500

    return health_bp 