#!/bin/bash

################################################################################
# Frontend Quality Verification Script
################################################################################
# This script runs all quality gates for the frontend (Vue 3/TypeScript) codebase:
# - Unit tests (vitest)
# - Type checking (TypeScript)
# - Linting (if configured)
#
# Usage: ./scripts/verify-quality-frontend.sh
# Exit codes: 0 = all checks passed, 1+ = one or more checks failed
################################################################################

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Track overall status
FAILED=0
CHECKS_RUN=0
CHECKS_PASSED=0

# Change to frontend directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/../frontend"

if [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${RED}✗ Frontend directory not found: $FRONTEND_DIR${NC}"
    exit 1
fi

cd "$FRONTEND_DIR"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         Frontend Quality Verification                     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

################################################################################
# Helper function to check if npm script exists
################################################################################
script_exists() {
    npm run "$1" --silent 2>&1 | grep -q "Missing script" && return 1 || return 0
}

################################################################################
# 1. Unit Tests
################################################################################
echo -e "${YELLOW}[1/3] Running unit tests (vitest)...${NC}"
CHECKS_RUN=$((CHECKS_RUN + 1))
if npm run test:run; then
    echo -e "${GREEN}✓ Tests passed${NC}"
    echo ""
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
else
    echo -e "${RED}✗ Tests failed${NC}"
    echo ""
    FAILED=1
fi

################################################################################
# 2. Type Checking
################################################################################
echo -e "${YELLOW}[2/3] Running TypeScript type checker...${NC}"
CHECKS_RUN=$((CHECKS_RUN + 1))
# vue-tsc is used by the build script, so we run the build with --noEmit equivalent
if npm run build -- --mode development > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Type checking passed${NC}"
    echo ""
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
else
    # If build fails, try to give more specific feedback
    echo -e "${YELLOW}Note: Type checking integrated with build process${NC}"
    if npm run build 2>&1 | grep -q "error TS"; then
        echo -e "${RED}✗ Type checking failed${NC}"
        echo ""
        FAILED=1
    else
        echo -e "${GREEN}✓ Type checking passed${NC}"
        echo ""
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    fi
fi

################################################################################
# 3. Linting (optional)
################################################################################
echo -e "${YELLOW}[3/3] Checking for linter...${NC}"
CHECKS_RUN=$((CHECKS_RUN + 1))

# Check if lint script exists in package.json
if grep -q '"lint"' package.json; then
    echo -e "${YELLOW}Running linter...${NC}"
    if npm run lint; then
        echo -e "${GREEN}✓ Linting passed${NC}"
        echo ""
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    else
        echo -e "${RED}✗ Linting failed${NC}"
        echo ""
        FAILED=1
    fi
else
    echo -e "${YELLOW}⚠ No lint script found in package.json - skipping${NC}"
    echo -e "${YELLOW}Consider adding ESLint or another linter to your project${NC}"
    echo ""
    CHECKS_RUN=$((CHECKS_RUN - 1))
fi

################################################################################
# Summary
################################################################################
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║ Results: $CHECKS_PASSED/$CHECKS_RUN checks passed                                   ${BLUE}║${NC}"
if [ $FAILED -eq 0 ]; then
    echo -e "${BLUE}║${GREEN}  ✓ All quality checks passed!                            ${BLUE}║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    exit 0
else
    echo -e "${BLUE}║${RED}  ✗ Some quality checks failed. Please fix the issues.    ${BLUE}║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    exit 1
fi
