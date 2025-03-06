#!/bin/bash

# Configuration
BRIDGE_SCRIPT="./grok_bridge.py"  # Same directory as script
HOST="0.0.0.0"
PORT="5000"
LOCAL_URL="http://$HOST:$PORT"
REQ_ID="test-$(date +%s)"
NGROK_PID=""
BRIDGE_PID=""
PUBLIC_URL=""
FAILURES=0

# Function to report test result
report_test() {
    local test_name="$1"
    local status="$2"
    if [ "$status" -eq 0 ]; then
        echo "PASS: $test_name"
    else
        echo "FAIL: $test_name"
        FAILURES=$((FAILURES + 1))
    fi
}

# Function to check if server is running
check_server() {
    local url="$1"
    local attempts=5
    local delay=2
    for ((i=1; i<=attempts; i++)); do
        if curl -s "$url/channel" > /dev/null 2>&1; then
            echo "Server is running at $url"
            return 0
        fi
        echo "Waiting for server (attempt $i/$attempts)..."
        sleep $delay
    done
    echo "Error: Server failed to start"
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

# Function to check port (portable alternative to lsof)
check_port() {
    local port="$1"
    if command -v netstat >/dev/null 2>&1; then
        netstat -tuln | grep -q ":$port " && return 0 || return 1
    elif command -v ss >/dev/null 2>&1; then
        ss -tuln | grep -q ":$port " && return 0 || return 1
    elif command -v lsof >/dev/null 2>&1; then
        lsof -iTCP:$port -sTCP:LISTEN -t >/dev/null 2>&1 && return 0 || return 1
    else
        echo "Warning: No suitable tool (netstat, ss, lsof) found to check port $port. Assuming free."
        return 1
    fi
}

# Cleanup function
cleanup() {
    echo "Cleaning up..."
    kill $BRIDGE_PID 2>/dev/null
    kill $NGROK_PID 2>/dev/null
    wait $BRIDGE_PID 2>/dev/null
    wait $NGROK_PID 2>/dev/null
    # Uncomment for production use
    # rm -f post_response.json response_ack.txt bridge.log ngrok.log ngrok_api.json
}

# Trap to ensure cleanup on exit
trap cleanup EXIT

# Step 0: Pre-test cleanup
echo "Checking for existing ngrok processes..."
EXISTING_NGROK=$(pgrep -f "ngrok")
if [ -n "$EXISTING_NGROK" ]; then
    echo "Killing existing ngrok processes: $EXISTING_NGROK"
    pkill -f "ngrok"
    sleep 2
fi

echo "Checking for processes on port $PORT..."
if check_port "$PORT"; then
    PORT_PID=$(lsof -iTCP:$PORT -sTCP:LISTEN -t 2>/dev/null || ps -p $(netstat -tuln | grep ":$PORT " | awk '{print $NF}') -o pid= | head -1)
    if [ -n "$PORT_PID" ]; then
        echo "Killing process on port $PORT: $PORT_PID"
        kill -9 $PORT_PID
        sleep 2
    fi
fi

echo "Killing any lingering Python processes related to $BRIDGE_SCRIPT..."
pkill -f "python.*$BRIDGE_SCRIPT"
sleep 2

echo "Clearing Python cached .pyc files..."
find .. -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find .. -name "*.pyc" -exec rm -f {} + 2>/dev/null
echo "Cache cleared."

if check_port "$PORT"; then
    echo "Error: Failed to free port $PORT."
    exit 1
fi
echo "Port $PORT is free."

# Check if grok_bridge.py exists
if [ ! -f "$BRIDGE_SCRIPT" ]; then
    echo "Error: $BRIDGE_SCRIPT not found."
    exit 1
fi

# Step 1: Start ngrok
echo "Starting ngrok..."
ngrok http $PORT --log=stdout --log-level debug > ngrok.log 2>&1 &
NGROK_PID=$!
sleep 10

if ! ps -p $NGROK_PID > /dev/null; then
    echo "FAIL: ngrok startup"
    cat ngrok.log
    exit 1
else
    report_test "ngrok startup" 0
fi

# Get public URL
if get_ngrok_url; then
    TEST_URL="$PUBLIC_URL"
    report_test "ngrok URL retrieval" 0
else
    echo "Warning: ngrok failed. Falling back to $LOCAL_URL for testing."
    TEST_URL="$LOCAL_URL"
    report_test "ngrok URL retrieval" 1
    cat ngrok.log
    cat ngrok_api.json
fi

# Step 2: Start grok_bridge
echo "Starting grok_bridge..."
PYTHONUNBUFFERED=1 python -u "$BRIDGE_SCRIPT" > bridge.log 2>&1 &
BRIDGE_PID=$!
sleep 5

if ! ps -p $BRIDGE_PID > /dev/null || ! check_server "$LOCAL_URL"; then
    echo "FAIL: grok_bridge startup"
    cat bridge.log
    kill $NGROK_PID 2>/dev/null
    exit 1
else
    report_test "grok_bridge startup" 0
    echo "grok_bridge started at $LOCAL_URL (public: $TEST_URL)"
fi

# Step 3: Test POST /channel
echo "Testing POST /channel with ID: $REQ_ID"
curl -s -X POST "$TEST_URL/channel"     -H "Content-Type: application/json"     -d "{\"input\": \"What is 2 + 2?\", \"id\": \"$REQ_ID\"}" > post_response.json
if [ $? -eq 0 ] && grep -q "\"status\": \"Request posted\"" post_response.json && grep -q "\"id\": \"$REQ_ID\"" post_response.json; then
    report_test "POST /channel" 0
    echo "Post response:"
    cat post_response.json
else
    report_test "POST /channel" 1
    echo "Error: Failed to post request or invalid response"
    cat post_response.json
    cat bridge.log
    exit 1
fi
echo ""

# Step 4: Test GET /channel (simulating Grok fetch)
echo "Simulating Grok fetching request from /channel..."
REQUEST=$(curl -s "$TEST_URL/channel")
if echo "$REQUEST" | grep -q "Input: \"What is 2 + 2?\"" && echo "$REQUEST" | grep -q "Identifier: \"$REQ_ID\""; then
    report_test "GET /channel (Grok fetch)" 0
    echo "Grok received:"
    echo "$REQUEST"
else
    report_test "GET /channel (Grok fetch)" 1
    echo "Error: Unexpected request content"
    echo "Received: $REQUEST"
    cat bridge.log
    exit 1
fi
echo ""

# Step 5: Test POST /response (simulating Grok response)
echo "Simulating Grok posting response to /response..."
curl -s "$TEST_URL/response?id=$REQ_ID&response=4" > response_ack.txt
if [ $? -eq 0 ] && grep -q "Response received" response_ack.txt; then
    report_test "POST /response (Grok response)" 0
    echo "Response acknowledgment:"
    cat response_ack.txt
else
    report_test "POST /response (Grok response)" 1
    echo "Error: Failed to post response"
    cat response_ack.txt
    cat bridge.log
    exit 1
fi
echo ""
sleep 2  # Wait for response to register

# Step 6: Test GET /get-response
echo "Verifying response from /get-response..."
RESPONSE=$(curl -s "$TEST_URL/get-response?id=$REQ_ID")
if [ "$RESPONSE" = "4" ]; then
    report_test "GET /get-response" 0
    echo "Received response: $RESPONSE"
    echo "End-to-end test successful!"
else
    report_test "GET /get-response" 1
    echo "Error: Expected '4', got: $RESPONSE"
    cat bridge.log
    exit 1
fi

# Summary
echo ""
if [ $FAILURES -eq 0 ]; then
    echo "All tests passed!"
    exit 0
else
    echo "$FAILURES test(s) failed."
    echo "Server logs:"
    cat bridge.log
    echo "ngrok logs:"
    cat ngrok.log
    exit 1
fi
