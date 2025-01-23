from flask import request, jsonify
from functools import wraps
import jwt
import datetime
from db import get_db_connection
from flask import current_app

def token_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        token = None

        # JWT is passed in the request header
        if 'x-access-tokens' in request.headers:
            token = request.headers['x-access-tokens']

        if not token:
            return jsonify({'message': 'A valid token is missing'}), 401

        try:
            # Decode the token to obtain the payload
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            # Connect to the database to retrieve the current user
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM web_users WHERE public_id = ?", (data['public_id'],))
            current_user = cursor.fetchone()
            conn.close()
            if current_user is None:
                return jsonify({'message': 'Token is invalid'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError as e:
            return jsonify({'message': 'Token is invalid', 'error': str(e)}), 401

        # Pass the current_user to the route
        return f(current_user, *args, **kwargs)

    return decorator
