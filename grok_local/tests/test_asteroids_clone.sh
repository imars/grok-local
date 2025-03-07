#!/bin/bash
# test_asteroids_clone.sh: Test grok_local cloning a complete Asteroids game with iteration

set -e  # Exit on error

REPO_DIR="/Users/ian/dev/projects/agents/local/grok/repo"
cd "$REPO_DIR" || { echo "Failed to cd to $REPO_DIR"; exit 1; }

LOG_FILE="grok_local/tests/ollama_logs.txt"
mkdir -p grok_local/tests
> "$LOG_FILE"

echo "Clearing .pyc files..."
find . -name "*.pyc" -exec rm -f {} \;

echo "Stopping Ollama if running..."
pkill -f "ollama serve" || echo "No Ollama process to stop."

echo "Starting Ollama with extended timeout, logging to $LOG_FILE (warnings silenced)..."
export OLLAMA_LOAD_TIMEOUT=10m
ollama serve >> "$LOG_FILE" 2>/dev/null &
OLLAMA_PID=$!
sleep 5  # Initial wait
if ! ps -p $OLLAMA_PID > /dev/null; then
    echo "Error: Ollama failed to start! Check $LOG_FILE"
    cat "$LOG_FILE"
    exit 1
fi
echo "Ollama running with PID $OLLAMA_PID"

echo "Pre-loading deepseek-r1:8b..."
curl -X POST http://localhost:11434/api/generate -d '{"model": "deepseek-r1:8b", "prompt": "Warm-up", "stream": false}' >> "$LOG_FILE" 2>/dev/null

echo "Waiting 360s for deepseek-r1:8b to be fully ready..."
sleep 355  # Total 360s

echo "Checking available models..."
ollama list >> "$LOG_FILE" 2>/dev/null
cat "$LOG_FILE" | tail -n 10

echo "Testing Asteroids clone command with running Ollama (debug on)..."
for attempt in {1..3}; do
    echo "Attempt $attempt of 3..."
    set +e
    if [ $attempt -eq 1 ]; then
        prompt="Clone the Asteroids game, creating a complete, runnable Pygame script with Ship and Asteroid classes, player movement with arrow keys (left/right to rotate, up/down to move), asteroid spawning and movement, collision detection, and rendering on an 800x600 screen. Generate only Python code in ```python\n<code>\n``` format with all necessary classes (Ship, Asteroid) and constants (e.g., SCREEN_WIDTH=800, SCREEN_HEIGHT=600) defined within the script, avoiding external imports beyond pygame, math, and random. Use simple tuples (x, y) for positions and velocities, not undefined functions like 'math向量'. Ensure the code runs without syntax errors."
    else
        prompt="Debug and refine 'projects/asteroids/asteroids.py' to ensure it’s a complete, runnable Asteroids game with Ship and Asteroid classes, player movement with arrow keys (left/right to rotate, up/down to move), asteroid spawning and movement, collision detection, and rendering on an 800x600 screen. Use 'debug script projects/asteroids/asteroids.py' to test and fix errors (e.g., replace 'math向量' with (x, y) tuples), generating only Python code in ```python\n<code>\n``` format with all classes and constants defined within, avoiding external imports beyond pygame, math, and random. Ensure no syntax errors."
    fi
    output=$(python -m grok_local --debug "$prompt" 2>&1)
    EXIT_CODE=$?
    set -e
    echo "Python exit code: $EXIT_CODE"
    echo "$output"
    if [ $EXIT_CODE -ne 0 ]; then
        echo "Python command failed with exit code $EXIT_CODE"
        if [ $attempt -lt 3 ]; then
            echo "Retrying in 10s with refined prompt..."
            sleep 10
            continue
        else
            echo "Asteroids clone failed after 3 attempts, continuing..."
            break
        fi
    fi
    if echo "$output" | grep -q "Saved game code to 'projects/asteroids/asteroids.py'" && \
       echo "$output" | grep -q "Debug result:.*pygame" && \
       ! echo "$output" | grep -q "Error:"; then
        echo "Success on attempt $attempt! Game appears runnable."
        break
    elif [ $attempt -lt 3 ]; then
        echo "Failed (incomplete or errors), retrying in 10s with refined prompt..."
        sleep 10
    else
        echo "Asteroids clone failed after 3 attempts, continuing..."
    fi
done

echo "Checking for Asteroids game file..."
if [ -f "grok_local/projects/asteroids/asteroids.py" ]; then
    echo "Asteroids game file created successfully!"
    head -n 30 grok_local/projects/asteroids/asteroids.py
else
    echo "Asteroids game file not found—check output!"
fi

echo "Testing direct mode checkpoint..."
python -m grok_local --do "checkpoint 'Completed functional Asteroids game clone'" || echo "Direct mode failed, continuing..."

echo "Checking Ollama process status..."
ollama ps >> "$LOG_FILE" 2>/dev/null
cat "$LOG_FILE" | tail -n 10

echo "Stopping Ollama..."
kill $OLLAMA_PID || echo "Ollama already stopped."
echo "Logs saved to $LOG_FILE"

echo "Tests complete!"
