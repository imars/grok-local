#!/bin/bash
# Test script for retry logic in git_ops.py's git_commit_and_push function

# Get the script's directory and set repo root
SCRIPT_DIR="$(dirname "$0")"
REPO_DIR="$(realpath "$SCRIPT_DIR/..")"

# Ensure venv is active (optional if already active)
if [ -f "$REPO_DIR/venv/bin/activate" ]; then
    source "$REPO_DIR/venv/bin/activate"
else
    echo "Warning: venv not found at $REPO_DIR/venv. Assuming dependencies are available."
fi

# Verify grok_local.py exists
if [ ! -f "$REPO_DIR/grok_local.py" ]; then
    echo "Error: grok_local.py not found at $REPO_DIR/grok_local.py"
    exit 1
fi

# Create a test file to commit
echo "Test retry logic" > "$REPO_DIR/test_file.txt"

# Commit and push with retry logic
echo "Running first commit..."
python "$REPO_DIR/grok_local.py" --ask "commit 'Test retry logic commit'"

# Simulate a network failure by committing again (manual interruption optional)
echo "Simulating push with potential retry..."
python "$REPO_DIR/grok_local.py" --ask "commit 'Test retry logic again'"

# Check logs for retry attempts
LOG_FILE="$REPO_DIR/grok_local.log"
if [ -f "$LOG_FILE" ]; then
    echo "Checking $LOG_FILE for retry attempts..."
    grep "Push attempt" "$LOG_FILE"
else
    echo "Warning: $LOG_FILE not found. No retry logs available."
fi

# Cleanup
rm "$REPO_DIR/test_file.txt"

echo "Test complete. Check GitHub for commits: https://github.com/imars/grok-local"
