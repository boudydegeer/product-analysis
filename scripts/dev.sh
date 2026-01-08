#!/bin/bash

################################################################################
# Development Environment Script
################################################################################
# This script starts backend and frontend services in FOREGROUND with real-time
# logs interleaved in the same terminal. Perfect for local development.
#
# Services:
# - Backend: http://localhost:8891
# - Frontend: http://localhost:8892
#
# Usage: ./scripts/dev.sh
# Stop: Press Ctrl+C (cleans up both processes automatically)
################################################################################

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR/.."
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

# Process IDs for cleanup
BACKEND_PID=""
FRONTEND_PID=""

################################################################################
# Cleanup function - kills both processes
################################################################################
cleanup() {
    echo ""
    echo -e "${YELLOW}Stopping services...${NC}"

    if [ ! -z "$BACKEND_PID" ] && ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo -e "${CYAN}[BACKEND]${NC} Stopping backend (PID: $BACKEND_PID)..."
        kill -TERM $BACKEND_PID 2>/dev/null
        wait $BACKEND_PID 2>/dev/null
        echo -e "${GREEN}✓ Backend stopped${NC}"
    fi

    if [ ! -z "$FRONTEND_PID" ] && ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo -e "${GREEN}[FRONTEND]${NC} Stopping frontend (PID: $FRONTEND_PID)..."
        kill -TERM $FRONTEND_PID 2>/dev/null
        wait $FRONTEND_PID 2>/dev/null
        echo -e "${GREEN}✓ Frontend stopped${NC}"
    fi

    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${GREEN}  ✓ Services stopped cleanly                              ${BLUE}║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    exit 0
}

# Register cleanup function for SIGINT (Ctrl+C) and SIGTERM
trap cleanup SIGINT SIGTERM

################################################################################
# Header
################################################################################
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         Development Environment - Product Analysis        ║${NC}"
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
    echo -e "${RED}✗ Cannot start - please free the port or stop existing services${NC}"
    echo -e "  Check with: ${BLUE}lsof -i :8891${NC}"
    echo -e "  Kill with:  ${BLUE}lsof -ti:8891 | xargs kill -9${NC}"
    exit 1
fi

if nc -z localhost 8892 2>/dev/null; then
    echo -e "${YELLOW}⚠ Port 8892 (frontend) is already in use${NC}"
    echo -e "${RED}✗ Cannot start - please free the port or stop existing services${NC}"
    echo -e "  Check with: ${BLUE}lsof -i :8892${NC}"
    echo -e "  Kill with:  ${BLUE}lsof -ti:8892 | xargs kill -9${NC}"
    exit 1
fi

# Check if backend directory exists
if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${RED}✗ Backend directory not found: $BACKEND_DIR${NC}"
    exit 1
fi

# Check if frontend directory exists
if [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${RED}✗ Frontend directory not found: $FRONTEND_DIR${NC}"
    exit 1
fi

echo ""

################################################################################
# Start Services
################################################################################
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${GREEN}  ✓ Prerequisites OK - Starting services...               ${BLUE}║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "Quick links:"
echo -e "  Frontend: ${BLUE}http://localhost:8892${NC}"
echo -e "  Backend:  ${BLUE}http://localhost:8891${NC}"
echo -e "  API Docs: ${BLUE}http://localhost:8891/docs${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

# Create temporary named pipes for output
BACKEND_PIPE=$(mktemp -u)
FRONTEND_PIPE=$(mktemp -u)
mkfifo "$BACKEND_PIPE"
mkfifo "$FRONTEND_PIPE"

# Cleanup pipes on exit
trap "rm -f $BACKEND_PIPE $FRONTEND_PIPE; cleanup" EXIT

# Start backend in background, piping to named pipe
(
    cd "$BACKEND_DIR"
    poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8891 2>&1
) > "$BACKEND_PIPE" &
BACKEND_PID=$!

# Start frontend in background, piping to named pipe
(
    cd "$FRONTEND_DIR"
    npm run dev 2>&1
) > "$FRONTEND_PIPE" &
FRONTEND_PID=$!

# Process backend output with prefix
while IFS= read -r line; do
    echo -e "${CYAN}[BACKEND]${NC}  $line"
done < "$BACKEND_PIPE" &
BACKEND_READER_PID=$!

# Process frontend output with prefix
while IFS= read -r line; do
    echo -e "${GREEN}[FRONTEND]${NC} $line"
done < "$FRONTEND_PIPE" &
FRONTEND_READER_PID=$!

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID

# If we reach here, one of the processes died
echo ""
echo -e "${RED}✗ One or both services stopped unexpectedly${NC}"
cleanup
