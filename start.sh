#!/bin/bash
set -e

echo "Starting Xvfb..."

# Clean up any stale lock files from previous runs
rm -f /tmp/.X99-lock /tmp/.X11-unix/X99
pkill -9 Xvfb 2>/dev/null || true
sleep 1

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

# Debug: Check if tkinter is accessible
echo "Checking Python and tkinter installation..."
python3 --version
python3 -c "import tkinter; print('✓ tkinter found')" || echo "✗ tkinter NOT found"
python3 -c "import _tkinter; print('✓ _tkinter found')" || echo "✗ _tkinter NOT found"

echo "Starting Flask application..."

# Run the Flask app
exec python3 squash.py --mode prod
