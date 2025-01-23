from flask import Flask
from flask_cors import CORS

from users.users import users_bp
from users.keys import user_keys_bp
from nodes.nodes import nodes_bp
from pre_auth_keys.pre_auth_keys import pre_auth_keys_bp
from resources.resources import resources_bp
from commands.commands import commands_bp



app = Flask(__name__)

# Enable CORS for all routes and all origins
CORS(app)

# Register the Blueprints
app.register_blueprint(users_bp)
app.register_blueprint(user_keys_bp)
app.register_blueprint(nodes_bp)
app.register_blueprint(pre_auth_keys_bp)
app.register_blueprint(resources_bp)
app.register_blueprint(commands_bp)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
