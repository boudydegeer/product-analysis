#!/bin/bash

################################################################################
# Stop All Services Script
################################################################################
# This script stops backend and frontend services started by start-services.sh
#
# Usage: ./scripts/stop-services.sh
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
LOGS_DIR="$PROJECT_DIR/.logs"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         Stopping Product Analysis Platform                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

SERVICES_STOPPED=0

################################################################################
# Stop Backend
################################################################################
if [ -f "$LOGS_DIR/backend.pid" ]; then
    BACKEND_PID=$(cat "$LOGS_DIR/backend.pid")
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}Stopping backend (PID: $BACKEND_PID)...${NC}"
        kill $BACKEND_PID 2>/dev/null
        sleep 1

        # Force kill if still running
        if ps -p $BACKEND_PID > /dev/null 2>&1; then
            kill -9 $BACKEND_PID 2>/dev/null
        fi

        echo -e "${GREEN}✓ Backend stopped${NC}"
        SERVICES_STOPPED=$((SERVICES_STOPPED + 1))
    else
        echo -e "${YELLOW}⚠ Backend process not found (PID: $BACKEND_PID)${NC}"
    fi
    rm -f "$LOGS_DIR/backend.pid"
else
    echo -e "${YELLOW}⚠ No backend PID file found${NC}"

    # Try to kill by port
    if lsof -ti:8891 > /dev/null 2>&1; then
        echo -e "${YELLOW}  Killing process on port 8891...${NC}"
        lsof -ti:8891 | xargs kill -9 2>/dev/null
        echo -e "${GREEN}✓ Killed process on port 8891${NC}"
        SERVICES_STOPPED=$((SERVICES_STOPPED + 1))
    fi
fi

echo ""

################################################################################
# Stop Frontend
################################################################################
if [ -f "$LOGS_DIR/frontend.pid" ]; then
    FRONTEND_PID=$(cat "$LOGS_DIR/frontend.pid")
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}Stopping frontend (PID: $FRONTEND_PID)...${NC}"
        kill $FRONTEND_PID 2>/dev/null
        sleep 1

        # Force kill if still running
        if ps -p $FRONTEND_PID > /dev/null 2>&1; then
            kill -9 $FRONTEND_PID 2>/dev/null
        fi

        echo -e "${GREEN}✓ Frontend stopped${NC}"
        SERVICES_STOPPED=$((SERVICES_STOPPED + 1))
    else
        echo -e "${YELLOW}⚠ Frontend process not found (PID: $FRONTEND_PID)${NC}"
    fi
    rm -f "$LOGS_DIR/frontend.pid"
else
    echo -e "${YELLOW}⚠ No frontend PID file found${NC}"

    # Try to kill by port
    if lsof -ti:8892 > /dev/null 2>&1; then
        echo -e "${YELLOW}  Killing process on port 8892...${NC}"
        lsof -ti:8892 | xargs kill -9 2>/dev/null
        echo -e "${GREEN}✓ Killed process on port 8892${NC}"
        SERVICES_STOPPED=$((SERVICES_STOPPED + 1))
    fi
fi

echo ""

################################################################################
# Summary
################################################################################
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
if [ $SERVICES_STOPPED -gt 0 ]; then
    echo -e "${BLUE}║${GREEN}  ✓ Services stopped ($SERVICES_STOPPED)                                ${BLUE}║${NC}"
else
    echo -e "${BLUE}║${YELLOW}  ⚠ No running services found                             ${BLUE}║${NC}"
fi
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
