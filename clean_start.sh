#!/bin/bash

echo "=== Fashion AI Server Clean Start ==="

# Stop any running server processes
echo "Stopping any running server processes..."
pkill -f "python run_server.py" || true
echo "All server processes stopped."

# Ensure we're in the right directory
echo "Changing to project root directory..."
cd "$(dirname "$0")"
CURRENT_DIR=$(pwd)
echo "Current directory: $CURRENT_DIR"

# Verify backend directory exists
if [ ! -d "backend" ]; then
  echo "Error: 'backend' directory not found in $CURRENT_DIR"
  exit 1
fi

# Check .env file in backend directory
echo "Checking .env file in backend directory..."
if [ ! -f "backend/.env" ]; then
  echo "Error: No .env file found in backend directory"
  exit 1
fi

# Verify SERPAPI_API_KEY in .env
SERPAPI_KEY=$(grep "SERPAPI_API_KEY" backend/.env | cut -d '=' -f2)
if [[ "$SERPAPI_KEY" == *"your"* || "$SERPAPI_KEY" == "" ]]; then
  echo "Error: SERPAPI_API_KEY in backend/.env contains placeholder value: $SERPAPI_KEY"
  echo "Please set a valid API key in backend/.env"
  exit 1
else
  MASKED_KEY="${SERPAPI_KEY:0:4}...${SERPAPI_KEY: -4}"
  echo "✅ Found valid SERPAPI_API_KEY: $MASKED_KEY"
fi

# Verify serpapi_analysis.json exists
if [ ! -f "backend/app/services/serpapi_analysis.json" ]; then
  echo "Warning: serpapi_analysis.json not found. Search optimization will use default settings."
else 
  echo "✅ Found serpapi_analysis.json for search optimization."
fi

# Start the server with explicit configuration
echo "Starting server on port 8001 with auto-reload disabled..."
cd backend
echo "Running from directory: $(pwd)"
python run_server.py --port 8001 --no-reload 