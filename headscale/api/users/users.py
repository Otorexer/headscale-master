from flask import Blueprint, request, jsonify
from datetime import datetime
from db import get_db_connection
import requests
import os

# Create a Blueprint for user routes
users_bp = Blueprint('users', __name__)

# You can adjust this base URL to match your deployment.
# For local development where your API is running on http://localhost:5000, do:
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5000")

@users_bp.route('/users', methods=['GET'])
def get_users():
    """Fetch all users."""
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users WHERE deleted_at IS NULL').fetchall()
    conn.close()
    return jsonify([dict(user) for user in users])

@users_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Fetch a single user by ID."""
    conn = get_db_connection()
    user = conn.execute(
        'SELECT * FROM users WHERE id = ? AND deleted_at IS NULL',
        (user_id,)
    ).fetchone()
    conn.close()
    if user is None:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(dict(user))

@users_bp.route('/users', methods=['POST'])
def create_user():
    """Create a new user with name as required and display_name and email as optional."""
    data = request.json
    name = data.get('name')  # Required field
    display_name = data.get('display_name')  # Optional field
    email = data.get('email')  # Optional field
    created_at = datetime.now()

    # Validate the presence of the required name field
    if not name:
        return jsonify({'error': 'Name is required'}), 400

    # Insert the new user into the database
    conn = get_db_connection()
    conn.execute(
        '''
        INSERT INTO users (created_at, updated_at, name, display_name, email)
        VALUES (?, ?, ?, ?, ?)
        ''',
        (created_at, created_at, name, display_name, email)
    )
    conn.commit()
    conn.close()
    return jsonify({'message': 'User created successfully!'}), 201

@users_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Update an existing user's information."""
    data = request.json
    name = data.get('name')  # Required field
    display_name = data.get('display_name')  # Optional field
    email = data.get('email')  # Optional field
    updated_at = datetime.now()

    # Validate the presence of the required name field
    if not name:
        return jsonify({'error': 'Name is required'}), 400

    conn = get_db_connection()

    # Check if the user exists and is not deleted
    user = conn.execute(
        'SELECT * FROM users WHERE id = ? AND deleted_at IS NULL',
        (user_id,)
    ).fetchone()
    if user is None:
        conn.close()
        return jsonify({'error': 'User not found'}), 404

    # Update the user information
    conn.execute(
        '''
        UPDATE users
        SET name = ?, display_name = ?, email = ?, updated_at = ?
        WHERE id = ?
        ''',
        (name, display_name, email, updated_at, user_id)
    )
    conn.commit()
    conn.close()
    return jsonify({'message': 'User updated successfully!'}), 200

@users_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """
    Delete a user by ID, removing them from the database.
    Also deletes any nodes belonging to this user first.
    """
    conn = get_db_connection()

    # Check if the user exists
    user = conn.execute(
        'SELECT * FROM users WHERE id = ? AND deleted_at IS NULL',
        (user_id,)
    ).fetchone()
    if user is None:
        conn.close()
        return jsonify({'error': 'User not found'}), 404

    # Fetch all nodes related to this user
    nodes = conn.execute(
        'SELECT id FROM nodes WHERE user_id = ? AND deleted_at IS NULL',
        (user_id,)
    ).fetchall()

    # Delete each node individually by calling the DELETE endpoint
    for node in nodes:
        node_id = node['id']
        delete_url = f"{API_BASE_URL}/nodes/{node_id}"
        try:
            resp = requests.delete(delete_url)
            if not resp.ok:
                # If node deletion fails, stop and return error
                conn.close()
                return jsonify({
                    'error': f'Failed to delete node {node_id}',
                    'details': resp.text
                }), 500
        except Exception as e:
            conn.close()
            return jsonify({
                'error': f'Exception occurred while deleting node {node_id}',
                'details': str(e)
            }), 500

    # If all nodes were successfully deleted, remove the user
    conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()

    return jsonify({'message': f'User {user_id} and all related nodes deleted successfully!'}), 200
