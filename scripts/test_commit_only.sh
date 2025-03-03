#!/bin/bash
# Test script to verify staging and committing in git_ops.py via grok_local.py

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
LOG_FILE="$REPO_DIR/grok_local.log"
if [ -f "$TEST_FILE" ]; then
    rm "$TEST_FILE"
fi
echo "Creating test file: $TEST_FILE"
echo "Test commit" > "$TEST_FILE"
if [ -f "$TEST_FILE" ]; then
    echo "Test file created successfully."
else
    echo "Error: Failed to create $TEST_FILE."
    exit 1
fi
echo "Clearing previous logs: $LOG_FILE"
echo "" > "$LOG_FILE"  # Clear the log file
echo "Git root: $(git -C "$REPO_DIR" rev-parse --show-toplevel)"

echo "Running commit test..."
python "$REPO_DIR/grok_local.py" --ask "commit 'Test commit only|$TEST_FILE'" --debug > "$REPO_DIR/test_output.log" 2>&1
COMMIT_STATUS=$?
echo "Commit command status: $COMMIT_STATUS"
echo "Full output from grok_local.py:"
cat "$REPO_DIR/test_output.log"

if [ -f "$LOG_FILE" ]; then
    echo "Checking $LOG_FILE for commit success..."
    if grep -q "Committed changes with message: 'Test commit only'" "$LOG_FILE"; then
        echo "Success: File was committed."
    else
        echo "Failure: File was not committed."
    fi
    echo "Last 5 log lines from $LOG_FILE:"
    tail -n 5 "$LOG_FILE"
else
    echo "Warning: $LOG_FILE not found."
fi

if [ $COMMIT_STATUS -eq 0 ]; then
    echo "Commit command succeeded."
else
    echo "Commit command failed (status: $COMMIT_STATUS)."
fi

rm -f "$TEST_FILE" "$REPO_DIR/test_output.log"
git -C "$REPO_DIR" reset -- "$TEST_FILE" 2>/dev/null

echo "Test complete."
exit 0
