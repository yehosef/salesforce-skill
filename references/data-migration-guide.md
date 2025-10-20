# Salesforce Data Migration Guide

Complete guide for migrating data between Salesforce environments using SFDMU, Data Loader, and custom solutions.

## Table of Contents

1. [Migration Tools Overview](#migration-tools-overview)
2. [SFDMU (Salesforce Data Move Utility)](#sfdmu-salesforce-data-move-utility)
3. [Data Loader](#data-loader)
4. [Bulk API](#bulk-api)
5. [Migration Patterns](#migration-patterns)
6. [External IDs](#external-ids)
7. [Relationship Mapping](#relationship-mapping)
8. [Common Challenges](#common-challenges)
9. [Best Practices](#best-practices)

---

## Migration Tools Overview

### Tool Comparison

| Tool | Best For | Pros | Cons |
|------|----------|------|------|
| **SFDMU** | Complex relationships, preserving hierarchies | Handles parent-child, auto external IDs | Requires configuration |
| **Data Loader** | Simple objects, large volumes | UI-based, widely used | Manual relationship mapping |
| **Bulk API** | Massive datasets (millions) | Fast, asynchronous | Complex error handling |
| **Apex Data** | Complex business logic | Full control, validation | Requires development |

### When to Use Each Tool

**SFDMU**:
- Migrating Account → Contact → Opportunity hierarchies
- Seeding scratch orgs with realistic data
- Preserving record IDs and relationships
- Complex custom object graphs

**Data Loader**:
- One-time migrations of independent objects
- Simple exports for backup
- Updating existing records in bulk

**Bulk API**:
- Migrating millions of records
- Background processing required
- High-volume data loads

---

## SFDMU (Salesforce Data Move Utility)

### Installation

```bash
# As Salesforce CLI plugin (recommended)
sf plugins install sfdmu

# As standalone npm package
npm install -g sfdmu

# Verify installation
sf sfdmu --version
```

### Basic Usage

```bash
# Migrate data from source to target
sf sfdmu run --sourceusername source-org --targetusername target-org --path ./config

# Or with standalone command
sfdmu run --sourceusername source-org --targetusername target-org --path ./config
```

### Configuration File (export.json)

Basic structure:

```json
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
      "query": "SELECT Id, Name FROM Account WHERE CreatedDate = LAST_N_DAYS:30",
      "operation": "Upsert",
      "externalId": "Name"
    }
  ]
}
```

### SFDMU Operations

| Operation | Use Case | Description |
|-----------|----------|-------------|
| **Insert** | New records only | Creates new records, fails on duplicates |
| **Update** | Existing records | Updates based on Id or external ID |
| **Upsert** | Insert or update | Matches by external ID, inserts if not found |
| **Delete** | Remove records | Deletes records in target org |
| **Readonly** | Reference data | Queries data without modifying target |

### Advanced SFDMU Configuration

#### Parent-Child Relationships

```json
{
  "objects": [
    {
      "query": "SELECT Id, Name, Industry FROM Account",
      "operation": "Upsert",
      "externalId": "Name"
    },
    {
      "query": "SELECT Id, FirstName, LastName, Email, Account.Name FROM Contact",
      "operation": "Upsert",
      "externalId": "Email"
    }
  ]
}
```

SFDMU automatically:
- Creates external ID mappings
- Resolves `Account.Name` to new Account ID in target
- Maintains parent-child relationships

#### Self-Referencing Objects

```json
{
  "query": "SELECT Id, Name, ParentId FROM Account WHERE ParentId != null",
  "operation": "Upsert",
  "externalId": "Name"
}
```

SFDMU handles circular references and self-lookups.

#### Filtering and Scope

```json
{
  "query": "SELECT Id, Name, StageName, CloseDate FROM Opportunity WHERE IsClosed = false AND CreatedDate = LAST_N_MONTHS:6",
  "operation": "Upsert",
  "externalId": "Name",
  "deleteOldData": true
}
```

Options:
- `deleteOldData: true` - Removes records in target that don't exist in source
- Use WHERE clauses to limit scope
- Use date literals (LAST_N_DAYS, THIS_YEAR, etc.)

#### Custom Object Migration

```json
{
  "query": "SELECT Id, Name, Custom_Field__c, Related_Object__r.Name FROM Custom_Object__c",
  "operation": "Upsert",
  "externalId": "Name"
}
```

Works with any custom object. Use `__r.Name` for lookups.

---

## Data Loader

### Installation

Download from Salesforce Setup → Data Loader, or:

```bash
# Command-line version
sf plugins install @salesforce/data-loader
```

### Export Data

1. Open Data Loader
2. Select "Export"
3. Choose object (e.g., Account)
4. Specify SOQL query or use wizard
5. Map fields to CSV
6. Save to file

### Import Data

1. Open Data Loader
2. Select "Insert", "Update", or "Upsert"
3. Choose CSV file
4. Map CSV columns to Salesforce fields
5. Run import
6. Review success/error logs

### Data Loader CLI

```bash
# Export
sf data export tree --query "SELECT Id, Name FROM Account" --output-dir ./data --target-org my-org

# Import
sf data import tree --plan ./data/Account-plan.json --target-org my-org
```

---

## Bulk API

### Using Bulk API 2.0

```bash
# Bulk export (>10k records)
sf data export bulk --query "SELECT Id, Name, Email FROM Contact WHERE CreatedDate = THIS_YEAR" --target-org my-org --output-dir ./exports

# Bulk import
sf data import bulk --sobject Account --file ./data/accounts.csv --target-org my-org
```

### Bulk API Best Practices

- **Batch Size**: 10,000 records per batch (default)
- **Parallel Mode**: Use for independent records (not parent-child)
- **Serial Mode**: Use when order matters
- **Hard Delete**: Use `--hard-delete` to bypass recycle bin

---

## Migration Patterns

### Pattern 1: Sandbox Refresh

After refreshing a sandbox, seed it with production-like data:

```bash
# Use SFDMU to copy data from production
sf sfdmu run --sourceusername production --targetusername refreshed-sandbox --path ./sfdmu-config
```

### Pattern 2: Scratch Org Seeding

Create realistic test data in scratch orgs:

```bash
# Copy sample data from dev sandbox
sf sfdmu run --sourceusername dev-sandbox --targetusername my-scratch --path ./sfdmu-scratch-seed
```

Use the provided `seed_scratch_org.sh` script for automation.

### Pattern 3: Data Archiving

Export data before deleting:

```bash
# Export old opportunities
sf data export bulk --query "SELECT Id, Name, StageName, CloseDate, Amount FROM Opportunity WHERE CloseDate < LAST_YEAR" --output-dir ./archive/opportunities-2023
```

### Pattern 4: Environment Promotion

Move configuration data (picklist values, custom settings) to higher environments:

```bash
# Export custom settings
sf data export tree --query "SELECT Id, Name, Value__c FROM Custom_Setting__c" --output-dir ./custom-settings

# Import to target
sf data import tree --plan ./custom-settings/Custom_Setting__c-plan.json --target-org uat-sandbox
```

---

## External IDs

### What Are External IDs?

External IDs are unique identifiers from external systems used to match records during data migrations.

### Creating External IDs

In Salesforce Setup:
1. Object Manager → [Object] → Fields & Relationships
2. Create new field (Text, Number, or Email)
3. Check "External ID"
4. Check "Unique" (optional but recommended)

### Common External ID Fields

| Object | External ID Field | Use Case |
|--------|-------------------|----------|
| Account | `External_Id__c` | CRM migration |
| Contact | `Email` | Email-based matching |
| Product | `SKU__c` | Product catalog sync |
| Custom Object | `Legacy_Id__c` | System migration |

### Using External IDs in Upsert

```bash
# Upsert accounts using External_Id__c
sf data import tree --sobject Account --file ./accounts.csv --external-id External_Id__c --target-org my-org
```

SFDMU example:

```json
{
  "query": "SELECT Id, Name, External_Id__c FROM Account",
  "operation": "Upsert",
  "externalId": "External_Id__c"
}
```

---

## Relationship Mapping

### Understanding Salesforce Relationships

**Lookup**: Optional relationship, can be null
**Master-Detail**: Required relationship, cascade delete
**Many-to-Many**: Junction object with two master-details

### Mapping Parent-Child Relationships

#### Option 1: Two-Pass Import

1. **Pass 1**: Import parent records (Accounts)
2. **Pass 2**: Import child records (Contacts) with parent IDs

```bash
# Pass 1: Import Accounts
sf data import tree --sobject Account --file ./accounts.csv --target-org my-org

# Map Account IDs to External IDs in contacts.csv
# Pass 2: Import Contacts
sf data import tree --sobject Contact --file ./contacts.csv --target-org my-org
```

#### Option 2: External ID Relationships

Use `Account.External_Id__c` instead of `AccountId`:

**contacts.csv:**
```csv
FirstName,LastName,Email,Account.External_Id__c
John,Doe,john@example.com,ACC-001
Jane,Smith,jane@example.com,ACC-002
```

Salesforce automatically resolves `Account.External_Id__c` to the correct AccountId.

#### Option 3: SFDMU (Automatic)

SFDMU handles relationships automatically:

```json
{
  "objects": [
    {
      "query": "SELECT Id, Name, External_Id__c FROM Account",
      "operation": "Upsert",
      "externalId": "External_Id__c"
    },
    {
      "query": "SELECT Id, FirstName, LastName, Email, Account.External_Id__c FROM Contact",
      "operation": "Upsert",
      "externalId": "Email"
    }
  ]
}
```

SFDMU creates internal mappings and resolves relationships.

### Self-Referencing Relationships

**Example**: Account hierarchy (Parent Account)

**Challenge**: Parent might not exist yet when importing child.

**Solution**: Import in multiple passes or use SFDMU which handles this automatically.

**Manual approach**:
1. Import accounts without ParentId
2. Create mapping file: `old_id → new_id`
3. Update accounts with correct ParentId

**SFDMU approach**:
```json
{
  "query": "SELECT Id, Name, ParentId FROM Account",
  "operation": "Upsert",
  "externalId": "Name"
}
```

SFDMU resolves self-references automatically.

### Many-to-Many Relationships

**Example**: Opportunity Contact Roles (junction object)

1. Import Opportunities
2. Import Contacts
3. Import OpportunityContactRole with external IDs:
   - `Opportunity.External_Id__c`
   - `Contact.Email`

---

## Common Challenges

### Challenge 1: Record Locking

**Problem**: Records locked during migration (UNABLE_TO_LOCK_ROW)

**Solutions**:
- Run migrations during off-hours
- Disable validation rules temporarily
- Use bulk API (retries automatically)
- Implement exponential backoff in custom scripts

### Challenge 2: Validation Rules

**Problem**: Validation rules block test data

**Solutions**:
- Bypass validation for migration user (formula: `$User.BypassValidation__c = true`)
- Temporarily deactivate validation rules
- Ensure test data meets validation criteria

### Challenge 3: Required Fields

**Problem**: Missing required fields in source data

**Solutions**:
- Add default values in CSV before import
- Create formula fields to populate defaults
- Modify object schema to make fields optional temporarily

### Challenge 4: Record Type Mapping

**Problem**: Record Type IDs differ between orgs

**Solutions**:
- Use Record Type Developer Names (not IDs)
- Query Record Type IDs before import: `SELECT Id, DeveloperName FROM RecordType WHERE SObjectType = 'Account'`
- Map Developer Names to IDs in import script

### Challenge 5: Large Data Volumes

**Problem**: Millions of records cause timeouts

**Solutions**:
- Use Bulk API 2.0 (handles up to 150 million records)
- Split into smaller batches
- Use parallel processing
- Schedule migrations overnight

### Challenge 6: Field-Level Security

**Problem**: Migration user lacks field access

**Solutions**:
- Grant migration user System Administrator profile
- Create permission set with all field access
- Verify FLS before migration: `sf org list permissions --target-org my-org`

---

## Best Practices

### Pre-Migration Checklist

- [ ] Create full org backup (metadata + data)
- [ ] Document external ID strategy
- [ ] Identify all relationships and dependencies
- [ ] Review validation rules and workflow rules
- [ ] Check field-level security for migration user
- [ ] Test migration in sandbox first
- [ ] Prepare rollback plan

### During Migration

- [ ] Monitor governor limits (API calls, CPU time)
- [ ] Watch for error logs and failed records
- [ ] Validate record counts after each batch
- [ ] Keep detailed logs of all operations
- [ ] Run in batches (don't migrate all at once)

### Post-Migration Checklist

- [ ] Verify record counts match source
- [ ] Spot-check relationships (parent-child links)
- [ ] Run validation queries (e.g., Contacts without Accounts)
- [ ] Re-enable validation rules and workflows
- [ ] Test critical business processes
- [ ] Document migration results and issues

### Data Quality

**Before migrating, clean your data:**

1. **Remove duplicates**: Use `find_duplicates.py` script
2. **Fill required fields**: Ensure no nulls in required fields
3. **Validate emails**: Check email format
4. **Normalize phone numbers**: Consistent format
5. **Fix broken relationships**: Ensure lookup IDs exist

### Performance Tips

**Optimize for speed:**

- Use Bulk API for large volumes
- Disable triggers during migration (if safe)
- Turn off validation rules temporarily
- Use "Serial Mode" for dependent data
- Use "Parallel Mode" for independent data
- Batch size: 10,000 records for Bulk API, 200 for SOAP API

### Security Considerations

**Protect sensitive data:**

- Mask PII in non-production environments
- Use field-level encryption for sensitive fields
- Restrict migration user to specific IP ranges
- Audit migration activity
- Delete migration files after completion

---

## SFDMU Examples

### Example 1: Full NPSP Migration

```json
{
  "orgs": [
    {"name": "source", "isSource": true},
    {"name": "target", "isTarget": true}
  ],
  "objects": [
    {
      "query": "SELECT Id, Name, npe01__One2OneContact__r.Email FROM Account WHERE RecordType.DeveloperName = 'HH_Account'",
      "operation": "Upsert",
      "externalId": "npe01__One2OneContact__r.Email"
    },
    {
      "query": "SELECT Id, FirstName, LastName, Email, AccountId FROM Contact",
      "operation": "Upsert",
      "externalId": "Email"
    },
    {
      "query": "SELECT Id, Name, Amount, StageName, CloseDate, AccountId, npe01__Contact_Id_for_Role__c FROM Opportunity",
      "operation": "Insert"
    },
    {
      "query": "SELECT Id, npe01__Opportunity__c, npe01__Payment_Amount__c, npe01__Payment_Date__c, npe01__Paid__c FROM npe01__OppPayment__c",
      "operation": "Insert"
    }
  ]
}
```

### Example 2: Custom Objects with Lookups

```json
{
  "objects": [
    {
      "query": "SELECT Id, Name, Status__c FROM Custom_Parent__c WHERE CreatedDate = THIS_YEAR",
      "operation": "Upsert",
      "externalId": "Name"
    },
    {
      "query": "SELECT Id, Name, Custom_Parent__r.Name, Amount__c FROM Custom_Child__c",
      "operation": "Upsert",
      "externalId": "Name"
    }
  ]
}
```

### Example 3: Delete Old Records

```json
{
  "objects": [
    {
      "query": "SELECT Id FROM Old_Object__c WHERE Status__c = 'Archived'",
      "operation": "Delete"
    }
  ]
}
```

---

## Automation Scripts

This skill includes automation scripts for common migration tasks:

### export_data.py

Export data with relationships to CSV:

```bash
./scripts/export_data.py "Account,Contact,Opportunity" my-org ./exports
```

Automatically:
- Exports all specified objects
- Preserves relationships via external IDs
- Creates import plan for Data Loader

### find_duplicates.py

Identify duplicate records before migration:

```bash
./scripts/find_duplicates.py Account "Name,BillingCity" my-org
```

Finds duplicates based on specified fields.

---

## Additional Resources

**Official Documentation**:
- [SFDMU Documentation](https://github.com/forcedotcom/SFDX-Data-Move-Utility)
- [Salesforce Data Loader Guide](https://help.salesforce.com/s/articleView?id=sf.data_loader.htm)
- [Bulk API 2.0 Developer Guide](https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/)

**Reference Guides in This Skill**:
- `duplicate-detection.md` - Finding and merging duplicate records
- `soql-patterns.md` - Efficient queries for data export
- `common-errors.md` - Troubleshooting migration errors

---

**Last Updated**: Phase 2 - October 2025
