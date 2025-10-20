# Salesforce Duplicate Detection Guide

Comprehensive guide for identifying, preventing, and merging duplicate records in Salesforce.

## Table of Contents

1. [Overview](#overview)
2. [Salesforce Duplicate Management](#salesforce-duplicate-management)
3. [Matching Rules](#matching-rules)
4. [Duplicate Rules](#duplicate-rules)
5. [Finding Duplicates with SOQL](#finding-duplicates-with-soql)
6. [Fuzzy Matching Algorithms](#fuzzy-matching-algorithms)
7. [Deduplication Strategies](#deduplication-strategies)
8. [Merging Records](#merging-records)
9. [Prevention Best Practices](#prevention-best-practices)
10. [Automation Scripts](#automation-scripts)

---

## Overview

### Why Duplicates Happen

Common causes:
- Multiple users creating the same record
- Data imports without deduplication
- Integration sync issues
- Lack of validation rules
- Missing matching rules

### Impact of Duplicates

- **Data Quality**: Inaccurate reports and dashboards
- **User Experience**: Confusion, wasted time
- **Storage Costs**: Unnecessary data storage
- **Integration Issues**: Syncing wrong records
- **Compliance**: GDPR/privacy violations

---

## Salesforce Duplicate Management

### Standard Duplicate Management

Salesforce provides built-in duplicate management for:
- Accounts
- Contacts
- Leads

**Access**: Setup → Duplicate Management

### Components

1. **Matching Rules**: Define how to identify duplicates
2. **Duplicate Rules**: Define what happens when a duplicate is found
3. **Duplicate Jobs**: Bulk find existing duplicates

---

## Matching Rules

### What Are Matching Rules?

Matching rules define the criteria for identifying potential duplicate records.

### Standard Matching Rules

Salesforce provides pre-built matching rules:

**Account Matching**:
- Account Name + Billing Address
- Account Name + Phone
- Account Name + Website

**Contact Matching**:
- Email address
- First Name + Last Name + Account

**Lead Matching**:
- Email address
- First Name + Last Name + Company

### Creating Custom Matching Rules

Setup → Duplicate Management → Matching Rules → New Rule

**Example: Account Matching Rule**

| Field | Match Criteria | Match Blank Fields |
|-------|---------------|-------------------|
| Name | Exact | No |
| BillingCity | Exact | No |
| BillingState | Exact | No |

**Match Equation**: (Name AND (BillingCity OR BillingState))

### Matching Algorithms

**Exact**: Fields must match exactly
- Use for: IDs, email addresses, phone numbers

**Fuzzy**: Allows minor differences (typos, spacing)
- Use for: Names, addresses, company names
- Example: "Acme Corp" matches "ACME CORP", "Acme  Corp"

**Edit Distance**: Levenshtein distance (number of character changes)
- Threshold: 1-10 characters difference allowed

### Fuzzy Matching Examples

```apex
// Built-in fuzzy matching in Matching Rules
// "John Smith" matches:
// - "john smith" (case)
// - "John  Smith" (spacing)
// - "Jon Smith" (1 char difference)
// - "John Smyth" (1 char difference)
```

### Performance Considerations

**Matching Rule Performance**:
- Index fields used in matching rules
- Limit matching to 1-2 fields when possible
- Use "Exact" over "Fuzzy" when appropriate
- Avoid matching on long text fields

---

## Duplicate Rules

### What Are Duplicate Rules?

Duplicate rules define **actions** when a duplicate is detected:
- **Alert**: Warn user but allow creation
- **Block**: Prevent record creation
- **Report**: Log duplicate but don't alert user

### Creating Duplicate Rules

Setup → Duplicate Management → Duplicate Rules → New Rule

**Example: Account Duplicate Rule**

- **Object**: Account
- **Record-Level Security**: Enforce sharing rules
- **Action on Create**: Alert
- **Action on Edit**: Alert
- **Matching Rule**: Standard Account Match Rule

### Bypass Options

Allow certain users to bypass duplicate rules:
- System Administrators
- Data migration users
- Integration users

**Permission**: "Allow duplicate records in API"

---

## Finding Duplicates with SOQL

### Strategy 1: GROUP BY with HAVING

Find duplicates based on a single field (e.g., Email):

```sql
SELECT Email, COUNT(Id) cnt
FROM Contact
WHERE Email != null
GROUP BY Email
HAVING COUNT(Id) > 1
ORDER BY COUNT(Id) DESC
```

Returns emails that appear more than once.

### Strategy 2: Self-Join (Composite Keys)

Find duplicates based on multiple fields:

```sql
SELECT Id, Name, Email, Phone
FROM Contact
WHERE Email IN (
  SELECT Email
  FROM Contact
  WHERE Email != null
  GROUP BY Email
  HAVING COUNT(Id) > 1
)
ORDER BY Email, Name
```

### Strategy 3: Multiple Field Matching

```sql
SELECT Id, FirstName, LastName, AccountId
FROM Contact
WHERE (FirstName + LastName + AccountId) IN (
  SELECT FirstName + LastName + AccountId
  FROM Contact
  GROUP BY FirstName, LastName, AccountId
  HAVING COUNT(Id) > 1
)
```

Note: SOQL doesn't support string concatenation in WHERE clause, so use subquery.

### Strategy 4: Fuzzy Matching with LIKE

Find similar names:

```sql
SELECT Id, Name, BillingCity
FROM Account
WHERE Name LIKE 'Acme%'
ORDER BY Name
```

Then compare in code for fuzzy matches.

---

## Fuzzy Matching Algorithms

### Levenshtein Distance

Measures the number of single-character edits (insertions, deletions, substitutions) needed to change one string into another.

**Example**:
- "kitten" → "sitting" = 3 edits
- "Saturday" → "Sunday" = 3 edits

**Implementation in Apex**:

```apex
public static Integer levenshteinDistance(String s1, String s2) {
    Integer len1 = s1.length();
    Integer len2 = s2.length();

    Integer[][] d = new Integer[len1 + 1][len2 + 1];

    for (Integer i = 0; i <= len1; i++) {
        d[i][0] = i;
    }

    for (Integer j = 0; j <= len2; j++) {
        d[0][j] = j;
    }

    for (Integer i = 1; i <= len1; i++) {
        for (Integer j = 1; j <= len2; j++) {
            Integer cost = (s1.substring(i-1, i) == s2.substring(j-1, j)) ? 0 : 1;
            d[i][j] = Math.min(
                Math.min(d[i-1][j] + 1, d[i][j-1] + 1),
                d[i-1][j-1] + cost
            );
        }
    }

    return d[len1][len2];
}
```

**Usage**:
```apex
Integer distance = levenshteinDistance('John Smith', 'Jon Smyth'); // Returns 2
```

### Soundex Algorithm

Phonetic matching: "Sounds like" comparison.

**Example**:
- "Smith" → S530
- "Smyth" → S530
- Both encode to same value, so they're phonetic matches

**Not natively supported in Salesforce**, but can be implemented in Apex.

### Token-Based Matching

Split strings into tokens and compare:

**Example**:
- "Acme Corporation Inc" → ["Acme", "Corporation", "Inc"]
- "Acme Corp" → ["Acme", "Corp"]
- Match score: 1 common token / 2 total = 50%

**Implementation**:

```apex
public static Decimal tokenMatchScore(String s1, String s2) {
    Set<String> tokens1 = new Set<String>(s1.toLowerCase().split('\\s+'));
    Set<String> tokens2 = new Set<String>(s2.toLowerCase().split('\\s+'));

    Set<String> intersection = tokens1.clone();
    intersection.retainAll(tokens2);

    Set<String> union = tokens1.clone();
    union.addAll(tokens2);

    return union.size() > 0 ? (Decimal)intersection.size() / union.size() : 0;
}
```

### Jaro-Winkler Distance

Similar to Levenshtein but gives more weight to matching prefixes.

**Use case**: Comparing first names, last names where typos are common at the end.

**Not natively supported in Salesforce** (requires custom implementation or external library).

---

## Deduplication Strategies

### Strategy 1: Prevent at Source

**Validation Rules**:
```apex
// Block creation if duplicate email exists
AND(
  ISBLANK(Id),
  NOT(ISBLANK(Email)),
  VLOOKUP($ObjectType.Contact.Fields.Email, $ObjectType.Contact.Fields.Email, Email) != null
)
```

Note: VLOOKUP is deprecated. Use Duplicate Rules instead.

**Duplicate Rules**:
- Enable standard duplicate rules
- Create custom matching rules for your use case

### Strategy 2: Identify and Merge

1. **Identify duplicates**: Use SOQL queries or run Duplicate Job
2. **Review manually**: Determine which record to keep (master)
3. **Merge records**: Use Salesforce merge functionality or API
4. **Verify**: Check that child records moved to master

### Strategy 3: Automated Deduplication

**Use Case**: Large volumes of duplicates

**Process**:
1. Export duplicates to CSV
2. Apply business logic to determine master record
3. Use Data Loader to merge or delete duplicates
4. Monitor error logs

**Caution**: Test thoroughly in sandbox first!

### Strategy 4: Prevention via Integration

**API-Level Deduplication**:
- Check for existing record before creating
- Use `Upsert` with external ID instead of `Insert`
- Implement retry logic with exponential backoff

**Example (Apex)**:

```apex
public static Id upsertAccount(String name, String externalId) {
    List<Account> existing = [
        SELECT Id FROM Account
        WHERE External_Id__c = :externalId
        LIMIT 1
    ];

    if (!existing.isEmpty()) {
        // Update existing
        existing[0].Name = name;
        update existing[0];
        return existing[0].Id;
    } else {
        // Insert new
        Account acc = new Account(Name = name, External_Id__c = externalId);
        insert acc;
        return acc.Id;
    }
}
```

---

## Merging Records

### UI-Based Merge

**Accounts, Contacts, Leads only**:

1. Select up to 3 records
2. Click "Merge" button
3. Choose master record
4. Select fields to keep from each record
5. Confirm merge

**What Happens**:
- Master record is kept
- Duplicate records are deleted
- Child records are reparented to master
- Activities and history are moved to master

### API-Based Merge

Use Salesforce Merge API for programmatic merging:

```apex
// Merge two accounts
Database.MergeResult result = Database.merge(masterAccount, duplicateAccount);

if (result.isSuccess()) {
    System.debug('Merge successful');
} else {
    for (Database.Error err : result.getErrors()) {
        System.debug('Merge error: ' + err.getMessage());
    }
}
```

### Bulk Merge

For large volumes, use:

**Option 1**: Data Loader with Delete operation
- Export child records
- Update child records with new parent ID
- Delete duplicate parent records

**Option 2**: Apex Batch Job

```apex
global class MergeDuplicatesBatch implements Database.Batchable<sObject> {

    global Database.QueryLocator start(Database.BatchableContext BC) {
        return Database.getQueryLocator([
            SELECT Id, Email, (SELECT Id FROM Contacts)
            FROM Account
            WHERE Email IN (
                SELECT Email FROM Account
                GROUP BY Email HAVING COUNT(Id) > 1
            )
        ]);
    }

    global void execute(Database.BatchableContext BC, List<Account> scope) {
        Map<String, List<Account>> duplicateMap = new Map<String, List<Account>>();

        // Group by email
        for (Account acc : scope) {
            if (!duplicateMap.containsKey(acc.Email)) {
                duplicateMap.put(acc.Email, new List<Account>());
            }
            duplicateMap.get(acc.Email).add(acc);
        }

        // Merge duplicates
        for (String email : duplicateMap.keySet()) {
            List<Account> duplicates = duplicateMap.get(email);
            if (duplicates.size() > 1) {
                Account master = duplicates[0]; // First one is master
                for (Integer i = 1; i < duplicates.size(); i++) {
                    Database.merge(master, duplicates[i]);
                }
            }
        }
    }

    global void finish(Database.BatchableContext BC) {
        System.debug('Merge batch complete');
    }
}
```

### Merge Considerations

**Before merging**:
- Backup data
- Test in sandbox
- Document merge criteria
- Notify users

**What gets merged**:
- ✅ Standard fields (you choose)
- ✅ Custom fields (you choose)
- ✅ Child records (automatic)
- ✅ Activities/Tasks (automatic)
- ✅ Notes/Attachments (automatic)
- ❌ Chatter posts (lost on duplicates)
- ❌ Field history (lost on duplicates)

---

## Prevention Best Practices

### 1. Enable Duplicate Rules

Setup → Duplicate Management → Duplicate Rules → Activate

**Start with**:
- Standard Account Duplicate Rule (Name + Address)
- Standard Contact Duplicate Rule (Email)
- Standard Lead Duplicate Rule (Email)

### 2. Create External IDs

For integrations, always use external IDs:
- Prevents duplicate creation from sync issues
- Enables upsert operations
- Provides audit trail

### 3. Validation Rules

Add validation to catch common issues:

**Example: Require Email Format**:
```apex
AND(
  NOT(ISBLANK(Email)),
  NOT(REGEX(Email, "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}"))
)
```

### 4. Data Import Best Practices

Before importing:
- Remove duplicates in CSV
- Use external IDs for upsert
- Enable duplicate rules
- Run in batches
- Validate after each batch

### 5. User Training

Educate users on:
- Searching before creating records
- Using global search
- Understanding duplicate warnings
- Following naming conventions

### 6. Regular Audits

Schedule quarterly duplicate audits:
- Run duplicate jobs
- Review duplicate reports
- Merge or delete as needed
- Update matching rules based on findings

---

## Automation Scripts

This skill includes scripts for duplicate detection:

### find_duplicates.py

Identify duplicates based on custom criteria:

```bash
# Find duplicate Contacts by Email
./scripts/find_duplicates.py Contact "Email" my-org

# Find duplicate Accounts by Name and City
./scripts/find_duplicates.py Account "Name,BillingCity" my-org

# Output: CSV of duplicate groups with IDs
```

**Features**:
- Supports multiple fields
- Generates merge recommendations
- Exports to CSV for review

### Usage Example

```bash
# Find duplicate Accounts
./scripts/find_duplicates.py Account "Name,BillingCity" dev-sandbox

# Output:
# Group 1:
#   - 0011234567890ABC | Acme Corp | New York
#   - 0011234567890DEF | Acme Corp | New York
#
# Group 2:
#   - 0011234567890GHI | ABC Company | Boston
#   - 0011234567890JKL | ABC Company | Boston
#
# Found 2 duplicate groups with 4 total records
# Exported to: ./duplicates-Account-2025-10-20.csv
```

---

## SOQL Examples

### Find Duplicate Contacts by Email

```sql
SELECT Email, COUNT(Id) cnt, MIN(Id) oldestId
FROM Contact
WHERE Email != null
GROUP BY Email
HAVING COUNT(Id) > 1
ORDER BY COUNT(Id) DESC
LIMIT 100
```

### Find Duplicate Accounts by Name

```sql
SELECT Name, COUNT(Id) cnt
FROM Account
GROUP BY Name
HAVING COUNT(Id) > 1
ORDER BY COUNT(Id) DESC
```

### List All Records in a Duplicate Group

```sql
SELECT Id, Name, Email, Phone, CreatedDate
FROM Contact
WHERE Email = 'john.doe@example.com'
ORDER BY CreatedDate ASC
```

First record (oldest) is typically the master.

### Find Contacts Without Accounts

```sql
SELECT Id, FirstName, LastName, Email
FROM Contact
WHERE AccountId = null
LIMIT 1000
```

These may be duplicates of Contacts with Accounts.

### Find Accounts with Similar Names

```sql
SELECT Id, Name, BillingCity
FROM Account
WHERE Name LIKE '%Acme%'
ORDER BY Name
```

Then manually review for fuzzy matches.

---

## Duplicate Job Reports

### Running a Duplicate Job

Setup → Duplicate Management → Duplicate Jobs → New Job

1. **Select Object**: Account, Contact, or Lead
2. **Select Matching Rule**: Choose rule to use
3. **Run Job**: Processes all records asynchronously
4. **View Results**: Download report of duplicate sets

### Interpreting Results

**Duplicate Set**: Group of records that match based on the rule

**Example Output**:
```
Duplicate Set 1:
- Master: 0011234567890ABC (John Smith, john.smith@example.com)
- Duplicate: 0011234567890DEF (John Smith, jsmith@example.com)

Duplicate Set 2:
- Master: 0011234567890GHI (Acme Corp, www.acme.com)
- Duplicate: 0011234567890JKL (ACME CORP, www.acme.com)
- Duplicate: 0011234567890MNO (Acme Corporation, www.acme.com)
```

### Actions After Duplicate Job

1. **Review**: Manually verify each set
2. **Merge**: Use Salesforce merge functionality
3. **Update Rules**: Refine matching rules based on false positives
4. **Re-run**: Schedule regular jobs to catch new duplicates

---

## Advanced Topics

### Custom Duplicate Detection with Apex

For complex matching logic:

```apex
public class CustomDuplicateDetector {

    public static List<Account> findSimilarAccounts(Account newAccount) {
        String namePattern = '%' + newAccount.Name.substring(0, 5) + '%';

        List<Account> potentialDuplicates = [
            SELECT Id, Name, Phone, Website, BillingCity
            FROM Account
            WHERE Name LIKE :namePattern
            AND Id != :newAccount.Id
            LIMIT 10
        ];

        List<Account> matches = new List<Account>();

        for (Account acc : potentialDuplicates) {
            Integer distance = levenshteinDistance(
                newAccount.Name.toLowerCase(),
                acc.Name.toLowerCase()
            );

            if (distance <= 3) {
                matches.add(acc);
            }
        }

        return matches;
    }

    // Levenshtein distance method from earlier
    public static Integer levenshteinDistance(String s1, String s2) {
        // Implementation omitted for brevity
    }
}
```

### Trigger-Based Prevention

```apex
trigger PreventDuplicateContacts on Contact (before insert) {
    Set<String> emails = new Set<String>();

    for (Contact c : Trigger.new) {
        if (c.Email != null) {
            emails.add(c.Email.toLowerCase());
        }
    }

    List<Contact> existingContacts = [
        SELECT Email FROM Contact
        WHERE Email IN :emails
    ];

    Set<String> existingEmails = new Set<String>();
    for (Contact c : existingContacts) {
        existingEmails.add(c.Email.toLowerCase());
    }

    for (Contact c : Trigger.new) {
        if (c.Email != null && existingEmails.contains(c.Email.toLowerCase())) {
            c.addError('A Contact with this email already exists.');
        }
    }
}
```

---

## Additional Resources

**Salesforce Documentation**:
- [Duplicate Management](https://help.salesforce.com/s/articleView?id=sf.duplicate_management.htm)
- [Matching Rules](https://help.salesforce.com/s/articleView?id=sf.matching_rules.htm)
- [Merge API](https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_dml_merge.htm)

**Related Guides in This Skill**:
- `data-migration-guide.md` - External IDs and upsert patterns
- `soql-patterns.md` - Efficient duplicate queries
- `common-errors.md` - DUPLICATE_VALUE errors

---

**Last Updated**: Phase 2 - October 2025
