#!/bin/bash
# Test script to simulate network failure and verify retry logic in git_ops.py

# Get the script's directory and set repo root
SCRIPT_DIR="$(dirname "$0")"
REPO_DIR="$(realpath "$SCRIPT_DIR/..")"

# Set venv path to repo's parent directory
VENV_DIR="$(realpath "$REPO_DIR/..")/venv"

# Ensure venv is active
if [ -f "$VENV_DIR/bin/activate" ]; then
    source "$VENV_DIR/bin/activate"
    echo "Activated venv at $VENV_DIR"
else
    echo "Error: venv not found at $VENV_DIR. Please run 'python -m venv venv' in $(dirname "$REPO_DIR") and install requirements."
    exit 1
fi

# Verify critical files exist
for FILE in "$REPO_DIR/grok_local.py" "$REPO_DIR/git_ops.py"; do
    if [ ! -f "$FILE" ]; then
        echo "Error: $FILE not found."
        exit 1
    fi
done

# Clean up any existing test file and prepare a fresh one
TEST_FILE="$REPO_DIR/network_test.txt"
if [ -f "$TEST_FILE" ]; then
    rm "$TEST_FILE"
fi
echo "Test network failure" > "$TEST_FILE"
git -C "$REPO_DIR" add "$TEST_FILE"  # Stage the file for commit

# Detect OS and set network block method (macOS only for now)
OS=$(uname)
if [ "$OS" != "Darwin" ]; then
    echo "Warning: Network block test only implemented for macOS (uses pfctl). Skipping on $OS."
    exit 0
fi

# macOS: Detect active network interface
echo "Checking active network interface..."
ACTIVE_IF=$(ifconfig | grep -B1 "status: active" | grep -o "^en[0-9]" | head -n 1)
if [ -z "$ACTIVE_IF" ]; then
    echo "Warning: Could not determine active interface. Defaulting to en0."
    ACTIVE_IF="en0"
fi
echo "Using interface: $ACTIVE_IF"

# Block GitHub SSH (port 22) with pfctl
echo "Blocking GitHub SSH (port 22) for test..."
sudo bash -c "echo 'block drop out on $ACTIVE_IF proto tcp to any port 22' > /tmp/pf.conf"
sudo pfctl -e 2>/dev/null  # Enable pf if not already
sudo pfctl -f /tmp/pf.conf 2>/dev/null
if [ $? -eq 0 ]; then
    echo "Network block active (port 22 blocked)."
else
    echo "Error: Failed to apply pfctl rules. Check sudo permissions or syntax."
    sudo pfctl -d 2>/dev/null
    sudo rm -f /tmp/pf.conf
    exit 1
fi

# Attempt commit with timeout (should fail and trigger retries in git_ops.py)
echo "Running commit with simulated network failure..."
timeout 30s python "$REPO_DIR/grok_local.py" --ask "commit 'Test network failure commit'" --debug > "$REPO_DIR/test_output.log" 2>&1
COMMIT_STATUS=$?

# Restore network access
echo "Restoring network access..."
sudo pfctl -d 2>/dev/null  # Disable pf to revert to default state
sudo rm -f /tmp/pf.conf    # Remove temp file with sudo
echo "Network restored."

# Check logs for retry attempts
LOG_FILE="$REPO_DIR/grok_local.log"
if [ -f "$LOG_FILE" ]; then
    echo "Checking $LOG_FILE for retry attempts..."
    RETRY_COUNT=$(grep "Push attempt" "$LOG_FILE" | grep "Test network failure commit" | wc -l)
    if [ "$RETRY_COUNT" -gt 0 ]; then
        echo "Success: Detected $RETRY_COUNT retry attempts for 'Test network failure commit'."
    else
        echo "Failure: No retry attempts found in logs for this commit."
    fi
    echo "Last 5 log lines for context:"
    tail -n 5 "$LOG_FILE"
else
    echo "Warning: $LOG_FILE not found. Cannot verify retry logic."
fi

# Verify commit status
if [ $COMMIT_STATUS -eq 0 ]; then
    echo "Warning: Commit succeeded unexpectedly during network block (retry logic may have bypassed failure)."
else
    echo "Expected: Commit failed due to network block (status: $COMMIT_STATUS)."
fi

# Cleanup
rm -f "$TEST_FILE" "$REPO_DIR/test_output.log"
git -C "$REPO_DIR" reset -- "$TEST_FILE"  # Unstage the test file

echo "Test complete. Review retry count and logs above for results."
exit 0
