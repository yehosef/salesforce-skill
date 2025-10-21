# Salesforce Skill Scripts

Complete documentation of all scripts in the salesforce-skill repository, including requirements, safety levels, and testing information.

## 📋 Quick Links

- **Safe to Run**: [Read-Only Scripts](#read-only-safe-scripts)
- **Dangerous**: [Destructive Scripts](#destructive-dangerous-scripts)
- **Requirements**: [Global Requirements](#global-requirements)
- **Testing Guide**: [How to Test](#testing-guide)

---

## 🛡️ Safety Levels

### ✅ READ-ONLY (Safe)
These scripts only **read** data and do not modify anything in Salesforce orgs.

### ⚠️ DESTRUCTIVE
These scripts **write, deploy, or modify** data/code in Salesforce orgs. Use with caution and always test in sandbox first.

---

## 📦 Global Requirements

**All scripts require:**
- Salesforce CLI (sf) v2.x+ installed
  - Install: `npm install -g @salesforce/cli`
- Authenticated Salesforce org(s) via: `sf org login web -a <org-alias>`
- bash shell (for .sh scripts)
- Python 3.8+ (for .py scripts)

**Optional utilities:**
- `jq` (for JSON processing - needed by report scripts)
- `git` (for git-based features)
- `npm` (for installing SFDMU and sf plugins)

---

## ✅ Read-Only (Safe) Scripts

Scripts in this section are safe to run - they only read data and make no changes to orgs.

### SOQL Query Tools

#### `query_soql.py`
Execute SOQL queries and format results as markdown tables.

**Requirements:**
- Salesforce CLI (sf)
- Python 3.8+
- Authenticated org

**Usage:**
```bash
./query_soql.py "SELECT Id, Name FROM Account LIMIT 5" my-org
./query_soql.py "SELECT Id FROM Contact WHERE Email != null" sandbox
```

**Safety:** READ-ONLY - Executes SELECT queries only.

---

#### `profile_soql.py`
Analyze SOQL query performance and get optimization recommendations.

**Requirements:**
- Salesforce CLI (sf)
- Python 3.8+
- Authenticated org

**Usage:**
```bash
./profile_soql.py "SELECT Id, Name FROM Account" my-org
./profile_soql.py "SELECT Id FROM Contact WHERE Email = 'test@example.com'" dev-sandbox
```

**Output:**
- Execution time
- Record count
- Query structure issues
- Optimization recommendations
- Index usage analysis

**Safety:** READ-ONLY - Executes SELECT queries only.

---

### Organization Analysis Tools

#### `org_health_check.py`
Comprehensive health check of Salesforce org.

**Requirements:**
- Salesforce CLI (sf)
- Python 3.8+
- Authenticated org

**Usage:**
```bash
./org_health_check.py my-org
./org_health_check.py production --detailed
```

**Output:**
- API limits usage
- Data storage usage
- Metadata counts
- Code coverage
- Health score (0-100)

**Safety:** READ-ONLY - Reads org metadata and limits only.

---

#### `org_limits_monitor.py`
Monitor Salesforce org limits and identify trending issues.

**Requirements:**
- Salesforce CLI (sf)
- Python 3.8+
- Authenticated org

**Usage:**
```bash
./org_limits_monitor.py my-org
./org_limits_monitor.py production --alert-threshold 80
```

**Safety:** READ-ONLY - Reads org limits only.

---

### Data Analysis Tools

#### `find_duplicates.py`
Find duplicate records based on specified fields.

**Requirements:**
- Salesforce CLI (sf)
- Python 3.8+
- Authenticated org
- Write permissions for export directory

**Usage:**
```bash
./find_duplicates.py Account "Name,BillingCity" my-org
./find_duplicates.py Contact "Email" dev-sandbox
./find_duplicates.py Custom_Object__c "External_Id__c" production
```

**Output:**
- CSV export of duplicate records
- Master record recommendations
- Merge analysis

**Safety:** READ-ONLY (with file export) - No org data modified.

---

#### `export_data.py`
Export Salesforce data with relationships preserved to CSV files.

**Requirements:**
- Salesforce CLI (sf)
- Python 3.8+
- Authenticated org
- Write permissions for output directory

**Usage:**
```bash
./export_data.py "Account,Contact,Opportunity" my-org ./exports
./export_data.py "Custom_Parent__c,Custom_Child__c" dev-sandbox ./data
```

**Output:**
- CSV files for each object
- External ID mappings
- Data Loader import plan

**Safety:** READ-ONLY (with file export) - No org data modified.

---

### Performance Analysis Tools

#### `analyze_apex_performance.py`
Analyze Apex debug logs for performance bottlenecks.

**Requirements:**
- Python 3.8+
- Salesforce debug log file

**How to get debug logs:**
1. Developer Console → Debug → Change Log Levels
2. Set Database = FINEST
3. Execute your code
4. Debug → View Log → Download

**Usage:**
```bash
./analyze_apex_performance.py ./debug-log.txt
./analyze_apex_performance.py ./logs/ApexLog-2025-10-20.log
```

**Output:**
- CPU time analysis by method
- Heap usage tracking
- SOQL query identification
- DML operation counts
- Governor limit summary

**Safety:** READ-ONLY (local file analysis) - No network or org access.

---

#### `find_slow_queries.sh`
Find slow SOQL queries in debug logs exceeding a threshold.

**Requirements:**
- bash shell
- Salesforce debug log files

**Usage:**
```bash
./find_slow_queries.sh ./logs 1000      # Find queries > 1 second
./find_slow_queries.sh ./debug 500      # Find queries > 500ms
```

**Safety:** READ-ONLY (local file analysis) - No network or org access.

---

### Metadata Comparison Tools

#### `compare_orgs.sh`
Compare metadata between two Salesforce orgs (interactive).

**Requirements:**
- Salesforce CLI (sf)
- Authenticated to both orgs
- bash, grep, diff, sed commands

**Usage:**
```bash
./compare_orgs.sh sandbox production
./compare_orgs.sh dev-sandbox uat-sandbox "ApexClass,ApexTrigger"
```

**Note:** Use `compare_orgs_and_report.sh` for automated reports.

**Safety:** READ-ONLY - Only reads and compares metadata.

---

#### `compare_orgs_and_report.sh`
Compare orgs and generate persistent reports with diffs.

**Requirements:**
- Salesforce CLI (sf)
- Authenticated to both orgs
- jq (for JSON processing)
- bash, grep, diff, sed commands
- ~/.claude/lib/report-manager.sh available

**Usage:**
```bash
./compare_orgs_and_report.sh sandbox production
./compare_orgs_and_report.sh dev uat "ApexClass,ApexTrigger"
```

**Output:**
Reports saved to: `.claude/reports/org-comparison/runs/<timestamp>/`

**Safety:** READ-ONLY - Only reads and compares metadata.

---

#### `retrieve_metadata.sh`
Retrieve multiple metadata types from an org.

**Requirements:**
- Salesforce CLI (sf)
- Authenticated org
- Valid SFDX project structure

**Usage:**
```bash
./retrieve_metadata.sh sandbox ApexClass ApexTrigger
./retrieve_metadata.sh production AuraDefinitionBundle LightningComponentBundle
```

**Safety:** READ-ONLY - Only retrieves and downloads metadata.

---

#### `run_tests.py`
Execute Apex tests and display formatted results.

**Requirements:**
- Salesforce CLI (sf)
- Python 3.8+
- Authenticated org with test classes

**Usage:**
```bash
./run_tests.py CreateDonationLightningController_Test my-org
./run_tests.py PaymentsBL_Test production
```

**Output:**
- Test pass/fail summary
- Code coverage information
- Individual test results

**Safety:** READ-ONLY (executes tests) - Does not modify org configuration.

---

### Report Management Tools

#### `view-latest-report.sh`
View the latest report for a tool.

**Usage:**
```bash
./view-latest-report.sh org-comparison
./view-latest-report.sh test-results
./view-latest-report.sh code-coverage
```

**Safety:** READ-ONLY - Only displays report files.

---

#### `list-reports.sh`
List all reports and runs for a tool.

**Usage:**
```bash
./list-reports.sh                  # List all tools
./list-reports.sh org-comparison   # List specific tool
```

**Safety:** READ-ONLY - Only lists report metadata.

---

#### `compare-reports.sh`
Compare two report runs side-by-side.

**Usage:**
```bash
./compare-reports.sh org-comparison 2025-10-21-1648 2025-10-24-0915
./compare-reports.sh test-results run1 run2
```

**Output:**
- Metadata comparison
- Report text diff
- Artifact differences

**Safety:** READ-ONLY - Only reads and compares report files.

---

## ⚠️ Destructive (Dangerous) Scripts

**CAUTION**: These scripts modify code or data in Salesforce orgs. Always:
1. Test in sandbox first
2. Have backups
3. Review changes before deploying

### Code Deployment Tools

#### `deploy_and_test.sh`
Deploy metadata with automatic test execution.

**Requirements:**
- Salesforce CLI (sf)
- Authenticated org
- Valid metadata in deployment path
- Apex test classes in target org

**Usage:**
```bash
./deploy_and_test.sh src/aura/MyComponent/ sandbox
./deploy_and_test.sh src/classes/ production --dry-run
```

**Safety:** ⚠️ DESTRUCTIVE - DEPLOYS CODE
Requires user confirmation before proceeding.

---

#### `snapshot_org.sh`
Create a metadata snapshot of org before deployment.

**Requirements:**
- Salesforce CLI (sf)
- Authenticated org
- Write permissions for output directory
- git command (optional)

**Usage:**
```bash
./snapshot_org.sh production ./backups/prod-2025-10-20
./snapshot_org.sh sandbox ./backups/sandbox-$(date +%Y-%m-%d)
```

**Output:**
- `package.xml`: Metadata manifest
- `src/`: All retrieved metadata
- `snapshot-info.json`: Snapshot metadata

**Safety:** READ-ONLY (with local file creation) - Reads org only, saves locally.

---

#### `rollback_deployment.sh`
Rollback org to a previous snapshot.

**Requirements:**
- Salesforce CLI (sf)
- Authenticated org
- Valid snapshot directory (from `snapshot_org.sh`)
- Write permissions for pre-rollback backup

**Usage:**
```bash
./rollback_deployment.sh production ./backups/prod-2025-10-19
./rollback_deployment.sh sandbox ./backups/sandbox-last-good
```

**Safety:** ⚠️ DESTRUCTIVE - DEPLOYS CODE
Requires explicit confirmation with "yes".
Creates pre-rollback backup automatically.

---

### Data Modification Tools

#### `seed_scratch_org.sh`
Seed a scratch org with test data from another org.

**Requirements:**
- Salesforce CLI (sf)
- SFDMU plugin: `sf plugins install sfdmu`
- Authenticated to both source and target orgs
- npm installed (alternative SFDMU install)

**Usage:**
```bash
./seed_scratch_org.sh dev-sandbox my-scratch
./seed_scratch_org.sh production my-scratch ./sfdmu-config
```

**Safety:** ⚠️ DESTRUCTIVE - WRITES DATA
Use only on scratch orgs or test environments.

---

#### `emergency_rollback.py`
Emergency data restoration from CSV backup.

**Requirements:**
- Salesforce CLI (sf)
- Python 3.8+
- Authenticated org
- CSV backup file with Id column

**Usage:**
```bash
./emergency_rollback.py Account ./backup-accounts.csv my-org
./emergency_rollback.py Contact ./backup-contacts.csv production
```

**Safety:** ⚠️ DESTRUCTIVE - WRITES DATA
For emergency use only. Requires confirmation before execution.

---

## 🧪 Testing Guide

### Testing Safe Scripts (Phase 2)

Safe scripts can be tested without risk. Use `breslov-sandbox` org:

**SOQL Tools:**
```bash
./query_soql.py "SELECT Id, Name FROM Account LIMIT 5" breslov-sandbox
./profile_soql.py "SELECT Id FROM Opportunity WHERE Amount > 1000" breslov-sandbox
```

**Analysis Tools:**
```bash
./org_health_check.py breslov-sandbox
./org_limits_monitor.py breslov-sandbox
./find_duplicates.py Account "Name" breslov-sandbox
./export_data.py "Account" breslov-sandbox /tmp/test-export
```

**Metadata Tools:**
```bash
./compare_orgs.sh breslov-sandbox breslov-production
./compare_orgs_and_report.sh breslov-sandbox breslov-production
./retrieve_metadata.sh breslov-sandbox ApexClass
```

**Performance Tools:**
```bash
./find_slow_queries.sh ./debug-logs 1000    # (requires log files)
./analyze_apex_performance.py ./debug-log.txt
```

### Testing Destructive Scripts

**DO NOT test in production.** Always use sandbox first.

**Backup Before Testing:**
```bash
./snapshot_org.sh breslov-sandbox ./backups/sandbox-before-test
```

**Test Deployment (dry-run):**
```bash
./deploy_and_test.sh src/aura/CreatePayments/ breslov-sandbox --dry-run
```

**Test on Scratch Org Only:**
```bash
./seed_scratch_org.sh breslov-sandbox my-test-scratch
```

---

## 📋 Requirements Matrix

| Script | Safety | Python | sf CLI | jq | bash | git | SFDMU | Debug Logs |
|--------|--------|--------|--------|-----|------|-----|-------|-----------|
| query_soql.py | ✅ | ✓ | ✓ | | | | | |
| profile_soql.py | ✅ | ✓ | ✓ | | | | | |
| org_health_check.py | ✅ | ✓ | ✓ | | | | | |
| org_limits_monitor.py | ✅ | ✓ | ✓ | | | | | |
| find_duplicates.py | ✅ | ✓ | ✓ | | | | | |
| export_data.py | ✅ | ✓ | ✓ | | | | | |
| analyze_apex_performance.py | ✅ | ✓ | | | | | | ✓ |
| find_slow_queries.sh | ✅ | | | | ✓ | | | ✓ |
| compare_orgs.sh | ✅ | | ✓ | | ✓ | | | |
| compare_orgs_and_report.sh | ✅ | | ✓ | ✓ | ✓ | ✓ | | |
| retrieve_metadata.sh | ✅ | | ✓ | | ✓ | | | |
| run_tests.py | ✅ | ✓ | ✓ | | | | | |
| view-latest-report.sh | ✅ | | | | ✓ | ✓ | | |
| list-reports.sh | ✅ | | | ✓ | ✓ | ✓ | | |
| compare-reports.sh | ✅ | | | ✓ | ✓ | ✓ | | |
| deploy_and_test.sh | ⚠️ | | ✓ | | ✓ | | | |
| snapshot_org.sh | ✅ | | ✓ | | ✓ | ✓ | | |
| rollback_deployment.sh | ⚠️ | | ✓ | | ✓ | | | |
| seed_scratch_org.sh | ⚠️ | | ✓ | | ✓ | | ✓ | |
| emergency_rollback.py | ⚠️ | ✓ | ✓ | | | | | |

---

## ✅ Summary

**Safe to test immediately:**
- 15 read-only scripts with no risk to orgs

**Requires caution:**
- 5 scripts that modify orgs or deploy code
- Test in sandbox first
- Create snapshots before deployment

**Dependencies:**
- All require Salesforce CLI
- Some need jq, python, or SFDMU
- Some need pre-existing debug logs

**Next Steps:**
1. Install global requirements
2. Test safe scripts first
3. Create snapshots before deploying
4. Use dry-run mode for deployment scripts

---

Generated by salesforce-skill repository