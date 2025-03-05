from flask import Flask, request

app = Flask(__name__)
responses = {}
current_request = None

@app.route('/channel', methods=['GET', 'POST'])
def channel():
    global current_request
    print(f"Request to /channel: {request.method} {request.args} {request.get_json(silent=True)}")
    if request.method == 'POST':
        data = request.get_json()
        if data and 'input' in data and 'id' in data:
            input_text = data['input']
            req_id = data['id']
            response_url = f"https://{request.host}/response?id={req_id}&response=[your_response_here]"
            current_request = (
                f"Input: \"{input_text}\"\n"
                f"Identifier: \"{req_id}\"\n"
                f"Instructions: \"Grok, process this input: '{input_text}'. Browse: {response_url}\""
            )
            print(f"Posted request: {req_id}")
            return {"status": "Request posted", "id": req_id}, 200
        print("Invalid POST data")
        return {"error": "Invalid request data"}, 400
    print("Serving channel page")
    return current_request if current_request else "No request posted yet.", 200

@app.route('/response', methods=['GET'])
def log_response():
    print(f"Request to /response: {request.method} {request.args}")
    req_id = request.args.get('id')
    response = request.args.get('response')
    if req_id and response:
        responses[req_id] = response
        print(f"Logged response for {req_id}: {response}")
        return "Response received"
    print("Invalid response request")
    return "Invalid request", 400

@app.route('/get-response', methods=['GET'])
def get_response():
    print(f"Request to /get-response: {request.method} {request.args}")
    req_id = request.args.get('id')
    if req_id in responses:
        print(f"Returning response for {req_id}: {responses[req_id]}")
        return responses[req_id]
    print(f"No response yet for {req_id}")
    return "No response yet", 404

if __name__ == "__main__":
    app.debug = True
    print("Starting GrokBridge...")
    app.run(host='0.0.0.0', port=5000, threaded=True)
