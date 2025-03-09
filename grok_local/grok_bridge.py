import requests
import time
from flask import Flask, request, jsonify
from grok_local.tools import log_conversation

app = Flask(__name__)
BRIDGE_URL = "http://0.0.0.0:5000"
responses = {}  # Store responses for simplicity in testing

@app.route('/ask', methods=['POST'])
def ask_grok():
    data = request.json
    question = data.get('question')
    if not question:
        return jsonify({"error": "No question provided"}), 400
    
    request_id = f"{time.time():.0f}-{hash(question) % 10000:04d}"
    responses[request_id] = {"status": "pending", "question": question}
    log_conversation(f"Posted request: {request_id}")
    return jsonify({"id": request_id, "status": "pending"}), 200

@app.route('/response', methods=['GET'])
def post_response():
    request_id = request.args.get('id')
    response = request.args.get('response')
    if not request_id or not response:
        return jsonify({"error": "Missing id or response"}), 400
    if request_id not in responses:
        return jsonify({"error": "Invalid request ID"}), 404
    
    responses[request_id] = {"status": "completed", "response": response}
    log_conversation(f"Response received for {request_id}: {response}")
    return jsonify({"id": request_id, "response": response, "status": "Response received"}), 200

def fetch_response(request_id, timeout=25):
    start_time = time.time()
    while time.time() - start_time < timeout:
        if request_id in responses and responses[request_id]["status"] == "completed":
            response = responses[request_id]["response"]
            log_conversation(f"Fetched response for {request_id}: {response}")
            return response
        time.sleep(1)
    raise TimeoutError(f"No response for {request_id} within {timeout}s")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
