# Deployment & Retrieval Guide

Comprehensive patterns for deploying and retrieving Salesforce metadata using the sf CLI.

## Pre-Deployment Checklist

Before any deployment, always:

1. **Preview the deployment**
   ```bash
   sf project deploy preview -d src/ -o <alias>
   ```
   - Shows what will be deployed
   - Identifies conflicts
   - Lists files excluded by .forceignore

2. **Validate first (dry-run)**
   ```bash
   sf project deploy start -d src/ -o <alias> --dry-run --test-level RunLocalTests
   ```
   - Tests deployment without committing changes
   - Runs tests to verify code quality
   - Identifies issues before actual deployment

3. **Check .forceignore**
   - Ensure temporary files are excluded
   - Verify no sensitive data is included
   - Common exclusions: `*.log`, `.sfdx/`, `node_modules/`

4. **Run tests locally** (if possible)
   - Execute Apex tests before deploying
   - Verify 75%+ code coverage
   - Fix any test failures

---

## Deployment Scenarios

### Deploy Single Component

**Use Case**: Quick fix to one class or component

```bash
# Apex class
sf project deploy start -m "ApexClass:MyClass" -o sandbox

# Aura component
sf project deploy start -m "AuraDefinitionBundle:MyComponent" -o sandbox

# LWC component
sf project deploy start -m "LightningComponentBundle:myComponent" -o sandbox

# Custom object
sf project deploy start -m "CustomObject:MyObject__c" -o sandbox
```

### Deploy Directory

**Use Case**: Deploy all changes in a specific folder

```bash
# Deploy Aura component directory
sf project deploy start -d src/aura/MyComponent/ -o sandbox

# Deploy all Apex classes
sf project deploy start -d src/classes/ -o sandbox

# Deploy entire src directory
sf project deploy start -d src/ -o sandbox
```

### Deploy with Tests

**Use Case**: Production deployment or validation

```bash
# Run local tests (tests in your package)
sf project deploy start -d src/ -o production --test-level RunLocalTests

# Run all tests in org
sf project deploy start -d src/ -o production --test-level RunAllTestsInOrg

# Run specific test classes
sf project deploy start -d src/ -o production --test-level RunSpecifiedTests --tests "MyTest, AnotherTest"

# No tests (sandbox only - not recommended)
sf project deploy start -d src/ -o sandbox --test-level NoTestRun
```

### Deploy with Extended Wait Time

**Use Case**: Large deployments that take longer

```bash
# Wait up to 60 minutes (default is 33)
sf project deploy start -d src/ -o production --test-level RunLocalTests --wait 60
```

### Deploy from package.xml

**Use Case**: Deploy specific components using manifest

```bash
# Create package.xml first, then:
sf project deploy start -x manifest/package.xml -o <alias>
```

---

## Retrieval Scenarios

### Retrieve Single Component

```bash
# Specific Apex class
sf project retrieve start -m "ApexClass:PaymentsBL" -o sandbox

# Specific Aura component
sf project retrieve start -m "AuraDefinitionBundle:CreatePayments" -o sandbox

# Specific custom object
sf project retrieve start -m "CustomObject:Standing_Order_Info__c" -o sandbox
```

### Retrieve All of a Type

```bash
# All Apex classes
sf project retrieve start -m "ApexClass" -o sandbox

# All Aura components
sf project retrieve start -m "AuraDefinitionBundle" -o sandbox

# All custom objects
sf project retrieve start -m "CustomObject" -o sandbox
```

### Retrieve Multiple Types

```bash
# Multiple types in one command
sf project retrieve start -m "ApexClass, ApexTrigger, AuraDefinitionBundle" -o sandbox
```

### Retrieve from package.xml

```bash
sf project retrieve start -x manifest/package.xml -o sandbox
```

### Retrieve to Specific Directory

```bash
sf project retrieve start -m "ApexClass" -o sandbox -d retrieved/
```

---

## Error Handling

### Check Deployment Status

```bash
# Check latest deployment
sf project deploy report -o <alias>

# Check specific deployment by ID
sf project deploy report -i 0AfXXXXXXXXXXXXXXX -o <alias>
```

### Cancel In-Progress Deployment

```bash
sf project deploy cancel -i 0AfXXXXXXXXXXXXXXX -o <alias>
```

### Common Errors and Solutions

#### Error: "INVALID_CROSS_REFERENCE_KEY"
**Cause**: Deploying component that references non-existent record

**Solution**:
- Deploy dependencies first
- Check for hard-coded IDs
- Verify lookup relationships exist in target org

#### Error: "FIELD_CUSTOM_VALIDATION_EXCEPTION"
**Cause**: Validation rule prevents deployment

**Solution**:
- Temporarily deactivate validation rules
- Ensure test data meets validation criteria
- Deploy validation rules separately

#### Error: "INSUFFICIENT_ACCESS"
**Cause**: User lacks permissions

**Solution**:
- Verify org permissions
- Check profile/permission set access
- Use admin user for deployment

#### Error: "CANNOT_DELETE_MANAGED_OBJECT"
**Cause**: Attempting to delete managed package components

**Solution**:
- Cannot delete managed components via metadata API
- Remove from package.xml if using manifest
- Uninstall package if necessary

#### Error: "This deployment includes changes to...which are currently org-dependent"
**Cause**: Deploying org-dependent metadata

**Solution**:
- Deploy to similar org configuration
- Remove org-dependent components
- Check Salesforce documentation for restrictions

---

## Best Practices

### 1. Always Preview First
```bash
sf project deploy preview -d src/ -o <alias>
```
- See what will change
- Identify conflicts before deploying
- Verify .forceignore is working correctly

### 2. Use Dry-Run for Validation
```bash
sf project deploy start -d src/ -o production --dry-run --test-level RunLocalTests
```
- Validate production deployments
- Catch errors without affecting org
- Verify tests pass before actual deployment

### 3. Incremental Deployments
- Deploy one feature at a time
- Easier to identify issues
- Faster rollback if problems occur
- Better change tracking

### 4. Test Levels for Different Environments

**Sandbox**:
```bash
sf project deploy start -d src/ -o sandbox --test-level NoTestRun
```

**UAT/Pre-Production**:
```bash
sf project deploy start -d src/ -o uat --test-level RunLocalTests
```

**Production**:
```bash
sf project deploy start -d src/ -o production --test-level RunLocalTests
```

### 5. Use .forceignore Effectively

```
# Package directories
**/package.json
**/node_modules/**

# Logs and temp files
**/*.log
.sfdx/**

# Local config
.vscode/**
.idea/**

# Generated files
**/.eslintcache
```

### 6. Deployment Sequence for Dependencies

Deploy in this order to avoid dependency errors:

1. Custom Objects
2. Custom Fields
3. Record Types
4. Page Layouts
5. Permission Sets
6. Apex Classes (without triggers)
7. Triggers
8. Flows
9. Validation Rules
10. UI Components (Aura/LWC)

### 7. Version Control Integration

```bash
# Commit before deploying
git add src/
git commit -m "feat: Add payment processing logic"

# Deploy to sandbox
sf project deploy start -d src/ -o sandbox

# After successful deployment, tag the release
git tag v1.2.3
git push origin v1.2.3
```

### 8. Rollback Strategy

```bash
# Retrieve current state before deployment
sf project retrieve start -x manifest/package.xml -o production -d backup/

# If deployment fails, redeploy from backup
sf project deploy start -d backup/ -o production
```

---

## Environment-Specific Patterns

### Sandbox Deployment
```bash
# Fast deployment without tests
sf project deploy start -d src/ -o sandbox --test-level NoTestRun

# With local tests for final validation
sf project deploy start -d src/ -o sandbox --test-level RunLocalTests
```

### Production Deployment
```bash
# Always run tests
sf project deploy start -d src/ -o production --test-level RunLocalTests --wait 60

# Critical deployments - run all tests
sf project deploy start -d src/ -o production --test-level RunAllTestsInOrg --wait 60
```

### Hot Fix Deployment
```bash
# Preview
sf project deploy preview -m "ApexClass:CriticalFix" -o production

# Validate
sf project deploy start -m "ApexClass:CriticalFix" -o production --dry-run --test-level RunLocalTests

# Deploy
sf project deploy start -m "ApexClass:CriticalFix" -o production --test-level RunLocalTests
```

---

## package.xml Templates

### Deploy All Metadata
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>*</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>*</members>
        <name>ApexTrigger</name>
    </types>
    <types>
        <members>*</members>
        <name>AuraDefinitionBundle</name>
    </types>
    <types>
        <members>*</members>
        <name>LightningComponentBundle</name>
    </types>
    <version>60.0</version>
</Package>
```

### Deploy Specific Components
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>PaymentsBL</members>
        <members>PaymentsBL_Test</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>CreatePayments</members>
        <name>AuraDefinitionBundle</name>
    </types>
    <version>60.0</version>
</Package>
```

---

## Troubleshooting Tips

### Deployment Stuck
- Check deployment status: `sf project deploy report -o <alias>`
- Cancel if necessary: `sf project deploy cancel -i <deploy-id> -o <alias>`
- Increase wait time: `--wait 60`

### Deployment Fails Silently
- Add `--json` flag to see detailed error messages
- Check deployment report for specific failures
- Review test failures if tests are running

### Components Not Deploying
- Verify components exist in source directory
- Check .forceignore isn't excluding them
- Ensure proper directory structure
- Use `sf project deploy preview` to verify

---

## Automation Example

```bash
#!/bin/bash
# Automated deployment script

ORG=$1
PATH_TO_DEPLOY=${2:-src/}

echo "🔍 Previewing deployment..."
sf project deploy preview -d "$PATH_TO_DEPLOY" -o "$ORG"

echo "✅ Validating deployment..."
sf project deploy start -d "$PATH_TO_DEPLOY" -o "$ORG" --dry-run --test-level RunLocalTests

if [ $? -eq 0 ]; then
    echo "🚀 Deploying to $ORG..."
    sf project deploy start -d "$PATH_TO_DEPLOY" -o "$ORG" --test-level RunLocalTests --wait 30
    echo "✅ Deployment complete!"
else
    echo "❌ Validation failed. Deployment aborted."
    exit 1
fi
```

Usage:
```bash
./deploy.sh production src/classes/
```
