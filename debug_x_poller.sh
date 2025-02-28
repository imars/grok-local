#!/bin/bash

# Debug script for x_poller.py
echo "Starting debug_x_poller.sh"

# Ensure script is executable
chmod +x debug_x_poller.sh
echo "Set debug_x_poller.sh as executable"

# Verify environment variables are set (without overwriting)
if [ -z "$X_USERNAME" ] || [ -z "$X_PASSWORD" ] || [ -z "$X_VERIFY" ]; then
    echo "Error: X_USERNAME, X_PASSWORD, and X_VERIFY must be set in the environment"
    exit 1
fi

# Run x_poller.py without flags (default 5s polling, silent) for 15 seconds
echo "Running x_poller.py with --headless (default 5s polling, silent)"
python x_poller.py --headless &
PID1=$!
sleep 15  # 15s to catch ~3 cycles at 5s each
kill $PID1
echo "Stopped x_poller.py after 15 seconds (silent)"

# Run x_poller.py with --info mode and default 5s polling for 15 seconds
echo "Running x_poller.py with --headless --info (default 5s polling)"
python x_poller.py --headless --info &
PID2=$!
sleep 15  # 15s to catch ~3 cycles at 5s each
kill $PID2
echo "Stopped x_poller.py after 15 seconds (info mode)"

# Run x_poller.py with --debug mode and 1s polling for 10 seconds
echo "Running x_poller.py with --headless --debug --poll-interval 1"
python x_poller.py --headless --debug --poll-interval 1 &
PID3=$!
sleep 10  # 10s to catch ~10 cycles at 1s each
kill $PID3
echo "Stopped x_poller.py after 10 seconds (debug mode, 1s polling)"

# Display logs
echo "Displaying last 20 lines of x_poller.log"
tail -n 20 x_poller.log
echo "Displaying last 20 lines of x_login_stub.log"
tail -n 20 x_login_stub.log

echo "Debug script completed"
