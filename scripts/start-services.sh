#!/bin/bash

################################################################################
# Start All Services Script
################################################################################
# This script starts backend and frontend services in the background with
# proper logging.
#
# Services:
# - Backend: http://localhost:8891
# - Frontend: http://localhost:8892
#
# Usage: ./scripts/start-services.sh
# Stop services: ./scripts/stop-services.sh
################################################################################

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR/.."
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
LOGS_DIR="$PROJECT_DIR/.logs"

# Create logs directory if it doesn't exist
mkdir -p "$LOGS_DIR"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         Starting Product Analysis Platform                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

################################################################################
# Check Prerequisites
################################################################################
echo -e "${YELLOW}Checking prerequisites...${NC}"

# Check if PostgreSQL is running
if ! nc -z localhost 5432 2>/dev/null; then
    echo -e "${RED}✗ PostgreSQL is not running${NC}"
    echo -e "  Start with: ${BLUE}docker run --name postgres-dev -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=product_analysis -p 5432:5432 -d postgres:16${NC}"
    exit 1
fi
echo -e "${GREEN}✓ PostgreSQL is running${NC}"

# Check if ports are available
if nc -z localhost 8891 2>/dev/null; then
    echo -e "${YELLOW}⚠ Port 8891 (backend) is already in use${NC}"
    read -p "  Kill existing process? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        lsof -ti:8891 | xargs kill -9 2>/dev/null
        echo -e "${GREEN}  Process killed${NC}"
    else
        echo -e "${RED}  Cannot start backend - port already in use${NC}"
        exit 1
    fi
fi

if nc -z localhost 8892 2>/dev/null; then
    echo -e "${YELLOW}⚠ Port 8892 (frontend) is already in use${NC}"
    read -p "  Kill existing process? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        lsof -ti:8892 | xargs kill -9 2>/dev/null
        echo -e "${GREEN}  Process killed${NC}"
    else
        echo -e "${RED}  Cannot start frontend - port already in use${NC}"
        exit 1
    fi
fi

echo ""

################################################################################
# Start Backend
################################################################################
echo -e "${YELLOW}Starting backend (port 8891)...${NC}"

if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${RED}✗ Backend directory not found: $BACKEND_DIR${NC}"
    exit 1
fi

cd "$BACKEND_DIR"

# Start backend in background
nohup poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8891 \
    > "$LOGS_DIR/backend.log" 2>&1 &
BACKEND_PID=$!

# Save PID
echo $BACKEND_PID > "$LOGS_DIR/backend.pid"

# Wait a bit and check if it's running
sleep 2
if ps -p $BACKEND_PID > /dev/null; then
    echo -e "${GREEN}✓ Backend started (PID: $BACKEND_PID)${NC}"
    echo -e "  URL: ${BLUE}http://localhost:8891${NC}"
    echo -e "  Logs: ${BLUE}$LOGS_DIR/backend.log${NC}"
else
    echo -e "${RED}✗ Backend failed to start${NC}"
    echo -e "  Check logs: ${BLUE}cat $LOGS_DIR/backend.log${NC}"
    exit 1
fi

echo ""

################################################################################
# Start Frontend
################################################################################
echo -e "${YELLOW}Starting frontend (port 8892)...${NC}"

if [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${RED}✗ Frontend directory not found: $FRONTEND_DIR${NC}"
    exit 1
fi

cd "$FRONTEND_DIR"

# Start frontend in background
nohup npm run dev > "$LOGS_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!

# Save PID
echo $FRONTEND_PID > "$LOGS_DIR/frontend.pid"

# Wait a bit and check if it's running
sleep 3
if ps -p $FRONTEND_PID > /dev/null; then
    echo -e "${GREEN}✓ Frontend started (PID: $FRONTEND_PID)${NC}"
    echo -e "  URL: ${BLUE}http://localhost:8892${NC}"
    echo -e "  Logs: ${BLUE}$LOGS_DIR/frontend.log${NC}"
else
    echo -e "${RED}✗ Frontend failed to start${NC}"
    echo -e "  Check logs: ${BLUE}cat $LOGS_DIR/frontend.log${NC}"
    exit 1
fi

echo ""

################################################################################
# Summary
################################################################################
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${GREEN}  ✓ All services started successfully!                    ${BLUE}║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "Quick links:"
echo -e "  Frontend: ${BLUE}http://localhost:8892${NC}"
echo -e "  Backend:  ${BLUE}http://localhost:8891${NC}"
echo -e "  API Docs: ${BLUE}http://localhost:8891/docs${NC}"
echo ""
echo -e "Logs:"
echo -e "  Backend:  ${BLUE}tail -f $LOGS_DIR/backend.log${NC}"
echo -e "  Frontend: ${BLUE}tail -f $LOGS_DIR/frontend.log${NC}"
echo ""
echo -e "Stop services with: ${BLUE}./scripts/stop-services.sh${NC}"
