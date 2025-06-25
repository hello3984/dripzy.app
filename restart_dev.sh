#!/bin/bash

# Script to restart frontend and backend development servers
echo "📦 Restarting development servers..."

# Kill any existing processes using the ports
echo "🔄 Cleaning up existing processes..."
lsof -ti:3006 | xargs kill -9 2>/dev/null || true
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Wait a moment for processes to fully terminate
sleep 2

# Create a logs directory if it doesn't exist
mkdir -p logs

# Start backend in background
echo "🚀 Starting backend server..."
cd backend
if [ -f .server.pid ]; then
  rm .server.pid
fi
python run_server.py > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > .server.pid
cd ..

# Wait for backend to initialize - check if it's actually running
echo "⏳ Waiting for backend to initialize..."
for i in {1..10}; do
  if curl -s http://localhost:8000 > /dev/null; then
    echo "✅ Backend is running!"
    break
  fi
  if [ $i -eq 10 ]; then
    echo "⚠️ Backend may not have started properly. Check logs/backend.log"
  fi
  echo "  Still waiting... ($i/10)"
  sleep 3
done

# Start frontend in background as well
echo "🚀 Starting frontend server..."
cd frontend
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > .server.pid
cd ..

# Wait a moment for frontend to start
sleep 5

echo "✅ Development servers should now be running."
echo "   Frontend: http://localhost:3006"
echo "   Backend:  http://localhost:8000"
echo ""
echo "📝 Logs are being saved to:"
echo "   Frontend: logs/frontend.log"
echo "   Backend:  logs/backend.log"
echo ""
echo "⚠️ Servers are running in the background. To stop them, use:"
echo "   lsof -ti:3006,8000 | xargs kill -9" 