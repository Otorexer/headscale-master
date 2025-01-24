# headscale/api/web_users/web_users.py
from flask import Blueprint, request, jsonify, make_response, current_app
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
import uuid
import sqlite3
from functools import wraps

from db import get_db_connection
from auth import token_required

web_users_bp = Blueprint('web_users', __name__)

@web_users_bp.route('/register', methods=['POST'])
@token_required
def signup_user(current_user):
    data = request.get_json()

    if not data or not data.get('name') or not data.get('password'):
        return jsonify({'message': 'Name and password are required'}), 400

    name = data['name']
    password = data['password']

    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    public_id = str(uuid.uuid4())

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO web_users (public_id, name, password, admin) VALUES (?, ?, ?, ?)",
            (public_id, name, hashed_password, False)
        )
        conn.commit()
        conn.close()
        return jsonify({'message': 'Registered successfully'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'message': 'User already exists'}), 409
    except Exception as e:
        return jsonify({'message': 'Registration failed', 'error': str(e)}), 500

@web_users_bp.route('/login', methods=['POST'])
def login_user():
    auth = request.authorization

    if not auth or not auth.username or not auth.password:
        return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'})

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM web_users WHERE name = ?", (auth.username,))
        user = cursor.fetchone()
        conn.close()

        if not user:
            return make_response('Could not verify',  401, {'WWW-Authenticate': 'Basic realm="Login required!"'})

        if check_password_hash(user['password'], auth.password):
            token = jwt.encode({
                'public_id': user['public_id'],
                'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=current_app.config['JWT_EXPIRATION_DELTA'])
            }, current_app.config['SECRET_KEY'], algorithm="HS256")

            return jsonify({'token' : token})

        return make_response('Could not verify',  401, {'WWW-Authenticate': 'Basic realm="Login required!"'})
    except Exception as e:
        return jsonify({'message': 'Login failed', 'error': str(e)}), 500

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
            'admin': bool(user['admin'])  # Convert int to bool
        })
    return jsonify(users_list)
