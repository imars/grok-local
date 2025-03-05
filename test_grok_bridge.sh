#!/bin/bash

# Configuration
BRIDGE_SCRIPT="./grok_bridge.py"
HOST="0.0.0.0"
PORT="5000"
LOCAL_URL="http://$HOST:$PORT"
REQ_ID="test-$(date +%s)"
NGROK_PID=""
BRIDGE_PID=""
PUBLIC_URL=""

# Check if grok_bridge.py exists
if [ ! -f "$BRIDGE_SCRIPT" ]; then
    echo "Error: $BRIDGE_SCRIPT not found."
    exit 1
fi

# Function to check if server is running
check_server() {
    local url="$1"
    local attempts=5
    local delay=2
    for ((i=1; i<=attempts; i++)); do
        if curl -s "$url/channel" > /dev/null 2>&1; then
            return 0
        fi
        echo "Waiting for server (attempt $i/$attempts)..."
        sleep $delay
    done
    return 1
}

# Function to get ngrok public URL
get_ngrok_url() {
    local attempts=15
    local delay=5
    echo "Fetching ngrok URL..."
    for ((i=1; i<=attempts; i++)); do
        curl -s http://localhost:4040/api/tunnels > ngrok_api.json
        if command -v jq >/dev/null 2>&1; then
            PUBLIC_URL=$(jq -r '.tunnels[0].public_url // empty' ngrok_api.json)
        else
            PUBLIC_URL=$(grep -o "https://[a-z0-9-]*\.ngrok-free\.app" ngrok_api.json)
        fi
        if [ -n "$PUBLIC_URL" ] && [ "$PUBLIC_URL" != "null" ]; then
            echo "ngrok public URL: $PUBLIC_URL"
            return 0
        fi
        echo "Waiting for ngrok URL (attempt $i/$attempts)..."
        sleep $delay
    done
    echo "Error: Failed to get ngrok URL after $((attempts * delay + 10)) seconds."
    return 1
}

# Step 0: Clean up existing processes and cached files
echo "Checking for existing ngrok processes..."
EXISTING_NGROK=$(pgrep -f "ngrok")
if [ -n "$EXISTING_NGROK" ]; then
    echo "Killing existing ngrok processes: $EXISTING_NGROK"
    pkill -f "ngrok"
    sleep 2
fi

echo "Checking for processes on port $PORT..."
PORT_PID=$(lsof -i :$PORT -t)
if [ -n "$PORT_PID" ]; then
    echo "Killing process on port $PORT: $PORT_PID"
    kill -9 $PORT_PID
    sleep 2
fi

echo "Killing any lingering Python processes related to $BRIDGE_SCRIPT..."
pkill -f "python.*$BRIDGE_SCRIPT"
sleep 2

echo "Clearing Python cached .pyc files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -exec rm -f {} + 2>/dev/null
echo "Cache cleared."

# Double-check the port is free
PORT_PID=$(lsof -i :$PORT -t)
if [ -n "$PORT_PID" ]; then
    echo "Error: Failed to free port $PORT. Process $PORT_PID persists after cleanup."
    exit 1
fi
echo "Port $PORT is free."

# Step 1: Start ngrok with debug logging
echo "Starting ngrok..."
ngrok http $PORT --log=stdout --log-level debug > ngrok.log 2>&1 &
NGROK_PID=$!
sleep 10

# Check ngrok
if ! ps -p $NGROK_PID > /dev/null; then
    echo "Error: ngrok failed to start."
    cat ngrok.log
    exit 1
fi

# Get public URL
if get_ngrok_url; then
    TEST_URL="$PUBLIC_URL"
else
    echo "Warning: ngrok failed. Falling back to $LOCAL_URL for testing."
    TEST_URL="$LOCAL_URL"
    cat ngrok.log
    cat ngrok_api.json
fi

# Step 2: Start grok_bridge
echo "Starting grok_bridge..."
PYTHONUNBUFFERED=1 python -u "$BRIDGE_SCRIPT" > bridge.log 2>&1 &
BRIDGE_PID=$!
sleep 5

# Check if grok_bridge is alive
if ! ps -p $BRIDGE_PID > /dev/null; then
    echo "Error: grok_bridge died."
    cat bridge.log
    kill $NGROK_PID 2>/dev/null
    exit 1
fi

# Verify server
if ! check_server "$LOCAL_URL"; then
    echo "Error: grok_bridge failed to bind. Check bridge.log:"
    cat bridge.log
    kill $BRIDGE_PID 2>/dev/null
    kill $NGROK_PID 2>/dev/null
    exit 1
fi
echo "grok_bridge started at $LOCAL_URL (public: $TEST_URL)"

# Step 3: Post request (simulating grok_local)
echo "Posting request with ID: $REQ_ID"
curl -s -X POST "$TEST_URL/channel" \
    -H "Content-Type: application/json" \
    -d "{\"input\": \"What is 2 + 2?\", \"id\": \"$REQ_ID\"}" > post_response.json
if [ $? -ne 0 ]; then
    echo "Error: Failed to post request"
    cat bridge.log
    kill $BRIDGE_PID 2>/dev/null
    kill $NGROK_PID 2>/dev/null
    exit 1
fi
echo "Post response:"
cat post_response.json
echo ""

# Check if grok_bridge is still alive
if ! ps -p $BRIDGE_PID > /dev/null; then
    echo "Error: grok_bridge crashed after POST. Check bridge.log:"
    cat bridge.log
    kill $NGROK_PID 2>/dev/null
    exit 1
fi

# Step 4: Simulate Grok fetching the request
echo "Simulating Grok fetching request from /channel..."
REQUEST=$(curl -s "$TEST_URL/channel")
echo "Grok received:"
echo "$REQUEST"
echo ""

# Step 5: Simulate Grok posting a response
echo "Simulating Grok posting response to /response..."
curl -s "$TEST_URL/response?id=$REQ_ID&response=4" > response_ack.txt
if [ $? -ne 0 ]; then
    echo "Error: Failed to post response"
    cat bridge.log
    kill $BRIDGE_PID 2>/dev/null
    kill $NGROK_PID 2>/dev/null
    exit 1
fi
echo "Response acknowledgment:"
cat response_ack.txt
echo ""

# Wait briefly for the response to register
sleep 2

# Step 6: Verify response (simulating grok_local fetching)
echo "Verifying response from /get-response..."
RESPONSE=$(curl -s "$TEST_URL/get-response?id=$REQ_ID")
if [ "$RESPONSE" = "No response yet" ]; then
    echo "Error: Response not received yet"
    cat bridge.log
    kill $BRIDGE_PID 2>/dev/null
    kill $NGROK_PID 2>/dev/null
    exit 1
fi
echo "Received response: $RESPONSE"
if [ "$RESPONSE" != "4" ]; then
    echo "Error: Unexpected response (expected '4')"
    cat bridge.log
    kill $BRIDGE_PID 2>/dev/null
    kill $NGROK_PID 2>/dev/null
    exit 1
fi
echo "End-to-end test successful!"

# Step 7: Stop everything
echo "Stopping grok_bridge and ngrok..."
kill $BRIDGE_PID 2>/dev/null
kill $NGROK_PID 2>/dev/null
wait $BRIDGE_PID 2>/dev/null
wait $NGROK_PID 2>/dev/null
echo "grok_bridge and ngrok stopped"

# Cleanup (commented for debugging)
# rm -f post_response.json response_ack.txt bridge.log ngrok.log ngrok_api.json
