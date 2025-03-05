#!/bin/bash

# Configuration
CLI_CMD=(python -u -m grok_local --ask 'send to grok "What is the capital of France?"')
BRIDGE_URL="http://0.0.0.0:5000"
OUTPUT_FILE="bridge_test_output.log"
TIMEOUT=25

# Cleanup from previous runs
echo "Cleaning up previous bridge processes..."
pkill -f "python.*grok_bridge.py" 2>/dev/null
sleep 2

# Step 1: Start the CLI and capture output
echo "Starting CLI: ${CLI_CMD[*]}"
"${CLI_CMD[@]}" > "$OUTPUT_FILE" 2>&1 &
CLI_PID=$!
echo "CLI PID: $CLI_PID"

# Step 2: Wait for bridge to start and get request ID
echo "Waiting for bridge to post request..."
for ((i=1; i<=10; i++)); do
    if grep -q "Posted request:" "$OUTPUT_FILE"; then
        REQUEST_ID=$(grep "Posted request:" "$OUTPUT_FILE" | tail -1 | awk '{print $NF}')
        echo "Request ID: $REQUEST_ID"
        break
    elif grep -q "id=[a-f0-9-]\{36\}" "$OUTPUT_FILE"; then
        # Fallback: Extract UUID from any line (POST or GET)
        REQUEST_ID=$(grep -o "id=[a-f0-9-]\{36\}" "$OUTPUT_FILE" | tail -1 | cut -d'=' -f2)
        if [ -n "$REQUEST_ID" ]; then
            echo "Request ID (from log): $REQUEST_ID"
            break
        fi
    fi
    echo "Attempt $i/10: Waiting for request ID..."
    echo "Current output file contents:"
    cat "$OUTPUT_FILE"
    sleep 1
done

if [ -z "$REQUEST_ID" ]; then
    echo "Error: Failed to get request ID"
    kill $CLI_PID 2>/dev/null
    cat "$OUTPUT_FILE"
    exit 1
fi

# Step 3: Post response to bridge
echo "Posting response for ID $REQUEST_ID..."
curl -s "$BRIDGE_URL/response?id=$REQUEST_ID&response=Paris" > curl_response.txt
if [ $? -ne 0 ] || ! grep -q "Response received" curl_response.txt; then
    echo "Error: Failed to post response"
    kill $CLI_PID 2>/dev/null
    cat "$OUTPUT_FILE"
    cat curl_response.txt
    exit 1
fi
echo "Response posted successfully"

# Step 4: Wait for CLI to finish and verify output
echo "Waiting for CLI to process response..."
wait $CLI_PID
if grep -q "Grok response: Paris" "$OUTPUT_FILE"; then
    echo "PASS: End-to-end test succeeded!"
    echo "Final output:"
    cat "$OUTPUT_FILE"
else
    echo "FAIL: Expected 'Grok response: Paris' not found"
    cat "$OUTPUT_FILE"
    exit 1
fi

# Cleanup
rm -f "$OUTPUT_FILE" curl_response.txt
echo "Test complete"
