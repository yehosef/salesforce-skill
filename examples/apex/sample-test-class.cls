/**
 * Example Apex Test Class
 *
 * Demonstrates best practices for Apex testing including:
 * - @TestSetup for data creation
 * - Positive and negative test cases
 * - Bulk testing (200+ records)
 * - Assertion patterns
 */
@isTest
private class AccountServiceTest {

    @TestSetup
    static void makeData() {
        // Create test data once for all test methods
        List<Account> accounts = new List<Account>();

        for (Integer i = 0; i < 200; i++) {
            accounts.add(new Account(
                Name = 'Test Account ' + i,
                Industry = 'Technology',
                AnnualRevenue = 100000 + (i * 1000)
            ));
        }

        insert accounts;
    }

    @isTest
    static void testPositive_UpdateAccountIndustry() {
        // Arrange
        List<Account> accounts = [SELECT Id, Industry FROM Account LIMIT 10];

        // Act
        Test.startTest();
        for (Account acc : accounts) {
            acc.Industry = 'Manufacturing';
        }
        update accounts;
        Test.stopTest();

        // Assert
        List<Account> updatedAccounts = [
            SELECT Id, Industry
            FROM Account
            WHERE Industry = 'Manufacturing'
        ];
        System.assertEquals(10, updatedAccounts.size(),
            'Expected 10 accounts to be updated');
    }

    @isTest
    static void testNegative_InvalidAccountName() {
        // Arrange
        Account acc = new Account(
            Name = '',  // Invalid: empty name
            Industry = 'Technology'
        );

        // Act & Assert
        Test.startTest();
        try {
            insert acc;
            System.assert(false, 'Expected DmlException for empty name');
        } catch (DmlException e) {
            System.assert(e.getMessage().contains('REQUIRED_FIELD_MISSING'),
                'Expected missing field error');
        }
        Test.stopTest();
    }

    @isTest
    static void testBulk_UpdateMultipleAccounts() {
        // Arrange
        List<Account> accounts = [SELECT Id, AnnualRevenue FROM Account];

        // Act
        Test.startTest();
        for (Account acc : accounts) {
            acc.AnnualRevenue = acc.AnnualRevenue * 1.1; // 10% increase
        }
        update accounts;
        Test.stopTest();

        // Assert
        List<Account> updatedAccounts = [
            SELECT Id, AnnualRevenue
            FROM Account
            WHERE AnnualRevenue > 100000
        ];
        System.assertEquals(200, updatedAccounts.size(),
            'All accounts should be updated');
    }
}
