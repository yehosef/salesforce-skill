---
name: salesforce-dev
description: Full-featured Salesforce development toolkit for deployment, testing, SOQL queries, org comparison, performance analysis, data migration, rollback, and health monitoring. Use for any Salesforce task including comparing environments, deploying components, running tests, finding duplicates, optimizing performance, error troubleshooting, or CI/CD integration.
---

# Salesforce Development

## Overview

Provide procedural knowledge and automation for Salesforce development using the sf CLI (v2.x+), including deployment and retrieval of metadata (Apex, Aura, LWC, objects, fields), execution and formatting of SOQL queries, running Apex tests with coverage reports, and navigating Salesforce architecture and metadata.

## When to Use

Trigger this skill when:
- User mentions Salesforce, sf/sfdx commands, SOQL, Apex, Lightning, Aura
- Tasks involve deploying or retrieving code or metadata
- Need to query Salesforce data or understand object schema
- Running or debugging Apex tests
- Exploring org structure (objects, fields, relationships)

## Core Capabilities

### 1. Deployment & Retrieval

Reference `references/deployment-guide.md` for comprehensive deployment patterns.

**Common Operations:**
- Deploy metadata: Use `sf project deploy start -d <path> -o <alias>`
- Preview before deploying: Always run `sf project deploy preview` first
- Validate without deploying: Add `--dry-run` flag
- Deploy with tests: Add `--test-level RunLocalTests`
- Retrieve metadata: Use `sf project retrieve start -m "<type>:<name>" -o <alias>`

**Automation:**
- Use `scripts/deploy_and_test.sh <path> <org-alias>` for automated deploy-with-tests workflow
- Use `scripts/retrieve_metadata.sh <org-alias> <type1> <type2>...` for bulk metadata retrieval

**Key Flags:**
- `--dry-run` - Validate without deploying
- `--test-level RunLocalTests` - Run local tests (default for deployment)
- `--wait <minutes>` - Wait time for deployment (default 33)
- `-m "<MetadataType>:<Name>"` - Specific component to deploy/retrieve

### 2. SOQL Query Execution

Reference `references/soql-patterns.md` for query optimization and common patterns.

**Executing Queries:**
- Basic query: `sf data query -q "SELECT Id, Name FROM Account" -o <alias>`
- Query from file: `sf data query -f query.soql -o <alias>`
- Bulk export (>10k records): `sf data export bulk -q "SELECT..." -o <alias>`

**Automation:**
- Use `scripts/query_soql.py "<SOQL>" <org-alias>` for formatted markdown table output
- Script automatically handles JSON parsing and table formatting

**Best Practices:**
- Check `references/governor-limits.md` for SOQL limits (100 synchronous, 200 async)
- Use indexed fields in WHERE clauses for better performance
- Limit results to prevent runaway queries
- For >10,000 records, use bulk export instead

### 3. Apex Testing

Reference `references/testing-guide.md` for comprehensive test strategies.

**Running Tests:**
- All tests: `sf apex test run -o <alias> -c`
- Specific class: `sf apex test run -n ClassName -o <alias> -c`
- Specific method: `sf apex test run -n ClassName.methodName -o <alias>`
- Get results: `sf apex test report -i <test-run-id> -o <alias>`

**Automation:**
- Use `scripts/run_tests.py <class-name> <org-alias>` for formatted test results
- Script shows pass/fail summary, coverage, and detailed failure messages

**Coverage Requirements:**
- Sandbox: No minimum (recommended 75%+)
- Production: 75% minimum required
- All triggers must have test coverage

**Templates:**
- Use `assets/apex-test-template.cls` as starting point for new test classes
- Template includes @TestSetup, positive/negative/bulk test patterns

### 4. Schema Exploration

Reference `references/metadata-types.md` for complete list of metadata types.

**Object Information:**
- List all objects: `sf sobject list -o <alias>`
- Describe object: `sf sobject describe -s Account -o <alias>`
- Query field metadata: `sf data query -q "SELECT QualifiedApiName, DataType FROM FieldDefinition WHERE EntityDefinition.QualifiedApiName='Account'" -o <alias>`

**Relationship Queries:**
- Parent to child: `SELECT Id, (SELECT Id FROM Contacts) FROM Account`
- Child to parent: `SELECT Id, Account.Name FROM Contact`
- Reference `references/soql-patterns.md` for relationship query examples

### 5. Command Reference

Reference `references/sf-cli-reference.md` for quick command lookup.

**Command Categories:**
- Org management: list, display, open, set default
- Project deployment: deploy, preview, validate
- Project retrieval: retrieve by type, by component, by package.xml
- Data queries: SOQL, bulk export, JSON output
- Apex testing: run tests, view results, coverage reports
- Object metadata: list objects, describe fields

**Note:** All commands use `sf` (not deprecated `sfdx force:*`)

### 6. Error Troubleshooting & Quick Fixes

Reference `references/common-errors.md` for comprehensive error solutions.

**Common Errors Covered:**
- INVALID_CROSS_REFERENCE_KEY → Deploy dependencies first
- UNABLE_TO_LOCK_ROW → Retry logic with exponential backoff
- TOO_MANY_SOQL_QUERIES → Bulkification patterns
- FIELD_CUSTOM_VALIDATION_EXCEPTION → Bypass or fix test data
- INSUFFICIENT_ACCESS → Permission fixes

**Quick Diagnostics:**
- Check deployment failures: `sf project deploy report`
- View governor limit usage in debug logs
- Analyze test failures with detailed error messages

### 7. Org Comparison & Report Management

**Compare Metadata Between Orgs (with Reports):**
- Use `scripts/compare_orgs_and_report.sh <source-org> <target-org> [metadata-types]` to generate stored reports
- Automatically saves detailed comparison reports to `.claude/reports/org-comparison/`
- Each run gets a unique timestamp-based ID (YYYY-MM-DD-HHMM)
- Includes diffs, metadata, artifacts for historical tracking

**Example:**
```bash
./scripts/compare_orgs_and_report.sh breslov-sandbox breslov-production
```

**View Reports:**
```bash
# View latest report
./scripts/view-latest-report.sh org-comparison

# List all runs
./scripts/list-reports.sh org-comparison

# Compare two runs side-by-side
./scripts/compare-reports.sh org-comparison 2025-10-21-1648 2025-10-24-0915
```

**Interactive Comparison (Legacy):**
- Use `scripts/compare_orgs.sh <source-org> <target-org>` for interactive mode
- Shows real-time differences and prompts for detailed diffs
- Does not save reports (use `compare_orgs_and_report.sh` for persistent reports)

**Report Structure:**
```
.claude/reports/org-comparison/
├── runs/
│   ├── 2025-10-21-1648/
│   │   ├── report.md           # Human-readable report
│   │   ├── metadata.json       # Machine-readable metadata
│   │   ├── diffs/              # Individual file diffs
│   │   └── artifacts/          # Retrieved metadata
│   ├── 2025-10-24-0915/
│   └── latest -> 2025-10-24-0915/  # Symlink to most recent
└── README.md
```

**Scratch Org Data Seeding:**
- Use `scripts/seed_scratch_org.sh <source-org> <scratch-org>` for quick setup
- Automatically creates SFDMU configuration if not present
- Seeds Account, Contact, Opportunity data from another org
- Requires SFDMU: `sf plugins install sfdmu`

### 8. CI/CD Integration

**GitHub Actions Templates:**
Reference `assets/salesforce-ci.yml` and `assets/validate-pr.yml` for ready-to-use CI/CD pipelines.

**What's Included:**
- `salesforce-ci.yml` - Full deployment pipeline with validation and production deploy
- `validate-pr.yml` - PR validation with automated testing and comments

**Setup Steps:**
1. Copy template to `.github/workflows/`
2. Add `SALESFORCE_AUTH_URL` secret to GitHub repository
3. Get auth URL: `sf org display -o <org> --verbose`
4. Push to trigger automated deployments

### 9. Data Migration & Duplicate Management

Reference `references/data-migration-guide.md` and `references/duplicate-detection.md` for comprehensive guidance.

**Data Migration:**
- Use SFDMU for complex parent-child relationships
- Export with relationships: `scripts/export_data.py "Account,Contact" <org> ./exports`
- Handles external IDs automatically
- Creates import plans for Data Loader

**Duplicate Detection:**
- Find duplicates: `scripts/find_duplicates.py Contact "Email" <org>`
- Groups duplicates by match fields
- Recommends master record for merging
- Exports to CSV for review

**Best Practices:**
- Use external IDs for upsert operations
- SFDMU handles relationship mapping automatically
- Always backup before mass data operations

### 10. Performance Profiling & Optimization

Reference `references/performance-tuning.md` for optimization strategies.

**SOQL Profiling:**
- Profile queries: `scripts/profile_soql.py "<SOQL>" <org>`
- Shows execution time, selectivity, and recommendations
- Identifies missing indexes and anti-patterns

**Apex Performance:**
- Analyze logs: `scripts/analyze_apex_performance.py ./debug-log.txt`
- Finds CPU hotspots and heap usage
- Shows governor limit usage by method

**Slow Query Detection:**
- Find slow queries: `scripts/find_slow_queries.sh ./logs 1000`
- Scans debug logs for queries >1000ms
- Generates optimization recommendations

**Quick Wins:**
- Use indexed fields in WHERE clauses
- Bulkify all triggers and loops
- Move SOQL outside loops
- Use Maps for lookups instead of nested loops

### 11. Rollback & Disaster Recovery

Reference `references/rollback-procedures.md` for comprehensive rollback strategies.

**Pre-Deployment Snapshots:**
- Create snapshot: `scripts/snapshot_org.sh <org> ./backups/snapshot-$(date +%Y-%m-%d)`
- Captures all metadata for rollback
- Includes Git commit hash for traceability

**Rollback Deployment:**
- Rollback: `scripts/rollback_deployment.sh <org> ./backups/snapshot-2025-10-19`
- Creates pre-rollback snapshot automatically
- Runs tests after rollback
- Full audit trail

**Emergency Data Recovery:**
- Quick restore: `scripts/emergency_rollback.py Account ./backup-accounts.csv <org>`
- Shows diff before applying
- Validates restored data
- Works with any sobject

**Best Practices:**
- Always snapshot before production deployments
- Test rollback procedures in sandbox
- Maintain backup retention policy (90 days minimum)
- Document rollback decision criteria

### 12. Org Health Monitoring

**Comprehensive Health Check:**
- Run check: `scripts/org_health_check.py <org>`
- Health score (0-100) with recommendations
- Checks API limits, storage, code coverage
- Identifies performance issues

**Continuous Monitoring:**
- Monitor limits: `scripts/org_limits_monitor.py <org> --alert-threshold 80`
- Tracks API usage, storage, async jobs
- Configurable alert thresholds
- Export history for trending analysis

**Key Metrics Monitored:**
- Daily API requests usage
- Data storage (MB)
- File storage (MB)
- Apex code coverage
- Failed tests
- Active triggers/workflows

## Resources

This skill includes automation scripts, comprehensive references, and templates:

### lib/

**Report Management Framework:**
- `report-manager.sh` - Standardized report generation and management library
  - Used by all reporting tools for consistent output structure
  - Manages timestamped runs, metadata tracking, and report indices
  - Source this library in your own scripts for report capabilities

### scripts/

**Core Automation:**
- `query_soql.py` - Execute SOQL and format results as markdown table
- `deploy_and_test.sh` - Automated deploy-with-tests workflow with preview
- `run_tests.py` - Execute Apex tests and format results with coverage
- `retrieve_metadata.sh` - Bulk metadata retrieval for multiple types

**Phase 1 (Environment Management):**
- `compare_orgs.sh` - Compare metadata between two orgs (interactive)
- `compare_orgs_and_report.sh` - **NEW** Compare orgs and save detailed timestamped reports
- `seed_scratch_org.sh` - Seed scratch org with data using SFDMU

**Report Management Tools:**
- `view-latest-report.sh` - **NEW** View the latest report for any tool
- `list-reports.sh` - **NEW** List all historical runs for a tool
- `compare-reports.sh` - **NEW** Compare two report runs side-by-side

**Phase 2 (Data & Migration):**
- `export_data.py` - **NEW** Export data with relationships to CSV
- `find_duplicates.py` - **NEW** Find duplicate records with merge recommendations

**Phase 2 (Performance):**
- `profile_soql.py` - **NEW** Analyze SOQL query performance
- `analyze_apex_performance.py` - **NEW** Parse debug logs for performance bottlenecks
- `find_slow_queries.sh` - **NEW** Identify slow queries in debug logs

**Phase 2 (Rollback):**
- `snapshot_org.sh` - **NEW** Create metadata snapshot before deployment
- `rollback_deployment.sh` - **NEW** Rollback to previous snapshot
- `emergency_rollback.py` - **NEW** Quick data restoration from backup

**Phase 2 (Monitoring):**
- `org_health_check.py` - **NEW** Comprehensive org health analysis
- `org_limits_monitor.py` - **NEW** Monitor API limits and usage

### references/

**Core References:**
- `sf-cli-reference.md` - Complete sf command reference
- `soql-patterns.md` - SOQL optimization patterns and examples
- `deployment-guide.md` - Deployment and retrieval best practices
- `testing-guide.md` - Apex testing strategies and patterns
- `governor-limits.md` - Salesforce limits and avoidance strategies
- `metadata-types.md` - Common metadata types for deployment

**Phase 1:**
- `common-errors.md` - Top 50+ Salesforce errors with solutions

**Phase 2:**
- `data-migration-guide.md` - **NEW** SFDMU, Data Loader, external IDs, relationships
- `duplicate-detection.md` - **NEW** Matching rules, fuzzy matching, deduplication
- `performance-tuning.md` - **NEW** SOQL optimization, CPU/heap, bulkification
- `rollback-procedures.md` - **NEW** Rollback strategies, disaster recovery, backups

### assets/
- `apex-test-template.cls` - Template for new Apex test classes
- `package-xml-template.xml` - Package.xml template for metadata retrieval
- `salesforce-ci.yml` - GitHub Actions CI/CD pipeline
- `validate-pr.yml` - GitHub Actions PR validation workflow
