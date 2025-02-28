#!/bin/bash

# Debug script for x_poller.py
echo "Starting debug_x_poller.sh"

# Function to clean up background processes
cleanup() {
    echo "Stopping all background processes..."
    for pid in $PID1 $PID2 $PID3; do
        if [ -n "$pid" ] && ps -p "$pid" > /dev/null; then
            kill "$pid"
            wait "$pid" 2>/dev/null
        fi
    done
    echo "Cleanup complete"
    exit 0
}

# Trap Ctrl+C and exit signals
trap cleanup INT TERM EXIT

# Ensure script is executable
chmod +x debug_x_poller.sh
echo "Set debug_x_poller.sh as executable"

# Verify environment variables are set
if [ -z "$X_USERNAME" ] || [ -z "$X_PASSWORD" ] || [ -z "$X_VERIFY" ]; then
    echo "Error: X_USERNAME, X_PASSWORD, and X_VERIFY must be set in the environment"
    exit 1
fi

# Clear log file to start fresh
rm -f x_poller.log
echo "Cleared x_poller.log for fresh start"

# Run x_poller.py with --debug (default 5s polling) for 20 seconds
echo "Running x_poller.py with --headless --debug (default 5s polling)"
python x_poller.py --headless --debug &
PID1=$!
sleep 20  # 20s to catch ~4 cycles at 5s each
kill $PID1
wait $PID1 2>/dev/null
echo "Stopped x_poller.py after 20 seconds (debug mode)"
echo "Log after debug run:"
tail -n 10 x_poller.log || echo "No log output"

# Run x_poller.py with --info (default 5s polling) for 15 seconds
echo "Running x_poller.py with --headless --info (default 5s polling)"
python x_poller.py --headless --info &
PID2=$!
sleep 15  # 15s to catch ~3 cycles at 5s each
kill $PID2
wait $PID2 2>/dev/null
echo "Stopped x_poller.py after 15 seconds (info mode)"
echo "Log after info run:"
tail -n 10 x_poller.log || echo "No log output"

# Run x_poller.py without flags (default 5s polling, silent) for 15 seconds
echo "Running x_poller.py with --headless (default 5s polling, silent)"
python x_poller.py --headless &
PID3=$!
sleep 15  # 15s to catch ~3 cycles at 5s each
kill $PID3
wait $PID3 2>/dev/null
echo "Stopped x_poller.py after 15 seconds (silent mode)"
echo "Log after silent run:"
tail -n 10 x_poller.log || echo "No log output"

# Display full logs
echo "Displaying last 20 lines of x_poller.log (all runs)"
tail -n 20 x_poller.log || echo "No log output"
echo "Displaying last 20 lines of x_login_stub.log"
tail -n 20 x_login_stub.log || echo "No log output"

echo "Debug script completed"
