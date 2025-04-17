#!/bin/bash

# Kill any existing Python processes running the server
pkill -f "python run_server.py" || true
echo "Killed any existing server processes"

# Check if ports are in use and kill processes if needed
for port in 8000 8001 8002 8003 8004; do
  pid=$(lsof -ti:$port)
  if [ ! -z "$pid" ]; then
    echo "Killing process $pid using port $port"
    kill -9 $pid || true
  fi
done

# Wait a moment to ensure ports are released
sleep 1

# Get port from argument or use default
PORT=${1:-8000}

# Start the server with appropriate flags
cd "$(dirname "$0")/.." # Move to backend directory
echo "Starting development server on port $PORT..."

# Use --stable flag for production-like stability (no auto-reload)
# Use --no-reload to disable auto-reload but still run in development mode
python run_server.py --port $PORT "$@" 