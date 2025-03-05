#!/bin/bash
# test_local_inference.sh: Batch tests for grok_local inference with Ollama, quieter output

set -e  # Exit on error

REPO_DIR="/Users/ian/dev/projects/agents/local/grok/repo"
cd "$REPO_DIR" || { echo "Failed to cd to $REPO_DIR"; exit 1; }

# Clear .pyc files
echo "Clearing .pyc files..."
find . -name "*.pyc" -exec rm -f {} \;

# Stop any running Ollama instance
echo "Stopping Ollama if running..."
pkill -f "ollama serve" || echo "No Ollama process to stop."

# Test with Ollama starting fresh (no debug unless needed)
echo "Starting Ollama fresh..."
ollama serve &
OLLAMA_PID=$!
sleep 5  # Give Ollama a moment to start

echo "Testing short command with fresh Ollama..."
python -m grok_local "Hi there"

echo "Testing conversational command with fresh Ollama..."
python -m grok_local "How are you today?"

# Test with Ollama running (with debug for medium command)
echo "Testing medium command with running Ollama (debug on)..."
python -m grok_local --debug "Can you summarize the latest changes in this repo?"

# Test direct mode (no debug)
echo "Testing direct mode checkpoint..."
python -m grok_local --do "checkpoint 'Quiet timeout test'"

# Clean up
echo "Stopping Ollama..."
kill $OLLAMA_PID || echo "Ollama already stopped."

echo "Tests complete!"
