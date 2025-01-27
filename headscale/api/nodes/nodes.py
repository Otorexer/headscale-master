from flask import Blueprint, request, jsonify
from datetime import datetime
from db import get_db_connection
import docker
import os
from auth import token_required

# Create a Blueprint for node routes
nodes_bp = Blueprint('nodes', __name__)

# Initialize Docker client
docker_client = docker.from_env()

# Name of the target container
HEADSCALE_CONTAINER_NAME = os.getenv('HEADSCALE_CONTAINER_NAME', 'headscale')

@nodes_bp.route('/nodes', methods=['GET'])
@token_required
def get_nodes(current_user):
    """Fetch all nodes, including the user name."""
    conn = get_db_connection()
    nodes = conn.execute('''
        SELECT nodes.*, users.name AS user_name
        FROM nodes
        LEFT JOIN users ON nodes.user_id = users.id
        WHERE nodes.deleted_at IS NULL
    ''').fetchall()
    conn.close()
    return jsonify([dict(node) for node in nodes])

@nodes_bp.route('/nodes/<int:node_id>', methods=['GET'])
@token_required
def get_node(current_user, node_id):
    """Fetch a single node by ID."""
    conn = get_db_connection()
    node = conn.execute('SELECT * FROM nodes WHERE id = ? AND deleted_at IS NULL', (node_id,)).fetchone()
    conn.close()
    if node is None:
        return jsonify({'error': 'Node not found'}), 404
    return jsonify(dict(node))

@nodes_bp.route('/nodes/<int:node_id>', methods=['PUT'])
@token_required
def update_node(current_user, node_id):
    """Update an existing node by ID."""
    data = request.json
    if not data:
        return jsonify({'error': 'No input data provided'}), 400

    conn = get_db_connection()
    node = conn.execute('SELECT * FROM nodes WHERE id = ? AND deleted_at IS NULL', (node_id,)).fetchone()
    if node is None:
        conn.close()
        return jsonify({'error': 'Node not found'}), 404

    # Define the fields that can be updated
    updatable_fields = {
        'auth_key_id',
        'disco_key',
        'endpoints',
        'expiry',
        'forced_tags',
        'given_name',
        'host_info',
        'hostname',
        'ipv4',
        'ipv6',
        'machine_key',
        'node_key',
        'register_method',
        'user_id'
    }

    # Prepare the fields to update
    fields_to_update = {}
    for field in updatable_fields:
        if field in data:
            fields_to_update[field] = data[field]

    if not fields_to_update:
        conn.close()
        return jsonify({'error': 'No valid fields provided for update'}), 400

    # Always update the updated_at timestamp
    fields_to_update['updated_at'] = datetime.utcnow()

    # Build the SQL query dynamically
    set_clause = ', '.join([f"{field} = ?" for field in fields_to_update.keys()])
    values = list(fields_to_update.values())
    values.append(node_id)  # For the WHERE clause

    try:
        conn.execute(
            f'''
            UPDATE nodes
            SET {set_clause}
            WHERE id = ?
            ''',
            tuple(values)
        )
        conn.commit()

        # Fetch the updated node
        updated_node = conn.execute('SELECT * FROM nodes WHERE id = ?', (node_id,)).fetchone()
        conn.close()

        return jsonify(dict(updated_node)), 200

    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

@nodes_bp.route('/nodes/<int:node_id>', methods=['DELETE'])
@token_required
def delete_node(current_user, node_id):
    """Delete a node by ID using the headscale CLI command."""
    try:
        # Get the headscale container
        container = docker_client.containers.get(HEADSCALE_CONTAINER_NAME)
    except docker.errors.NotFound:
        return jsonify({'error': f'Container "{HEADSCALE_CONTAINER_NAME}" not found.'}), 404
    except docker.errors.APIError as e:
        return jsonify({'error': f'Docker API error: {str(e)}'}), 500

    # Construct the command
    command = [
        "headscale",
        "nodes",
        "delete",
        "-i",
        str(node_id),
        "--force"
    ]

    try:
        # Execute the command inside the container
        exec_result = container.exec_run(cmd=command, stdout=True, stderr=True)

        stdout = exec_result.output.decode('utf-8') if exec_result.output else ''
        exit_code = exec_result.exit_code

        if exit_code == 0:
            # Command executed successfully, perform soft delete in the database
            conn = get_db_connection()
            deleted_at = datetime.utcnow()
            conn.execute(
                '''
                UPDATE nodes
                SET deleted_at = ?
                WHERE id = ?
                ''',
                (deleted_at, node_id)
            )
            conn.commit()
            conn.close()
            return jsonify({'message': f'Node {node_id} deleted successfully.', 'output': stdout}), 200
        else:
            # Command failed
            return jsonify({'error': 'Command execution failed.', 'details': stdout}), 500

    except docker.errors.APIError as e:
        return jsonify({'error': f'Failed to execute command: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500
