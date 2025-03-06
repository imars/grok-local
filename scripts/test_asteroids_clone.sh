#!/bin/bash
# test_asteroids_clone.sh: Test grok_local cloning Asteroids with deepseek-r1:8b

set -e  # Exit on error

REPO_DIR="/Users/ian/dev/projects/agents/local/grok/repo"
cd "$REPO_DIR" || { echo "Failed to cd to $REPO_DIR"; exit 1; }

# Clear .pyc files
echo "Clearing .pyc files..."
find . -name "*.pyc" -exec rm -f {} \;

# Stop any running Ollama instance
echo "Stopping Ollama if running..."
pkill -f "ollama serve" || echo "No Ollama process to stop."

# Test with Ollama starting fresh (quiet output)
echo "Starting Ollama fresh (output redirected)..."
ollama serve > /dev/null 2>&1 &
OLLAMA_PID=$!
sleep 10  # 10s for Ollama startup

# Test Asteroids clone
echo "Testing Asteroids clone command with running Ollama (debug on)..."
python -m grok_local --debug "Clone the Asteroids game" || echo "Asteroids clone failed, continuing..."

# Test direct mode checkpoint
echo "Testing direct mode checkpoint..."
python -m grok_local --do "checkpoint 'Asteroids clone test'" || echo "Direct mode failed, continuing..."

# Clean up
echo "Stopping Ollama..."
kill $OLLAMA_PID || echo "Ollama already stopped."

echo "Tests complete!"
