#!/bin/bash

echo "🧹 Cleaning up running processes..."
lsof -ti:3006,3007,8000 | xargs kill -9 2>/dev/null || echo "No processes to clean up"

echo "🧹 Cleaning frontend build artifacts..."
cd frontend
rm -rf node_modules/.cache
cd ..

echo "🚀 Starting backend server..."
cd backend
nohup uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > ../backend.pid
cd ..

echo "⏳ Waiting for backend to initialize..."
for i in {1..10}; do
  if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend is running!"
    break
  fi
  echo "  Still waiting... ($i/10)"
  sleep 1
  if [ $i -eq 10 ]; then
    echo "❌ Backend failed to start within the timeout period"
    exit 1
  fi
done

echo "🚀 Starting frontend server..."
cd frontend
PORT=3007 nohup npm start > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../frontend.pid
cd ..

echo "✅ Development servers should now be running."
echo "   Frontend: http://localhost:3007"
echo "   Backend:  http://localhost:8000"
echo
echo "📝 Logs are being saved to:"
echo "   Frontend: logs/frontend.log"
echo "   Backend:  logs/backend.log"
echo
echo "⚠️  Servers are running in the background. To stop them, use:"
echo "   lsof -ti:3007,8000 | xargs kill -9" 