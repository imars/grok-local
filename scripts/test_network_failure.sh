#!/bin/bash
# Test script to simulate network failure and verify retry logic in git_ops.py

# Get the script's directory and set repo root
SCRIPT_DIR="$(dirname "$0")"
REPO_DIR="$(realpath "$SCRIPT_DIR/..")"

# Set venv path
VENV_DIR="/Users/ian/dev/projects/agents/local/grok/venv"

# Ensure venv is active
if [ -f "$VENV_DIR/bin/activate" ]; then
    source "$VENV_DIR/bin/activate"
    echo "Activated venv at $VENV_DIR"
else
    echo "Error: venv not found at $VENV_DIR. Please ensure it exists and retry."
    exit 1
fi

# Verify grok_local.py exists
if [ ! -f "$REPO_DIR/grok_local.py" ]; then
    echo "Error: grok_local.py not found at $REPO_DIR/grok_local.py"
    exit 1
fi

# Create a test file to commit
echo "Test network failure" > "$REPO_DIR/network_test.txt"

# macOS: Use pfctl to block GitHub SSH (port 22)
echo "Blocking GitHub SSH (port 22) for test..."
sudo bash -c "echo 'block drop out on en0 to 140.82.121.4 port 22' > /tmp/pf.conf"
sudo pfctl -f /tmp/pf.conf -E 2>/dev/null
echo "Network block active. Running commit..."

# Attempt commit (should trigger retries due to network failure)
python "$REPO_DIR/grok_local.py" --ask "commit 'Test network failure commit'"

# Restore network access
echo "Restoring network access..."
sudo pfctl -f /etc/pf.conf 2>/dev/null || sudo pfctl -d 2>/dev/null
rm /tmp/pf.conf
echo "Network restored."

# Check logs for retry attempts
LOG_FILE="$REPO_DIR/grok_local.log"
if [ -f "$LOG_FILE" ]; then
    echo "Checking $LOG_FILE for retry attempts..."
    grep "Push attempt" "$LOG_FILE" | grep "Test network failure commit" || echo "No retry attempts found for this commit"
else
    echo "Warning: $LOG_FILE not found. No retry logs available."
fi

# Cleanup
rm "$REPO_DIR/network_test.txt"

echo "Test complete. Verify retry logs above."
