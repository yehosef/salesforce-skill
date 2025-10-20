# Salesforce Governor Limits

Reference guide for Salesforce governor limits and strategies to avoid hitting them.

## What Are Governor Limits?

Salesforce enforces execution limits to ensure platform stability and fair resource usage. When code exceeds these limits, it throws a `System.LimitException`.

---

## Key Limits by Category

### SOQL Queries

| Limit | Synchronous | Asynchronous |
|-------|-------------|--------------|
| Total SOQL queries | 100 | 200 |
| Records retrieved by SOQL | 50,000 | 50,000 |
| Records retrieved by Database.getQueryLocator | 10,000 | 10,000 |

**Common Error**: "Too many SOQL queries: 101"

**Solution**:
```apex
// ❌ BAD - Query in loop
for (Account acc : accounts) {
    List<Contact> contacts = [SELECT Id FROM Contact WHERE AccountId = :acc.Id];
}

// ✅ GOOD - Single query
Set<Id> accountIds = (new Map<Id, Account>(accounts)).keySet();
List<Contact> contacts = [SELECT Id, AccountId FROM Contact WHERE AccountId IN :accountIds];
Map<Id, List<Contact>> contactsByAccount = new Map<Id, List<Contact>>();
for (Contact c : contacts) {
    if (!contactsByAccount.containsKey(c.AccountId)) {
        contactsByAccount.put(c.AccountId, new List<Contact>());
    }
    contactsByAccount.get(c.AccountId).add(c);
}
```

---

### DML Operations

| Limit | Synchronous | Asynchronous |
|-------|-------------|--------------|
| Total DML statements | 150 | 150 |
| Total records processed by DML | 10,000 | 10,000 |

**Common Error**: "Too many DML statements: 151"

**Solution**:
```apex
// ❌ BAD - DML in loop
for (Contact c : contacts) {
    c.Status__c = 'Active';
    update c;
}

// ✅ GOOD - Bulk DML
List<Contact> contactsToUpdate = new List<Contact>();
for (Contact c : contacts) {
    c.Status__c = 'Active';
    contactsToUpdate.add(c);
}
update contactsToUpdate;
```

---

### CPU Time

| Limit | Synchronous | Asynchronous |
|-------|-------------|--------------|
| Total CPU time | 10,000 ms (10 sec) | 60,000 ms (60 sec) |

**Common Error**: "Apex CPU time limit exceeded"

**Causes**:
- Complex loops
- Inefficient algorithms
- Processing large data sets
- Excessive string manipulation

**Solutions**:
```apex
// ❌ BAD - Inefficient nested loops
for (Account acc : accounts) {
    for (Contact c : contacts) {
        if (c.AccountId == acc.Id) {
            // Process
        }
    }
}

// ✅ GOOD - Use maps
Map<Id, Account> accountMap = new Map<Id, Account>(accounts);
for (Contact c : contacts) {
    Account acc = accountMap.get(c.AccountId);
    if (acc != null) {
        // Process
    }
}
```

---

### Heap Size

| Limit | Synchronous | Asynchronous |
|-------|-------------|--------------|
| Total heap size | 6 MB | 12 MB |

**Common Error**: "Apex heap size too large"

**Causes**:
- Large collections in memory
- Storing too many records
- Large string concatenation

**Solutions**:
```apex
// ❌ BAD - Accumulating large strings
String result = '';
for (Integer i = 0; i < 10000; i++) {
    result += 'value' + i;  // Creates new string each iteration
}

// ✅ GOOD - Use string builder pattern
List<String> parts = new List<String>();
for (Integer i = 0; i < 10000; i++) {
    parts.add('value' + i);
}
String result = String.join(parts, '');

// ✅ BEST - Process in batches
for (List<Account> batch : [SELECT Id FROM Account]) {
    // Process 200 records at a time
    // Batch completes, heap clears
}
```

---

### Callouts

| Limit | Value |
|-------|-------|
| Total HTTP callouts | 100 |
| Max callout time per request | 120 seconds |
| Max callout size (request/response) | 6 MB |

**Solution**:
- Minimize number of callouts
- Use @future or Queueable for async callouts
- Batch multiple operations in single callout

---

### Email

| Limit | Value |
|-------|-------|
| Single email messages | 10 |
| Mass email messages | 10 |
| Total emails per day | 5,000 (or user licenses × 10) |

---

## Checking Limits in Code

### Query Current Usage
```apex
// SOQL queries used
Integer soqlUsed = Limits.getQueries();
Integer soqlLimit = Limits.getLimitQueries();
System.debug('SOQL: ' + soqlUsed + ' / ' + soqlLimit);

// DML statements used
Integer dmlUsed = Limits.getDmlStatements();
Integer dmlLimit = Limits.getLimitDmlStatements();
System.debug('DML: ' + dmlUsed + ' / ' + dmlLimit);

// CPU time used
Integer cpuUsed = Limits.getCpuTime();
Integer cpuLimit = Limits.getLimitCpuTime();
System.debug('CPU: ' + cpuUsed + ' / ' + cpuLimit);

// Heap size used
Integer heapUsed = Limits.getHeapSize();
Integer heapLimit = Limits.getLimitHeapSize();
System.debug('Heap: ' + heapUsed + ' / ' + heapLimit);
```

### Conditional Logic Based on Limits
```apex
if (Limits.getQueries() >= Limits.getLimitQueries() - 10) {
    // Approaching query limit, take action
    throw new CustomException('Approaching SOQL limit');
}
```

---

## Bulkification Patterns

### Pattern 1: Bulkify SOQL
```apex
// Get all related records in one query
Set<Id> accountIds = new Set<Id>();
for (Opportunity opp : opportunities) {
    accountIds.add(opp.AccountId);
}
Map<Id, Account> accountMap = new Map<Id, Account>(
    [SELECT Id, Name, Industry FROM Account WHERE Id IN :accountIds]
);
```

### Pattern 2: Bulkify DML
```apex
// Collect all changes, then execute once
List<Contact> contactsToUpdate = new List<Contact>();
for (Account acc : accounts) {
    for (Contact c : acc.Contacts) {
        c.AccountName__c = acc.Name;
        contactsToUpdate.add(c);
    }
}
update contactsToUpdate;
```

### Pattern 3: Use Maps for Lookups
```apex
// Build map once, lookup many times
Map<Id, Account> accountMap = new Map<Id, Account>(accounts);
for (Contact c : contacts) {
    Account acc = accountMap.get(c.AccountId);
    // Process
}
```

---

## Async Processing for Heavy Operations

### @future Method
```apex
@future
public static void processHeavyWork(Set<Id> recordIds) {
    // Runs asynchronously
    // Gets: 200 SOQL, 60 sec CPU, 12 MB heap
}
```

### Queueable
```apex
public class HeavyProcessor implements Queueable {
    private List<Id> recordIds;

    public HeavyProcessor(List<Id> ids) {
        this.recordIds = ids;
    }

    public void execute(QueueableContext context) {
        // Process records
    }
}

// Enqueue
System.enqueueJob(new HeavyProcessor(recordIds));
```

### Batch Apex
```apex
global class AccountProcessor implements Database.Batchable<SObject> {
    global Database.QueryLocator start(Database.BatchableContext BC) {
        return Database.getQueryLocator('SELECT Id FROM Account');
    }

    global void execute(Database.BatchableContext BC, List<Account> scope) {
        // Process up to 200 records
        // Fresh governor limits for each batch
    }

    global void finish(Database.BatchableContext BC) {
        // Post-processing
    }
}

// Execute
Database.executeBatch(new AccountProcessor(), 200);
```

---

## Query Optimization

### Use Selective Queries
```apex
// ✅ GOOD - Uses indexed field
SELECT Id FROM Account WHERE Id = '001XXXXXXXXXXXXXXX'

// ❌ BAD - Not indexed, scans full table
SELECT Id FROM Account WHERE Description LIKE '%test%'
```

### Standard Indexed Fields
- Id
- Name
- OwnerId
- CreatedDate
- SystemModstamp
- RecordTypeId
- Master-Detail fields
- Lookup fields
- External ID fields

### Request Custom Index
For frequently queried non-indexed fields:
1. Open Salesforce support case
2. Request custom index on field
3. Provide query examples and use case

---

## Complete Limits Reference

### Per-Transaction Limits

| Resource | Synchronous | Asynchronous |
|----------|-------------|--------------|
| SOQL queries | 100 | 200 |
| SOQL query rows | 50,000 | 50,000 |
| SOSL queries | 20 | 20 |
| DML statements | 150 | 150 |
| DML rows | 10,000 | 10,000 |
| CPU time | 10,000 ms | 60,000 ms |
| Heap size | 6 MB | 12 MB |
| Callouts | 100 | 100 |
| Callout time | 120 sec | 120 sec |

### Platform Limits

| Resource | Limit |
|----------|-------|
| Batch Apex jobs in queue | 5 |
| Scheduled Apex jobs | 100 |
| @future calls per 24 hours | 250,000 or user licenses × 200 |
| Queueable jobs per transaction | 50 |
| Email invocations (single) | 10 |
| Email invocations (mass) | 10 |
| Total email per day | 5,000 or user licenses × 10 |

---

## Debugging Limit Issues

### Check Debug Logs
1. Setup → Debug Logs
2. Add user trace flag
3. Reproduce issue
4. Review log for:
   - `LIMIT_USAGE_FOR_NS` - Shows limits used
   - `CUMULATIVE_LIMIT_USAGE` - Running totals

### Debug Log Output
```
LIMIT_USAGE_FOR_NS|(default)|
  Number of SOQL queries: 42 out of 100
  Number of DML statements: 5 out of 150
  Maximum CPU time: 1234 out of 10000
  Maximum heap size: 1048576 out of 6291456
```

### System.debug Limits
```apex
System.debug('===== GOVERNOR LIMITS =====');
System.debug('SOQL Queries: ' + Limits.getQueries() + '/' + Limits.getLimitQueries());
System.debug('DML Statements: ' + Limits.getDmlStatements() + '/' + Limits.getLimitDmlStatements());
System.debug('CPU Time: ' + Limits.getCpuTime() + '/' + Limits.getLimitCpuTime());
System.debug('Heap Size: ' + Limits.getHeapSize() + '/' + Limits.getLimitHeapSize());
```

---

## Best Practices Summary

1. **Never Query or DML in Loops** - Always bulkify
2. **Use Maps for Relationships** - Avoid nested loops
3. **Process Large Datasets in Batches** - Use Batch Apex or SOQL for loops
4. **Monitor Limits Proactively** - Use Limits class
5. **Use Indexed Fields** - Query performance and selectivity
6. **Offload to Async** - Use @future, Queueable, or Batch for heavy processing
7. **Optimize Algorithms** - Reduce CPU time with efficient code
8. **Manage Heap** - Don't accumulate large collections
