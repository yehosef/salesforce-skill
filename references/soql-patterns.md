# SOQL Query Patterns & Best Practices

Comprehensive guide to SOQL (Salesforce Object Query Language) with optimization techniques, common patterns, and pitfalls to avoid.

## Basic Query Structure

```sql
SELECT field1, field2, field3
FROM ObjectName
WHERE condition
ORDER BY field1 ASC
LIMIT 100
```

---

## Basic Queries

### Simple SELECT
```sql
SELECT Id, Name, Email FROM Contact

SELECT Id, Name, CreatedDate FROM Account WHERE Industry = 'Technology'

SELECT COUNT() FROM Opportunity WHERE StageName = 'Closed Won'
```

### Field Selection
```sql
-- Specific fields (recommended)
SELECT Id, Name, Email, Phone FROM Contact

-- All fields (avoid - inefficient)
-- Note: SOQL does NOT support SELECT *
-- You must specify fields explicitly
```

---

## Filtering with WHERE

### Equality Operators
```sql
SELECT Id, Name FROM Account WHERE Name = 'Acme Corporation'

SELECT Id, Amount FROM Opportunity WHERE Amount > 10000

SELECT Id, CloseDate FROM Opportunity WHERE CloseDate >= 2024-01-01
```

### Multiple Conditions
```sql
-- AND
SELECT Id, Name FROM Contact
WHERE LastName = 'Smith' AND Email != null

-- OR
SELECT Id, Name FROM Opportunity
WHERE (StageName = 'Prospecting' OR StageName = 'Qualification')
AND Amount > 5000

-- IN clause
SELECT Id, Name FROM Account
WHERE Industry IN ('Technology', 'Finance', 'Healthcare')

-- NOT IN
SELECT Id, Name FROM Contact
WHERE Email NOT IN ('test@example.com', 'spam@example.com')
```

### NULL Checks
```sql
SELECT Id, Name FROM Contact WHERE Email != null

SELECT Id, Name FROM Account WHERE Website = null
```

### LIKE Operator (String Matching)
```sql
-- Starts with
SELECT Id, Name FROM Account WHERE Name LIKE 'Acme%'

-- Ends with
SELECT Id, Email FROM Contact WHERE Email LIKE '%@gmail.com'

-- Contains
SELECT Id, Name FROM Account WHERE Name LIKE '%Corp%'

-- Single character wildcard
SELECT Id, Name FROM Account WHERE Name LIKE 'A_me'
```

**⚠️ WARNING**: LIKE with leading wildcards (`%value`) is not indexed and will be slow on large datasets.

---

## Date Filtering

### Date Literals
```sql
-- Specific date
SELECT Id, CreatedDate FROM Account WHERE CreatedDate = 2024-01-01

-- Date range
SELECT Id, CreatedDate FROM Opportunity
WHERE CreatedDate >= 2024-01-01 AND CreatedDate <= 2024-12-31
```

### Relative Dates
```sql
-- Today
SELECT Id, CreatedDate FROM Account WHERE CreatedDate = TODAY

-- Yesterday
SELECT Id, CreatedDate FROM Account WHERE CreatedDate = YESTERDAY

-- This week
SELECT Id, CreatedDate FROM Account WHERE CreatedDate = THIS_WEEK

-- This month
SELECT Id, CreatedDate FROM Opportunity WHERE CloseDate = THIS_MONTH

-- This year
SELECT Id, CreatedDate FROM Account WHERE CreatedDate = THIS_YEAR

-- Last N days
SELECT Id, CreatedDate FROM Account WHERE CreatedDate = LAST_N_DAYS:7
SELECT Id, CreatedDate FROM Account WHERE CreatedDate = LAST_N_DAYS:30

-- Next N days
SELECT Id, CloseDate FROM Opportunity WHERE CloseDate = NEXT_N_DAYS:30

-- Last N weeks/months/years
SELECT Id, CreatedDate FROM Account WHERE CreatedDate = LAST_N_WEEKS:4
SELECT Id, CreatedDate FROM Account WHERE CreatedDate = LAST_N_MONTHS:6
SELECT Id, CreatedDate FROM Account WHERE CreatedDate = LAST_N_YEARS:2
```

---

## Relationship Queries

### Parent to Child (Subqueries)
```sql
-- One-to-many relationship
SELECT Id, Name, (SELECT Id, FirstName, LastName FROM Contacts)
FROM Account

-- With WHERE in subquery
SELECT Id, Name, (SELECT Id, Amount FROM Opportunities WHERE Amount > 10000)
FROM Account

-- Multiple subqueries
SELECT Id, Name,
  (SELECT Id, FirstName FROM Contacts),
  (SELECT Id, Subject FROM Tasks)
FROM Account
```

### Child to Parent (Relationship Fields)
```sql
-- Access parent fields
SELECT Id, FirstName, LastName, Account.Name, Account.Industry
FROM Contact

-- Multiple levels (up to 5)
SELECT Id, Name, Account.Owner.Name, Account.Owner.Profile.Name
FROM Opportunity

-- Custom relationships
SELECT Id, Name, CustomObject__r.CustomField__c
FROM AnotherObject__c
```

**Naming Conventions:**
- Standard relationships: Use singular name (e.g., `Account`)
- Custom relationships: Use `__r` instead of `__c` (e.g., `CustomObject__r`)
- Child relationships: Use plural name (e.g., `Contacts`, `Opportunities`)
- Custom child relationships: Use `__r` (e.g., `CustomObjects__r`)

---

## Aggregation Functions

### COUNT
```sql
-- Count all records
SELECT COUNT() FROM Account

-- Count specific field
SELECT COUNT(Id) FROM Account

-- Count with alias
SELECT COUNT(Id) totalAccounts FROM Account

-- Count with GROUP BY
SELECT Industry, COUNT(Id) accountCount
FROM Account
GROUP BY Industry
```

### SUM, AVG, MIN, MAX
```sql
-- Sum
SELECT SUM(Amount) FROM Opportunity WHERE StageName = 'Closed Won'

-- Average
SELECT AVG(Amount) FROM Opportunity

-- Minimum and Maximum
SELECT MIN(Amount), MAX(Amount) FROM Opportunity

-- Multiple aggregates
SELECT SUM(Amount) totalRevenue, AVG(Amount) avgDeal, COUNT(Id) dealCount
FROM Opportunity
WHERE StageName = 'Closed Won'
```

### GROUP BY
```sql
-- Group by single field
SELECT StageName, COUNT(Id) oppCount, SUM(Amount) totalAmount
FROM Opportunity
GROUP BY StageName

-- Group by multiple fields
SELECT StageName, Type, COUNT(Id)
FROM Opportunity
GROUP BY StageName, Type

-- Group by relationship field
SELECT Account.Name, COUNT(Id)
FROM Opportunity
GROUP BY Account.Name
```

### HAVING (Filter on Aggregates)
```sql
-- Filter aggregated results
SELECT StageName, COUNT(Id) oppCount
FROM Opportunity
GROUP BY StageName
HAVING COUNT(Id) > 5

-- Complex HAVING
SELECT Account.Name, SUM(Amount) totalRevenue
FROM Opportunity
WHERE StageName = 'Closed Won'
GROUP BY Account.Name
HAVING SUM(Amount) > 100000
```

---

## Sorting and Limiting

### ORDER BY
```sql
-- Ascending (default)
SELECT Id, Name FROM Account ORDER BY Name

SELECT Id, Name FROM Account ORDER BY Name ASC

-- Descending
SELECT Id, Amount FROM Opportunity ORDER BY Amount DESC

-- Multiple fields
SELECT Id, Name, Industry FROM Account
ORDER BY Industry ASC, Name ASC

-- Order by relationship field
SELECT Id, FirstName, LastName FROM Contact
ORDER BY Account.Name, LastName
```

### LIMIT
```sql
-- Limit results
SELECT Id, Name FROM Account LIMIT 10

-- Combined with ORDER BY
SELECT Id, Amount FROM Opportunity
ORDER BY Amount DESC
LIMIT 5  -- Top 5 opportunities
```

### OFFSET
```sql
-- Skip first N records (pagination)
SELECT Id, Name FROM Account LIMIT 10 OFFSET 20  -- Records 21-30
```

---

## Governor Limit Optimization

### Query Limits
- **Synchronous Apex**: 100 SOQL queries per transaction
- **Asynchronous Apex**: 200 SOQL queries per transaction
- **Query Rows**: 50,000 rows per transaction
- **Query Locator**: Use for >10,000 rows in batch contexts

### Best Practices to Avoid Limits

#### 1. Query Outside Loops
```apex
// ❌ BAD - Query in loop
for (Account acc : accounts) {
    List<Contact> contacts = [SELECT Id FROM Contact WHERE AccountId = :acc.Id];
}

// ✅ GOOD - Single query with IN clause
Set<Id> accountIds = new Set<Id>();
for (Account acc : accounts) {
    accountIds.add(acc.Id);
}
List<Contact> contacts = [SELECT Id, AccountId FROM Contact WHERE AccountId IN :accountIds];
```

#### 2. Use Indexed Fields in WHERE
```sql
-- ✅ Indexed (fast)
SELECT Id FROM Account WHERE Id = '001XXXXXXXXXXXXXX'
SELECT Id FROM Contact WHERE Email = 'test@example.com' -- If custom indexed

-- ❌ Not indexed (slow on large datasets)
SELECT Id FROM Account WHERE Website LIKE '%example.com'
SELECT Id FROM Contact WHERE Phone = '555-1234'
```

**Standard Indexed Fields:**
- Id
- Name
- OwnerId
- CreatedDate
- SystemModstamp
- RecordTypeId
- Master-detail relationship fields
- Lookup relationship fields
- External ID fields

#### 3. Selective Queries
```sql
-- ✅ GOOD - Selective (indexed field)
SELECT Id, Name FROM Account WHERE Id IN :idSet

-- ❌ BAD - Non-selective (scans full table)
SELECT Id, Name FROM Account WHERE Description LIKE '%keyword%'
```

#### 4. Limit Result Size
```sql
-- Always use LIMIT for large datasets
SELECT Id, Name FROM Account WHERE Industry = 'Technology' LIMIT 10000
```

#### 5. Use Bulk Queries for Large Data
For more than 10,000 records, use:
- `Database.getQueryLocator()` in batch Apex
- `sf data export bulk` CLI command

---

## Advanced Patterns

### SOQL Injection Prevention
```apex
// ❌ VULNERABLE
String searchTerm = getSearchTerm(); // User input
String query = 'SELECT Id FROM Account WHERE Name = \'' + searchTerm + '\'';
List<Account> accounts = Database.query(query);

// ✅ SAFE - Use bind variables
String searchTerm = getSearchTerm();
List<Account> accounts = [SELECT Id FROM Account WHERE Name = :searchTerm];

// ✅ SAFE - Escape special characters
String searchTerm = String.escapeSingleQuotes(getSearchTerm());
String query = 'SELECT Id FROM Account WHERE Name = \'' + searchTerm + '\'';
```

### Dynamic SOQL
```apex
// Build query dynamically
String query = 'SELECT Id, Name FROM Account';
if (filterByIndustry) {
    query += ' WHERE Industry = :industry';
}
query += ' ORDER BY Name LIMIT 100';
List<Account> accounts = Database.query(query);
```

### SOQL for Loops (Batch Processing)
```apex
// Process records in batches of 200
for (List<Account> batch : [SELECT Id, Name FROM Account WHERE Industry = 'Technology']) {
    // Process batch (200 records at a time)
    // Helps avoid heap size limits
}
```

### Semi-Join (Filtering by Related Records)
```sql
-- Accounts that have opportunities
SELECT Id, Name FROM Account WHERE Id IN (SELECT AccountId FROM Opportunity)

-- Contacts with tasks
SELECT Id, Name FROM Contact WHERE Id IN (SELECT WhoId FROM Task)
```

### Anti-Join (Filtering by Absence)
```sql
-- Accounts without opportunities
SELECT Id, Name FROM Account WHERE Id NOT IN (SELECT AccountId FROM Opportunity)

-- Contacts without cases
SELECT Id, Name FROM Contact WHERE Id NOT IN (SELECT ContactId FROM Case)
```

---

## Common Pitfalls and Solutions

### Problem: Query Timeout
**Symptom**: Query takes too long and times out

**Solutions:**
- Use indexed fields in WHERE clause
- Add LIMIT clause
- Make query more selective (narrow down results)
- Use bulk query API for large datasets

### Problem: Too Many Query Rows
**Symptom**: "Too many query rows: 50001" error

**Solutions:**
- Add more restrictive WHERE conditions
- Use LIMIT clause
- Use batch Apex with Database.getQueryLocator()
- Use SOQL for Loops for automatic batching

### Problem: Query Not Selective
**Symptom**: Slow query performance on large objects

**Solutions:**
- Filter on indexed fields (Id, Name, OwnerId, CreatedDate, etc.)
- Request custom index from Salesforce for frequently queried fields
- Use compound indexes for multiple field filters
- Avoid leading wildcards in LIKE queries

### Problem: Null Pointer Exception
**Symptom**: Error accessing relationship fields

**Solutions:**
```sql
-- Check for null relationships
SELECT Id, Account.Name FROM Contact WHERE Account.Id != null
```

---

## Quick Reference: Common Queries

### Get Recent Records
```sql
SELECT Id, Name, CreatedDate FROM Account
ORDER BY CreatedDate DESC
LIMIT 10
```

### Find Duplicates
```sql
SELECT Email, COUNT(Id) dupCount
FROM Contact
GROUP BY Email
HAVING COUNT(Id) > 1
```

### Get Records Modified Today
```sql
SELECT Id, Name, LastModifiedDate FROM Account
WHERE LastModifiedDate = TODAY
```

### Complex Multi-Level Query
```sql
SELECT Id, Name, Owner.Name, Owner.Profile.Name,
  (SELECT Id, FirstName, LastName FROM Contacts WHERE Email != null),
  (SELECT Id, Amount, StageName FROM Opportunities WHERE Amount > 10000)
FROM Account
WHERE Industry IN ('Technology', 'Finance')
AND CreatedDate = LAST_N_DAYS:30
ORDER BY Name
LIMIT 100
```

---

## Resources

- **Salesforce SOQL Reference**: https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/
- **Query Plan Tool**: Use in Developer Console to analyze query performance
- **Custom Indexes**: Request from Salesforce support for frequently queried non-indexed fields
