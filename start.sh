#!/bin/bash
set -e

echo "Starting Xvfb..."
# Start Xvfb on display :99
Xvfb :99 -screen 0 1920x1080x24 -ac -nolisten tcp -nolisten unix &
XVFB_PID=$!

# Set display environment variable
export DISPLAY=:99

# Wait for Xvfb to be ready
sleep 3

# Verify Xvfb is running
if ! ps -p $XVFB_PID > /dev/null; then
    echo "ERROR: Xvfb failed to start"
    exit 1
fi

echo "Xvfb started successfully on display :99"
echo "Starting Flask application..."

# Run the Flask app
exec python3 squash.py --mode prod
