#!/bin/bash
# Start the backend server
cd "$(dirname "$0")/backend"
source venv/bin/activate
python -m uvicorn app.main:app --reload &
BACKEND_PID=$!
# Wait a bit for the backend to start
sleep 3
# Start the frontend server
cd "$(dirname "$0")/frontend"
npm start &
FRONTEND_PID=$!
echo "Servers started. Press Ctrl+C to stop."
trap "kill $BACKEND_PID $FRONTEND_PID; exit 0" INT TERM
wait
