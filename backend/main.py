import json
from ibm_watson import AssistantV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from flask import Flask, request, jsonify

app = Flask(__name__)

# Load the configuration file
with open('credentials.json') as f:
    config = json.load(f)

# Create an authenticator
authenticator = IAMAuthenticator(apikey=config['api_key'])

assistant = AssistantV1(
    version='2022-04-07',
    authenticator=authenticator
)

# Set the URL
assistant.set_service_url(config['url'])

# Define a route for the homepage
@app.route('/', methods=['GET'])
def index():
    return 'Welcome to the Watson Assistant API!'

# Define a route for sending messages to the assistant
@app.route('/message', methods=['POST'])
def send_message():
    try:
        # Get the message from the request body
        message = request.get_json()['message']

        # Validate the input message
        if not message:
            return jsonify({'error': 'Message is required'}), 400

        # Send the message to the assistant
        response = assistant.message(
            assistant_id=config['assistant_id'],
            input={'message_type': 'text', 'text': message}
        )

        # Return the response
        return jsonify(response.get_result())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Run the application
if __name__ == '__main__':
    app.run(debug=True)
