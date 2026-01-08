#!/bin/bash

################################################################################
# Service Status Verification Script
################################################################################
# This script checks if backend and frontend services are running on their
# configured ports:
# - Backend: 8891
# - Frontend: 8892
#
# Usage: ./scripts/check-services.sh
# Exit codes: 0 = all services running, 1 = one or more services down
################################################################################

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Service configuration
BACKEND_PORT=8891
FRONTEND_PORT=8892
BACKEND_HEALTH_PATH="/docs"
FRONTEND_PATH="/"

# Track overall status
ALL_RUNNING=true

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         Service Status Check                              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

################################################################################
# Check Backend Service
################################################################################
echo -e "${YELLOW}Checking backend service (port ${BACKEND_PORT})...${NC}"

if nc -z localhost ${BACKEND_PORT} 2>/dev/null; then
    # Port is open, try to verify it's actually our service
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:${BACKEND_PORT}${BACKEND_HEALTH_PATH} | grep -q "200"; then
        echo -e "${GREEN}✓ Backend is running on http://localhost:${BACKEND_PORT}${NC}"
        echo -e "  API Docs: ${BLUE}http://localhost:${BACKEND_PORT}/docs${NC}"
    else
        echo -e "${GREEN}✓ Backend port is open${NC}"
        echo -e "  ${YELLOW}⚠ Could not verify service health${NC}"
    fi
else
    echo -e "${RED}✗ Backend is NOT running on port ${BACKEND_PORT}${NC}"
    echo -e "  Start with: ${BLUE}cd backend && poetry run uvicorn app.main:app --reload --port ${BACKEND_PORT}${NC}"
    ALL_RUNNING=false
fi

echo ""

################################################################################
# Check Frontend Service
################################################################################
echo -e "${YELLOW}Checking frontend service (port ${FRONTEND_PORT})...${NC}"

if nc -z localhost ${FRONTEND_PORT} 2>/dev/null; then
    echo -e "${GREEN}✓ Frontend is running on http://localhost:${FRONTEND_PORT}${NC}"
else
    echo -e "${RED}✗ Frontend is NOT running on port ${FRONTEND_PORT}${NC}"
    echo -e "  Start with: ${BLUE}cd frontend && npm run dev${NC}"
    ALL_RUNNING=false
fi

echo ""

################################################################################
# Check Database Service
################################################################################
echo -e "${YELLOW}Checking PostgreSQL database (port 5432)...${NC}"

if nc -z localhost 5432 2>/dev/null; then
    echo -e "${GREEN}✓ PostgreSQL is running on port 5432${NC}"
else
    echo -e "${RED}✗ PostgreSQL is NOT running${NC}"
    echo -e "  Start with: ${BLUE}docker run --name postgres-dev -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=product_analysis -p 5432:5432 -d postgres:16${NC}"
    ALL_RUNNING=false
fi

echo ""

################################################################################
# Summary
################################################################################
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
if [ "$ALL_RUNNING" = true ]; then
    echo -e "${BLUE}║${GREEN}  ✓ All services are running!                             ${BLUE}║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "Quick links:"
    echo -e "  Frontend: ${BLUE}http://localhost:${FRONTEND_PORT}${NC}"
    echo -e "  Backend:  ${BLUE}http://localhost:${BACKEND_PORT}${NC}"
    echo -e "  API Docs: ${BLUE}http://localhost:${BACKEND_PORT}/docs${NC}"
    exit 0
else
    echo -e "${BLUE}║${RED}  ✗ Some services are not running. See above for details.  ${BLUE}║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    exit 1
fi
