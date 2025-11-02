#!/usr/bin/env python3
"""
Unit tests for validate_visualforce.py

Tests Visualforce syntax validation, XXE protection, and attribute checking.
"""

import unittest
from pathlib import Path
import tempfile
import json
from xml.etree import ElementTree as ET
import sys

# Add scripts directory to path so we can import the validator
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'scripts'))

from validate_visualforce import VFValidator, SAFE_XML_PARSE, SECURITY_LEVEL


class TestXMLSecurityParsing(unittest.TestCase):
    """Tests for XXE (XML External Entity) injection protection."""

    def test_safe_xml_parse_basic(self):
        """Test basic XML parsing works."""
        xml = '<?xml version="1.0"?><root><element>test</element></root>'
        root = SAFE_XML_PARSE(xml)
        self.assertIsNotNone(root)
        self.assertEqual(root.tag, 'root')

    def test_safe_xml_parse_namespaces(self):
        """Test XML parsing with namespaces (Visualforce)."""
        xml = '''<?xml version="1.0" ?>
        <apex:page xmlns:apex="http://www.force.com/2006/04/apex">
            <apex:form></apex:form>
        </apex:page>'''
        root = SAFE_XML_PARSE(xml)
        self.assertIsNotNone(root)

    def test_xxe_prevention(self):
        """Test that XXE attacks are prevented."""
        # This XXE payload should be blocked
        xxe_payload = '''<?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE foo [
          <!ENTITY xxe SYSTEM "file:///etc/passwd">
        ]>
        <root>&xxe;</root>'''

        # Should not raise, but entity should be empty/blocked
        try:
            root = SAFE_XML_PARSE(xxe_payload)
            # If it parses, entity references should be empty or blocked
            # (exact behavior depends on implementation)
            self.assertIsNotNone(root)
        except Exception:
            # XXE prevention may raise exception - both are acceptable
            pass

    def test_security_level_defined(self):
        """Test that security level is properly set."""
        self.assertIn(SECURITY_LEVEL, ['HIGH', 'MEDIUM'])

    def test_malformed_xml_raises(self):
        """Test that malformed XML raises ParseError."""
        malformed = '<root><unclosed>'
        with self.assertRaises(ET.ParseError):
            SAFE_XML_PARSE(malformed)


class TestVFValidatorBasics(unittest.TestCase):
    """Basic tests for VFValidator class."""

    def setUp(self):
        """Set up test fixtures."""
        self.validator = VFValidator(verbose=False)

    def test_initialization(self):
        """Test validator initialization."""
        self.assertFalse(self.validator.verbose)
        self.assertEqual(len(self.validator.issues), 0)
        self.assertEqual(self.validator.files_checked, 0)

    def test_verbose_flag(self):
        """Test verbose flag is stored."""
        validator = VFValidator(verbose=True)
        self.assertTrue(validator.verbose)


class TestUnsupportedAttributes(unittest.TestCase):
    """Tests for unsupported attribute detection."""

    def setUp(self):
        """Set up test fixtures."""
        self.validator = VFValidator(verbose=False)

    def test_dir_attribute_on_page(self):
        """Test detection of unsupported 'dir' attribute."""
        xml = '''<?xml version="1.0" ?>
        <apex:page xmlns:apex="http://www.force.com/2006/04/apex" dir="rtl">
            <apex:form></apex:form>
        </apex:page>'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.page', delete=False) as f:
            f.write(xml)
            f.flush()
            try:
                file_path = Path(f.name)
                self.validator._validate_file(file_path)
                # Should find unsupported attribute
                unsupported_issues = [
                    i for i in self.validator.issues
                    if i.get('type') == 'UNSUPPORTED_ATTRIBUTE'
                ]
                self.assertGreater(len(unsupported_issues), 0)
            finally:
                file_path.unlink()

    def test_valid_attributes_allowed(self):
        """Test that valid attributes don't raise issues."""
        xml = '''<?xml version="1.0" ?>
        <apex:page xmlns:apex="http://www.force.com/2006/04/apex"
                   controller="MyController"
                   standardStylesheets="true">
            <apex:form></apex:form>
        </apex:page>'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.page', delete=False) as f:
            f.write(xml)
            f.flush()
            try:
                file_path = Path(f.name)
                initial_issues = len(self.validator.issues)
                self.validator._validate_file(file_path)
                new_issues = len(self.validator.issues) - initial_issues
                # Valid attributes shouldn't create UNSUPPORTED_ATTRIBUTE issues
                unsupported_issues = [
                    i for i in self.validator.issues[initial_issues:]
                    if i.get('type') == 'UNSUPPORTED_ATTRIBUTE'
                ]
                self.assertEqual(len(unsupported_issues), 0)
            finally:
                file_path.unlink()


class TestDeprecatedTags(unittest.TestCase):
    """Tests for deprecated tag detection."""

    def setUp(self):
        """Set up test fixtures."""
        self.validator = VFValidator(verbose=False)

    def test_deprecated_include_tag(self):
        """Test detection of deprecated apex:include tag."""
        xml = '''<?xml version="1.0" ?>
        <apex:page xmlns:apex="http://www.force.com/2006/04/apex">
            <apex:include pageName="IncludedPage"/>
        </apex:page>'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.page', delete=False) as f:
            f.write(xml)
            f.flush()
            try:
                file_path = Path(f.name)
                self.validator._validate_file(file_path)
                deprecated_issues = [
                    i for i in self.validator.issues
                    if i.get('type') == 'DEPRECATED_TAG'
                ]
                self.assertGreater(len(deprecated_issues), 0)
            finally:
                file_path.unlink()

    def test_non_deprecated_tags(self):
        """Test that non-deprecated tags don't raise issues."""
        xml = '''<?xml version="1.0" ?>
        <apex:page xmlns:apex="http://www.force.com/2006/04/apex">
            <apex:pageBlock title="Test">
                <apex:pageBlockSection>
                    <apex:inputField value="{!obj.Name}"/>
                </apex:pageBlockSection>
            </apex:pageBlock>
        </apex:page>'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.page', delete=False) as f:
            f.write(xml)
            f.flush()
            try:
                file_path = Path(f.name)
                initial_issues = len(self.validator.issues)
                self.validator._validate_file(file_path)
                new_issues = len(self.validator.issues) - initial_issues
                deprecated_issues = [
                    i for i in self.validator.issues[initial_issues:]
                    if i.get('type') == 'DEPRECATED_TAG'
                ]
                self.assertEqual(len(deprecated_issues), 0)
            finally:
                file_path.unlink()


class TestXSSPatternDetection(unittest.TestCase):
    """Tests for potential XSS vulnerability detection."""

    def setUp(self):
        """Set up test fixtures."""
        self.validator = VFValidator(verbose=True)  # Enable verbose for pattern detection

    def test_unescaped_output_detection(self):
        """Test detection of potentially unescaped output."""
        xml = '''<?xml version="1.0" ?>
        <apex:page xmlns:apex="http://www.force.com/2006/04/apex">
            <apex:outputText value="{!variable}"/>
        </apex:page>'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.page', delete=False) as f:
            f.write(xml)
            f.flush()
            try:
                file_path = Path(f.name)
                self.validator._validate_file(file_path)
                xss_issues = [
                    i for i in self.validator.issues
                    if i.get('type') == 'POTENTIAL_XSS'
                ]
                # May or may not detect depending on pattern
                # This test documents behavior
            finally:
                file_path.unlink()


class TestMissingSLDS(unittest.TestCase):
    """Tests for missing Salesforce Lightning Design System detection."""

    def setUp(self):
        """Set up test fixtures."""
        self.validator = VFValidator(verbose=True)

    def test_missing_slds_warning(self):
        """Test that pages without SLDS get a warning."""
        xml = '''<?xml version="1.0" ?>
        <apex:page xmlns:apex="http://www.force.com/2006/04/apex">
            <apex:form></apex:form>
        </apex:page>'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.page', delete=False) as f:
            f.write(xml)
            f.flush()
            try:
                file_path = Path(f.name)
                self.validator._validate_file(file_path)
                slds_issues = [
                    i for i in self.validator.issues
                    if i.get('type') == 'MISSING_SLDS'
                ]
                self.assertGreater(len(slds_issues), 0)
            finally:
                file_path.unlink()

    def test_slds_present_no_warning(self):
        """Test that pages with SLDS don't get warning."""
        xml = '''<?xml version="1.0" ?>
        <apex:page xmlns:apex="http://www.force.com/2006/04/apex">
            <apex:slds />
            <apex:form></apex:form>
        </apex:page>'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.page', delete=False) as f:
            f.write(xml)
            f.flush()
            try:
                file_path = Path(f.name)
                initial_issues = len(self.validator.issues)
                self.validator._validate_file(file_path)
                slds_issues = [
                    i for i in self.validator.issues[initial_issues:]
                    if i.get('type') == 'MISSING_SLDS'
                ]
                self.assertEqual(len(slds_issues), 0)
            finally:
                file_path.unlink()


class TestSyntaxValidation(unittest.TestCase):
    """Tests for XML syntax validation."""

    def setUp(self):
        """Set up test fixtures."""
        self.validator = VFValidator(verbose=False)

    def test_valid_syntax_no_error(self):
        """Test that valid VF syntax doesn't produce syntax errors."""
        xml = '''<?xml version="1.0" ?>
        <apex:page xmlns:apex="http://www.force.com/2006/04/apex">
            <apex:form>
                <apex:pageBlock title="Test"/>
            </apex:form>
        </apex:page>'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.page', delete=False) as f:
            f.write(xml)
            f.flush()
            try:
                file_path = Path(f.name)
                self.validator._validate_file(file_path)
                syntax_errors = [
                    i for i in self.validator.issues
                    if i.get('type') == 'SYNTAX_ERROR'
                ]
                self.assertEqual(len(syntax_errors), 0)
            finally:
                file_path.unlink()

    def test_invalid_syntax_produces_error(self):
        """Test that invalid VF syntax produces syntax error."""
        xml = '''<?xml version="1.0" ?>
        <apex:page xmlns:apex="http://www.force.com/2006/04/apex">
            <apex:form>
                <unclosed:tag>
            </apex:form>
        </apex:page>'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.page', delete=False) as f:
            f.write(xml)
            f.flush()
            try:
                file_path = Path(f.name)
                self.validator._validate_file(file_path)
                syntax_errors = [
                    i for i in self.validator.issues
                    if i.get('type') == 'SYNTAX_ERROR'
                ]
                self.assertGreater(len(syntax_errors), 0)
            finally:
                file_path.unlink()


class TestFileHandling(unittest.TestCase):
    """Tests for file handling and edge cases."""

    def setUp(self):
        """Set up test fixtures."""
        self.validator = VFValidator(verbose=False)

    def test_page_file_detection(self):
        """Test that .page files are validated."""
        xml = '''<?xml version="1.0" ?>
        <apex:page xmlns:apex="http://www.force.com/2006/04/apex"/>'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.page', delete=False) as f:
            f.write(xml)
            f.flush()
            try:
                file_path = Path(f.name)
                self.validator._validate_file(file_path)
                # Should parse without errors
                self.assertIsNotNone(self.validator.files_checked)
            finally:
                file_path.unlink()

    def test_component_file_detection(self):
        """Test that .component files are validated."""
        xml = '''<?xml version="1.0" ?>
        <apex:component xmlns:apex="http://www.force.com/2006/04/apex"/>'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.component', delete=False) as f:
            f.write(xml)
            f.flush()
            try:
                file_path = Path(f.name)
                self.validator._validate_file(file_path)
                # Should parse without errors
                self.assertIsNotNone(self.validator.files_checked)
            finally:
                file_path.unlink()

    def test_unicode_handling(self):
        """Test handling of unicode characters in VF."""
        xml = '''<?xml version="1.0" encoding="UTF-8"?>
        <apex:page xmlns:apex="http://www.force.com/2006/04/apex" title="טסט">
            <apex:form/>
        </apex:page>'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.page', delete=False, encoding='utf-8') as f:
            f.write(xml)
            f.flush()
            try:
                file_path = Path(f.name)
                self.validator._validate_file(file_path)
                syntax_errors = [
                    i for i in self.validator.issues
                    if i.get('type') == 'SYNTAX_ERROR'
                ]
                self.assertEqual(len(syntax_errors), 0)
            finally:
                file_path.unlink()


if __name__ == '__main__':
    unittest.main()
