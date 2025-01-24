# headscale/api/app.py
from flask import Flask
from flask_cors import CORS
import os
import time

from users.users import users_bp
from users.keys import user_keys_bp
from nodes.nodes import nodes_bp
from pre_auth_keys.pre_auth_keys import pre_auth_keys_bp
from resources.resources import resources_bp
from commands.commands import commands_bp
from db import get_db_connection, ensure_web_users_table
from auth import token_required
from web_users.web_users import web_users_bp  # Import the new Blueprint

import sqlite3

app = Flask(__name__)

# Enable CORS for all routes and origins
CORS(app)

# Configuration
app.config['SECRET_KEY'] = 'Th1s1ss3cr3t'  # Change this to a more secure key in production
app.config['JWT_EXPIRATION_DELTA'] = 30  # JWT expiration in minutes

# Initialize the web_users table and ensure default user once when the app starts
with app.app_context():
    conn = None
    while True:
        try:
            conn = get_db_connection()
            break  # Exit the loop if connection is successful
        except FileNotFoundError as e:
            print(f"Database not found: {e}. Retrying in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            print(f"Error connecting to database: {e}. Retrying in 5 seconds...")
            time.sleep(5)
    
    try:
        ensure_web_users_table(conn)
        
        # Retrieve default user credentials from environment variables
        default_user_name = os.getenv('DEFAULT_USER_NAME')
        default_user_password = os.getenv('DEFAULT_USER_PASSWORD')

        if default_user_name and default_user_password:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM web_users WHERE name = ?", (default_user_name,))
            user = cursor.fetchone()
            
            if not user:
                # Create default user
                hashed_password = generate_password_hash(default_user_password, method='pbkdf2:sha256')
                public_id = str(uuid.uuid4())
                cursor.execute(
                    "INSERT INTO web_users (public_id, name, password, admin) VALUES (?, ?, ?, ?)",
                    (public_id, default_user_name, hashed_password, True)  # Set admin=True for the default user
                )
                conn.commit()
                print(f"Default user '{default_user_name}' created.")
            else:
                print(f"Default user '{default_user_name}' already exists.")
        else:
            print("Default user credentials not set in environment variables.")
    except Exception as e:
        print(f"Error ensuring default user: {e}")
    finally:
        if conn:
            conn.close()

# Register the Blueprints
app.register_blueprint(users_bp)
app.register_blueprint(user_keys_bp)
app.register_blueprint(nodes_bp)
app.register_blueprint(pre_auth_keys_bp)
app.register_blueprint(resources_bp)
app.register_blueprint(commands_bp)
app.register_blueprint(web_users_bp)  # Register the new Blueprint

# Removed the /login and /register route definitions from here

# Example of a Protected Route
@app.route('/protected', methods=['GET'])
@token_required
def protected_route(current_user):
    return jsonify({'message': f'Hello, {current_user["name"]}! This is a protected route.'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
