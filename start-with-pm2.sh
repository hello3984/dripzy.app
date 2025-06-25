#!/bin/bash

echo "🧹 Cleaning up any existing processes..."
# Kill any processes on the ports we plan to use
lsof -ti:3006,8000 | xargs kill -9 2>/dev/null || echo "No processes to clean up"

# Create logs directory if it doesn't exist
echo "📁 Creating logs directory..."
mkdir -p logs

# Check virtual environment in root directory
if [ ! -d "./.venv" ]; then
  echo "⚠️ Virtual environment not found in root directory!"
  echo "❌ Please make sure to set up the Python virtual environment first"
  exit 1
fi

# Check if uvicorn is installed in the virtual environment
if [ ! -f "./.venv/bin/uvicorn" ]; then
  echo "⚠️ uvicorn not found in virtual environment!"
  echo "Installing uvicorn in virtual environment..."
  ./.venv/bin/pip install uvicorn
fi

# Start the application using PM2
echo "🚀 Starting application with PM2..."
npx pm2 start ecosystem.config.js

# Show status
echo "✅ Services started with PM2"
echo "📊 Here's the current status:"
npx pm2 status

echo ""
echo "📝 View logs with: npm run pm2:logs"
echo "🔄 Restart services with: npm run pm2:restart"
echo "⛔ Stop services with: npm run pm2:stop"
echo "🖥️ Monitor services with: npm run pm2:monit" 