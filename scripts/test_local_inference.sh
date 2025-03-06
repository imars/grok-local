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

# Test with Ollama starting fresh (quiet output)
echo "Starting Ollama fresh (output redirected)..."
ollama serve > /dev/null 2>&1 &
OLLAMA_PID=$!
sleep 10  # 10s for Ollama startup

echo "Testing short command with fresh Ollama..."
python -m grok_local "Hi there" || echo "Short command failed, continuing..."

echo "Testing conversational command with fresh Ollama..."
python -m grok_local "How are you today?" || echo "Conversational command failed, continuing..."

# Test with Ollama running (with debug for Git summary)
echo "Testing Git summary command with running Ollama (debug on)..."
python -m grok_local --debug "Can you summarize the latest changes in this repo?" || echo "Git summary failed, continuing..."

# Test raw Git log for comparison
echo "Testing raw Git log command..."
python -m grok_local "git log -n 3 --oneline" || echo "Raw Git log failed, continuing..."

# Test direct mode checkpoint
echo "Testing direct mode checkpoint..."
python -m grok_local --do "checkpoint 'Extended timeout test'" || echo "Direct mode failed, continuing..."

# Clean up
echo "Stopping Ollama..."
kill $OLLAMA_PID || echo "Ollama already stopped."

echo "Tests complete!"
