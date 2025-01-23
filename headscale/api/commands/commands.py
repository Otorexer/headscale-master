from flask import Blueprint, request, jsonify
import docker
import os

# Create a Blueprint for command routes
commands_bp = Blueprint('commands', __name__)

# Initialize Docker client
# Ensure that the Docker environment variables are correctly set.
# If Docker is running on a different host or requires special configuration,
# you may need to adjust the parameters accordingly.
docker_client = docker.from_env()

# Name of the target container
HEADSCALE_CONTAINER_NAME = os.getenv('HEADSCALE_CONTAINER_NAME', 'headscale')

@commands_bp.route('/commands/register', methods=['POST'])
def register_node():
    """
    Register a node in the headscale container by executing the
    headscale nodes register command with the provided username and key.
    
    Expected JSON payload:
    {
        "username": "USERNAME",
        "key": "mkey:20a6c523dbeadb6fcaacf53f7c2d2cd9f5d650c843c4cf07d956270e3f79f944"
    }
    """
    data = request.get_json()

    # Validate input
    username = data.get('username')
    key = data.get('key')

    if not username or not key:
        return jsonify({'error': 'Both "username" and "key" are required.'}), 400

    try:
        # Get the headscale container
        container = docker_client.containers.get(HEADSCALE_CONTAINER_NAME)
    except docker.errors.NotFound:
        return jsonify({'error': f'Container "{HEADSCALE_CONTAINER_NAME}" not found.'}), 404
    except docker.errors.APIError as e:
        return jsonify({'error': f'Docker API error: {str(e)}'}), 500

    # Construct the command
    command = [
        "headscale",
        "nodes",
        "register",
        "--user", username,
        "--key", key
    ]

    try:
        # Execute the command inside the container
        exec_result = container.exec_run(cmd=command, stdout=True, stderr=True, demux=True)

        stdout, stderr = exec_result.output

        if exec_result.exit_code == 0:
            # Command executed successfully
            output = stdout.decode('utf-8') if stdout else 'Command executed successfully.'
            return jsonify({'message': 'Node registered successfully!', 'output': output}), 200
        else:
            # Command failed
            error_output = stderr.decode('utf-8') if stderr else 'An error occurred while executing the command.'
            return jsonify({'error': 'Command execution failed.', 'details': error_output}), 500

    except docker.errors.APIError as e:
        return jsonify({'error': f'Failed to execute command: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500
