from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import jwt
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

from users.users import users_bp
from users.keys import user_keys_bp
from nodes.nodes import nodes_bp
from pre_auth_keys.pre_auth_keys import pre_auth_keys_bp
from resources.resources import resources_bp
from commands.commands import commands_bp
from db import get_db_connection
from auth import token_required  # Import the decorator from auth.py

app = Flask(__name__)

# Enable CORS for all routes and origins
CORS(app)

# Configuration
app.config['SECRET_KEY'] = 'Th1s1ss3cr3t'  # Change this to a more secure key in production
app.config['JWT_EXPIRATION_DELTA'] = datetime.timedelta(minutes=30)

# Register the Blueprints
app.register_blueprint(users_bp)
app.register_blueprint(user_keys_bp)
app.register_blueprint(nodes_bp)
app.register_blueprint(pre_auth_keys_bp)
app.register_blueprint(resources_bp)
app.register_blueprint(commands_bp)

# Registration Route
@app.route('/register', methods=['POST'])
def signup_user():
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
        cursor.execute("INSERT INTO web_users (public_id, name, password, admin) VALUES (?, ?, ?, ?)",
                       (public_id, name, hashed_password, False))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Registered successfully'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'message': 'User already exists'}), 409
    except Exception as e:
        return jsonify({'message': 'Registration failed', 'error': str(e)}), 500

# Login Route
@app.route('/login', methods=['POST'])
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
                'exp' : datetime.datetime.utcnow() + app.config['JWT_EXPIRATION_DELTA']
            }, app.config['SECRET_KEY'], algorithm="HS256")

            return jsonify({'token' : token})

        return make_response('Could not verify',  401, {'WWW-Authenticate': 'Basic realm="Login required!"'})
    except Exception as e:
        return jsonify({'message': 'Login failed', 'error': str(e)}), 500

# Example of a Protected Route
@app.route('/protected', methods=['GET'])
@token_required
def protected_route(current_user):
    return jsonify({'message': f'Hello, {current_user["name"]}! This is a protected route.'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
