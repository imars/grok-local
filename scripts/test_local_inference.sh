#!/bin/bash
# test_local_inference.sh: Batch tests for grok_local inference with Ollama

# Ensure we're in the repo root
cd "$(dirname "$0")/../" || exit 1

# Clear .pyc files
echo "Clearing .pyc files..."
find . -name "*.pyc" -exec rm -f {} \;

# Stop any running Ollama instance
echo "Stopping Ollama if running..."
pkill -f "ollama serve" || echo "No Ollama process to stop."

# Test with Ollama starting fresh
echo "Starting Ollama fresh..."
ollama serve &
OLLAMA_PID=$!
sleep 5  # Give Ollama a moment to start

echo "Testing short command with fresh Ollama..."
python -m grok_local "Hi there"

echo "Testing conversational command with fresh Ollama..."
python -m grok_local "How are you today?"

# Test with Ollama running
echo "Testing medium command with running Ollama..."
python -m grok_local "Can you summarize the latest changes in this repo?"

# Test direct mode
echo "Testing direct mode checkpoint..."
python -m grok_local --do "checkpoint 'Timeout fix test'"

# Clean up
echo "Stopping Ollama..."
kill $OLLAMA_PID || echo "Ollama already stopped."

echo "Done!"
