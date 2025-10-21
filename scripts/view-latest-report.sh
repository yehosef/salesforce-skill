#!/bin/bash
# View the latest report for a tool
# Usage: ./view-latest-report.sh org-comparison

TOOL=${1:?Usage: view-latest-report.sh <tool-name>}

# Find project root
PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
REPORT_FILE="$PROJECT_ROOT/.claude/reports/$TOOL/runs/latest/report.md"

if [[ ! -f "$REPORT_FILE" ]]; then
    echo "❌ No report found for: $TOOL"
    echo "Available reports:"
    ls -d "$PROJECT_ROOT/.claude/reports"/*/ 2>/dev/null | xargs -n1 basename || echo "  (none)"
    exit 1
fi

# Use less if available, cat otherwise
if command -v less &> /dev/null; then
    less "$REPORT_FILE"
else
    cat "$REPORT_FILE"
fi
