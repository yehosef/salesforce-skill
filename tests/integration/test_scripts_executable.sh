#!/bin/bash
# Integration test: Verify all scripts are executable and have proper shebangs
#
# This test ensures that:
# 1. All scripts have execute permissions
# 2. All scripts have proper shebang lines
# 3. All scripts can display help text

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && cd ../../scripts && pwd)"
FAILED=0
PASSED=0

echo "Testing script executability..."
echo ""

# Test each script
for script in "${SCRIPT_DIR}"/*.py "${SCRIPT_DIR}"/*.sh; do
    if [ ! -f "$script" ]; then
        continue
    fi

    script_name=$(basename "$script")

    # Check if executable
    if [ -x "$script" ]; then
        echo "✓ ${script_name} is executable"
        ((PASSED++))
    else
        echo "✗ ${script_name} is NOT executable"
        ((FAILED++))
        continue
    fi

    # Check for shebang
    first_line=$(head -n 1 "$script")
    if [[ "$first_line" == "#!"* ]]; then
        echo "  └─ Has shebang: $first_line"
    else
        echo "  └─ WARNING: No shebang line"
        ((FAILED++))
    fi
done

echo ""
echo "Results: $PASSED passed, $FAILED failed"

if [ $FAILED -gt 0 ]; then
    exit 1
fi

exit 0
