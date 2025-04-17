#!/bin/bash

# Kill any existing uvicorn processes
echo "Checking for existing uvicorn processes..."
pkill -f "uvicorn app.main:app" && echo "Killed existing uvicorn processes" || echo "No existing uvicorn processes found"

# Wait a moment for processes to terminate
sleep 1

# Check if port 8000 is still in use
PORT_CHECK=$(lsof -i :8000 | grep LISTEN)
if [ ! -z "$PORT_CHECK" ]; then
    echo "Port 8000 is still in use by another process:"
    echo "$PORT_CHECK"
    echo "Attempting to force kill..."
    lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9
    sleep 1
fi

# Start the server
echo "Starting server..."
cd "$(dirname "$0")"
python -m uvicorn app.main:app --reload

# If we get here, the server has stopped
echo "Server has stopped." 