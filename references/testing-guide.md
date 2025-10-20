# Apex Testing Guide

Comprehensive guide to Apex test execution, best practices, and patterns.

## Test Execution

### Run All Tests
```bash
# Run all tests in org
sf apex test run -o <alias>

# Run all tests with code coverage
sf apex test run -o <alias> -c
```

### Run Specific Test Class
```bash
# Single test class
sf apex test run -n MyClassTest -o <alias> -c

# Multiple test classes
sf apex test run -n "MyClassTest, AnotherTest, ThirdTest" -o <alias> -c
```

### Run Specific Test Method
```bash
sf apex test run -n MyClassTest.testSpecificMethod -o <alias>
```

### Synchronous vs Asynchronous
```bash
# Synchronous (wait for completion, better for small test sets)
sf apex test run -n MyClassTest -o <alias> -c --synchronous

# Asynchronous (default, better for large test sets)
sf apex test run -n MyClassTest -o <alias> -c
```

### Get Test Results
```bash
# Latest test results
sf apex test report -o <alias>

# Specific test run by ID
sf apex test report -i 707XXXXXXXXXXXXXXX -o <alias>

# JSON format for automation
sf apex test report -i 707XXXXXXXXXXXXXXX -o <alias> --json
```

---

## Coverage Requirements

### Minimum Coverage
- **Sandbox**: No minimum (recommended 75%+)
- **Production**: 75% minimum required for deployment
- **Best Practice**: Aim for 85%+

### What Counts Toward Coverage
✅ **Counted**:
- Apex classes
- Apex triggers
- Lines executed during test runs

❌ **Not Counted**:
- Test classes themselves
- System.debug() statements
- Comments and blank lines
- Unreachable code (after return/throw)

### View Code Coverage
```bash
# Org-wide coverage
sf apex get test -o <alias> -c

# Coverage for specific classes
sf apex get test -o <alias> -c --class-names "MyClass, AnotherClass"
```

---

## Test Class Structure

### Basic Test Class Template
```apex
@isTest
private class MyClassTest {

    // Setup method - runs once before all test methods
    @TestSetup
    static void setup() {
        // Create test data here
        // This data is available to all test methods
        Account testAccount = new Account(Name = 'Test Account');
        insert testAccount;
    }

    // Positive test case
    @isTest
    static void testPositiveScenario() {
        // Arrange - Get test data
        Account acc = [SELECT Id FROM Account LIMIT 1];

        // Act - Execute the code being tested
        Test.startTest();
        MyClass.doSomething(acc.Id);
        Test.stopTest();

        // Assert - Verify expected results
        Account updatedAcc = [SELECT Id, Name, Status__c FROM Account WHERE Id = :acc.Id];
        System.assertEquals('Active', updatedAcc.Status__c, 'Account should be active');
    }

    // Negative test case
    @isTest
    static void testNegativeScenario() {
        // Test error handling
        Test.startTest();
        try {
            MyClass.doSomethingInvalid(null);
            System.assert(false, 'Should have thrown exception');
        } catch (MyCustomException e) {
            System.assert(true, 'Exception expected');
            System.assert(e.getMessage().contains('Invalid'), 'Error message should mention Invalid');
        }
        Test.stopTest();
    }

    // Bulk test case
    @isTest
    static void testBulkScenario() {
        // Test with 200+ records to verify bulkification
        List<Account> accounts = new List<Account>();
        for (Integer i = 0; i < 200; i++) {
            accounts.add(new Account(Name = 'Bulk Test ' + i));
        }

        Test.startTest();
        insert accounts;
        MyClass.processList(accounts);
        Test.stopTest();

        List<Account> processed = [SELECT Id FROM Account WHERE Processed__c = true];
        System.assertEquals(200, processed.size(), 'All 200 accounts should be processed');
    }
}
```

---

## Test Data Creation

### @TestSetup Method
```apex
@TestSetup
static void setupTestData() {
    // Runs once before all tests in the class
    // More efficient than creating data in each test method

    Account acc = new Account(Name = 'Test Account');
    insert acc;

    List<Contact> contacts = new List<Contact>();
    for (Integer i = 0; i < 10; i++) {
        contacts.add(new Contact(
            FirstName = 'Test',
            LastName = 'Contact ' + i,
            AccountId = acc.Id
        ));
    }
    insert contacts;
}
```

### Test Data Factory Pattern
```apex
@isTest
public class TestDataFactory {

    public static Account createAccount(String name, Boolean doInsert) {
        Account acc = new Account(Name = name, Industry = 'Technology');
        if (doInsert) insert acc;
        return acc;
    }

    public static List<Contact> createContacts(Integer count, Id accountId, Boolean doInsert) {
        List<Contact> contacts = new List<Contact>();
        for (Integer i = 0; i < count; i++) {
            contacts.add(new Contact(
                FirstName = 'Test',
                LastName = 'Contact ' + i,
                AccountId = accountId
            ));
        }
        if (doInsert) insert contacts;
        return contacts;
    }
}

// Usage in test class
@isTest
static void testWithFactory() {
    Account acc = TestDataFactory.createAccount('Test', true);
    List<Contact> contacts = TestDataFactory.createContacts(5, acc.Id, true);
    // ... test logic
}
```

---

## Test.startTest() and Test.stopTest()

### Governor Limit Reset
```apex
@isTest
static void testGovernorLimits() {
    // Setup code here uses governor limits
    Account acc = new Account(Name = 'Test');
    insert acc;  // Uses 1 DML

    // Governor limits reset here
    Test.startTest();

    // Code being tested gets fresh governor limits
    // Gets new set of: 100 SOQL, 150 DML, 10 seconds CPU
    MyClass.doWork(acc.Id);

    // Execution completes, async jobs finish
    Test.stopTest();

    // Assertions
    Account updated = [SELECT Status__c FROM Account WHERE Id = :acc.Id];
    System.assertEquals('Processed', updated.Status__c);
}
```

### Async Code Testing
```apex
@isTest
static void testFutureMethod() {
    Account acc = new Account(Name = 'Test');
    insert acc;

    Test.startTest();
    MyClass.processFuture(acc.Id);  // @future method
    Test.stopTest();  // All async jobs complete here

    // Future method has completed
    Account updated = [SELECT Processed__c FROM Account WHERE Id = :acc.Id];
    System.assertEquals(true, updated.Processed__c);
}
```

---

## Assertions

### System.assert Methods
```apex
// Assert true
System.assert(value == true, 'Value should be true');

// Assert equals
System.assertEquals(expected, actual, 'Values should match');

// Assert not equals
System.assertNotEquals(unexpected, actual, 'Values should not match');
```

### Best Practices for Assertions
```apex
// ✅ GOOD - Specific message
System.assertEquals(5, contacts.size(), 'Should have exactly 5 contacts');

// ❌ BAD - No message
System.assertEquals(5, contacts.size());

// ✅ GOOD - Check multiple conditions
System.assertEquals('Active', opp.StageName, 'Stage should be Active');
System.assertNotEquals(null, opp.CloseDate, 'CloseDate should be set');
System.assert(opp.Amount > 0, 'Amount should be positive');

// ❌ BAD - Single generic assertion
System.assert(true);
```

---

## Mocking External Callouts

### HTTP Callout Mock
```apex
@isTest
global class MockHttpResponse implements HttpCalloutMock {
    global HTTPResponse respond(HTTPRequest req) {
        HttpResponse res = new HttpResponse();
        res.setHeader('Content-Type', 'application/json');
        res.setBody('{"status":"success"}');
        res.setStatusCode(200);
        return res;
    }
}

// Use in test
@isTest
static void testCallout() {
    Test.setMock(HttpCalloutMock.class, new MockHttpResponse());

    Test.startTest();
    String response = MyClass.makeCallout();
    Test.stopTest();

    System.assert(response.contains('success'));
}
```

### WebService Callout Mock
```apex
@isTest
global class MockWebService implements WebServiceMock {
    global void doInvoke(
        Object stub, Object request, Map<String, Object> response,
        String endpoint, String soapAction, String requestName,
        String responseNS, String responseName, String responseType
    ) {
        // Mock response here
    }
}
```

---

## Testing Triggers

### Trigger Test Template
```apex
@isTest
private class AccountTriggerTest {

    @isTest
    static void testInsert() {
        Account acc = new Account(Name = 'Test');

        Test.startTest();
        insert acc;  // Trigger fires
        Test.stopTest();

        Account inserted = [SELECT Id, Status__c FROM Account WHERE Id = :acc.Id];
        System.assertEquals('New', inserted.Status__c, 'Status should be set by trigger');
    }

    @isTest
    static void testUpdate() {
        Account acc = new Account(Name = 'Test');
        insert acc;

        Test.startTest();
        acc.Name = 'Updated';
        update acc;  // Trigger fires
        Test.stopTest();

        Account updated = [SELECT ModifiedReason__c FROM Account WHERE Id = :acc.Id];
        System.assertEquals('Name changed', updated.ModifiedReason__c);
    }

    @isTest
    static void testBulk() {
        List<Account> accounts = new List<Account>();
        for (Integer i = 0; i < 200; i++) {
            accounts.add(new Account(Name = 'Bulk ' + i));
        }

        Test.startTest();
        insert accounts;  // Trigger must handle bulk
        Test.stopTest();

        List<Account> inserted = [SELECT Id FROM Account WHERE Status__c = 'New'];
        System.assertEquals(200, inserted.size(), 'Trigger should handle all 200');
    }
}
```

---

## Common Testing Patterns

### Test with Different User Permissions
```apex
@isTest
static void testAsStandardUser() {
    User standardUser = [SELECT Id FROM User WHERE Profile.Name = 'Standard User' LIMIT 1];

    System.runAs(standardUser) {
        Test.startTest();
        // Code runs with standard user permissions
        MyClass.doSomething();
        Test.stopTest();
    }
}
```

### Test Record Types
```apex
@isTest
static void testRecordType() {
    Id businessRT = Schema.SObjectType.Account.getRecordTypeInfosByDeveloperName()
                    .get('Business_Account').getRecordTypeId();

    Account acc = new Account(Name = 'Test', RecordTypeId = businessRT);
    insert acc;
    // ... test logic
}
```

### Test with Sharing
```apex
// Test respects sharing rules
@isTest
static void testWithSharing() {
    User limitedUser = createLimitedUser();

    System.runAs(limitedUser) {
        List<Account> accounts = [SELECT Id FROM Account];
        System.assertEquals(2, accounts.size(), 'User should only see 2 accounts');
    }
}
```

---

## Troubleshooting Test Failures

### Debug Test Failures
```apex
// Add debug statements
System.debug('Account ID: ' + acc.Id);
System.debug('Expected: ' + expected + ', Actual: ' + actual);

// Check SOQL queries
System.debug('Contacts found: ' + [SELECT Id FROM Contact WHERE AccountId = :acc.Id]);
```

### Common Failure Reasons

**FIELD_CUSTOM_VALIDATION_EXCEPTION**
- Validation rule preventing test data creation
- Solution: Use `@TestSetup` or ensure test data meets validation

**REQUIRED_FIELD_MISSING**
- Missing required field in test data
- Solution: Include all required fields when creating records

**UNABLE_TO_LOCK_ROW**
- Record locking conflict
- Solution: Avoid querying same record multiple times, use fresh queries

**System.AssertException**
- Assertion failed
- Solution: Check debug logs, verify expected vs actual values

---

## Best Practices

### 1. Always Use Test.startTest() and Test.stopTest()
- Resets governor limits
- Ensures async code completes
- Makes test boundaries clear

### 2. Test Bulk Scenarios
```apex
// Always test with 200+ records
List<Account> accounts = new List<Account>();
for (Integer i = 0; i < 200; i++) {
    accounts.add(new Account(Name = 'Test ' + i));
}
insert accounts;
```

### 3. Use @TestSetup for Efficiency
- Runs once per class
- Faster than creating data in each test
- Data rolls back between test methods

### 4. Avoid Hard-Coded IDs
```apex
// ❌ BAD
Id accountId = '001XXXXXXXXXXXXXXX';

// ✅ GOOD
Id accountId = [SELECT Id FROM Account LIMIT 1].Id;

// ✅ BEST
Account acc = new Account(Name = 'Test');
insert acc;
Id accountId = acc.Id;
```

### 5. Test Positive and Negative Cases
- Test expected behavior (positive)
- Test error handling (negative)
- Test edge cases (null, empty, boundary values)

### 6. Meaningful Assertion Messages
```apex
// ✅ GOOD
System.assertEquals(5, contacts.size(), 'Should create exactly 5 contacts');

// ❌ BAD
System.assertEquals(5, contacts.size());
```

### 7. Use SeeAllData Sparingly
```apex
// ❌ AVOID - Can cause unpredictable results
@isTest(SeeAllData=true)
static void testWithRealData() { }

// ✅ PREFER - Create your own test data
@isTest
static void testWithTestData() {
    Account acc = new Account(Name = 'Test');
    insert acc;
}
```

---

## Test Coverage Tips

### Cover All Branches
```apex
// Method to test
public static String getStatus(Integer value) {
    if (value > 100) {
        return 'High';
    } else if (value > 50) {
        return 'Medium';
    } else {
        return 'Low';
    }
}

// Tests covering all branches
@isTest
static void testHighStatus() {
    System.assertEquals('High', MyClass.getStatus(150));
}

@isTest
static void testMediumStatus() {
    System.assertEquals('Medium', MyClass.getStatus(75));
}

@isTest
static void testLowStatus() {
    System.assertEquals('Low', MyClass.getStatus(25));
}
```

### Cover Exception Handling
```apex
@isTest
static void testExceptionHandling() {
    try {
        MyClass.methodThatThrows(null);
        System.assert(false, 'Should have thrown exception');
    } catch (MyException e) {
        System.assert(true, 'Exception expected');
    }
}
```

---

## Running Tests Before Deployment

### Local Testing
```bash
# Run tests for classes you're deploying
sf apex test run -n "MyClass_Test, AnotherClass_Test" -o sandbox -c
```

### Deployment with Tests
```bash
# Automatically runs tests during deployment
sf project deploy start -d src/ -o production --test-level RunLocalTests
```

### Pre-Deployment Validation
```bash
# Validate without deploying
sf project deploy start -d src/ -o production --dry-run --test-level RunLocalTests
```
