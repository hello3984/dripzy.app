#!/bin/bash

# Fashion AI Development Environment Starter Script
# This script properly initializes a clean development environment
# by killing existing processes and starting both frontend and backend

# Set script to exit on error
set -e

# Text formatting
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║      Fashion AI - Dev Environment      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"

# ========================================================
# CONFIGURATION SECTION - Edit these values as needed
# ========================================================
# Standard port configuration across all services
BACKEND_PORT=8000            # Main backend API port
FRONTEND_PORT=3006           # Frontend development server port
# Additional service ports if needed in the future
#SOCKET_PORT=8001            # For websocket server if implemented
#ADMIN_PORT=8002             # For admin panel if implemented

# Directory configuration
BACKEND_DIR="backend"
FRONTEND_DIR="frontend"
# ========================================================

# Function to kill processes on ports
kill_port_processes() {
  for port in "$@"; do
    pid=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pid" ]; then
      echo -e "${RED}Killing process on port $port (PID: $pid)${NC}"
      kill -9 $pid 2>/dev/null || true
    fi
  done
}

# Kill all relevant processes that might be leftover
echo -e "${YELLOW}Cleaning up environment...${NC}"
pkill -f "python run_server.py" 2>/dev/null || true
kill_port_processes $BACKEND_PORT $FRONTEND_PORT 3000 3001 8001 8002 8003 8004

# Wait a moment to ensure ports are released
sleep 1

# Working directory 
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
cd "$SCRIPT_DIR"

# Display configuration for confirmation
echo -e "${BLUE}Configuration:${NC}"
echo -e "  Backend port: ${GREEN}$BACKEND_PORT${NC}"
echo -e "  Frontend port: ${GREEN}$FRONTEND_PORT${NC}"
echo -e "  Backend directory: ${GREEN}$BACKEND_DIR${NC}"
echo -e "  Frontend directory: ${GREEN}$FRONTEND_DIR${NC}"

# Start backend in background
echo -e "${GREEN}Starting backend server on port $BACKEND_PORT...${NC}"
cd "$SCRIPT_DIR/$BACKEND_DIR"
python run_server.py --port $BACKEND_PORT --no-reload &
BACKEND_PID=$!

# Start frontend in background
echo -e "${GREEN}Starting frontend server on port $FRONTEND_PORT...${NC}"
cd "$SCRIPT_DIR/$FRONTEND_DIR"
PORT=$FRONTEND_PORT npm start &
FRONTEND_PID=$!

# Handle script exit
trap 'kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true' EXIT

# Keep script running
echo -e "${GREEN}Development environment started!${NC}"
echo -e "${GREEN}Backend: http://localhost:$BACKEND_PORT${NC}"
echo -e "${GREEN}Frontend: http://localhost:$FRONTEND_PORT${NC}"
echo -e "${BLUE}Press Ctrl+C to stop both servers${NC}"

# Wait for child processes
wait 