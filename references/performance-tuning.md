# Salesforce Performance Tuning Guide

Comprehensive guide for optimizing SOQL queries, Apex code, and governor limit management.

## Table of Contents

1. [Overview](#overview)
2. [SOQL Query Optimization](#soql-query-optimization)
3. [Apex CPU Time Optimization](#apex-cpu-time-optimization)
4. [Heap Size Optimization](#heap-size-optimization)
5. [Bulkification Patterns](#bulkification-patterns)
6. [Asynchronous Processing](#asynchronous-processing)
7. [Governor Limit Management](#governor-limit-management)
8. [Database Optimization](#database-optimization)
9. [Lightning Component Performance](#lightning-component-performance)
10. [Profiling and Monitoring](#profiling-and-monitoring)

---

## Overview

### Salesforce Performance Challenges

Common performance issues:
- Slow SOQL queries (missing indexes, large data volumes)
- CPU timeout errors (complex calculations, loops)
- Heap size exceptions (large collections in memory)
- Too many SOQL queries (non-bulkified code)
- View state too large (Lightning/Visualforce pages)

### Governor Limits Quick Reference

| Resource | Synchronous | Asynchronous |
|----------|-------------|--------------|
| **SOQL Queries** | 100 | 200 |
| **DML Statements** | 150 | 150 |
| **CPU Time** | 10,000 ms | 60,000 ms |
| **Heap Size** | 6 MB | 12 MB |
| **Records Retrieved** | 50,000 | 50,000 |
| **Email Invocations** | 10 | 10 |

Full reference: `governor-limits.md`

---

## SOQL Query Optimization

### Rule 1: Use Indexed Fields in WHERE Clauses

**Indexed Fields** (automatic):
- Id
- Name
- RecordTypeId
- CreatedDate
- SystemModstamp
- OwnerId (on most objects)
- Lookup/Master-Detail fields
- External ID fields (custom)

**Example: Optimized Query**

```sql
-- FAST: Uses indexed field (Id)
SELECT Id, Name FROM Account WHERE Id = '001xxxxxxxxxxxxxxx'

-- FAST: Uses indexed field (OwnerId)
SELECT Id, Name FROM Opportunity WHERE OwnerId = '005xxxxxxxxxxxxxxx'

-- FAST: Uses custom indexed field
SELECT Id, Name FROM Contact WHERE External_Id__c = 'EXT-12345'
```

**Example: Unoptimized Query**

```sql
-- SLOW: Non-indexed custom field
SELECT Id, Name FROM Account WHERE Custom_Status__c = 'Active'

-- SLOW: Function on indexed field (prevents index use)
SELECT Id, Name FROM Contact WHERE YEAR(CreatedDate) = 2024
```

### Rule 2: Limit Result Set Size

Always use `LIMIT` clause:

```sql
-- GOOD: Limited to 1000 records
SELECT Id, Name FROM Account WHERE Industry = 'Technology' LIMIT 1000

-- BAD: Could retrieve millions of records
SELECT Id, Name FROM Account WHERE Industry = 'Technology'
```

### Rule 3: Selective Queries (Filter Ratio)

Salesforce query optimizer requires **selective queries** (filters return <10% of total records).

**Check Selectivity**:

```sql
-- Total records
SELECT COUNT(Id) FROM Account

-- Filtered records
SELECT COUNT(Id) FROM Account WHERE Industry = 'Technology'

-- If filtered / total < 0.1, query is selective
```

**Make Queries More Selective**:

```sql
-- Add more filters
SELECT Id, Name
FROM Account
WHERE Industry = 'Technology'
AND CreatedDate = THIS_YEAR
AND OwnerId = '005xxxxxxxxxxxxxxx'
```

### Rule 4: Avoid Query Locks with FOR UPDATE

If you need to prevent record locking conflicts:

```sql
-- Explicit lock
SELECT Id, Name FROM Account WHERE Id = :accountId FOR UPDATE

-- Prevents UNABLE_TO_LOCK_ROW errors in concurrent updates
```

### Rule 5: Use Relationship Queries Instead of Multiple Queries

**BAD: Multiple SOQL queries**

```apex
List<Account> accounts = [SELECT Id FROM Account LIMIT 10];
for (Account acc : accounts) {
    List<Contact> contacts = [SELECT Id FROM Contact WHERE AccountId = :acc.Id];
    // Process contacts
}
// Result: 11 SOQL queries (1 + 10)
```

**GOOD: Single relationship query**

```apex
List<Account> accounts = [
    SELECT Id, (SELECT Id FROM Contacts)
    FROM Account
    LIMIT 10
];
for (Account acc : accounts) {
    List<Contact> contacts = acc.Contacts;
    // Process contacts
}
// Result: 1 SOQL query
```

### Rule 6: Use Aggregate Functions

Instead of retrieving all records and counting in Apex:

**BAD: Retrieve all, count in Apex**

```apex
List<Opportunity> opps = [SELECT Id FROM Opportunity WHERE StageName = 'Closed Won'];
Integer count = opps.size(); // Wastes heap memory
```

**GOOD: Use COUNT() in SOQL**

```apex
Integer count = [SELECT COUNT() FROM Opportunity WHERE StageName = 'Closed Won'];
// No heap usage, faster
```

### Rule 7: Avoid Wildcards in LIKE Clauses

**SLOW: Leading wildcard (cannot use index)**

```sql
SELECT Id, Name FROM Account WHERE Name LIKE '%Corp'
```

**FAST: Trailing wildcard (can use index)**

```sql
SELECT Id, Name FROM Account WHERE Name LIKE 'Acme%'
```

### Rule 8: Use Query Plan Tool

Check if your query uses an index:

```sql
-- In Developer Console → Query Plan
SELECT Id, Name FROM Account WHERE Custom_Field__c = 'Value'
```

Query plan shows:
- **Index**: Query uses an index (fast)
- **Table Scan**: Query scans all records (slow)

---

## Apex CPU Time Optimization

### Understanding CPU Time

**What Counts as CPU Time**:
- Loops and iterations
- Complex calculations (math, string operations)
- Apex method calls
- DML operations (processing)
- SOQL queries (processing results)

**What Doesn't Count**:
- Database time (waiting for SOQL/DML)
- HTTP callout time (waiting for response)
- @future, Queueable wait time

### Rule 1: Avoid Nested Loops

**BAD: O(n²) complexity**

```apex
for (Account acc : accounts) {
    for (Contact con : contacts) {
        if (con.AccountId == acc.Id) {
            // Process
        }
    }
}
// 1000 accounts × 10,000 contacts = 10,000,000 iterations
```

**GOOD: Use Maps (O(n) complexity)**

```apex
Map<Id, Account> accountMap = new Map<Id, Account>(accounts);

for (Contact con : contacts) {
    if (accountMap.containsKey(con.AccountId)) {
        Account acc = accountMap.get(con.AccountId);
        // Process
    }
}
// 1000 + 10,000 = 11,000 iterations
```

### Rule 2: Minimize DML Inside Loops

**BAD: DML in loop**

```apex
for (Account acc : accounts) {
    acc.Name = acc.Name + ' (Updated)';
    update acc; // 100 DML statements if 100 accounts
}
```

**GOOD: Bulk DML**

```apex
List<Account> accountsToUpdate = new List<Account>();

for (Account acc : accounts) {
    acc.Name = acc.Name + ' (Updated)';
    accountsToUpdate.add(acc);
}

update accountsToUpdate; // 1 DML statement
```

### Rule 3: Use Collections Efficiently

**Use Maps for Lookups**:

```apex
// Create map for O(1) lookups
Map<Id, Contact> contactMap = new Map<Id, Contact>([
    SELECT Id, AccountId FROM Contact
]);

// Fast lookup
Contact con = contactMap.get(contactId);
```

**Use Sets for Uniqueness**:

```apex
Set<Id> accountIds = new Set<Id>();
for (Opportunity opp : opportunities) {
    accountIds.add(opp.AccountId);
}
// Automatically deduplicates
```

### Rule 4: Avoid Expensive String Operations

**SLOW: String concatenation in loop**

```apex
String result = '';
for (Integer i = 0; i < 1000; i++) {
    result += 'Value ' + i + ', ';
}
// Creates 1000 intermediate string objects
```

**FAST: Use StringBuilder pattern**

```apex
List<String> parts = new List<String>();
for (Integer i = 0; i < 1000; i++) {
    parts.add('Value ' + i);
}
String result = String.join(parts, ', ');
// Single string concatenation
```

### Rule 5: Cache Expensive Calculations

```apex
// BAD: Recalculate in loop
for (Account acc : accounts) {
    Decimal tax = calculateTax(acc.AnnualRevenue); // Expensive
    acc.Tax__c = tax;
}

// GOOD: Cache results
Map<Decimal, Decimal> taxCache = new Map<Decimal, Decimal>();

for (Account acc : accounts) {
    if (!taxCache.containsKey(acc.AnnualRevenue)) {
        taxCache.put(acc.AnnualRevenue, calculateTax(acc.AnnualRevenue));
    }
    acc.Tax__c = taxCache.get(acc.AnnualRevenue);
}
```

---

## Heap Size Optimization

### Understanding Heap Size

Heap stores:
- Collection variables (List, Set, Map)
- SOQL query results
- sObject variables
- String variables

### Rule 1: Don't Load Unnecessary Fields

**BAD: Load all fields**

```apex
List<Account> accounts = [SELECT FIELDS(ALL) FROM Account LIMIT 10000];
// Huge heap usage
```

**GOOD: Load only needed fields**

```apex
List<Account> accounts = [SELECT Id, Name FROM Account LIMIT 10000];
// Minimal heap usage
```

### Rule 2: Process in Batches

**BAD: Load all records at once**

```apex
List<Account> accounts = [SELECT Id, Name FROM Account]; // Could be millions
for (Account acc : accounts) {
    // Process
}
```

**GOOD: Use Database.QueryLocator in batch**

```apex
global class ProcessAccountsBatch implements Database.Batchable<sObject> {
    global Database.QueryLocator start(Database.BatchableContext BC) {
        return Database.getQueryLocator([SELECT Id, Name FROM Account]);
    }

    global void execute(Database.BatchableContext BC, List<Account> scope) {
        // Process 200 records at a time (default batch size)
        for (Account acc : scope) {
            // Process
        }
    }

    global void finish(Database.BatchableContext BC) {}
}
```

### Rule 3: Clear Large Collections After Use

```apex
List<Account> largeList = [SELECT Id, Name FROM Account LIMIT 10000];

// Process list
for (Account acc : largeList) {
    // Do something
}

// Clear memory
largeList.clear();
largeList = null;
```

### Rule 4: Use Streaming SOQL for Large Data

```apex
// Standard query (loads all into heap)
List<Account> accounts = [SELECT Id FROM Account];

// Streaming query (iterator, lower heap)
for (Account acc : [SELECT Id FROM Account]) {
    // Process one at a time
    // Lower heap usage
}
```

---

## Bulkification Patterns

### What is Bulkification?

Writing code that handles multiple records efficiently in a single transaction.

### Pattern 1: Bulkified Trigger

**BAD: Non-bulkified trigger**

```apex
trigger AccountTrigger on Account (after insert) {
    Account acc = Trigger.new[0]; // Only handles first record

    Contact con = new Contact(
        LastName = 'Default',
        AccountId = acc.Id
    );
    insert con; // Single DML
}
// Fails if multiple accounts inserted at once
```

**GOOD: Bulkified trigger**

```apex
trigger AccountTrigger on Account (after insert) {
    List<Contact> contactsToInsert = new List<Contact>();

    for (Account acc : Trigger.new) {
        Contact con = new Contact(
            LastName = 'Default',
            AccountId = acc.Id
        );
        contactsToInsert.add(con);
    }

    if (!contactsToInsert.isEmpty()) {
        insert contactsToInsert; // Bulk DML
    }
}
// Handles 1 or 200 accounts efficiently
```

### Pattern 2: Collect IDs, Query Once

**BAD: Query in loop**

```apex
for (Opportunity opp : opportunities) {
    Account acc = [SELECT Name FROM Account WHERE Id = :opp.AccountId];
    // 100 SOQL queries if 100 opportunities
}
```

**GOOD: Collect IDs, query once**

```apex
Set<Id> accountIds = new Set<Id>();
for (Opportunity opp : opportunities) {
    accountIds.add(opp.AccountId);
}

Map<Id, Account> accountMap = new Map<Id, Account>([
    SELECT Id, Name FROM Account WHERE Id IN :accountIds
]);
// 1 SOQL query

for (Opportunity opp : opportunities) {
    Account acc = accountMap.get(opp.AccountId);
    // Use account
}
```

### Pattern 3: Use Maps for Related Records

```apex
// Get all accounts
Map<Id, Account> accountMap = new Map<Id, Account>([
    SELECT Id, Name FROM Account WHERE Id IN :accountIds
]);

// Get related contacts
Map<Id, List<Contact>> contactsByAccount = new Map<Id, List<Contact>>();

for (Contact con : [SELECT AccountId FROM Contact WHERE AccountId IN :accountIds]) {
    if (!contactsByAccount.containsKey(con.AccountId)) {
        contactsByAccount.put(con.AccountId, new List<Contact>());
    }
    contactsByAccount.get(con.AccountId).add(con);
}

// Process
for (Id accId : accountIds) {
    Account acc = accountMap.get(accId);
    List<Contact> contacts = contactsByAccount.get(accId);
    // Process account and contacts together
}
```

---

## Asynchronous Processing

### When to Use Async

Use asynchronous processing when:
- Processing takes >10 seconds
- Large data volumes (>10,000 records)
- Need higher governor limits
- Long-running operations (HTTP callouts, complex calculations)

### Option 1: @future Methods

**Best for**: Single callout, simple async task

```apex
public class AccountService {
    @future(callout=true)
    public static void updateAccountFromExternalSystem(Id accountId) {
        // 60 seconds CPU time instead of 10
        // Can make HTTP callouts
    }
}
```

**Limitations**:
- Cannot pass sObjects (only primitives)
- No chaining (can't call another @future)
- No monitoring

### Option 2: Queueable Apex

**Best for**: Complex async tasks, chaining

```apex
public class ProcessAccountsQueueable implements Queueable {
    private List<Id> accountIds;

    public ProcessAccountsQueueable(List<Id> accountIds) {
        this.accountIds = accountIds;
    }

    public void execute(QueueableContext context) {
        // Process accounts
        List<Account> accounts = [SELECT Id, Name FROM Account WHERE Id IN :accountIds];

        for (Account acc : accounts) {
            // Complex processing
        }

        update accounts;

        // Chain another job if needed
        if (/* more work to do */) {
            System.enqueueJob(new ProcessAccountsQueueable(moreAccountIds));
        }
    }
}

// Usage
System.enqueueJob(new ProcessAccountsQueueable(accountIds));
```

**Benefits**:
- Can pass sObjects
- Can chain jobs
- Monitoring via Setup → Apex Jobs

### Option 3: Batch Apex

**Best for**: Processing millions of records

```apex
global class ProcessAccountsBatch implements Database.Batchable<sObject> {

    global Database.QueryLocator start(Database.BatchableContext BC) {
        return Database.getQueryLocator([SELECT Id, Name FROM Account]);
    }

    global void execute(Database.BatchableContext BC, List<Account> scope) {
        // Process 200 records at a time (default)
        for (Account acc : scope) {
            acc.Name = acc.Name + ' (Processed)';
        }
        update scope;
    }

    global void finish(Database.BatchableContext BC) {
        // Send completion email, start next job, etc.
    }
}

// Usage
Database.executeBatch(new ProcessAccountsBatch(), 200); // Batch size
```

**Benefits**:
- Processes unlimited records
- Each batch has fresh governor limits
- Configurable batch size

### Option 4: Scheduled Apex

**Best for**: Recurring jobs

```apex
global class DailyAccountCleanup implements Schedulable {
    global void execute(SchedulableContext SC) {
        // Runs on schedule
        Database.executeBatch(new ProcessAccountsBatch());
    }
}

// Schedule: Every day at 2 AM
System.schedule('Daily Account Cleanup', '0 0 2 * * ?', new DailyAccountCleanup());
```

---

## Governor Limit Management

### Monitoring Limits in Code

```apex
System.debug('SOQL Queries: ' + Limits.getQueries() + '/' + Limits.getLimitQueries());
System.debug('DML Statements: ' + Limits.getDmlStatements() + '/' + Limits.getLimitDmlStatements());
System.debug('CPU Time: ' + Limits.getCpuTime() + '/' + Limits.getLimitCpuTime());
System.debug('Heap Size: ' + Limits.getHeapSize() + '/' + Limits.getLimitHeapSize());
```

### Proactive Limit Checking

```apex
public class AccountService {
    public static void processAccounts(List<Account> accounts) {
        List<Account> batch = new List<Account>();

        for (Account acc : accounts) {
            batch.add(acc);

            // Check if approaching SOQL limit
            if (Limits.getQueries() > 90) {
                // Stop and defer to async
                System.enqueueJob(new ProcessAccountsQueueable(accountIds));
                return;
            }

            // Process in batches of 100
            if (batch.size() >= 100) {
                update batch;
                batch.clear();
            }
        }

        // Update remaining
        if (!batch.isEmpty()) {
            update batch;
        }
    }
}
```

---

## Database Optimization

### Use Database Methods with Partial Success

```apex
// Standard DML: All-or-nothing
update accounts; // Fails entire operation if one record fails

// Database DML: Partial success
Database.SaveResult[] results = Database.update(accounts, false);

for (Database.SaveResult result : results) {
    if (!result.isSuccess()) {
        for (Database.Error err : result.getErrors()) {
            System.debug('Error: ' + err.getMessage());
        }
    }
}
// Other records still saved
```

### Use Platform Cache for Frequently Accessed Data

```apex
// Store in cache
Cache.Org.put('AccountTypes', accountTypeList, 3600); // 1 hour TTL

// Retrieve from cache
List<String> accountTypes = (List<String>)Cache.Org.get('AccountTypes');

if (accountTypes == null) {
    // Cache miss - query database
    accountTypes = queryAccountTypes();
    Cache.Org.put('AccountTypes', accountTypes, 3600);
}
```

---

## Lightning Component Performance

### LWC Best Practices

**1. Use @wire for Data Loading**

```javascript
import { LightningElement, wire } from 'lwc';
import getAccounts from '@salesforce/apex/AccountController.getAccounts';

export default class AccountList extends LightningElement {
    @wire(getAccounts)
    accounts;
    // Auto-refreshes, caches results
}
```

**2. Lazy Load Data**

```javascript
// Don't load all data on component init
// Load on-demand (button click, scroll)
handleLoadMore() {
    loadMoreAccounts({ offset: this.offset })
        .then(result => {
            this.accounts = [...this.accounts, ...result];
        });
}
```

**3. Use Lightning Data Service (LDS)**

```javascript
import { LightningElement, wire } from 'lwc';
import { getRecord } from 'lightning/uiRecordApi';

export default class AccountDetail extends LightningElement {
    @wire(getRecord, { recordId: '$recordId', fields: ['Account.Name'] })
    account;
    // Automatically cached, refreshes across components
}
```

---

## Profiling and Monitoring

### Use Developer Console Logs

1. Developer Console → Debug → Change Log Levels
2. Set Apex Code = FINEST
3. Set Database = FINEST
4. Run your code
5. View log: Execution tab shows performance

**Key Metrics in Logs**:
- `SOQL_EXECUTE_BEGIN` / `SOQL_EXECUTE_END` - Query time
- `DML_BEGIN` / `DML_END` - DML operation time
- `CUMULATIVE_LIMIT_USAGE` - Governor limit summary

### Use Query Plan

Developer Console → Query Editor → Query Plan

Shows:
- Index usage
- Cardinality (estimated rows)
- Cost (relative expense)

### Use Event Monitoring

Setup → Event Monitoring → Transaction Security

Monitors:
- Slow queries
- Large record retrievals
- High CPU usage
- API usage patterns

---

## Performance Tuning Scripts

This skill includes automation scripts for performance analysis:

### profile_soql.py

Analyze SOQL query performance:

```bash
./scripts/profile_soql.py "SELECT Id, Name FROM Account WHERE Industry = 'Technology'" my-org
```

Shows:
- Query execution time
- Record count
- Recommendations for optimization

### analyze_apex_performance.py

Parse debug logs for CPU/heap usage:

```bash
./scripts/analyze_apex_performance.py ./debug-log.txt
```

Identifies:
- CPU-intensive methods
- Heap usage by method
- SOQL query hotspots

### find_slow_queries.sh

Identify slow queries in debug logs:

```bash
./scripts/find_slow_queries.sh ./logs/ 1000
```

Finds all queries taking >1000ms.

---

## Quick Wins Checklist

- [ ] Index custom fields used in WHERE clauses
- [ ] Add LIMIT to all queries
- [ ] Move SOQL outside loops
- [ ] Bulkify all triggers
- [ ] Use Maps for lookups instead of nested loops
- [ ] Replace @future with Queueable when possible
- [ ] Use batch Apex for >10,000 records
- [ ] Enable query plan for slow queries
- [ ] Add logging for governor limit usage
- [ ] Use Platform Cache for repeated queries

---

## Additional Resources

**Salesforce Documentation**:
- [Apex Developer Guide - Best Practices](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_bestpractices.htm)
- [Query & Search Optimization](https://developer.salesforce.com/docs/atlas.en-us.salesforce_app_limits_cheatsheet.meta/salesforce_app_limits_cheatsheet/salesforce_app_limits_platform_bulkification.htm)

**Related Guides in This Skill**:
- `governor-limits.md` - Complete limits reference
- `soql-patterns.md` - Efficient query patterns
- `common-errors.md` - TOO_MANY_SOQL_QUERIES, CPU_LIMIT_EXCEEDED errors

---

**Last Updated**: Phase 2 - October 2025
