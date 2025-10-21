#!/bin/bash
# Seed a scratch org with test data from another org
# Uses SFDMU (Salesforce Data Move Utility)
#
# Requirements:
#   - Salesforce CLI (sf) v2.x+ installed
#   - SFDMU plugin installed: sf plugins install sfdmu
#   - Authenticated to both source and target orgs
#   - npm installed (for alternative SFDMU install)
#
# Safety: ⚠️ DESTRUCTIVE - WRITES DATA
#   This script WRITES DATA to the target org.
#   Use only on scratch orgs or test environments.
#
# Usage:
#   ./seed_scratch_org.sh dev-sandbox my-scratch
#   ./seed_scratch_org.sh production my-scratch ./sfdmu-config
#
# Installation:
#   sf plugins install sfdmu
#   OR: npm install -g sfdmu

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

if [ $# -lt 2 ]; then
    echo "Usage: seed_scratch_org.sh <source-org> <target-scratch-org> [config-path]"
    echo ""
    echo "Seeds a scratch org with data from another org using SFDMU."
    echo ""
    echo "Examples:"
    echo "  seed_scratch_org.sh dev-sandbox my-scratch"
    echo "  seed_scratch_org.sh production my-scratch ./sfdmu-config"
    echo ""
    echo "Prerequisites:"
    echo "  - SFDMU plugin must be installed: sf plugins install sfdmu"
    echo "  - Or use: npm install -g sfdmu"
    exit 1
fi

SOURCE_ORG=$1
TARGET_ORG=$2
CONFIG_PATH=${3:-"./data-seed-config"}

echo -e "${BLUE}🌱 Seeding scratch org with data...${NC}"
echo "Source: $SOURCE_ORG"
echo "Target: $TARGET_ORG"
echo ""

# Check if SFDMU is installed
if ! command -v sfdmu &> /dev/null && ! sf sfdmu --help &> /dev/null 2>&1; then
    echo -e "${RED}❌ SFDMU not found!${NC}"
    echo ""
    echo "Please install SFDMU first:"
    echo ""
    echo -e "${YELLOW}Option 1: As sf plugin (recommended)${NC}"
    echo "  sf plugins install sfdmu"
    echo ""
    echo -e "${YELLOW}Option 2: As npm package${NC}"
    echo "  npm install -g sfdmu"
    echo ""
    echo "After installation, run this script again."
    exit 1
fi

# Check if config directory exists
if [ ! -d "$CONFIG_PATH" ]; then
    echo -e "${YELLOW}📝 Config directory not found. Creating default configuration...${NC}"
    mkdir -p "$CONFIG_PATH"

    # Create default export.json for SFDMU
    cat > "$CONFIG_PATH/export.json" <<'EOF'
{
  "orgs": [
    {
      "name": "source",
      "isSource": true
    },
    {
      "name": "target",
      "isTarget": true
    }
  ],
  "objects": [
    {
      "query": "SELECT Id, Name, Industry, Type, BillingStreet, BillingCity, BillingState, BillingPostalCode, BillingCountry FROM Account WHERE CreatedDate = LAST_N_DAYS:90",
      "operation": "Upsert",
      "externalId": "Name"
    },
    {
      "query": "SELECT Id, FirstName, LastName, Email, Phone, AccountId FROM Contact WHERE CreatedDate = LAST_N_DAYS:90",
      "operation": "Upsert",
      "externalId": "Email"
    },
    {
      "query": "SELECT Id, Name, StageName, CloseDate, Amount, AccountId FROM Opportunity WHERE CreatedDate = LAST_N_DAYS:90",
      "operation": "Insert"
    }
  ]
}
EOF

    echo -e "${GREEN}✓ Created default configuration at: $CONFIG_PATH/export.json${NC}"
    echo ""
    echo -e "${YELLOW}📋 Default objects included:${NC}"
    echo "  - Account (last 90 days)"
    echo "  - Contact (last 90 days)"
    echo "  - Opportunity (last 90 days)"
    echo ""
    echo "You can customize $CONFIG_PATH/export.json to include your custom objects."
    echo ""
fi

# Run SFDMU
echo -e "${BLUE}🚀 Running SFDMU data migration...${NC}"
echo ""

# Try sf plugin first, fall back to standalone command
if sf sfdmu --help &> /dev/null 2>&1; then
    sf sfdmu run --sourceusername "$SOURCE_ORG" --targetusername "$TARGET_ORG" --path "$CONFIG_PATH"
else
    sfdmu run --sourceusername "$SOURCE_ORG" --targetusername "$TARGET_ORG" --path "$CONFIG_PATH"
fi

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Data seeding complete!${NC}"
    echo ""
    echo -e "${BLUE}Summary:${NC}"

    # Show record counts in target org
    echo "Verifying data in $TARGET_ORG..."

    ACCOUNT_COUNT=$(sf data query -q "SELECT COUNT(Id) cnt FROM Account" -o "$TARGET_ORG" --json 2>/dev/null | grep -o '"cnt":[0-9]*' | grep -o '[0-9]*' || echo "0")
    CONTACT_COUNT=$(sf data query -q "SELECT COUNT(Id) cnt FROM Contact" -o "$TARGET_ORG" --json 2>/dev/null | grep -o '"cnt":[0-9]*' | grep -o '[0-9]*' || echo "0")
    OPP_COUNT=$(sf data query -q "SELECT COUNT(Id) cnt FROM Opportunity" -o "$TARGET_ORG" --json 2>/dev/null | grep -o '"cnt":[0-9]*' | grep -o '[0-9]*' || echo "0")

    echo "  Accounts: $ACCOUNT_COUNT"
    echo "  Contacts: $CONTACT_COUNT"
    echo "  Opportunities: $OPP_COUNT"
    echo ""
    echo -e "${GREEN}🎉 Scratch org is ready for development!${NC}"
else
    echo -e "${RED}❌ Data seeding failed${NC}"
    echo ""
    echo "Check the error messages above for details."
    echo "Common issues:"
    echo "  - Required fields missing in export.json"
    echo "  - Validation rules blocking inserts"
    echo "  - Field-level security issues"
    echo ""
    echo "To debug, check the SFDMU logs in: $CONFIG_PATH"
    exit 1
fi

# Show next steps
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  1. Open scratch org: sf org open -o $TARGET_ORG"
echo "  2. Verify data: Check Account, Contact, Opportunity records"
echo "  3. Start developing!"
echo ""
echo -e "${YELLOW}💡 Tip: Save this configuration for future use!${NC}"
echo "   The config is at: $CONFIG_PATH/export.json"
