#!/bin/bash
# Test script for retry logic in git_ops.py's git_commit_and_push function

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

# Create a test file for first commit
echo "Test retry logic - first commit" > "$REPO_DIR/test_file.txt"

# First commit and push
echo "Running first commit..."
python "$REPO_DIR/grok_local.py" --ask "commit 'Test retry logic commit 1'"

# Modify the test file for second commit
echo "Test retry logic - second commit" >> "$REPO_DIR/test_file.txt"

# Second commit and push (test retry logic)
echo "Running second commit (potential retry)..."
python "$REPO_DIR/grok_local.py" --ask "commit 'Test retry logic commit 2'"

# Check logs for retry attempts
LOG_FILE="$REPO_DIR/grok_local.log"
if [ -f "$LOG_FILE" ]; then
    echo "Checking $LOG_FILE for retry attempts from this run..."
    grep "Push attempt.*Test retry logic commit" "$LOG_FILE" || echo "No retry attempts found in log for these commits"
else
    echo "Warning: $LOG_FILE not found. No retry logs available."
fi

# Cleanup
rm "$REPO_DIR/test_file.txt"

echo "Test complete. Check GitHub for commits: https://github.com/imars/grok-local"
