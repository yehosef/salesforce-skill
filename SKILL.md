---
name: salesforce-dev
description: Comprehensive Salesforce development workflow automation for deployment, SOQL queries, Apex testing, and metadata management using the Salesforce CLI (sf command). Use when working with Salesforce projects including Aura/LWC components, Apex classes, SOQL queries, deployments, or test execution.
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

### 7. Org Comparison & Environment Management

**Compare Metadata Between Orgs:**
- Use `scripts/compare_orgs.sh <source-org> <target-org>` to identify differences
- Shows components only in source, only in target, and modified
- Helps ensure sandbox and production stay in sync

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

## Resources

This skill includes automation scripts, comprehensive references, and templates:

### scripts/
- `query_soql.py` - Execute SOQL and format results as markdown table
- `deploy_and_test.sh` - Automated deploy-with-tests workflow with preview
- `run_tests.py` - Execute Apex tests and format results with coverage
- `retrieve_metadata.sh` - Bulk metadata retrieval for multiple types
- `compare_orgs.sh` - **NEW** Compare metadata between two orgs
- `seed_scratch_org.sh` - **NEW** Seed scratch org with data using SFDMU

### references/
- `sf-cli-reference.md` - Complete sf command reference
- `soql-patterns.md` - SOQL optimization patterns and examples
- `deployment-guide.md` - Deployment and retrieval best practices
- `testing-guide.md` - Apex testing strategies and patterns
- `governor-limits.md` - Salesforce limits and avoidance strategies
- `metadata-types.md` - Common metadata types for deployment
- `common-errors.md` - **NEW** Top 50+ Salesforce errors with solutions

### assets/
- `apex-test-template.cls` - Template for new Apex test classes
- `package-xml-template.xml` - Package.xml template for metadata retrieval
- `salesforce-ci.yml` - **NEW** GitHub Actions CI/CD pipeline
- `validate-pr.yml` - **NEW** GitHub Actions PR validation workflow
