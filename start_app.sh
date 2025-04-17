#!/bin/bash
# Script to automate starting the fashion AI application

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Fashion AI application...${NC}"

# Step 1: Kill any existing Python and Node processes for the app
echo -e "${YELLOW}Stopping any existing processes...${NC}"
pkill -f "python run_server.py" || true
pkill -f "node.*fashion AI/frontend" || true
echo "Waiting for processes to terminate..."
sleep 2

# Step 2: Start backend on port 8004
echo -e "${YELLOW}Starting backend on port 8004...${NC}"
cd backend
python run_server.py --port 8004 &
BACKEND_PID=$!
echo "Backend started with PID: $BACKEND_PID"
echo "Waiting for backend to initialize..."
sleep 5

# Test if backend is running
echo -e "${YELLOW}Testing backend...${NC}"
BACKEND_RESPONSE=$(curl -s http://localhost:8004)
if [[ $BACKEND_RESPONSE == *"Welcome to the Dripzy Fashion AI API"* ]]; then
  echo -e "${GREEN}Backend is running successfully!${NC}"
else
  echo -e "${RED}Backend might not be running correctly. Response: $BACKEND_RESPONSE${NC}"
fi

# Step 3: Start frontend on port 3006
echo -e "${YELLOW}Starting frontend on port 3006...${NC}"
cd ../frontend
PORT=3006 npm start &
FRONTEND_PID=$!
echo "Frontend started with PID: $FRONTEND_PID"
echo "Waiting for frontend to initialize..."
sleep 10

# Test if frontend is running
echo -e "${YELLOW}Testing frontend...${NC}"
FRONTEND_RESPONSE=$(curl -s http://localhost:3006)
if [[ $FRONTEND_RESPONSE == *"<!DOCTYPE html>"* ]]; then
  echo -e "${GREEN}Frontend is running successfully!${NC}"
else
  echo -e "${RED}Frontend might not be running correctly${NC}"
fi

# Test the API connection from frontend to backend
echo -e "${YELLOW}Testing API connection...${NC}"
TEST_RESPONSE=$(curl -s http://localhost:8004/outfits/generate-test | head -c 100)
echo "API test response: $TEST_RESPONSE"

echo -e "${GREEN}Setup complete!${NC}"
echo "Backend running on: http://localhost:8004"
echo "Frontend running on: http://localhost:3006"
echo ""
echo "Press Ctrl+C to shut down all services"

# Keep the script running to maintain the processes
wait 