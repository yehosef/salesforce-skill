#!/bin/bash
# Run All Tests
#
# Executes the complete test suite for the Salesforce skill.
#
# Usage:
#   ./run-all-tests.sh [--verbose] [--coverage]

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

VERBOSE=false
COVERAGE=false
FAILED=0
PASSED=0

# Parse arguments
for arg in "$@"; do
    case $arg in
        --verbose)
            VERBOSE=true
            ;;
        --coverage)
            COVERAGE=true
            ;;
        --help)
            echo "Usage: $0 [--verbose] [--coverage]"
            echo ""
            echo "Options:"
            echo "  --verbose   Show detailed output"
            echo "  --coverage  Generate coverage report"
            echo "  --help      Show this help"
            exit 0
            ;;
    esac
done

print_header() {
    echo -e "${BLUE}===================================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}===================================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

print_header "Salesforce Skill Test Suite"

# Run Python unit tests
print_header "Python Unit Tests"

if [ "$COVERAGE" = true ]; then
    if command -v pytest &> /dev/null; then
        pytest "${TEST_DIR}/unit/" --cov=scripts --cov-report=html --cov-report=term
        TEST_RESULT=$?
    else
        python3 -m unittest discover -s "${TEST_DIR}/unit" -p "test_*.py"
        TEST_RESULT=$?
    fi
else
    if command -v pytest &> /dev/null; then
        pytest "${TEST_DIR}/unit/" -v
        TEST_RESULT=$?
    else
        python3 -m unittest discover -s "${TEST_DIR}/unit" -p "test_*.py"
        TEST_RESULT=$?
    fi
fi

if [ $TEST_RESULT -eq 0 ]; then
    print_success "Python unit tests passed"
    ((PASSED++))
else
    print_error "Python unit tests failed"
    ((FAILED++))
fi

echo ""

# Run shell integration tests
print_header "Shell Integration Tests"

for test_script in "${TEST_DIR}"/integration/*.sh; do
    if [ -f "$test_script" ]; then
        test_name=$(basename "$test_script")
        echo "Running ${test_name}..."

        if [ "$VERBOSE" = true ]; then
            bash "$test_script"
            TEST_RESULT=$?
        else
            bash "$test_script" > /dev/null 2>&1
            TEST_RESULT=$?
        fi

        if [ $TEST_RESULT -eq 0 ]; then
            print_success "${test_name} passed"
            ((PASSED++))
        else
            print_error "${test_name} failed"
            ((FAILED++))
        fi
    fi
done

echo ""

# Summary
print_header "Test Summary"

echo "Total tests: $((PASSED + FAILED))"
echo -e "${GREEN}Passed: ${PASSED}${NC}"
echo -e "${RED}Failed: ${FAILED}${NC}"

echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed! ✓${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed. ✗${NC}"
    exit 1
fi
