#!/bin/bash
# Compare two report runs side-by-side
#
# Requirements:
#   - bash, jq, diff commands available
#   - Report runs exist in .claude/reports/<tool>/runs/
#   - Two run IDs to compare
#
# Safety: READ-ONLY
#   This script only reads and compares report files.
#
# Usage:
#   ./compare-reports.sh org-comparison 2025-10-21-1648 2025-10-24-0915
#   ./compare-reports.sh test-results run1 run2
#
# Output:
#   - Metadata comparison (JSON diff)
#   - Report text diff
#   - Artifact file differences
#   - Line count differences

TOOL=${1:?Usage: compare-reports.sh <tool> <run1> <run2>}
RUN1=${2:?}
RUN2=${3:?}

# Find project root
PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
REPORTS_DIR="$PROJECT_ROOT/.claude/reports"

# Resolve runs
RUN1_DIR="$REPORTS_DIR/$TOOL/runs/$RUN1"
RUN2_DIR="$REPORTS_DIR/$TOOL/runs/$RUN2"

# Validate
if [[ ! -d "$RUN1_DIR" ]]; then
    echo "❌ Run not found: $RUN1"
    exit 1
fi

if [[ ! -d "$RUN2_DIR" ]]; then
    echo "❌ Run not found: $RUN2"
    exit 1
fi

echo "📊 Comparing Reports"
echo "Tool: $TOOL"
echo "Run 1: $RUN1"
echo "Run 2: $RUN2"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""

# Compare metadata
echo "## Metadata Comparison"
echo ""
echo "Run 1 metadata:"
jq '.' "$RUN1_DIR/metadata.json" 2>/dev/null | sed 's/^/  /'

echo ""
echo "Run 2 metadata:"
jq '.' "$RUN2_DIR/metadata.json" 2>/dev/null | sed 's/^/  /'

echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""

# Compare reports
echo "## Report Diff"
echo ""
diff -u "$RUN1_DIR/report.md" "$RUN2_DIR/report.md" || true

echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""

# Show artifacts that differ
echo "## Artifact Differences"
echo ""

RUN1_ARTIFACTS=$(find "$RUN1_DIR/artifacts" -type f 2>/dev/null | sort)
RUN2_ARTIFACTS=$(find "$RUN2_DIR/artifacts" -type f 2>/dev/null | sort)

for artifact in $RUN1_ARTIFACTS; do
    artifact_name=${artifact##*/}
    run2_artifact="$RUN2_DIR/artifacts/$artifact_name"

    if [[ ! -f "$run2_artifact" ]]; then
        echo "Only in Run 1: $artifact_name"
    elif ! diff -q "$artifact" "$run2_artifact" > /dev/null 2>&1; then
        echo "Different: $artifact_name"
        echo "  Run 1: $(wc -l < "$artifact") lines"
        echo "  Run 2: $(wc -l < "$run2_artifact") lines"
    fi
done

for artifact in $RUN2_ARTIFACTS; do
    artifact_name=${artifact##*/}
    if [[ ! -f "$RUN1_DIR/artifacts/$artifact_name" ]]; then
        echo "Only in Run 2: $artifact_name"
    fi
done

echo ""
echo "✅ Comparison complete"
