#!/bin/bash

# Kill any existing uvicorn process
echo "Stopping any existing uvicorn processes..."
pkill -f uvicorn

# Wait a moment
sleep 1

# Start server on port 9999
echo "Starting server on port 9999..."
uvicorn app.main:app --reload --port 9999 --host 0.0.0.0 