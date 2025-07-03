#!/usr/bin/env python3
"""
MCP Eval LLM Backend Server

A Flask backend server for the MCP Eval LLM system.
Provides REST APIs for task generation, verification, evaluation, and MCP server interaction.
"""

from flask import Flask, jsonify
from flask_cors import CORS

# Import configuration and core modules
from config.config_loader import load_config, parse_args
from core.job_manager import JobManager
from core.mcp_client import MCPClientManager

# Import route modules
from routes.health import create_health_routes
from routes.mcp import create_mcp_routes
from routes.files import create_files_routes
from routes.workspace import create_workspace_routes
from routes.tasks import create_tasks_routes
from routes.auto import create_auto_routes


def create_app(config_path=None):
    """Create and configure the Flask application"""
    
    # Load configuration
    config = load_config(config_path)
    
    # Create Flask app
    app = Flask(__name__)
    
    # Enable CORS
    CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000"])
    
    # Initialize core managers
    job_manager = JobManager(config)
    mcp_client_manager = MCPClientManager()
    
    # Register all route blueprints
    app.register_blueprint(create_health_routes(job_manager, mcp_client_manager))
    app.register_blueprint(create_mcp_routes(mcp_client_manager))
    app.register_blueprint(create_files_routes(config, job_manager))
    app.register_blueprint(create_workspace_routes(config, job_manager))
    app.register_blueprint(create_tasks_routes(config, job_manager))
    app.register_blueprint(create_auto_routes(config, job_manager))
    
    # Root endpoint
    @app.route('/')
    def root():
        """Root endpoint with API information"""
        return jsonify({
            'service': 'MCP Eval LLM Backend',
            'version': '1.0.0',
            'status': 'running',
            'endpoints': {
                'health': '/api/health',
                'status': '/api/status',
                'servers': '/api/servers',
                'mcp': {
                    'connect': '/api/mcp/connect',
                    'disconnect': '/api/mcp/disconnect',
                    'chat': '/api/mcp/chat',
                    'status': '/api/mcp/status'
                },
                'files': {
                    'list': '/api/files',
                    'upload': '/api/upload',
                    'download': '/api/download/<filename>',
                    'delete': '/api/files/<filename>',
                    'content': '/api/file-content/<filename>'
                },
                'workspace': {
                    'create': '/api/workspace/create',
                    'list': '/api/workspace/list',
                    'delete': '/api/workspace/<name>'
                },
                'tasks': {
                    'generate': '/api/generate-tasks',
                    'verify': '/api/verify-tasks',
                    'evaluate': '/api/evaluate-model',
                    'analyze': '/api/analyze-results',
                    'job_status': '/api/job/<job_id>'
                },
                'auto': {
                    'run': '/api/auto/run',
                    'validate': '/api/auto/config/validate',
                    'save': '/api/auto/config/save',
                    'load': '/api/auto/config/load/<name>',
                    'list': '/api/auto/config/list'
                }
            }
        })
    
    # Handle frontend static file requests gracefully
    @app.route('/manifest.json')
    def manifest():
        """Return 404 for manifest.json - should be served by frontend"""
        return jsonify({'error': 'manifest.json should be served by frontend'}), 404
    
    @app.route('/favicon.ico')
    def favicon():
        """Return 404 for favicon.ico - should be served by frontend"""
        return jsonify({'error': 'favicon.ico should be served by frontend'}), 404
    
    # Store configuration and managers in app context for debugging
    app.config['MCP_CONFIG'] = config
    app.config['JOB_MANAGER'] = job_manager
    app.config['MCP_CLIENT_MANAGER'] = mcp_client_manager
    
    return app


def main():
    """Main entry point"""
    # Parse command line arguments
    args = parse_args()
    
    # Create the Flask app
    app = create_app(args.config)
    
    # Get configuration
    config = app.config['MCP_CONFIG']
    app_config = config.get('app', {})
    
    # Print startup information
    print("="*60)
    print("🚀 MCP Eval LLM Backend Server")
    print("="*60)
    print(f"Host: {app_config.get('host', '0.0.0.0')}")
    print(f"Port: {app_config.get('port', 22358)}")
    print(f"Debug: {app_config.get('debug', True)}")
    print(f"Config: {args.config or 'backend.yaml'}")
    print("="*60)
    print("Available endpoints:")
    print("  Health:     GET  /api/health")
    print("  Status:     GET  /api/status")
    print("  Servers:    GET  /api/servers")
    print("  MCP Chat:   POST /api/mcp/chat")
    print("  Files:      GET  /api/files")
    print("  Upload:     POST /api/upload")
    print("  Tasks:      POST /api/generate-tasks")
    print("  Auto:       POST /api/auto/run")
    print("="*60)
    print("Frontend URL: http://localhost:3000")
    print("Backend URL:  http://localhost:22358")
    print("="*60)
    
    # Run the Flask app
    try:
        app.run(
            host=app_config.get('host', '0.0.0.0'),
            port=app_config.get('port', 22358),
            debug=app_config.get('debug', True)
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        exit(1)


if __name__ == '__main__':
    main() 