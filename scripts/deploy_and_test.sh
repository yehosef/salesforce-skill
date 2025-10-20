#!/bin/bash
# Deploy metadata and run tests automatically with preview and validation

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

if [ $# -lt 2 ]; then
    echo "Usage: deploy_and_test.sh <path> <org-alias> [--dry-run]"
    echo ""
    echo "Examples:"
    echo "  deploy_and_test.sh src/aura/MyComponent/ sandbox"
    echo "  deploy_and_test.sh src/classes/ production --dry-run"
    exit 1
fi

PATH_TO_DEPLOY=$1
ORG_ALIAS=$2
DRY_RUN=""

if [ "$3" == "--dry-run" ]; then
    DRY_RUN="--dry-run"
    echo -e "${YELLOW}🔍 Validation mode (dry-run)${NC}"
fi

# Step 1: Preview deployment
echo -e "${BLUE}📦 Previewing deployment...${NC}"
sf project deploy preview -d "$PATH_TO_DEPLOY" -o "$ORG_ALIAS"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Preview failed${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Preview complete. Review the changes above.${NC}"
read -p "Continue with deployment? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}❌ Deployment cancelled${NC}"
    exit 0
fi

# Step 2: Deploy with tests
echo -e "${BLUE}🚀 Deploying to $ORG_ALIAS...${NC}"

if [ -n "$DRY_RUN" ]; then
    echo -e "${YELLOW}Running validation (dry-run) with tests...${NC}"
else
    echo -e "${YELLOW}Deploying with tests...${NC}"
fi

sf project deploy start \
    -d "$PATH_TO_DEPLOY" \
    -o "$ORG_ALIAS" \
    --test-level RunLocalTests \
    $DRY_RUN \
    --wait 30

if [ $? -eq 0 ]; then
    if [ -n "$DRY_RUN" ]; then
        echo -e "${GREEN}✅ Validation successful!${NC}"
    else
        echo -e "${GREEN}✅ Deployment complete!${NC}"
    fi
else
    echo -e "${RED}❌ Deployment failed${NC}"
    echo ""
    echo "Check the error output above for details."
    echo "You can also check deployment status with:"
    echo "  sf project deploy report -o $ORG_ALIAS"
    exit 1
fi
