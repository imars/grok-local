#!/bin/bash
# test_agent_architecture.sh (Mar 09, 2025): Runs 10 simple tests for grok_local agent architecture.
# Note: Uses python -m grok_local for modular execution with direct commands.

# Setup
cd /Users/ian/dev/projects/agents/local/grok/repo/
echo "Running tests for grok_local agent architecture..."
echo "Results will be logged to test_results.log"
rm -f test_results.log

# Helper function to run a test and check output
run_test() {
    TEST_NAME="$1"
    COMMAND="$2"
    EXPECTED="$3"
    echo "Running: $TEST_NAME"
    RESULT=$(python -m grok_local "$COMMAND" 2>/dev/null)
    if echo "$RESULT" | grep -q "$EXPECTED"; then
        echo "PASS: $TEST_NAME" >> test_results.log
        echo "  Expected (contains): $EXPECTED"
        echo "  Got: $RESULT"
    else
        echo "FAIL: $TEST_NAME" >> test_results.log
        echo "  Expected (contains): $EXPECTED"
        echo "  Got: $RESULT"
        echo "FAIL: $TEST_NAME - Full output: \"$RESULT\"" >&2
    fi
    echo "----------------------------------------"
}

# Test 1: Get current time
run_test "Get current time" "what time is it" "2025-03-09"  # Match date only

# Test 2: Get version
run_test "Get version" "version" "grok_local v0.1.0"

# Test 3: List files in current directory
run_test "List directory" "list files" "grok_bootstrap.py"  # Match one file

# Test 4: Generate directory tree
run_test "Generate tree" "tree" "__main__.py"  # Match part of tree

# Test 5: Copy file to clipboard
run_test "Copy file to clipboard" "copy grok_bootstrap.py" "Copied 1 file(s) to clipboard"

# Test 6: Clean repo
run_test "Clean repo" "clean repo" "clean"  # Match partial git_ops output

# Test 7: Create a spaceship fuel script (placeholder)
run_test "Create spaceship fuel script" "create spaceship fuel script" "TODO: Implement spaceship fuel script generation"

# Test 8: Create an X login stub (placeholder)
run_test "Create X login stub" "create x login stub" "TODO: Implement X login stub generation"

# Test 9: Handle unknown command (generate factorial code)
run_test "Unknown command" "calculate factorial of 5" "def factorial"  # Expect a function definition

# Test 10: Save a checkpoint
run_test "Save checkpoint" "checkpoint 'Test checkpoint from script'" "Checkpoint saved"

# Summary
echo "Test Summary:"
cat test_results.log
echo "Tests completed. See test_results.log for details."
