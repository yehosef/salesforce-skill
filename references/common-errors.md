# Common Salesforce Errors & Solutions

Quick reference for the most common Salesforce deployment, development, and runtime errors with practical solutions.

## Deployment Errors

### INVALID_CROSS_REFERENCE_KEY
**Error Message**: "invalid cross reference id"

**Cause**: Deploying a component that references a record ID or metadata that doesn't exist in the target org.

**Solutions**:
```bash
# 1. Deploy dependencies first
sf project deploy start -m "CustomObject:Parent__c" -o <alias>
# Then deploy the dependent component
sf project deploy start -m "CustomObject:Child__c" -o <alias>

# 2. Remove hard-coded IDs from code
# Search for hard-coded IDs in your code:
grep -r "00[135][a-zA-Z0-9]{15}" src/

# 3. Check lookup/master-detail relationships exist
sf data query -q "SELECT Id, DeveloperName FROM RecordType WHERE SObjectType='Account'" -o <alias>
```

---

### FIELD_CUSTOM_VALIDATION_EXCEPTION
**Error Message**: "FIELD_CUSTOM_VALIDATION_EXCEPTION: Validation formula evaluated to false"

**Cause**: Validation rule is blocking the deployment or data operation.

**Solutions**:
```bash
# Option 1: Temporarily deactivate validation rules (use with caution!)
# Deploy without activating:
# 1. Set validation rules to inactive in metadata
# 2. Deploy
# 3. Re-activate after deployment

# Option 2: Create test data that passes validation
# In test class:
@TestSetup
static void setup() {
    Account acc = new Account(
        Name = 'Test',
        Industry = 'Technology',  // Required by validation
        BillingCountry = 'USA'     // Required by validation
    );
    insert acc;
}

# Option 3: Deploy validation rules separately
sf project deploy start -m "ValidationRule" -o <alias>
```

---

### CANNOT_INSERT_UPDATE_ACTIVATE_ENTITY
**Error Message**: "CANNOT_INSERT_UPDATE_ACTIVATE_ENTITY: Trigger error"

**Cause**: Error in trigger code during deployment or execution.

**Solutions**:
```bash
# 1. Check trigger for errors in debug log
sf apex log tail -o <alias>

# 2. Deploy trigger without activation
# Use ToolingAPI to deploy inactive

# 3. Test trigger with single record first
# In test class:
@isTest
static void testTrigger() {
    Account acc = new Account(Name = 'Test');
    Test.startTest();
    insert acc;  // Trigger fires here
    Test.stopTest();
}

# 4. Add try-catch in trigger for debugging
trigger AccountTrigger on Account (before insert) {
    try {
        // Your logic
    } catch (Exception e) {
        System.debug('Trigger error: ' + e.getMessage());
        System.debug('Stack trace: ' + e.getStackTraceString());
    }
}
```

---

### INSUFFICIENT_ACCESS
**Error Message**: "insufficient access rights on cross-reference id" or "insufficient access rights on object"

**Cause**: User/profile lacks permissions for deployment or operation.

**Solutions**:
```bash
# 1. Deploy with admin user
sf config set target-org=admin-alias

# 2. Check and update profile permissions
sf data query -q "SELECT Id, Name, PermissionsModifyAllData FROM Profile WHERE Name='System Administrator'" -o <alias>

# 3. Deploy permission sets with the code
sf project deploy start -m "PermissionSet:MyPermSet" -o <alias>

# 4. Grant temporary permissions
# Via Setup → Permission Sets → Assign to deployment user
```

---

### CANNOT_DELETE_MANAGED_OBJECT
**Error Message**: "cannot delete managed object"

**Cause**: Attempting to delete components from a managed package.

**Solutions**:
```bash
# 1. Remove from package.xml if using manifest
# Edit package.xml and remove managed components

# 2. Uninstall package if truly not needed
# Setup → Installed Packages → Uninstall

# 3. Cannot delete managed components via metadata API
# This is a Salesforce limitation - managed packages can only be uninstalled
```

---

### FIELD_NOT_WRITEABLE
**Error Message**: "Field is not writeable: ObjectName.fieldName"

**Cause**: Your code attempts to update a field that Salesforce doesn't allow to be written to. Common causes:
- **Formula fields** - Calculated values, not stored (read-only by design)
- **Roll-up summary fields** - Aggregated values, not directly updatable
- **External fields** - Integration fields, not directly updatable
- **System fields** - CreatedDate, LastModifiedDate, CreatedById, etc.
- **Read-only custom fields** - Field-level security or field definition settings
- **Lookup fields on certain objects** - Some objects don't allow direct lookup updates

**Solutions**:

```apex
// Solution 1: Update parent/lookup records instead
Account parent = [SELECT Id FROM Account WHERE Name = 'Parent'];

// DON'T do this:
Contact c = new Contact(AccountId = '001...');  // If Account lookup is read-only
c.Account__c = parent.Id;  // ✗ NOT WRITEABLE
update c;

// DO this instead:
Contact c = new Contact(AccountId = parent.Id);  // Use standard relationship
update c;

// Solution 2: Check if field is writeable before updating
Map<String, SObjectField> fields = Account.getSObjectType().getDescribe().fields.getMap();
SObjectField field = fields.get('CustomField__c');
if (field.getDescribe().isUpdateable()) {
    // Safe to update
    acc.CustomField__c = value;
    update acc;
}

// Solution 3: Use alternative fields
// If Quote.Group_Name__c is not writeable, use different field
Quote q = [SELECT Id, Name FROM Quote WHERE Id = :quoteId];
// Update OpportunityId instead, which is updateable
q.OpportunityId = newOppId;
update q;
```

**Prevention**:

```bash
# 1. Validate field writeability before deployment
./scripts/validate_field_writeability.py src/ your-org

# 2. Check field metadata in Salesforce CLI
sf sobject describe -s Quote -o your-org | grep "Group_Name"

# 3. Review field definition in Setup
# Setup → Object Manager → ObjectName → Fields → FieldName → Check "Writeable"

# 4. Use isUpdateable() in tests
Apex:
Boolean canUpdate = Schema.Quote.Group_Name__c.getDescribe().isUpdateable();

JavaScript/LWC:
import { getFieldValue } from 'lightning/uiRecordApi';
```

**Common Objects with Read-Only Lookup Fields**:
- `Quote.Group_Name__c` - Often a formula or external field
- `Quote.OpportunityId` - Locked after Quote creation in certain orgs
- `Task.WhatId` - Can be read-only depending on config
- `Event.WhatId` - Can be read-only depending on config

**Quick Check**:
```apex
// Get field info
Map<String, SObjectField> fields = Account.getSObjectType()
    .getDescribe()
    .fields
    .getMap();

SObjectField customField = fields.get('CustomField__c');
DescribeFieldResult dfr = customField.getDescribe();

System.debug('Updateable: ' + dfr.isUpdateable());        // false = read-only
System.debug('Type: ' + dfr.getType());                    // Can indicate reason
System.debug('Is Calculated: ' + dfr.isCalculated());      // Formula field?
System.debug('Label: ' + dfr.getLabel());                  // Field name for debugging
```

---

## Runtime Errors

### UNABLE_TO_LOCK_ROW
**Error Message**: "UNABLE_TO_LOCK_ROW: unable to obtain exclusive access to this record"

**Cause**: Another process is modifying the same record simultaneously (record locking conflict).

**Solutions**:
```apex
// Solution 1: Retry with exponential backoff
public static void updateWithRetry(Id recordId, Integer maxRetries) {
    Integer attempts = 0;
    while (attempts < maxRetries) {
        try {
            Account acc = [SELECT Id, Status__c FROM Account WHERE Id = :recordId FOR UPDATE];
            acc.Status__c = 'Updated';
            update acc;
            break;  // Success
        } catch (DmlException e) {
            if (e.getMessage().contains('UNABLE_TO_LOCK_ROW')) {
                attempts++;
                if (attempts >= maxRetries) throw e;
                // Wait before retry (exponential backoff)
                Integer waitTime = 100 * Math.pow(2, attempts).intValue();
                // Note: Apex doesn't have sleep, use Database.executeBatch for retry logic
            } else {
                throw e;
            }
        }
    }
}

// Solution 2: Use FOR UPDATE to lock record first
List<Account> accounts = [SELECT Id FROM Account WHERE Id = :recordId FOR UPDATE];

// Solution 3: Reduce concurrent processes
// Avoid parallel workflows/flows on same record
```

---

### TOO_MANY_SOQL_QUERIES: 101
**Error Message**: "System.LimitException: Too many SOQL queries: 101"

**Cause**: Exceeded 100 SOQL query limit in a single transaction.

**Solutions**:
```apex
// ❌ BAD - Query in loop
for (Account acc : accounts) {
    List<Contact> contacts = [SELECT Id FROM Contact WHERE AccountId = :acc.Id];
}

// ✅ GOOD - Single query, use map
Map<Id, List<Contact>> contactsByAccount = new Map<Id, List<Contact>>();
List<Contact> allContacts = [SELECT Id, AccountId FROM Contact WHERE AccountId IN :accountIds];
for (Contact c : allContacts) {
    if (!contactsByAccount.containsKey(c.AccountId)) {
        contactsByAccount.put(c.AccountId, new List<Contact>());
    }
    contactsByAccount.get(c.AccountId).add(c);
}

// ✅ Use relationship queries
List<Account> accounts = [
    SELECT Id, (SELECT Id, Name FROM Contacts)
    FROM Account
    WHERE Id IN :accountIds
];
```

---

### TOO_MANY_DML_STATEMENTS: 151
**Error Message**: "System.LimitException: Too many DML statements: 151"

**Cause**: Exceeded 150 DML operation limit.

**Solutions**:
```apex
// ❌ BAD - DML in loop
for (Contact c : contacts) {
    c.Status__c = 'Active';
    update c;  // DML in loop!
}

// ✅ GOOD - Bulk DML
List<Contact> contactsToUpdate = new List<Contact>();
for (Contact c : contacts) {
    c.Status__c = 'Active';
    contactsToUpdate.add(c);
}
if (!contactsToUpdate.isEmpty()) {
    update contactsToUpdate;  // Single DML
}

// ✅ BEST - Use Database methods for partial success
Database.SaveResult[] results = Database.update(contactsToUpdate, false);
for (Database.SaveResult sr : results) {
    if (!sr.isSuccess()) {
        for (Database.Error err : sr.getErrors()) {
            System.debug('Error: ' + err.getMessage());
        }
    }
}
```

---

### APEX_CPU_TIME_LIMIT_EXCEEDED
**Error Message**: "System.LimitException: Apex CPU time limit exceeded"

**Cause**: Code execution exceeded 10-second CPU limit (synchronous).

**Solutions**:
```apex
// Solution 1: Optimize loops
// ❌ BAD - Nested loops
for (Account acc : accounts) {
    for (Contact c : contacts) {
        if (c.AccountId == acc.Id) {
            // Process
        }
    }
}

// ✅ GOOD - Use map
Map<Id, Account> accountMap = new Map<Id, Account>(accounts);
for (Contact c : contacts) {
    Account acc = accountMap.get(c.AccountId);
    // Process in O(1) time
}

// Solution 2: Move to @future for more time
@future
public static void processAsync(Set<Id> recordIds) {
    // Gets 60 seconds instead of 10
}

// Solution 3: Use Batch Apex for large datasets
global class MyBatch implements Database.Batchable<SObject> {
    global Database.QueryLocator start(Database.BatchableContext BC) {
        return Database.getQueryLocator('SELECT Id FROM Account');
    }

    global void execute(Database.BatchableContext BC, List<Account> scope) {
        // Process 200 records at a time
        // Fresh governor limits per batch
    }

    global void finish(Database.BatchableContext BC) {}
}
```

---

### HEAP_SIZE_LIMIT_EXCEEDED
**Error Message**: "System.LimitException: Apex heap size too large"

**Cause**: Memory usage exceeded 6 MB limit.

**Solutions**:
```apex
// ❌ BAD - Accumulating large collections
List<Account> allAccounts = new List<Account>();
for (Integer i = 0; i < 50000; i++) {
    allAccounts.addAll([SELECT Id FROM Account LIMIT 100]);
}

// ✅ GOOD - Process in batches, clear memory
for (List<Account> batch : [SELECT Id FROM Account]) {
    // Process 200 records
    // Batch cleared after loop iteration
}

// ❌ BAD - String concatenation in loop
String result = '';
for (Integer i = 0; i < 10000; i++) {
    result += 'value' + i;  // Creates new string each time!
}

// ✅ GOOD - Use list then join
List<String> parts = new List<String>();
for (Integer i = 0; i < 10000; i++) {
    parts.add('value' + i);
}
String result = String.join(parts, '');
```

---

## Test Failures

### System.AssertException: Assertion Failed
**Error Message**: "System.AssertException: Assertion Failed: Expected X but was Y"

**Cause**: Test assertion failed - actual value doesn't match expected.

**Solutions**:
```apex
// Solution 1: Add debug statements
System.debug('Expected: ' + expectedValue);
System.debug('Actual: ' + actualValue);
System.assertEquals(expectedValue, actualValue, 'Values should match');

// Solution 2: Query again after DML
Account acc = new Account(Name = 'Test');
insert acc;

Test.startTest();
MyClass.processAccount(acc.Id);
Test.stopTest();

// Re-query to get updated values
Account updated = [SELECT Id, Status__c FROM Account WHERE Id = :acc.Id];
System.assertEquals('Processed', updated.Status__c);

// Solution 3: Use Test.startTest/stopTest for async operations
Test.startTest();
MyClass.callFutureMethod(acc.Id);
Test.stopTest();  // Future completes here

// Now check results
```

---

### REQUIRED_FIELD_MISSING
**Error Message**: "REQUIRED_FIELD_MISSING: Required fields are missing"

**Cause**: Required field not populated in test data or actual operation.

**Solutions**:
```apex
// Solution 1: Include all required fields
Account acc = new Account(
    Name = 'Test',                  // Required
    Industry = 'Technology',        // Required (if validation exists)
    BillingCountry = 'USA'          // Required (if validation exists)
);
insert acc;

// Solution 2: Check object describe for required fields
Map<String, Schema.SObjectField> fieldMap = Schema.SObjectType.Account.fields.getMap();
for (String fieldName : fieldMap.keySet()) {
    Schema.DescribeFieldResult dfr = fieldMap.get(fieldName).getDescribe();
    if (!dfr.isNillable() && !dfr.isDefaultedOnCreate()) {
        System.debug('Required field: ' + fieldName);
    }
}

// Solution 3: Use @TestSetup with complete data
@TestSetup
static void setup() {
    Account acc = TestDataFactory.createAccount(true);  // All required fields
    insert acc;
}
```

---

## Quick Diagnostic Commands

### Check Governor Limit Usage
```bash
# View current limits in debug log
sf apex log tail -o <alias>

# Or add to code:
System.debug('SOQL Queries: ' + Limits.getQueries() + '/' + Limits.getLimitQueries());
System.debug('DML Statements: ' + Limits.getDmlStatements() + '/' + Limits.getLimitDmlStatements());
System.debug('CPU Time: ' + Limits.getCpuTime() + '/' + Limits.getLimitCpuTime());
System.debug('Heap Size: ' + Limits.getHeapSize() + '/' + Limits.getLimitHeapSize());
```

### Find Deployment Failures
```bash
# Check latest deployment status
sf project deploy report -o <alias>

# Get specific deployment details
sf project deploy report -i <deploy-id> -o <alias> --json
```

### Analyze Test Failures
```bash
# Run tests and see detailed failures
sf apex test run -n MyClassTest -o <alias> -c --json

# Get specific test results
sf apex test report -i <test-run-id> -o <alias>
```

---

## Prevention Checklist

Before deploying, always:

✅ Run `sf project deploy preview` to see what will change
✅ Use `--dry-run` to validate without deploying
✅ Run tests: `--test-level RunLocalTests`
✅ Check code coverage: Must be ≥75% for production
✅ Review debug logs for warnings
✅ Check governor limit usage in tests
✅ Verify all dependencies exist in target org

---

## Common Error Patterns

| Error Pattern | Root Cause | Quick Fix |
|---------------|------------|-----------|
| INVALID_CROSS_REFERENCE | Missing dependency | Deploy parent first |
| UNABLE_TO_LOCK_ROW | Concurrent updates | Add retry logic |
| TOO_MANY_SOQL | Query in loop | Bulkify with map |
| TOO_MANY_DML | DML in loop | Collect and bulk update |
| CPU_TIME_LIMIT | Inefficient code | Use maps, avoid nested loops |
| HEAP_SIZE_LIMIT | Large collections | Process in batches |
| INSUFFICIENT_ACCESS | Permission issue | Deploy with admin or add permission set |
| FIELD_VALIDATION | Validation rule | Bypass or fix test data |

---

## Emergency Troubleshooting

When deployment fails in production:

1. **Get deployment ID** from error message or:
   ```bash
   sf project deploy report -o production
   ```

2. **Check what failed**:
   ```bash
   sf project deploy report -i <deploy-id> -o production --json | grep -A 10 "componentFailures"
   ```

3. **Quick rollback** (if you have backup):
   ```bash
   sf project deploy start -d backup/ -o production --test-level NoTestRun
   ```

4. **Cancel stuck deployment**:
   ```bash
   sf project deploy cancel -i <deploy-id> -o production
   ```

5. **Emergency: Skip tests** (use only in extreme cases):
   ```bash
   # Not recommended - only for critical hotfixes
   sf project deploy start -d src/ -o production --test-level NoTestRun
   ```

---

## Validation Tools

### validate_field_writeability.py
**Purpose**: Pre-deployment validation of field writeability to catch `FIELD_NOT_WRITEABLE` errors early.

**Usage**:
```bash
# Check for field writeability issues in src/
./scripts/validate_field_writeability.py src/ my-sandbox

# Verbose output to see all fields checked
./scripts/validate_field_writeability.py src/ production --verbose

# JSON output for CI/CD integration
./scripts/validate_field_writeability.py src/ staging --json
```

**Detection Patterns**:
This validator detects field assignments in Apex code:
- Direct assignment: `account.CustomField__c = value`
- Constructor: `new Account(CustomField__c = value)`
- Array/List: `accounts[0].CustomField__c = value`
- Dynamic put(): `obj.put('CustomField__c', value)` [field detected, SObject type unknown]

**Example: Detecting put() pattern**:
```apex
// This pattern is detected:
Map<String, Object> fields = new Map<String, Object>();
fields.put('Group_Name__c', 'NewValue');  // ← Detected as field assignment
account.putAll(fields);

// But SObject type cannot be determined from put() alone
// The validator will warn that manual review is needed
```

**Limitations**:
- `obj.put(variableName, value)` - Cannot detect if field name is in a variable
- Dynamic reflection: `obj.setSObjectField(...)` - Not detected

---

### validate_visualforce.py
**Purpose**: Validate Visualforce syntax and catch unsupported attributes before deployment.

**Usage**:
```bash
# Check all VF files in src/
./scripts/validate_visualforce.py src/

# Verbose output
./scripts/validate_visualforce.py src/ --verbose

# JSON output for CI/CD
./scripts/validate_visualforce.py src/ --json > vf-report.json
```

**Security Features**:
- **XXE Protection**: XML parsing uses `resolve_entities=False` (Python 3.8+) or `defusedxml` for enhanced protection
- **Path Traversal Protection**: Validates file paths to prevent symlink attacks
- **File Size Limits**: Maximum 10MB per file to prevent DoS

**Detection Examples**:
```xml
<!-- ✗ ERROR: Unsupported attribute 'dir' -->
<apex:page dir="rtl">

<!-- ✓ FIX: Use CSS instead -->
<apex:page>
    <div style="direction: rtl; text-align: right;">
        <!-- content -->
    </div>
</apex:page>

<!-- ✗ WARNING: Deprecated tag -->
<apex:include pageName="OtherPage"/>

<!-- ✓ FIX: Use apex:dynamicComponent instead -->
<apex:dynamicComponent componentVar="{!dynamicComp}"/>
```

---

## Resources

- **Debug Logs**: Setup → Debug Logs → Add trace flag
- **Deployment History**: Setup → Deployment Status
- **Governor Limits Dashboard**: Setup → System Overview → Limits
- **Error Documentation**: https://developer.salesforce.com/docs/atlas.en-us.api.meta/api/sforce_api_calls_concepts_core_data_objects.htm
