#!/bin/bash

################################################################################
# Backend Quality Verification Script
################################################################################
# This script runs all quality gates for the backend (FastAPI/Python) codebase:
# - Test coverage (minimum 90%)
# - Code linting (ruff)
# - Code formatting (black)
# - Type checking (mypy)
#
# Usage: ./scripts/verify-quality-backend.sh
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

# Change to backend directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/../backend"

if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${RED}✗ Backend directory not found: $BACKEND_DIR${NC}"
    exit 1
fi

cd "$BACKEND_DIR"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         Backend Quality Verification                      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

################################################################################
# 1. Test Coverage
################################################################################
echo -e "${YELLOW}[1/4] Running pytest with coverage (minimum 90%)...${NC}"
if poetry run pytest --cov=app --cov-report=term --cov-fail-under=90; then
    echo -e "${GREEN}✓ Tests passed with sufficient coverage${NC}"
    echo ""
else
    echo -e "${RED}✗ Tests failed or coverage below 90%${NC}"
    echo ""
    FAILED=1
fi

################################################################################
# 2. Linting (ruff)
################################################################################
echo -e "${YELLOW}[2/4] Running ruff linter...${NC}"
if poetry run ruff check .; then
    echo -e "${GREEN}✓ Linting passed${NC}"
    echo ""
else
    echo -e "${RED}✗ Linting failed${NC}"
    echo ""
    FAILED=1
fi

################################################################################
# 3. Code Formatting (black)
################################################################################
echo -e "${YELLOW}[3/4] Checking code formatting with black...${NC}"
if poetry run black --check .; then
    echo -e "${GREEN}✓ Code formatting is correct${NC}"
    echo ""
else
    echo -e "${RED}✗ Code formatting issues detected. Run 'poetry run black .' to fix${NC}"
    echo ""
    FAILED=1
fi

################################################################################
# 4. Type Checking (mypy)
################################################################################
echo -e "${YELLOW}[4/4] Running type checker (mypy)...${NC}"
if poetry run mypy app; then
    echo -e "${GREEN}✓ Type checking passed${NC}"
    echo ""
else
    echo -e "${RED}✗ Type checking failed${NC}"
    echo ""
    FAILED=1
fi

################################################################################
# Summary
################################################################################
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
if [ $FAILED -eq 0 ]; then
    echo -e "${BLUE}║${GREEN}  ✓ All quality checks passed!                            ${BLUE}║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    exit 0
else
    echo -e "${BLUE}║${RED}  ✗ Some quality checks failed. Please fix the issues.    ${BLUE}║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    exit 1
fi
