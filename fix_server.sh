#!/bin/bash

echo "=== Fashion AI Server Fix ==="
echo "Stopping any running server processes..."
pkill -f "python run_server.py" || true

echo "Checking environment..."
cd "$(dirname "$0")"
if [ ! -f ".env" ]; then
  echo "Warning: No .env file found in the root directory."
fi

if [ ! -f "backend/.env" ]; then
  echo "Warning: No .env file found in the backend directory."
  echo "Copying .env to backend..."
  cp .env backend/ 2>/dev/null || echo "Failed to copy .env file."
fi

echo "Checking SERPAPI_API_KEY..."
grep -q "SERPAPI_API_KEY" backend/.env
if [ $? -ne 0 ]; then
  echo "Warning: SERPAPI_API_KEY not found in backend/.env"
  echo "Please ensure SERPAPI_API_KEY is set in your .env files."
else
  echo "SERPAPI_API_KEY found in backend/.env"
fi

echo "Starting server on port 8001 with auto-reload disabled..."
cd backend
python run_server.py --port 8001 --no-reload 