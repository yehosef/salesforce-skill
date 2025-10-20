# Salesforce Rollback & Disaster Recovery

Complete guide for rolling back deployments, recovering from failed changes, and implementing backup strategies.

## Table of Contents

1. [Overview](#overview)
2. [Pre-Deployment Backups](#pre-deployment-backups)
3. [Rollback Strategies](#rollback-strategies)
4. [Emergency Rollback Procedures](#emergency-rollback-procedures)
5. [Data Recovery](#data-recovery)
6. [Metadata Recovery](#metadata-recovery)
7. [Version Control Integration](#version-control-integration)
8. [Testing Rollbacks](#testing-rollbacks)
9. [Backup Best Practices](#backup-best-practices)
10. [Automation Scripts](#automation-scripts)

---

## Overview

### Why Rollback Planning Matters

Common deployment failures:
- Breaking changes in production
- Data corruption from triggers
- Validation rules blocking critical operations
- Performance degradation after deployment
- Integration failures

**Golden Rule**: Never deploy to production without a rollback plan.

---

## Pre-Deployment Backups

### What to Backup

**Metadata**:
- All components being deployed
- Related/dependent components
- Configuration (custom settings, metadata types)

**Data** (if deployment affects data):
- Records modified by triggers
- Records affected by validation rules
- Related child records

### Creating Metadata Snapshots

Use the `snapshot_org.sh` script:

```bash
# Create snapshot before deployment
./scripts/snapshot_org.sh production ./backups/prod-snapshot-2025-10-20

# Snapshot includes:
# - All metadata from manifest
# - Timestamp for reference
# - Git commit hash (if in repo)
```

Manual snapshot:

```bash
# Retrieve all metadata for components you're deploying
sf project retrieve start \
  -m "ApexClass:MyClass,ApexTrigger:MyTrigger,CustomObject:Custom__c" \
  -o production \
  -d ./backup-prod-2025-10-20
```

### Creating Data Backups

**Option 1**: Data Loader Export

```bash
# Export affected records
sf data export bulk \
  -q "SELECT Id, Name, Status__c FROM Custom__c WHERE Status__c = 'Active'" \
  -o production \
  --output-dir ./data-backup
```

**Option 2**: Weekly Data Export

Setup → Data Export → Schedule Export
- All data weekly
- Critical objects daily

---

## Rollback Strategies

### Strategy 1: Quick Rollback (Deploy Previous Version)

**Best for**: Apex classes, triggers, Visualforce/LWC components

**Steps**:
1. Locate previous version (from backup or Git)
2. Deploy previous version to production
3. Run validation tests
4. Monitor for 24 hours

**Example**:

```bash
# Rollback to previous commit
git checkout abc123 -- src/classes/MyClass.cls

# Deploy
sf project deploy start -d src/classes/MyClass.cls -o production
```

**Pros**: Fast, simple
**Cons**: Only works for metadata, not data

### Strategy 2: Destructive Changes

**Best for**: Removing problematic components

**Steps**:
1. Create destructiveChanges.xml
2. Deploy with empty package.xml
3. Verify removal

**Example destructiveChanges.xml**:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>ProblematicClass</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>ProblematicTrigger</members>
        <name>ApexTrigger</name>
    </types>
    <version>64.0</version>
</Package>
```

```bash
# Deploy destructive changes
sf project deploy start \
  --post-destructive-changes ./destructiveChanges.xml \
  -d ./empty-pkg \
  -o production
```

**Pros**: Complete removal
**Cons**: Cannot be undone, requires manual recreation

### Strategy 3: Feature Flags

**Best for**: Proactive rollback capability

**Implementation**:

```apex
// Check custom setting before executing new code
if (FeatureFlags__c.getInstance().New_Validation_Enabled__c) {
    // New logic
} else {
    // Old logic (fallback)
}
```

**Rollback**:
1. Navigate to Setup → Custom Settings → Feature Flags
2. Uncheck "New_Validation_Enabled__c"
3. Immediate rollback without deployment

**Pros**: Instant, no deployment needed
**Cons**: Requires planning ahead

### Strategy 4: Data Rollback (Restore from Backup)

**Best for**: Data corruption, mass update errors

**Steps**:
1. Export corrupted data
2. Restore from backup CSV
3. Validate restored data

**Example**:

```bash
# Restore data from backup
sf data import bulk \
  --sobject Account \
  --file ./backup-accounts.csv \
  -o production
```

**Pros**: Precise data recovery
**Cons**: Time-consuming for large volumes

---

## Emergency Rollback Procedures

### Scenario 1: Production Outage Due to Deployment

**Symptoms**:
- Users unable to access critical functions
- Errors on page load
- Integration failures

**Emergency Response** (5-minute plan):

```bash
# 1. Create snapshot of current state (if not already done)
./scripts/snapshot_org.sh production ./emergency-backup

# 2. Rollback to last known good state
./scripts/rollback_deployment.sh production ./backup-prod-previous

# 3. Verify critical functions
# - Test key user flows
# - Check integrations
# - Run smoke tests

# 4. Communicate with stakeholders
```

### Scenario 2: Trigger Causing Data Corruption

**Symptoms**:
- Incorrect field values after save
- Child records being deleted unexpectedly
- Calculation errors

**Emergency Response**:

```apex
// Option 1: Disable trigger immediately
// Setup → Apex Triggers → Deactivate

// Option 2: Add bypass logic (requires quick deploy)
trigger MyTrigger on Account (before update) {
    if (Utils.isTriggerDisabled('MyTrigger')) return; // Emergency bypass
    // Trigger logic
}
```

```bash
# Restore corrupted data
./scripts/emergency_rollback.py Account ./data-backup/accounts.csv production
```

### Scenario 3: Validation Rule Blocking Critical Operations

**Symptoms**:
- Cannot save records
- Order processing stopped
- Integration failures

**Emergency Response**:

```bash
# Deactivate validation rule via metadata
# 1. Retrieve validation rule
sf project retrieve start \
  -m "ValidationRule:Account.Critical_Validation" \
  -o production \
  -d ./temp

# 2. Edit and set <active>false</active>

# 3. Deploy
sf project deploy start -d ./temp -o production
```

Faster: Setup → Object Manager → Validation Rules → Deactivate

---

## Data Recovery

### Recovering Deleted Records

**Recycle Bin** (up to 15 days):

```bash
# Query recycle bin
sf data query \
  -q "SELECT Id, Name FROM Account WHERE IsDeleted = true" \
  -o production \
  --use-tooling-api

# Restore via UI
# Setup → Recycle Bin → Select → Undelete
```

### Recovering from Mass Update Errors

```bash
# 1. Export current (corrupted) data
sf data export bulk \
  -q "SELECT Id, Field1__c, Field2__c FROM Custom__c" \
  -o production \
  --output-dir ./corrupted-data

# 2. Compare with backup
# Use Excel/Python to identify differences

# 3. Restore correct values
sf data import bulk \
  --sobject Custom__c \
  --file ./corrected-data.csv \
  -o production
```

### Point-in-Time Recovery

If you have daily backups:

1. Identify last good backup date
2. Restore that backup
3. Re-apply valid changes made since backup

---

## Metadata Recovery

### Recovering Overwritten Code

**From Git**:

```bash
# View file history
git log --follow src/classes/MyClass.cls

# Restore specific version
git checkout abc123 -- src/classes/MyClass.cls

# Deploy
sf project deploy start -d src/classes/MyClass.cls -o production
```

**From Salesforce Backup**:

```bash
# If you created snapshot before deployment
cp ./backup-prod-previous/classes/MyClass.cls ./src/classes/MyClass.cls

# Deploy
sf project deploy start -d src/classes/MyClass.cls -o production
```

### Recovering Deleted Metadata

Retrieve from another environment:

```bash
# Retrieve from sandbox
sf project retrieve start \
  -m "ApexClass:DeletedClass" \
  -o sandbox \
  -d ./recovery

# Deploy to production
sf project deploy start -d ./recovery -o production
```

---

## Version Control Integration

### Git-Based Rollback

**Best Practice**: Tag every production deployment

```bash
# Before deployment
git tag prod-deploy-2025-10-20
git push origin prod-deploy-2025-10-20

# Rollback to previous tag
git checkout prod-deploy-2025-10-19

# Deploy previous version
sf project deploy start -d src/ -o production
```

### Deployment History Tracking

Maintain deployment log:

```bash
# deployments.log
2025-10-20 14:30 | Deployed MyClass v2.1 | commit abc123 | success
2025-10-20 16:45 | Deployed MyTrigger v3.0 | commit def456 | FAILED
2025-10-20 17:00 | Rollback to abc123 | success
```

---

## Testing Rollbacks

### Rollback Testing Checklist

Before production deployment:

- [ ] Create full metadata backup
- [ ] Test rollback procedure in sandbox
- [ ] Document rollback steps
- [ ] Identify rollback decision criteria
- [ ] Assign rollback authority (who can authorize)
- [ ] Test data restoration process
- [ ] Verify rollback time estimate

### Sandbox Rollback Test

```bash
# 1. Deploy to sandbox
sf project deploy start -d src/ -o sandbox

# 2. Verify issues (simulate production failure)

# 3. Execute rollback
./scripts/rollback_deployment.sh sandbox ./backup-sandbox

# 4. Verify rollback success
# - Run tests
# - Check data integrity
# - Verify UI functionality
```

---

## Backup Best Practices

### Backup Frequency

**Metadata**:
- Before every production deployment
- Weekly scheduled backups
- After major configuration changes

**Data**:
- Daily for critical objects (Accounts, Opportunities, Payments)
- Weekly for all data
- Real-time backup for high-value transactions

### Backup Storage

**Requirements**:
- Off-site storage (not in Salesforce)
- Version control (Git for metadata)
- Encrypted (for sensitive data)
- Retention policy (90 days minimum for compliance)

**Storage Options**:
- Git repository (metadata)
- AWS S3 / Google Cloud Storage (data exports)
- Local file server (short-term backups)
- Salesforce Shield Backup (if available)

### Backup Validation

Monthly:
- Restore test backup to scratch org
- Verify all components deploy successfully
- Check data integrity
- Test critical workflows

---

## Automation Scripts

This skill includes automation scripts for rollback and backup:

### snapshot_org.sh

Create metadata snapshot before deployment:

```bash
./scripts/snapshot_org.sh production ./backups/prod-2025-10-20

# Creates timestamped backup with:
# - All deployment metadata
# - Manifest file
# - Git commit hash
```

### rollback_deployment.sh

Rollback to previous deployment:

```bash
./scripts/rollback_deployment.sh production ./backups/prod-2025-10-19

# Automatically:
# - Validates backup
# - Creates pre-rollback snapshot
# - Deploys previous version
# - Runs tests
# - Reports success/failure
```

### emergency_rollback.py

Quick data restoration:

```bash
./scripts/emergency_rollback.py Account ./backup-accounts.csv production

# Restores data from CSV backup
# Shows diff before applying
# Validates after restoration
```

---

## Rollback Decision Matrix

| Severity | Symptoms | Response Time | Rollback Method |
|----------|----------|---------------|-----------------|
| **Critical** | Production down, data loss | Immediate | Emergency rollback script |
| **High** | Major features broken, integrations failing | <30 min | Deploy previous version |
| **Medium** | Non-critical errors, degraded performance | <2 hours | Targeted fix or rollback |
| **Low** | UI issues, minor bugs | Next deployment | Include fix in next release |

---

## Post-Rollback Actions

After rolling back:

1. **Root Cause Analysis**:
   - What went wrong?
   - Why didn't testing catch it?
   - How to prevent in future?

2. **Communication**:
   - Notify stakeholders of rollback
   - Explain impact and timeline
   - Provide updated deployment plan

3. **Fix and Redeploy**:
   - Fix issue in sandbox
   - Test thoroughly
   - Schedule new deployment

4. **Update Procedures**:
   - Document what was learned
   - Update deployment checklist
   - Improve testing process

---

## Additional Resources

**Salesforce Documentation**:
- [Deployment Best Practices](https://developer.salesforce.com/docs/atlas.en-us.packagingGuide.meta/packagingGuide/packaging_intro.htm)
- [Data Backup & Restore](https://help.salesforce.com/s/articleView?id=sf.admin_data_backup.htm)

**Related Guides in This Skill**:
- `deployment-guide.md` - Pre-deployment preparation
- `common-errors.md` - Troubleshooting deployment failures
- `data-migration-guide.md` - Data backup and restoration

---

**Last Updated**: Phase 2 - October 2025
