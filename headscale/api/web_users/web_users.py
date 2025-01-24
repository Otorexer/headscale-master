from flask import Blueprint, jsonify
from db import get_db_connection
from auth import token_required

# Create a Blueprint for web_users routes
web_users_bp = Blueprint('web_users', __name__)

@web_users_bp.route('/web_users', methods=['GET'])
@token_required
def get_web_users(current_user):
    """
    Fetch all web users, including only their name and admin status.
    Requires authentication.
    """
    conn = get_db_connection()
    users = conn.execute('SELECT name, admin FROM web_users').fetchall()
    conn.close()
    
    # Convert to a list of dictionaries, including only required fields
    users_list = []
    for user in users:
      users_list.append({
        'name': user['name'],
        'admin': bool(user['admin']) # Convert int to bool
      })
    return jsonify(users_list)