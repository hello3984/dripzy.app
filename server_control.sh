#!/bin/bash
# server_control.sh - Zero-mistake process management for Fashion AI
# Kill zombie processes and manage server instances with fixed ports

# Configuration
FASHION_AI_ROOT="/Users/fatihbayraktar/fashion AI"
BACKEND_DIR="$FASHION_AI_ROOT/backend"
FRONTEND_DIR="$FASHION_AI_ROOT/frontend"
BACKEND_PORT=8000
FRONTEND_PORT=3010
BACKEND_PID_FILE="$BACKEND_DIR/.server.pid"
FRONTEND_PID_FILE="$FRONTEND_DIR/.server.pid"
LOG_FILE="$FASHION_AI_ROOT/server.log"

# Colors for better visibility
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Logging
log() {
  echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Kill all zombie processes
clean_zombies() {
  log "${YELLOW}Cleaning up zombie processes...${NC}"
  
  # Kill backend Python processes
  pkill -f "python run_server.py" || true
  
  # Kill any processes on specific ports
  kill $(lsof -ti:$BACKEND_PORT) 2>/dev/null || true
  kill $(lsof -ti:$FRONTEND_PORT) 2>/dev/null || true
  
  # Kill any stale PID-tracked processes
  if [ -f "$BACKEND_PID_FILE" ]; then
    BACKEND_PID=$(cat "$BACKEND_PID_FILE")
    kill $BACKEND_PID 2>/dev/null || true
    rm "$BACKEND_PID_FILE"
  fi
  
  if [ -f "$FRONTEND_PID_FILE" ]; then
    FRONTEND_PID=$(cat "$FRONTEND_PID_FILE")
    kill $FRONTEND_PID 2>/dev/null || true
    rm "$FRONTEND_PID_FILE"
  fi
  
  # Ensure ports are definitely free
  sleep 2
  log "${GREEN}✓ Zombie processes cleaned${NC}"
}

# Start backend server
start_backend() {
  log "${YELLOW}Starting backend on port $BACKEND_PORT...${NC}"
  cd "$BACKEND_DIR"
  
  # Important! Use --no-reload to prevent zombie processes
  python run_server.py --port $BACKEND_PORT --no-reload &
  
  # Store PID
  echo $! > "$BACKEND_PID_FILE"
  log "${GREEN}✓ Backend started (PID: $!)${NC}"
}

# Start frontend server
start_frontend() {
  log "${YELLOW}Starting frontend on port $FRONTEND_PORT...${NC}"
  cd "$FRONTEND_DIR"
  
  # Start with fixed port
  PORT=$FRONTEND_PORT npm start &
  
  # Store PID
  echo $! > "$FRONTEND_PID_FILE"
  log "${GREEN}✓ Frontend started (PID: $!)${NC}"
}

# Check server status
check_status() {
  log "${YELLOW}Checking server status...${NC}"
  
  # Check backend status
  BACKEND_RUNNING=false
  if [ -f "$BACKEND_PID_FILE" ]; then
    BACKEND_PID=$(cat "$BACKEND_PID_FILE")
    if ps -p $BACKEND_PID > /dev/null; then
      log "${GREEN}✓ Backend running (PID: $BACKEND_PID)${NC}"
      BACKEND_RUNNING=true
    fi
  fi
  
  if ! $BACKEND_RUNNING; then
    log "${RED}✗ Backend not running${NC}"
  fi
  
  # Check if port 8000 is used by something else
  PORT_8000_PID=$(lsof -ti:$BACKEND_PORT 2>/dev/null)
  if [ -n "$PORT_8000_PID" ] && [ "$PORT_8000_PID" != "$BACKEND_PID" ]; then
    log "${RED}⚠ Warning: Port $BACKEND_PORT used by another process: $PORT_8000_PID${NC}"
  fi
  
  # Check frontend status
  FRONTEND_RUNNING=false
  if [ -f "$FRONTEND_PID_FILE" ]; then
    FRONTEND_PID=$(cat "$FRONTEND_PID_FILE")
    if ps -p $FRONTEND_PID > /dev/null; then
      log "${GREEN}✓ Frontend running (PID: $FRONTEND_PID)${NC}"
      FRONTEND_RUNNING=true
    fi
  fi
  
  if ! $FRONTEND_RUNNING; then
    log "${RED}✗ Frontend not running${NC}"
  fi
}

# Command handling
case "$1" in
  start)
    clean_zombies
    start_backend
    start_frontend
    ;;
  stop)
    clean_zombies
    log "${GREEN}All servers stopped${NC}"
    ;;
  restart)
    clean_zombies
    start_backend
    start_frontend
    ;;
  status)
    check_status
    ;;
  backend)
    clean_zombies
    start_backend
    ;;
  frontend)
    clean_zombies
    start_frontend
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|status|backend|frontend}"
    exit 1
esac

# Success message
if [ "$1" != "status" ]; then
  log "${GREEN}Command '$1' completed successfully${NC}"
  log "Backend URL: http://localhost:$BACKEND_PORT"
  log "Frontend URL: http://localhost:$FRONTEND_PORT"
fi

exit 0 