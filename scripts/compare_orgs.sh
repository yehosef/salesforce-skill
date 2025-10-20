#!/bin/bash
# Compare metadata between two Salesforce orgs
# Shows what's different between source and target orgs

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

if [ $# -lt 2 ]; then
    echo "Usage: compare_orgs.sh <source-org> <target-org> [metadata-type]"
    echo ""
    echo "Compares metadata between two orgs and shows differences."
    echo ""
    echo "Examples:"
    echo "  compare_orgs.sh sandbox production"
    echo "  compare_orgs.sh sandbox production ApexClass"
    echo "  compare_orgs.sh dev-sandbox uat-sandbox \"ApexClass,ApexTrigger\""
    echo ""
    echo "Common metadata types:"
    echo "  ApexClass, ApexTrigger, AuraDefinitionBundle, LightningComponentBundle"
    echo "  CustomObject, Flow, ValidationRule, WorkflowRule"
    exit 1
fi

SOURCE_ORG=$1
TARGET_ORG=$2
METADATA_TYPE=${3:-"ApexClass,ApexTrigger,AuraDefinitionBundle,LightningComponentBundle"}

TEMP_DIR=$(mktemp -d)
SOURCE_DIR="$TEMP_DIR/source"
TARGET_DIR="$TEMP_DIR/target"

trap "rm -rf $TEMP_DIR" EXIT

echo -e "${BLUE}🔍 Comparing metadata between orgs...${NC}"
echo "Source: $SOURCE_ORG"
echo "Target: $TARGET_ORG"
echo "Types: $METADATA_TYPE"
echo ""

# Create directories
mkdir -p "$SOURCE_DIR"
mkdir -p "$TARGET_DIR"

# Retrieve from source org
echo -e "${BLUE}📥 Retrieving from $SOURCE_ORG...${NC}"
sf project retrieve start -m "$METADATA_TYPE" -o "$SOURCE_ORG" -d "$SOURCE_DIR" --ignore-conflicts > /dev/null 2>&1

if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠️  Warning: Some components may not exist in $SOURCE_ORG${NC}"
fi

# Retrieve from target org
echo -e "${BLUE}📥 Retrieving from $TARGET_ORG...${NC}"
sf project retrieve start -m "$METADATA_TYPE" -o "$TARGET_ORG" -d "$TARGET_DIR" --ignore-conflicts > /dev/null 2>&1

if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠️  Warning: Some components may not exist in $TARGET_ORG${NC}"
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo -e "${BLUE}   METADATA COMPARISON RESULTS${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo ""

# Find files only in source
echo -e "${GREEN}✓ Components only in $SOURCE_ORG (not in $TARGET_ORG):${NC}"
ONLY_IN_SOURCE=$(find "$SOURCE_DIR" -type f -name "*.cls" -o -name "*.trigger" -o -name "*.cmp" -o -name "*.js" 2>/dev/null | while read file; do
    RELATIVE_PATH=$(echo "$file" | sed "s|$SOURCE_DIR/||")
    if [ ! -f "$TARGET_DIR/$RELATIVE_PATH" ]; then
        echo "  - $RELATIVE_PATH"
    fi
done)

if [ -z "$ONLY_IN_SOURCE" ]; then
    echo -e "  ${YELLOW}(none)${NC}"
else
    echo "$ONLY_IN_SOURCE"
fi

echo ""

# Find files only in target
echo -e "${RED}✗ Components only in $TARGET_ORG (not in $SOURCE_ORG):${NC}"
ONLY_IN_TARGET=$(find "$TARGET_DIR" -type f -name "*.cls" -o -name "*.trigger" -o -name "*.cmp" -o -name "*.js" 2>/dev/null | while read file; do
    RELATIVE_PATH=$(echo "$file" | sed "s|$TARGET_DIR/||")
    if [ ! -f "$SOURCE_DIR/$RELATIVE_PATH" ]; then
        echo "  - $RELATIVE_PATH"
    fi
done)

if [ -z "$ONLY_IN_TARGET" ]; then
    echo -e "  ${YELLOW}(none)${NC}"
else
    echo "$ONLY_IN_TARGET"
fi

echo ""

# Find files with differences
echo -e "${YELLOW}⚠ Components that differ between orgs:${NC}"
DIFFERENCES=$(find "$SOURCE_DIR" -type f -name "*.cls" -o -name "*.trigger" -o -name "*.cmp" -o -name "*.js" 2>/dev/null | while read file; do
    RELATIVE_PATH=$(echo "$file" | sed "s|$SOURCE_DIR/||")
    TARGET_FILE="$TARGET_DIR/$RELATIVE_PATH"

    if [ -f "$TARGET_FILE" ]; then
        if ! diff -q "$file" "$TARGET_FILE" > /dev/null 2>&1; then
            echo "  - $RELATIVE_PATH"

            # Show line count difference
            SOURCE_LINES=$(wc -l < "$file" | tr -d ' ')
            TARGET_LINES=$(wc -l < "$TARGET_FILE" | tr -d ' ')
            DIFF_LINES=$((SOURCE_LINES - TARGET_LINES))

            if [ $DIFF_LINES -gt 0 ]; then
                echo "    ($SOURCE_ORG has +$DIFF_LINES lines)"
            elif [ $DIFF_LINES -lt 0 ]; then
                echo "    ($TARGET_ORG has +${DIFF_LINES#-} lines)"
            else
                echo "    (same line count, but content differs)"
            fi
        fi
    fi
done)

if [ -z "$DIFFERENCES" ]; then
    echo -e "  ${GREEN}✓ All common components are identical!${NC}"
else
    echo "$DIFFERENCES"
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo ""

# Summary counts
SOURCE_COUNT=$(find "$SOURCE_DIR" -type f \( -name "*.cls" -o -name "*.trigger" -o -name "*.cmp" -o -name "*.js" \) 2>/dev/null | wc -l | tr -d ' ')
TARGET_COUNT=$(find "$TARGET_DIR" -type f \( -name "*.cls" -o -name "*.trigger" -o -name "*.cmp" -o -name "*.js" \) 2>/dev/null | wc -l | tr -d ' ')

echo -e "${BLUE}Summary:${NC}"
echo "  $SOURCE_ORG: $SOURCE_COUNT components"
echo "  $TARGET_ORG: $TARGET_COUNT components"
echo ""

# Ask if user wants detailed diff
echo -e "${YELLOW}Would you like to see detailed diff for any file? (y/n)${NC}"
read -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Enter relative path of file to diff (or 'q' to quit):"
    read FILE_PATH

    if [ "$FILE_PATH" != "q" ] && [ "$FILE_PATH" != "" ]; then
        SOURCE_FILE="$SOURCE_DIR/$FILE_PATH"
        TARGET_FILE="$TARGET_DIR/$FILE_PATH"

        if [ -f "$SOURCE_FILE" ] && [ -f "$TARGET_FILE" ]; then
            echo ""
            echo -e "${BLUE}Diff for: $FILE_PATH${NC}"
            echo -e "${BLUE}═══════════════════════════════════════${NC}"
            diff -u "$SOURCE_FILE" "$TARGET_FILE" || true
        else
            echo -e "${RED}File not found in one or both orgs${NC}"
        fi
    fi
fi

echo ""
echo -e "${GREEN}✅ Comparison complete!${NC}"
echo ""
echo "Note: This comparison only checks file existence and content."
echo "It does not compare field-level metadata or org configuration."
