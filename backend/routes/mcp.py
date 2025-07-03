from flask import Blueprint, jsonify, request


def create_mcp_routes(mcp_client_manager):
    """Create MCP route handlers"""
    mcp_bp = Blueprint('mcp', __name__)

    @mcp_bp.route('/api/mcp/connect', methods=['POST'])
    def mcp_connect():
        """Connect to multiple MCP servers"""
        try:
            data = request.get_json()
            servers = data.get('servers', [])
            server_args = data.get('server_args', [])
            server_types = data.get('server_types', [])
            llm_config = data.get('llm_config', {})
            
            result = mcp_client_manager.connect_to_servers(servers, server_args, llm_config, server_types)
            return jsonify(result)
            
        except Exception as e:
            import traceback
            print("Full traceback:")
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    @mcp_bp.route('/api/mcp/disconnect', methods=['POST'])
    def mcp_disconnect():
        """Disconnect from MCP servers"""
        try:
            result = mcp_client_manager.disconnect_from_servers()
            return jsonify(result)
            
        except Exception as e:
            print(f"Error in disconnect: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    @mcp_bp.route('/api/mcp/chat', methods=['POST'])
    def mcp_chat():
        """Send a message to the MCP client"""
        try:
            data = request.get_json()
            message = data.get('message', '')
            
            result = mcp_client_manager.send_message(message)
            return jsonify(result)
            
        except Exception as e:
            print(f"Error in mcp_chat: {e}")
            import traceback
            traceback.print_exc()
            
            # Check for API key related errors
            if 'API key' in str(e) or 'authentication' in str(e).lower():
                error_message = 'Invalid API key. Please check your OpenAI API key configuration.'
            else:
                error_message = str(e)
            
            return jsonify({'success': False, 'error': error_message}), 500

    @mcp_bp.route('/api/mcp/status', methods=['GET'])
    def mcp_status():
        """Get MCP client status"""
        try:
            status = mcp_client_manager.get_status()
            return jsonify(status)
            
        except Exception as e:
            return jsonify({'connected': False, 'error': str(e)}), 500

    return mcp_bp 