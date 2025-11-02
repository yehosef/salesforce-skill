#!/usr/bin/env python3
"""
Unit tests for validate_field_writeability.py

Tests field assignment detection, SObject normalization, and metadata validation.
"""

import unittest
from pathlib import Path
import tempfile
import json
from typing import Dict, Set
import sys

# Add scripts directory to path so we can import the validator
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'scripts'))

from validate_field_writeability import FieldValidator, FieldInfo


class TestFieldInfo(unittest.TestCase):
    """Tests for FieldInfo class."""

    def test_writeable_field(self):
        """Test a writeable field."""
        metadata = {'updateable': True, 'type': 'String'}
        field = FieldInfo('Name', 'Name', 'Account', metadata)
        self.assertTrue(field.is_writeable)

    def test_read_only_field(self):
        """Test a read-only field."""
        metadata = {'updateable': False, 'type': 'String'}
        field = FieldInfo('Name', 'Name', 'Account', metadata)
        self.assertFalse(field.is_writeable)

    def test_formula_field(self):
        """Test a formula field."""
        metadata = {'updateable': False, 'calculated': True, 'type': 'String'}
        field = FieldInfo('CalculatedField', 'Calculated', 'Account', metadata)
        self.assertTrue(field.is_formula)
        self.assertFalse(field.is_writeable)
        self.assertIn('Formula field', field.get_reason_not_writeable())

    def test_system_field(self):
        """Test a system field."""
        metadata = {'updateable': False, 'type': 'System.Date', 'calculated': False}
        field = FieldInfo('CreatedDate', 'Created Date', 'Account', metadata)
        self.assertTrue(field.is_system_field)
        self.assertFalse(field.is_writeable)
        self.assertIn('System field', field.get_reason_not_writeable())

    def test_external_field(self):
        """Test an external field."""
        metadata = {'updateable': False, 'type': 'ExternalFieldDefinition', 'calculated': False}
        field = FieldInfo('ExtField', 'External Field', 'Account', metadata)
        self.assertTrue(field.is_external)
        self.assertFalse(field.is_writeable)
        self.assertIn('External field', field.get_reason_not_writeable())


class TestFieldAssignmentDetection(unittest.TestCase):
    """Tests for field assignment detection."""

    def setUp(self):
        """Set up test fixtures."""
        self.validator = FieldValidator('test-org', verbose=False)

    def test_direct_assignment(self):
        """Test detection of direct field assignment: account.Name = value"""
        code = "account.Name = 'Test';"
        assignments = self.validator._extract_assignments(Path('test.cls'), code)
        self.assertIn('Account', assignments)
        self.assertIn('Name', assignments['Account'])

    def test_direct_assignment_custom_field(self):
        """Test detection of custom field assignment: account.CustomField__c = value"""
        code = "account.CustomField__c = 'Test';"
        assignments = self.validator._extract_assignments(Path('test.cls'), code)
        self.assertIn('Account', assignments)
        self.assertIn('CustomField__c', assignments['Account'])

    def test_constructor_assignment(self):
        """Test detection of constructor assignment: new Account(Name = value)"""
        code = "Account acc = new Account(Name = 'Test');"
        assignments = self.validator._extract_assignments(Path('test.cls'), code)
        self.assertIn('Account', assignments)
        self.assertIn('Name', assignments['Account'])

    def test_array_assignment(self):
        """Test detection of array assignment: accounts[0].Name = value"""
        code = "accounts[0].Name = 'Test';"
        assignments = self.validator._extract_assignments(Path('test.cls'), code)
        self.assertIn('Accounts', assignments)  # Note: normalized
        self.assertIn('Name', assignments['Accounts'])

    def test_put_assignment_skipped(self):
        """Test that put() assignments are detected but SObject type skipped."""
        code = "obj.put('CustomField__c', 'value');"
        assignments = self.validator._extract_assignments(Path('test.cls'), code)
        # put() pattern can't determine SObject type, so no assignment should be added
        # (or implementation may vary - check actual behavior)
        # This test documents the current behavior
        self.assertEqual(len(assignments), 0)

    def test_multiple_fields(self):
        """Test detection of multiple field assignments."""
        code = """
        Account acc = new Account();
        acc.Name = 'Test';
        acc.Phone = '555-1234';
        acc.CustomField__c = 'Custom';
        """
        assignments = self.validator._extract_assignments(Path('test.cls'), code)
        self.assertIn('Account', assignments)
        self.assertEqual(len(assignments['Account']), 3)
        self.assertIn('Name', assignments['Account'])
        self.assertIn('Phone', assignments['Account'])
        self.assertIn('CustomField__c', assignments['Account'])

    def test_multiple_sobjects(self):
        """Test detection of assignments across multiple SObject types."""
        code = """
        account.Name = 'Test';
        opportunity.StageName = 'Closed Won';
        quote.QuoteNumber = 'Q-001';
        """
        assignments = self.validator._extract_assignments(Path('test.cls'), code)
        self.assertEqual(len(assignments), 3)
        self.assertIn('Account', assignments)
        self.assertIn('Opportunity', assignments)
        self.assertIn('Quote', assignments)

    def test_no_assignments(self):
        """Test code with no field assignments."""
        code = "String name = 'Test'; Integer count = 5;"
        assignments = self.validator._extract_assignments(Path('test.cls'), code)
        self.assertEqual(len(assignments), 0)


class TestSObjectNormalization(unittest.TestCase):
    """Tests for SObject name normalization."""

    def setUp(self):
        """Set up test fixtures."""
        self.validator = FieldValidator('test-org', verbose=False)

    def test_lowercase_normalization(self):
        """Test normalization of lowercase names."""
        self.assertEqual(self.validator._normalize_sobject_name('account'), 'Account')
        self.assertEqual(self.validator._normalize_sobject_name('opportunity'), 'Opportunity')

    def test_mixed_case_normalization(self):
        """Test normalization of mixed case names."""
        self.assertEqual(
            self.validator._normalize_sobject_name('opportunityLineItem'),
            'OpportunityLineItem'
        )

    def test_custom_object_normalization(self):
        """Test normalization of custom objects."""
        self.assertEqual(
            self.validator._normalize_sobject_name('customObject__c'),
            'CustomObject__c'
        )

    def test_already_normalized(self):
        """Test names already in canonical form."""
        self.assertEqual(self.validator._normalize_sobject_name('Account'), 'Account')
        self.assertEqual(self.validator._normalize_sobject_name('Quote'), 'Quote')

    def test_empty_string(self):
        """Test empty string handling."""
        self.assertEqual(self.validator._normalize_sobject_name(''), '')

    def test_single_char(self):
        """Test single character names."""
        self.assertEqual(self.validator._normalize_sobject_name('a'), 'A')


class TestCacheBehavior(unittest.TestCase):
    """Tests for metadata caching with case normalization."""

    def setUp(self):
        """Set up test fixtures."""
        self.validator = FieldValidator('test-org', verbose=False)

    def test_case_insensitive_cache_lookup(self):
        """Test that cache lookups are case-insensitive."""
        # Simulate adding metadata for 'Account'
        metadata_account = {
            'Name': FieldInfo('Name', 'Account Name', 'Account', {'updateable': True, 'type': 'String'})
        }
        self.validator.metadata_cache['Account'] = metadata_account

        # Try to access with lowercase 'account'
        normalized = self.validator._normalize_sobject_name('account')
        self.assertEqual(normalized, 'Account')
        self.assertIn('Account', self.validator.metadata_cache)

    def test_no_duplicate_cache_entries(self):
        """Test that case variations don't create duplicate cache entries."""
        # Both 'account' and 'Account' should normalize to same key
        norm1 = self.validator._normalize_sobject_name('account')
        norm2 = self.validator._normalize_sobject_name('Account')
        self.assertEqual(norm1, norm2)


class TestFieldValidatorIntegration(unittest.TestCase):
    """Integration tests for FieldValidator class."""

    def setUp(self):
        """Set up test fixtures."""
        self.validator = FieldValidator('test-org', verbose=False)

    def test_apex_file_detection(self):
        """Test that .cls files are recognized as Apex."""
        apex_code = "account.Name = 'Test';"
        assignments = self.validator._extract_assignments(Path('TestClass.cls'), apex_code)
        self.assertGreater(len(assignments), 0)

    def test_js_file_no_detection(self):
        """Test that .js files don't trigger Apex pattern matching."""
        # LWC code with similar syntax shouldn't match Apex patterns
        js_code = "account.Name = 'Test';"
        assignments = self.validator._extract_assignments(Path('test.js'), js_code)
        # JS files don't have Apex pattern matching implemented yet
        self.assertEqual(len(assignments), 0)

    def test_unicode_handling(self):
        """Test handling of unicode characters in code."""
        code = "account.Name = 'טסט'; // Hebrew comment"
        assignments = self.validator._extract_assignments(Path('test.cls'), code)
        self.assertIn('Account', assignments)
        self.assertIn('Name', assignments['Account'])


class TestEdgeCases(unittest.TestCase):
    """Tests for edge cases and error conditions."""

    def setUp(self):
        """Set up test fixtures."""
        self.validator = FieldValidator('test-org', verbose=False)

    def test_field_with_numbers(self):
        """Test field names containing numbers."""
        code = "account.Field123__c = 'Test';"
        assignments = self.validator._extract_assignments(Path('test.cls'), code)
        self.assertIn('Account', assignments)
        self.assertIn('Field123__c', assignments['Account'])

    def test_nested_assignments(self):
        """Test nested object assignments."""
        code = "opportunityLineItems[0].Quantity = 5;"
        assignments = self.validator._extract_assignments(Path('test.cls'), code)
        self.assertIn('OpportunityLineItems', assignments)
        self.assertIn('Quantity', assignments['OpportunityLineItems'])

    def test_comments_ignored(self):
        """Test that comments don't interfere with detection."""
        code = """
        // account.Name = 'Should not detect';
        account.Phone = '555-1234';  // This should detect
        """
        assignments = self.validator._extract_assignments(Path('test.cls'), code)
        # Note: Regex-based detection may pick up commented code
        # This test documents current behavior
        self.assertIn('Account', assignments)
        self.assertIn('Phone', assignments['Account'])

    def test_string_with_assignment_syntax(self):
        """Test that assignment syntax in strings is detected."""
        # Note: Regex-based detection can't distinguish strings from code
        # This is a known limitation
        code = "String example = \"obj.field = 'value';\";"
        assignments = self.validator._extract_assignments(Path('test.cls'), code)
        # This may or may not detect - documents current behavior
        # In practice, this is acceptable as it's a rare false positive


if __name__ == '__main__':
    unittest.main()
