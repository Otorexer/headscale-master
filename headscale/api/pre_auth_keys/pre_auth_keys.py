from flask import Blueprint, request, jsonify
from datetime import datetime
from db import get_db_connection

# Create a Blueprint for pre_auth_keys
pre_auth_keys_bp = Blueprint('pre_auth_keys', __name__)

# Fetch all pre-auth keys
@pre_auth_keys_bp.route('/pre_auth_keys', methods=['GET'])
def get_pre_auth_keys():
    """Fetch all pre-auth keys, including the username."""
    conn = get_db_connection()
    keys = conn.execute('''
        SELECT pre_auth_keys.*, users.name AS username
        FROM pre_auth_keys
        LEFT JOIN users ON pre_auth_keys.user_id = users.id
    ''').fetchall()
    conn.close()
    return jsonify([dict(key) for key in keys])

# Fetch a single pre-auth key by ID
@pre_auth_keys_bp.route('/pre_auth_keys/<int:key_id>', methods=['GET'])
def get_pre_auth_key(key_id):
    """Fetch a single pre-auth key by ID, including the username."""
    conn = get_db_connection()
    key = conn.execute('''
        SELECT pre_auth_keys.*, users.name AS username
        FROM pre_auth_keys
        LEFT JOIN users ON pre_auth_keys.user_id = users.id
        WHERE pre_auth_keys.id = ?
    ''', (key_id,)).fetchone()
    conn.close()

    if key is None:
        return jsonify({'error': 'Pre-auth key not found'}), 404

    return jsonify(dict(key))

# Create a new pre-auth key
@pre_auth_keys_bp.route('/pre_auth_keys', methods=['POST'])
def create_pre_auth_key():
    """Create a new pre-auth key using either user_id or username."""
    data = request.json
    key = data.get('key')
    user_id = data.get('user_id')
    username = data.get('username')  # New: Allow using username instead of user_id
    reusable = data.get('reusable', 0)
    ephemeral = data.get('ephemeral', 0)
    tags = data.get('tags', '')
    expiration = data.get('expiration')
    created_at = datetime.now()

    if not key:
        return jsonify({'error': 'Key is required'}), 400

    conn = get_db_connection()

    # Resolve username to user_id if username is provided
    if username:
        user = conn.execute(
            'SELECT id FROM users WHERE name = ?', (username,)
        ).fetchone()

        if user is None:
            conn.close()
            return jsonify({'error': f'Username "{username}" not found'}), 404

        user_id = user['id']

    # Validate that user_id is available
    if not user_id:
        conn.close()
        return jsonify({'error': 'Either user_id or username is required'}), 400

    # Insert the pre-auth key into the database
    conn.execute(
        '''
        INSERT INTO pre_auth_keys (key, user_id, reusable, ephemeral, tags, created_at, expiration)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''',
        (key, user_id, reusable, ephemeral, tags, created_at, expiration)
    )
    conn.commit()
    conn.close()

    return jsonify({'message': 'Pre-auth key created successfully!'}), 201

    return jsonify({'message': 'Pre-auth key created successfully!'}), 201

# Update an existing pre-auth key
@pre_auth_keys_bp.route('/pre_auth_keys/<int:key_id>', methods=['PUT'])
def update_pre_auth_key(key_id):
    """Update an existing pre-auth key."""
    data = request.json
    key = data.get('key')
    user_id = data.get('user_id')
    reusable = data.get('reusable')
    ephemeral = data.get('ephemeral')
    used = data.get('used')
    tags = data.get('tags')
    expiration = data.get('expiration')
    updated_at = datetime.now()

    conn = get_db_connection()
    existing_key = conn.execute('SELECT * FROM pre_auth_keys WHERE id = ?', (key_id,)).fetchone()

    if existing_key is None:
        conn.close()
        return jsonify({'error': 'Pre-auth key not found'}), 404

    conn.execute(
        '''
        UPDATE pre_auth_keys
        SET key = ?, user_id = ?, reusable = ?, ephemeral = ?, used = ?, tags = ?, expiration = ?, created_at = ?
        WHERE id = ?
        ''',
        (key, user_id, reusable, ephemeral, used, tags, expiration, updated_at, key_id)
    )
    conn.commit()
    conn.close()

    return jsonify({'message': 'Pre-auth key updated successfully!'})

# Delete a pre-auth key
@pre_auth_keys_bp.route('/pre_auth_keys/<int:key_id>', methods=['DELETE'])
def delete_pre_auth_key(key_id):
    """Delete a pre-auth key."""
    conn = get_db_connection()
    existing_key = conn.execute('SELECT * FROM pre_auth_keys WHERE id = ?', (key_id,)).fetchone()

    if existing_key is None:
        conn.close()
        return jsonify({'error': 'Pre-auth key not found'}), 404

    conn.execute('DELETE FROM pre_auth_keys WHERE id = ?', (key_id,))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Pre-auth key deleted successfully!'})
