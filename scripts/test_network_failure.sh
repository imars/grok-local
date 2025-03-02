#!/bin/bash
# Test script to simulate network failure and verify retry logic in git_ops.py

SCRIPT_DIR="$(dirname "$0")"
REPO_DIR="$(realpath "$SCRIPT_DIR/..")"
VENV_DIR="$(realpath "$REPO_DIR/..")/venv"

if [ -f "$VENV_DIR/bin/activate" ]; then
    source "$VENV_DIR/bin/activate"
    echo "Activated venv at $VENV_DIR"
else
    echo "Error: venv not found at $VENV_DIR."
    exit 1
fi

for FILE in "$REPO_DIR/grok_local.py" "$REPO_DIR/git_ops.py"; do
    if [ ! -f "$FILE" ]; then
        echo "Error: $FILE not found."
        exit 1
    fi
done

TEST_FILE="$REPO_DIR/test_network_failure.unique"
if [ -f "$TEST_FILE" ]; then
    rm "$TEST_FILE"
fi
echo "Creating test file: $TEST_FILE"
echo "Test network failure" > "$TEST_FILE"
if [ -f "$TEST_FILE" ]; then
    echo "Test file created successfully."
else
    echo "Error: Failed to create $TEST_FILE."
    exit 1
fi
echo "Git root: $(git -C "$REPO_DIR" rev-parse --show-toplevel)"

OS=$(uname)
if [ "$OS" != "Darwin" ]; then
    echo "Warning: Network block test only implemented for macOS."
    exit 0
fi

echo "Checking active network interface..."
ACTIVE_IF=$(route get github.com 2>/dev/null | grep interface | awk '{print $2}')
if [ -z "$ACTIVE_IF" ]; then
    echo "Warning: Could not determine active interface. Defaulting to en0."
    ACTIVE_IF="en0"
fi
echo "Using interface: $ACTIVE_IF"

echo "Blocking GitHub SSH (port 22)..."
sudo bash -c "echo 'block drop out on $ACTIVE_IF proto tcp to any port 22' > /tmp/pf.conf"
sudo pfctl -e 2>/dev/null
sudo pfctl -f /tmp/pf.conf 2>/dev/null
if [ $? -eq 0 ]; then
    echo "Network block active (port 22 blocked)."
else
    echo "Error: Failed to apply pfctl rules."
    sudo pfctl -d 2>/dev/null
    sudo rm -f /tmp/pf.conf
    exit 1
fi

echo "Testing SSH block to GitHub..."
ssh -T git@github.com > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "SSH block confirmed."
else
    echo "Error: SSH block failed."
    sudo pfctl -d 2>/dev/null
    sudo rm -f /tmp/pf.conf
    exit 1
fi

echo "Running commit with simulated network failure..."
timeout 30s python "$REPO_DIR/grok_local.py" --ask "commit 'Test network failure commit'" --debug > "$REPO_DIR/test_output.log" 2>&1
COMMIT_STATUS=$?
echo "Commit command status: $COMMIT_STATUS"
echo "Full output from grok_local.py:"
cat "$REPO_DIR/test_output.log"

echo "Testing manual Git push..."
git -C "$REPO_DIR" push > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "Error: Manual push succeeded."
    sudo pfctl -d 2>/dev/null
    sudo rm -f /tmp/pf.conf
    exit 1
else
    echo "Manual push failed as expected."
fi

echo "Restoring network access..."
sudo pfctl -d 2>/dev/null
sudo rm -f /tmp/pf.conf
echo "Network restored."

LOG_FILE="$REPO_DIR/grok_local.log"
if [ -f "$LOG_FILE" ]; then
    echo "Checking $LOG_FILE for retry attempts..."
    RETRY_COUNT=$(grep "Push attempt" "$LOG_FILE" | grep "Test network failure commit" | wc -l)
    if [ "$RETRY_COUNT" -gt 0 ]; then
        echo "Success: Detected $RETRY_COUNT retry attempts."
    else
        echo "Failure: No retry attempts found."
    fi
    echo "Last 5 log lines from $LOG_FILE:"
    tail -n 5 "$LOG_FILE"
else
    echo "Warning: $LOG_FILE not found."
fi

if [ $COMMIT_STATUS -eq 0 ]; then
    echo "Warning: Commit succeeded unexpectedly."
else
    echo "Expected: Commit failed (status: $COMMIT_STATUS)."
fi

rm -f "$TEST_FILE" "$REPO_DIR/test_output.log" "$REPO_DIR/staged_files.log"
git -C "$REPO_DIR" reset -- "$TEST_FILE" 2>/dev/null

echo "Test complete."
exit 0
