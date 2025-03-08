#!/bin/bash
# test_agent_framework.sh: Test grok_local agent framework with toy tasks

set -e  # Exit on error

REPO_DIR="/Users/ian/dev/projects/agents/local/grok/repo"
cd "$REPO_DIR" || { echo "Failed to cd to $REPO_DIR"; exit 1; }

LOG_FILE="grok_local/tests/agent_test_logs.txt"
mkdir -p grok_local/tests
> "$LOG_FILE"

echo "Clearing .pyc files..." | tee -a "$LOG_FILE"
find . -name "*.pyc" -exec rm -f {} \;

echo "Stopping Ollama if running..." | tee -a "$LOG_FILE"
pkill -f "ollama serve" || echo "No Ollama process to stop." | tee -a "$LOG_FILE"

echo "Starting Ollama, logging to $LOG_FILE (warnings silenced)..." | tee -a "$LOG_FILE"
export OLLAMA_LOAD_TIMEOUT=10m
ollama serve >> "$LOG_FILE" 2>/dev/null &
OLLAMA_PID=$!
sleep 10  # Wait for startup
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "Error: Ollama failed to start! Check $LOG_FILE" | tee -a "$LOG_FILE"
    cat "$LOG_FILE"
    exit 1
fi
echo "Ollama running with PID $OLLAMA_PID" | tee -a "$LOG_FILE"

echo "Running agent framework tests..." | tee -a "$LOG_FILE"

# Test 1: Factorial Function
echo "Test 1: Generate factorial function" | tee -a "$LOG_FILE"
output=$(python -m grok_local --debug "Generate a Python function to compute the factorial of a number." --model "llama3.2:latest" 2>&1)
EXIT_CODE=$?
echo "Exit code: $EXIT_CODE" | tee -a "$LOG_FILE"
echo "$output" | tee -a "$LOG_FILE"
if [ $EXIT_CODE -eq 0 ] && echo "$output" | grep -q "Saved code to" && ! echo "$output" | grep -q "Error:"; then
    echo "Test 1 passed" | tee -a "$LOG_FILE"
else
    echo "Test 1 failed" | tee -a "$LOG_FILE"
fi
echo "----------------------------------------" | tee -a "$LOG_FILE"

# Test 2: Fix Syntax Error (Force Debugger)
echo "Test 2: Fix syntax error in broken function" | tee -a "$LOG_FILE"
cat << 'PY' > grok_local/projects/test.py
def add(a b):  # Initial broken code
    return a + b
PY
output=$(python -m grok_local --debug "Fix the syntax error in 'projects/test.py' and make it add two numbers." --model "llama3.2:latest" 2>&1)
EXIT_CODE=$?
echo "Exit code: $EXIT_CODE" | tee -a "$LOG_FILE"
echo "$output" | tee -a "$LOG_FILE"
if [ $EXIT_CODE -eq 0 ] && echo "$output" | grep -q "Saved code to" && ! echo "$output" | grep -q "Error:"; then
    echo "Test 2 passed" | tee -a "$LOG_FILE"
else
    echo "Test 2 failed" | tee -a "$LOG_FILE"
fi
echo "----------------------------------------" | tee -a "$LOG_FILE"

# Test 3: List Reversal
echo "Test 3: Generate list reversal function" | tee -a "$LOG_FILE"
output=$(python -m grok_local --debug "Generate a Python function to reverse a list." --model "llama3.2:latest" 2>&1)
EXIT_CODE=$?
echo "Exit code: $EXIT_CODE" | tee -a "$LOG_FILE"
echo "$output" | tee -a "$LOG_FILE"
if [ $EXIT_CODE -eq 0 ] && echo "$output" | grep -q "Saved code to" && ! echo "$output" | grep -q "Error:"; then
    echo "Test 3 passed" | tee -a "$LOG_FILE"
else
    echo "Test 3 failed" | tee -a "$LOG_FILE"
fi
echo "----------------------------------------" | tee -a "$LOG_FILE"

echo "Stopping Ollama..." | tee -a "$LOG_FILE"
kill $OLLAMA_PID || echo "Ollama already stopped." | tee -a "$LOG_FILE"
echo "Tests complete! Logs saved to $LOG_FILE" | tee -a "$LOG_FILE"
