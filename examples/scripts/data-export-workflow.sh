#!/bin/bash
# Data Export and Analysis Workflow Example
#
# Demonstrates exporting data, finding duplicates, and generating reports.

set -euo pipefail

ORG="my-org"
EXPORT_DIR="./data-exports/$(date +%Y%m%d)"

echo "=== Data Export and Analysis Workflow ==="
echo ""

# Step 1: Export data
echo "Step 1: Exporting Account and Contact data..."
mkdir -p "$EXPORT_DIR"
./scripts/export_data.py "Account,Contact" "$ORG" "$EXPORT_DIR"
echo "✓ Data exported to $EXPORT_DIR"
echo ""

# Step 2: Find duplicate contacts by email
echo "Step 2: Finding duplicate contacts by Email..."
./scripts/find_duplicates.py Contact "Email" "$ORG"
echo ""

# Step 3: Find duplicate accounts by name and city
echo "Step 3: Finding duplicate accounts by Name and BillingCity..."
./scripts/find_duplicates.py Account "Name,BillingCity" "$ORG"
echo ""

# Step 4: Check org health
echo "Step 4: Running org health check..."
./scripts/org_health_check.py "$ORG"

echo ""
echo "=== Analysis Complete ==="
echo ""
echo "Next steps:"
echo "  - Review duplicate reports in current directory"
echo "  - Review exported data in $EXPORT_DIR"
echo "  - Clean up duplicates using Salesforce UI or Data Loader"
