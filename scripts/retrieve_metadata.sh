#!/bin/bash
# Retrieve multiple metadata types from Salesforce org

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

if [ $# -lt 2 ]; then
    echo "Usage: retrieve_metadata.sh <org-alias> <type1> [type2] [type3] ..."
    echo ""
    echo "Examples:"
    echo "  retrieve_metadata.sh sandbox ApexClass ApexTrigger"
    echo "  retrieve_metadata.sh production AuraDefinitionBundle LightningComponentBundle"
    echo ""
    echo "Common types:"
    echo "  ApexClass, ApexTrigger, AuraDefinitionBundle, LightningComponentBundle"
    echo "  CustomObject, Flow, Layout, Profile, PermissionSet"
    exit 1
fi

ORG=$1
shift

echo -e "${BLUE}📥 Retrieving metadata from $ORG...${NC}"
echo ""

for TYPE in "$@"; do
    echo -e "${BLUE}Retrieving: $TYPE${NC}"
    sf project retrieve start -m "$TYPE" -o "$ORG"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $TYPE retrieved successfully${NC}"
    else
        echo -e "${RED}❌ Failed to retrieve $TYPE${NC}"
    fi
    echo ""
done

echo -e "${GREEN}✅ Retrieval complete!${NC}"
