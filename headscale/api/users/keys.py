from flask import Blueprint, jsonify
from db import get_db_connection

# Create a Blueprint for the new API
user_keys_bp = Blueprint('user_keys', __name__)

@user_keys_bp.route('/users/keys', methods=['GET'])
def list_users_with_keys():
    """List all users and their corresponding pre-auth keys."""
    conn = get_db_connection()
    data = conn.execute('''
        SELECT 
            users.id AS user_id,
            users.name AS username,
            pre_auth_keys.id AS key_id,
            pre_auth_keys.key AS api_key,
            pre_auth_keys.reusable,
            pre_auth_keys.ephemeral,
            pre_auth_keys.used,
            pre_auth_keys.tags,
            pre_auth_keys.expiration
        FROM users
        LEFT JOIN pre_auth_keys ON users.id = pre_auth_keys.user_id
        ORDER BY users.id
    ''').fetchall()
    conn.close()

    # Process the result to group keys under each user
    users = {}
    for row in data:
        user_id = row['user_id']
        if user_id not in users:
            users[user_id] = {
                'user_id': user_id,
                'username': row['username'],
                'keys': []
            }
        if row['key_id'] is not None:  # Check if the user has keys
            users[user_id]['keys'].append({
                'key_id': row['key_id'],
                'api_key': row['api_key'],
                'reusable': row['reusable'],
                'ephemeral': row['ephemeral'],
                'used': row['used'],
                'tags': row['tags'],
                'expiration': row['expiration']
            })

    # Convert to a list for the response
    return jsonify(list(users.values()))
