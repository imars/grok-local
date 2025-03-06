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
sleep 20  # Increased to 20s for deepseek-r1:8b startup

# Test Asteroids clone with debug and retries
echo "Testing Asteroids clone command with running Ollama (debug on)..."
for attempt in {1..3}; do
    echo "Attempt $attempt of 3..."
    output=$(python -m grok_local --debug "Clone the Asteroids game" 2>&1)
    echo "$output"
    if echo "$output" | grep -q "Saved game code to 'projects/asteroids/asteroids.py'"; then
        echo "Success on attempt $attempt!"
        break
    elif [ $attempt -lt 3 ]; then
        echo "Failed, retrying in 10s..."
        sleep 10
    else
        echo "Asteroids clone failed after 3 attempts, continuing..."
    fi
done

# Verify file creation
echo "Checking for Asteroids game file..."
if [ -f "grok_local/projects/asteroids/asteroids.py" ]; then
    echo "Asteroids game file created successfully at grok_local/projects/asteroids/asteroids.py!"
    head -n 10 grok_local/projects/asteroids/asteroids.py  # Show first 10 lines
else
    echo "Asteroids game file not found—check output!"
fi

# Test direct mode checkpoint
echo "Testing direct mode checkpoint..."
python -m grok_local --do "checkpoint 'Asteroids clone retry test'" || echo "Direct mode failed, continuing..."

# Clean up
echo "Stopping Ollama..."
kill $OLLAMA_PID || echo "Ollama already stopped."

echo "Tests complete!"
