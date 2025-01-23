from flask import Blueprint, jsonify
from db import get_db_connection
from auth import token_required

# Create a Blueprint for information resources
resources_bp = Blueprint('resources', __name__)

@resources_bp.route('/resources/nodes/count', methods=['GET'])
@token_required
def count_nodes(current_user):
    """Count all nodes in the database."""
    conn = get_db_connection()
    count = conn.execute('SELECT COUNT(*) AS total FROM nodes WHERE deleted_at IS NULL').fetchone()
    conn.close()

    if count:
        return jsonify({'total_nodes': count['total']}), 200
    else:
        return jsonify({'error': 'Unable to count nodes'}), 500

@resources_bp.route('/resources/users/count', methods=['GET'])
@token_required
def count_users(current_user):
    """Count all users in the database."""
    conn = get_db_connection()
    count = conn.execute('SELECT COUNT(*) AS total FROM users WHERE deleted_at IS NULL').fetchone()
    conn.close()

    if count:
        return jsonify({'total_users': count['total']}), 200
    else:
        return jsonify({'error': 'Unable to count users'}), 500

@resources_bp.route('/resources/summary', methods=['GET'])
@token_required
def get_summary(current_user):
    """Get a summary of counts for nodes and users."""
    conn = get_db_connection()
    try:
        total_nodes = conn.execute('SELECT COUNT(*) AS total FROM nodes WHERE deleted_at IS NULL').fetchone()['total']
        total_users = conn.execute('SELECT COUNT(*) AS total FROM users WHERE deleted_at IS NULL').fetchone()['total']
        conn.close()

        return jsonify({
            'total_nodes': total_nodes,
            'total_users': total_users
        }), 200
    except Exception as e:
        conn.close()
        return jsonify({'error': f'Unable to fetch summary: {str(e)}'}), 500
