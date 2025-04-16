#!/bin/bash
# Start the backend server
cd "$(dirname "$0")/backend"
# Try to activate the virtual environment, but continue if it doesn't exist
if [ -f .venv/bin/activate ]; then
  source .venv/bin/activate
elif [ -f ../.venv/bin/activate ]; then
  source ../.venv/bin/activate
fi

# Check if port 8000 is already in use and use a different port if needed
PORT=8000
while lsof -i:$PORT &> /dev/null; do
  echo "Port $PORT is already in use, trying port $((PORT+1))"
  PORT=$((PORT+1))
done

python -m uvicorn app.main:app --reload --port $PORT &
BACKEND_PID=$!
echo "Backend started on port $PORT"

# Wait a bit for the backend to start
sleep 3

# Start the frontend server
cd "$(dirname "$0")/frontend"
# Check if port 3000 is already in use and use a different port if needed
PORT=3000
while lsof -i:$PORT &> /dev/null; do
  echo "Port $PORT is already in use, trying port $((PORT+1))"
  PORT=$((PORT+1))
done

npm start --port $PORT &
FRONTEND_PID=$!
echo "Frontend started on port $PORT"

echo "Servers started. Press Ctrl+C to stop."
trap "kill $BACKEND_PID $FRONTEND_PID; exit 0" INT TERM
wait
