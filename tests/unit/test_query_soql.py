#!/usr/bin/env python3
"""
Unit tests for query_soql.py

Tests the SOQL query execution and formatting logic.
"""

import unittest
import sys
from pathlib import Path

# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

# Import after path modification
import query_soql


class TestFlattenRecord(unittest.TestCase):
    """Test the flatten_record function."""

    def test_simple_record(self):
        """Test flattening a simple record with no relationships."""
        record = {
            "attributes": {"type": "Account"},
            "Id": "001xx000003DGb2AAG",
            "Name": "Acme Corp"
        }
        result = query_soql.flatten_record(record)
        self.assertEqual(result["Id"], "001xx000003DGb2AAG")
        self.assertEqual(result["Name"], "Acme Corp")
        self.assertNotIn("attributes", result)

    def test_nested_relationship(self):
        """Test flattening a record with parent relationship."""
        record = {
            "attributes": {"type": "Contact"},
            "Id": "003xx000004TmiZAAS",
            "Name": "John Doe",
            "Account": {
                "attributes": {"type": "Account"},
                "Id": "001xx000003DGb2AAG",
                "Name": "Acme Corp"
            }
        }
        result = query_soql.flatten_record(record)
        self.assertEqual(result["Name"], "John Doe")
        self.assertEqual(result["Account.Id"], "001xx000003DGb2AAG")
        self.assertEqual(result["Account.Name"], "Acme Corp")

    def test_null_values(self):
        """Test handling of null values."""
        record = {
            "attributes": {"type": "Account"},
            "Id": "001xx000003DGb2AAG",
            "Name": "Test",
            "Website": None
        }
        result = query_soql.flatten_record(record)
        self.assertIsNone(result["Website"])


class TestFormatTable(unittest.TestCase):
    """Test the format_table function."""

    def test_empty_results(self):
        """Test formatting empty result set."""
        result = query_soql.format_table([])
        self.assertEqual(result, "No results found.")

    def test_simple_table(self):
        """Test formatting a simple table."""
        records = [
            {"Id": "001", "Name": "Test 1"},
            {"Id": "002", "Name": "Test 2"}
        ]
        result = query_soql.format_table(records)
        self.assertIn("| Id | Name |", result)
        self.assertIn("| 001 | Test 1 |", result)
        self.assertIn("| 002 | Test 2 |", result)

    def test_long_values_truncated(self):
        """Test that long values are truncated."""
        long_string = "A" * 100
        records = [{"Id": "001", "LongField": long_string}]
        result = query_soql.format_table(records)
        self.assertIn("...", result)


if __name__ == "__main__":
    unittest.main()
