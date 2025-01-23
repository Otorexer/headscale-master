from flask import Flask, render_template
import os
import yaml

app = Flask(__name__)

# Retrieve the API_BASE_URL from environment variables, default to a fallback if not set
API_BASE_URL = os.getenv("API_BASE_URL")

HEADSCALE_CONFIG_PATH = "/etc/headscale/config.yaml"


def get_headscale_server(config_path):
    """
    Reads the Headscale configuration file and extracts the server_url.
    """
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            server_url = config.get('server_url')
            if not server_url:
                raise ValueError("server_url not found in config.yaml")
            return server_url
    except Exception as e:
        print(f"Error reading Headscale config: {e}")
        # Fallback to a default value or handle as needed
        return "https://default-headscale-server.com"
    
HEADSCALE_SERVER = get_headscale_server(HEADSCALE_CONFIG_PATH)


# Inject API_BASE_URL into all templates
@app.context_processor
def inject_api_base_url():
    """
    This function makes the API_BASE_URL available to all templates.
    """
    return {
        "API_BASE_URL": API_BASE_URL,
        "HEADSCALE_SERVER": HEADSCALE_SERVER
    }

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/nodes")
def nodes():
    return render_template("nodes/nodes.html")

@app.route("/users")
def users():
    return render_template("users/users.html")

@app.route("/pre_auth_keys")
def pre_auth_keys():
    return render_template("pre_auth_keys/pre_auth_keys.html")

@app.route('/register')
def register():
    return render_template('register/register.html')

@app.route('/deploy')
def deploy():
    return render_template('deploy/deploy.html')

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8080)
