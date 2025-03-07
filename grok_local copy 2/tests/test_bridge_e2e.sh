#!/bin/bash

# Configuration
BRIDGE_URL="http://0.0.0.0:5000"
OUTPUT_FILE="bridge_test_output.log"
TIMEOUT=25

# Cleanup from previous runs
echo "Cleaning up previous bridge processes..."
pkill -f "python.*grok_bridge.py" 2>/dev/null
sleep 2

# Step 1: Send request to Grok via bridge
echo "Starting bridge test..."
CLI_CMD=(python -u -m grok_local --ask 'send to grok "What is the capital of France?"')
echo "Running: ${CLI_CMD[*]}"
"${CLI_CMD[@]}" > "$OUTPUT_FILE" 2>&1 &
CLI_PID=$!
echo "CLI PID: $CLI_PID"

# Wait for bridge to post request and get ID
echo "Waiting for bridge to post request..."
for ((i=1; i<=10; i++)); do
    if grep -q "Posted request:" "$OUTPUT_FILE"; then
        REQUEST_ID=$(grep "Posted request:" "$OUTPUT_FILE" | tail -1 | awk '{print $NF}')
        echo "Request ID: $REQUEST_ID"
        break
    elif grep -q "id=[a-f0-9-]\{36\}" "$OUTPUT_FILE"; then
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

# Post response to bridge
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

# Wait for CLI to finish and verify bridge response
echo "Waiting for bridge response..."
wait $CLI_PID
if ! grep -q "Grok response: Paris" "$OUTPUT_FILE"; then
    echo "FAIL: Expected 'Grok response: Paris' not found in bridge test"
    cat "$OUTPUT_FILE"
    exit 1
fi
echo "Bridge test passed!"

# Step 2: Checkpoint the result
echo "Checkpointing test result..."
CHECKPOINT_CMD=(python -u -m grok_local --ask 'checkpoint "Bridge test successful" --git')
echo "Running: ${CHECKPOINT_CMD[*]}"
"${CHECKPOINT_CMD[@]}" > "$OUTPUT_FILE" 2>&1 &
CHECKPOINT_PID=$!
echo "Checkpoint PID: $CHECKPOINT_PID"

# Wait for checkpoint to complete
echo "Waiting for checkpoint to complete..."
wait $CHECKPOINT_PID
if ! grep -q "Checkpoint saved:" "$OUTPUT_FILE" || ! grep -q "Committed and pushed:" "$OUTPUT_FILE"; then
    echo "FAIL: Checkpoint or Git commit failed"
    cat "$OUTPUT_FILE"
    exit 1
fi
echo "Checkpoint test passed!"

# Final verification
echo "PASS: End-to-end test succeeded!"
echo "Final checkpoint output:"
cat "$OUTPUT_FILE"

# Cleanup
rm -f "$OUTPUT_FILE" curl_response.txt
echo "Test complete"
