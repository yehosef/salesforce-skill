# Salesforce CLI Command Reference (sf v2.x)

Complete reference for the modern Salesforce CLI (`sf` command). All commands shown here use the new `sf` syntax, not the deprecated `sfdx force:*` commands.

## Org Management

### List Orgs
```bash
sf org list
sf org list --all  # Include expired/scratch orgs
```

### Display Org Information
```bash
sf org display -o <alias>
sf org display --target-org <alias> --json  # JSON output
```

### Open Org in Browser
```bash
sf org open -o <alias>
sf org open -o <alias> -p lightning/setup/SetupOneHome/home  # Specific path
```

### Set Default Org
```bash
sf config set target-org=<alias>
sf config set target-dev-hub=<alias>
```

### Login to Org
```bash
sf org login web -a <alias>  # Web-based login
sf org login sfdx-url -f <auth-file>  # URL-based login
```

---

## Project Deployment

### Deploy Metadata
```bash
# Deploy directory
sf project deploy start -d src/ -o <alias>

# Deploy specific directory
sf project deploy start -d src/aura/MyComponent/ -o <alias>

# Deploy specific component by type and name
sf project deploy start -m "ApexClass:MyClass" -o <alias>
sf project deploy start -m "AuraDefinitionBundle:MyComponent" -o <alias>

# Deploy with tests
sf project deploy start -d src/ -o <alias> --test-level RunLocalTests
sf project deploy start -d src/ -o <alias> --test-level RunAllTestsInOrg

# Deploy with wait time
sf project deploy start -d src/ -o <alias> --wait 30  # Wait up to 30 minutes
```

### Validate Deployment (Dry-Run)
```bash
sf project deploy start -d src/ -o <alias> --dry-run
sf project deploy start -m "ApexClass:MyClass" -o <alias> --dry-run --test-level RunLocalTests
```

### Preview Deployment
```bash
sf project deploy preview -d src/ -o <alias>
sf project deploy preview -m "ApexClass" -o <alias>
```

### Check Deployment Status
```bash
sf project deploy report -o <alias>
sf project deploy report -i <deploy-id> -o <alias>
```

### Cancel Deployment
```bash
sf project deploy cancel -i <deploy-id> -o <alias>
```

---

## Project Retrieval

### Retrieve Metadata
```bash
# Retrieve by metadata type (all instances)
sf project retrieve start -m "ApexClass" -o <alias>
sf project retrieve start -m "AuraDefinitionBundle" -o <alias>

# Retrieve specific component
sf project retrieve start -m "ApexClass:MyClass" -o <alias>
sf project retrieve start -m "AuraDefinitionBundle:MyComponent" -o <alias>

# Retrieve multiple types
sf project retrieve start -m "ApexClass, ApexTrigger" -o <alias>

# Retrieve using package.xml
sf project retrieve start -x manifest/package.xml -o <alias>

# Retrieve to specific directory
sf project retrieve start -m "ApexClass" -o <alias> -d retrieved/
```

### Preview Retrieval
```bash
sf project retrieve preview -m "ApexClass" -o <alias>
sf project retrieve preview -x manifest/package.xml -o <alias>
```

### Check Retrieval Status
```bash
sf project retrieve report -o <alias>
sf project retrieve report -i <retrieve-id> -o <alias>
```

---

## Data Queries (SOQL)

### Basic Queries
```bash
# Simple query
sf data query -q "SELECT Id, Name FROM Account" -o <alias>

# Query with WHERE clause
sf data query -q "SELECT Id, Name FROM Contact WHERE LastName = 'Smith'" -o <alias>

# Query from file
sf data query -f query.soql -o <alias>
```

### Output Formats
```bash
# JSON output
sf data query -q "SELECT Id, Name FROM Account" -o <alias> --json

# CSV output
sf data query -q "SELECT Id, Name FROM Account" -o <alias> --result-format csv
```

### Bulk Export (for >10k records)
```bash
sf data export bulk -q "SELECT Id, Name FROM Account" -o <alias>
sf data export bulk -f query.soql -o <alias> --wait 30
```

### Relationship Queries
```bash
# Parent to child
sf data query -q "SELECT Id, Name, (SELECT Id, FirstName FROM Contacts) FROM Account" -o <alias>

# Child to parent
sf data query -q "SELECT Id, FirstName, Account.Name FROM Contact" -o <alias>
```

---

## Apex Testing

### Run Tests
```bash
# Run all tests in org
sf apex test run -o <alias>

# Run all tests with code coverage
sf apex test run -o <alias> -c

# Run specific test class
sf apex test run -n MyClassTest -o <alias> -c

# Run specific test method
sf apex test run -n MyClassTest.testMethod -o <alias>

# Run multiple test classes
sf apex test run -n "MyClassTest, AnotherTest" -o <alias> -c

# Synchronous run (wait for completion)
sf apex test run -n MyClassTest -o <alias> -c --synchronous
```

### Get Test Results
```bash
# Get latest test results
sf apex test report -o <alias>

# Get specific test run results
sf apex test report -i <test-run-id> -o <alias>

# Get results in JSON format
sf apex test report -i <test-run-id> -o <alias> --json
```

### Code Coverage
```bash
# Get org-wide coverage
sf apex get test -o <alias> -c

# Get coverage for specific classes
sf apex get test -o <alias> -c --class-names "MyClass, AnotherClass"
```

---

## Object Metadata

### List Objects
```bash
# List all standard and custom objects
sf sobject list -o <alias>

# List custom objects only
sf sobject list -o <alias> --sobject-type custom

# List with details
sf sobject list -o <alias> --sobject-type all
```

### Describe Object
```bash
# Describe object schema
sf sobject describe -s Account -o <alias>

# JSON output for programmatic use
sf sobject describe -s Account -o <alias> --json
```

### Query Field Metadata
```bash
# Get all fields for an object
sf data query -q "SELECT QualifiedApiName, DataType, Label FROM FieldDefinition WHERE EntityDefinition.QualifiedApiName = 'Account'" -o <alias>

# Get custom fields only
sf data query -q "SELECT QualifiedApiName, DataType FROM FieldDefinition WHERE EntityDefinition.QualifiedApiName = 'Account' AND IsCustom = true" -o <alias>
```

---

## Data Manipulation

### Insert Records
```bash
# Insert single record
sf data create record -s Account -v "Name='Test Account'" -o <alias>

# Insert with multiple fields
sf data create record -s Contact -v "FirstName='John' LastName='Doe' Email='john@example.com'" -o <alias>
```

### Update Records
```bash
# Update by ID
sf data update record -s Account -i <record-id> -v "Name='Updated Name'" -o <alias>
```

### Delete Records
```bash
# Delete by ID
sf data delete record -s Account -i <record-id> -o <alias>
```

### Bulk Data Operations
```bash
# Bulk insert from CSV
sf data import bulk -s Account -f accounts.csv -o <alias>

# Bulk update from CSV
sf data update bulk -s Account -f accounts.csv -o <alias>

# Bulk delete
sf data delete bulk -s Account -f account-ids.csv -o <alias>
```

---

## Scratch Orgs (for Dev Hub users)

### Create Scratch Org
```bash
sf org create scratch -f config/project-scratch-def.json -a <alias>
sf org create scratch -f config/project-scratch-def.json -a <alias> -d 30  # 30-day duration
```

### Delete Scratch Org
```bash
sf org delete scratch -o <alias>
sf org delete scratch -o <alias> --no-prompt  # Skip confirmation
```

### List Scratch Orgs
```bash
sf org list --scratch
```

---

## Useful Flags (applicable to many commands)

### Common Flags
- `-o, --target-org <alias>` - Specify target org
- `--json` - Output in JSON format
- `--wait <minutes>` - Wait time for async operations (default varies by command)
- `--dry-run` - Validate without executing (deployment only)
- `-c, --code-coverage` - Include code coverage in test results
- `-d, --source-dir <path>` - Specify source directory
- `-m, --metadata <types>` - Specify metadata types/components

### Output Formats
- `--json` - Machine-readable JSON
- `--result-format csv` - CSV format (queries)
- `--result-format human` - Human-readable table (default)

---

## Migration from SFDX to SF

If you're used to the old `sfdx` commands, here are the equivalents:

| Old (sfdx) | New (sf) |
|------------|----------|
| `sfdx force:source:deploy` | `sf project deploy start` |
| `sfdx force:source:retrieve` | `sf project retrieve start` |
| `sfdx force:data:soql:query` | `sf data query` |
| `sfdx force:apex:test:run` | `sf apex test run` |
| `sfdx force:org:list` | `sf org list` |
| `sfdx force:org:display` | `sf org display` |
| `sfdx force:org:open` | `sf org open` |

---

## Tips and Best Practices

1. **Use Aliases**: Always use org aliases instead of usernames for clarity
2. **Preview First**: Run `sf project deploy preview` before deploying
3. **Validate in Production**: Use `--dry-run` to validate production deployments
4. **Set Defaults**: Use `sf config set target-org=<alias>` to avoid repeating `-o`
5. **JSON for Automation**: Use `--json` flag when scripting or automating
6. **Wait Times**: Increase `--wait` for large deployments (default is often too short)
7. **Test Coverage**: Always use `-c` flag when running tests to see coverage
8. **Bulk Operations**: For >10k records, always use bulk commands
