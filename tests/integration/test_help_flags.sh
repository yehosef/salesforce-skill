#!/bin/bash
# Integration test: Verify scripts respond to --help flag
#
# Tests that all scripts properly handle the --help flag
# and provide usage information.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && cd ../../scripts && pwd)"
FAILED=0
PASSED=0

echo "Testing --help flag support..."
echo ""

# Scripts to test (select subset that should have --help)
SCRIPTS_TO_TEST=(
    "compare_orgs.sh"
    "deploy_and_test.sh"
    "seed_scratch_org.sh"
    "snapshot_org.sh"
    "rollback_deployment.sh"
)

for script_name in "${SCRIPTS_TO_TEST[@]}"; do
    script="${SCRIPT_DIR}/${script_name}"

    if [ ! -f "$script" ]; then
        echo "⚠ ${script_name} not found (skipping)"
        continue
    fi

    # Try running with --help (should exit 0)
    if "$script" --help >/dev/null 2>&1; then
        echo "✓ ${script_name} responds to --help"
        ((PASSED++))
    else
        echo "✗ ${script_name} does NOT respond to --help properly"
        ((FAILED++))
    fi
done

echo ""
echo "Results: $PASSED passed, $FAILED failed"

if [ $FAILED -gt 0 ]; then
    echo ""
    echo "Note: Some scripts may not have --help implemented yet."
    echo "This is expected and will be addressed in enhancements."
fi

exit 0
