#!/bin/bash

# Check if ollama is installed and running
if ! command -v ollama &> /dev/null; then
    echo "Ollama is not installed or not in PATH. Please install it first."
    exit 1
fi

# Check if any models are running
RUNNING_MODELS=$(ollama ps)
if [ -z "$RUNNING_MODELS" ] || [ "$RUNNING_MODELS" == "NAME	ID	SIZE	PROCESSOR	UNTIL" ]; then
    echo "No models are currently running."
    exit 0
fi

echo "Currently running models:"
echo "$RUNNING_MODELS"
echo ""

# Find and kill the Ollama server process
echo "Stopping Ollama inference..."
OLLAMA_PID=$(ps aux | grep '[o]llama serve' | awk '{print $2}')
if [ -z "$OLLAMA_PID" ]; then
    echo "No Ollama server process found. Checking for any ollama processes..."
    OLLAMA_PID=$(ps aux | grep '[o]llama' | awk '{print $2}')
    if [ -z "$OLLAMA_PID" ]; then
        echo "No Ollama processes found. Inference may already be stopped."
        exit 0
    fi
fi

# Kill the process(es)
for PID in $OLLAMA_PID; do
    kill -9 "$PID"
    if [ $? -eq 0 ]; then
        echo "Successfully stopped Ollama process (PID: $PID)."
    else
        echo "Failed to stop Ollama process (PID: $PID)."
    fi
done

# Verify that no models are running
sleep 2 # Give it a moment to shut down
RUNNING_MODELS=$(ollama ps 2>/dev/null)
if [ $? -ne 0 ] || [ -z "$RUNNING_MODELS" ] || [ "$RUNNING_MODELS" == "NAME	ID	SIZE	PROCESSOR	UNTIL" ]; then
    echo "Inference stopped successfully. No models are running."
else
    echo "Warning: Some models may still be running:"
    echo "$RUNNING_MODELS"
fi

exit 0