#!/bin/bash
# Compare Salesforce orgs and generate a stored report
#
# Requirements:
#   - Salesforce CLI (sf) v2.x+ installed
#   - Authenticated to both source and target orgs
#   - ~/.claude/lib/report-manager.sh available
#   - jq installed (for JSON processing)
#   - bash, grep, diff, sed, sort commands available
#
# Safety: READ-ONLY
#   This script only reads and compares metadata.
#   Saves reports to .claude/reports/ directory.
#   No changes are made to either org.
#
# Usage:
#   ./compare_orgs_and_report.sh sandbox production
#   ./compare_orgs_and_report.sh dev uat "ApexClass,ApexTrigger"
#
# Output:
#   Reports saved to: .claude/reports/org-comparison/runs/<timestamp>/

set -e

# Get script directory and source report manager
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(dirname "$SCRIPT_DIR")"
source "$SKILL_ROOT/lib/report-manager.sh"

# Parse arguments
SOURCE_ORG=${1:?Usage: compare_orgs_and_report.sh <source-org> <target-org> [metadata-types]}
TARGET_ORG=${2:?}
METADATA_TYPE=${3:-"ApexClass,ApexTrigger,AuraDefinitionBundle,LightningComponentBundle"}

# Initialize report
METADATA=$(cat <<EOF
{
    "tool": "org-comparison",
    "source_org": "$SOURCE_ORG",
    "target_org": "$TARGET_ORG",
    "metadata_types": "$METADATA_TYPE"
}
EOF
)

REPORT_DIR=$(create_report_run "org-comparison" "$METADATA")
echo -e "📊 Creating comparison report..."
echo -e "Run ID: $REPORT_RUN_ID"
echo ""

# Temporary directories
TEMP_DIR=$(mktemp -d)
SOURCE_DIR="$TEMP_DIR/source"
TARGET_DIR="$TEMP_DIR/target"
trap "rm -rf $TEMP_DIR" EXIT

# Create directories
mkdir -p "$SOURCE_DIR" "$TARGET_DIR"

# Retrieve from source org
echo -e "📥 Retrieving from $SOURCE_ORG..."
sf project retrieve start -m "$METADATA_TYPE" -o "$SOURCE_ORG" -d "$SOURCE_DIR" --ignore-conflicts > /dev/null 2>&1 || true

# Retrieve from target org
echo -e "📥 Retrieving from $TARGET_ORG..."
sf project retrieve start -m "$METADATA_TYPE" -o "$TARGET_ORG" -d "$TARGET_DIR" --ignore-conflicts > /dev/null 2>&1 || true

# Find all components
echo -e "🔍 Analyzing differences..."

# Components only in source
ONLY_IN_SOURCE=$(find "$SOURCE_DIR" -type f \( -name "*.cls" -o -name "*.trigger" -o -name "*.cmp" -o -name "*.js" -o -name "*.xml" \) 2>/dev/null | while read file; do
    RELATIVE_PATH=$(echo "$file" | sed "s|$SOURCE_DIR/||")
    if [ ! -f "$TARGET_DIR/$RELATIVE_PATH" ]; then
        echo "$RELATIVE_PATH"
    fi
done)

# Components only in target
ONLY_IN_TARGET=$(find "$TARGET_DIR" -type f \( -name "*.cls" -o -name "*.trigger" -o -name "*.cmp" -o -name "*.js" -o -name "*.xml" \) 2>/dev/null | while read file; do
    RELATIVE_PATH=$(echo "$file" | sed "s|$TARGET_DIR/||")
    if [ ! -f "$SOURCE_DIR/$RELATIVE_PATH" ]; then
        echo "$RELATIVE_PATH"
    fi
done)

# Components with differences
DIFFERENCES=$(find "$SOURCE_DIR" -type f \( -name "*.cls" -o -name "*.trigger" -o -name "*.cmp" -o -name "*.js" -o -name "*.xml" \) 2>/dev/null | while read file; do
    RELATIVE_PATH=$(echo "$file" | sed "s|$SOURCE_DIR/||")
    TARGET_FILE="$TARGET_DIR/$RELATIVE_PATH"

    if [ -f "$TARGET_FILE" ]; then
        if ! diff -q "$file" "$TARGET_FILE" > /dev/null 2>&1; then
            echo "$RELATIVE_PATH"
            # Save individual diff
            save_diff "$(basename "$RELATIVE_PATH").diff" "$file" "$TARGET_FILE" || true
        fi
    fi
done)

# Count components
SOURCE_COUNT=$(find "$SOURCE_DIR" -type f \( -name "*.cls" -o -name "*.trigger" -o -name "*.cmp" -o -name "*.js" -o -name "*.xml" \) 2>/dev/null | wc -l | tr -d ' ')
TARGET_COUNT=$(find "$TARGET_DIR" -type f \( -name "*.cls" -o -name "*.trigger" -o -name "*.cmp" -o -name "*.js" -o -name "*.xml" \) 2>/dev/null | wc -l | tr -d ' ')

# Determine status
DIFFERENCES_COUNT=$(echo "$DIFFERENCES" | grep -c . || echo 0)
ONLY_SOURCE_COUNT=$(echo "$ONLY_IN_SOURCE" | grep -c . || echo 0)
ONLY_TARGET_COUNT=$(echo "$ONLY_IN_TARGET" | grep -c . || echo 0)
TOTAL_DIFFS=$((DIFFERENCES_COUNT + ONLY_SOURCE_COUNT + ONLY_TARGET_COUNT))

STATUS="success"
[[ $TOTAL_DIFFS -gt 0 ]] && STATUS="warning"

# Generate markdown report
cat > "$REPORT_DIR/report.md" <<REPORT
# Salesforce Org Comparison Report

**Date**: $(date)
**Source Org**: $SOURCE_ORG
**Target Org**: $TARGET_ORG
**Metadata Types**: $METADATA_TYPE

---

## Summary

| Metric | Value |
|--------|-------|
| Source Components | $SOURCE_COUNT |
| Target Components | $TARGET_COUNT |
| Identical | $((SOURCE_COUNT - DIFFERENCES_COUNT - ONLY_SOURCE_COUNT)) |
| Differences Found | $TOTAL_DIFFS |
| Only in Source | $ONLY_SOURCE_COUNT |
| Only in Target | $ONLY_TARGET_COUNT |
| Code Differences | $DIFFERENCES_COUNT |

**Status**: $([ $TOTAL_DIFFS -eq 0 ] && echo "✅ IDENTICAL" || echo "⚠️ DIFFERENCES FOUND")

---

## Components Only in $SOURCE_ORG

$(if [ -z "$ONLY_IN_SOURCE" ]; then
    echo "(none)"
else
    echo "$ONLY_IN_SOURCE" | sed 's/^/- /'
fi)

---

## Components Only in $TARGET_ORG

$(if [ -z "$ONLY_IN_TARGET" ]; then
    echo "(none)"
else
    echo "$ONLY_IN_TARGET" | sed 's/^/- /'
fi)

---

## Components with Code Differences

$(if [ -z "$DIFFERENCES" ]; then
    echo "✅ All common components are identical!"
else
    echo "$DIFFERENCES" | sed 's/^/- /'
    echo ""
    echo "Detailed diffs available in \`diffs/\` directory"
fi)

---

## Detailed Diffs

To view differences for a specific component:
\`\`\`bash
cat diffs/ComponentName.diff
\`\`\`

---

## Commands to Compare Again

**Compare same orgs again**:
\`\`\`bash
$SKILL_ROOT/scripts/compare_orgs_and_report.sh $SOURCE_ORG $TARGET_ORG
\`\`\`

**Compare with different metadata types**:
\`\`\`bash
$SKILL_ROOT/scripts/compare_orgs_and_report.sh $SOURCE_ORG $TARGET_ORG "ApexClass,ApexTrigger"
\`\`\`

---

Generated by: Salesforce Skill Report Manager
REPORT

# Save metadata with counts
jq --arg diffs "$TOTAL_DIFFS" --arg status "$STATUS" \
    '.differences_found = ($diffs | tonumber) | .status = $status' \
    "$REPORT_DIR/metadata.json" > "$REPORT_DIR/metadata.json.tmp" && \
    mv "$REPORT_DIR/metadata.json.tmp" "$REPORT_DIR/metadata.json"

# Finalize report
finalize_report "org-comparison" "$STATUS"

# Summary
echo ""
echo "📊 Comparison Summary"
echo "  Source Org: $SOURCE_ORG ($SOURCE_COUNT components)"
echo "  Target Org: $TARGET_ORG ($TARGET_COUNT components)"
echo "  Differences: $TOTAL_DIFFS"
echo ""
echo "📁 Report Location: $REPORT_DIR/report.md"
echo "📝 View Report: ./scripts/view-latest-report.sh org-comparison"
echo "📋 List All Runs: ./scripts/list-reports.sh org-comparison"
