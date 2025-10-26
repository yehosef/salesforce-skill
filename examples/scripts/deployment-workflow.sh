#!/bin/bash
# Complete Deployment Workflow Example
#
# This example demonstrates a full deployment workflow:
# 1. Create a snapshot
# 2. Compare environments
# 3. Deploy with tests
# 4. Verify deployment

set -euo pipefail

ORG="production"
SOURCE_DIR="src/classes"

echo "=== Salesforce Deployment Workflow Example ==="
echo ""

# Step 1: Create pre-deployment snapshot
echo "Step 1: Creating pre-deployment snapshot..."
./scripts/snapshot_org.sh "$ORG" "./backups/pre-deploy-$(date +%Y%m%d)"
echo "✓ Snapshot created"
echo ""

# Step 2: Compare with target org (if you have a staging org)
echo "Step 2: Comparing with staging environment..."
./scripts/compare_orgs.sh staging "$ORG"
echo ""
read -p "Continue with deployment? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 0
fi

# Step 3: Deploy with tests
echo "Step 3: Deploying to $ORG..."
./scripts/deploy_and_test.sh "$SOURCE_DIR" "$ORG"

if [ $? -eq 0 ]; then
    echo "✓ Deployment successful!"
else
    echo "✗ Deployment failed!"
    echo ""
    echo "To rollback:"
    echo "  ./scripts/rollback_deployment.sh $ORG ./backups/pre-deploy-$(date +%Y%m%d)"
    exit 1
fi

# Step 4: Run health check
echo ""
echo "Step 4: Running post-deployment health check..."
./scripts/org_health_check.py "$ORG"

echo ""
echo "=== Deployment Complete ==="
