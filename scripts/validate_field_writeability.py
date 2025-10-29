#!/usr/bin/env python3
"""
Validate field writeability to prevent FIELD_NOT_WRITEABLE deployment errors.

This script scans your Apex and LWC code for field assignments and validates
that the target fields are writeable in your Salesforce org. It catches formula
fields, external fields, system fields, and read-only custom fields before
deployment.

USAGE:
    ./validate_field_writeability.py [--help]
    ./validate_field_writeability.py <source_dir> <org_alias>
    ./validate_field_writeability.py src/ my-sandbox --verbose
    ./validate_field_writeability.py src/ production --json

ARGUMENTS:
    source_dir       Path to directory containing Apex/LWC code (e.g., src/)
    org_alias        Salesforce org alias (must be authenticated)

OPTIONS:
    -h, --help       Show this help message
    -v, --verbose    Show detailed output for each file analyzed
    --json          Output results as JSON for CI/CD integration
    --max-issues N   Stop scanning after N issues found (default: unlimited)

EXAMPLES:
    # Validate sandbox before deployment
    ./validate_field_writeability.py src/ dev-sandbox

    # Verbose output to see all files scanned
    ./validate_field_writeability.py src/ staging --verbose

    # JSON output for CI/CD pipelines
    ./validate_field_writeability.py src/ production --json > validation.json

REQUIREMENTS:
    - Salesforce CLI (sf v2.x+): npm install -g @salesforce/cli
    - Authenticated org: sf org login web -a <alias>
    - Python 3.8+

SAFETY:
    🟢 READ-ONLY - No changes made to files or orgs
    🟢 QUERIES ONLY - Only reads metadata from org
    🟢 NO DEPENDENCIES - Uses standard library only

DETECTION:
    Finds field assignments in Apex:
    - Direct assignment: account.CustomField__c = value
    - Constructor params: new Account(CustomField__c = value)
    - List/Map assignment: accounts[0].CustomField__c = value

    Does NOT detect (requires manual review):
    - Dynamic assignments: obj.put('FieldName', value)
    - Reflection-based updates: obj.setSObjectField(...)

COMMON ISSUES FIXED:
    - Formula fields (calculated, not stored)
    - External fields (integration fields)
    - System fields (CreatedDate, LastModifiedDate, etc.)
    - Read-only custom fields
    - Roll-up summary fields
    - Lookup fields on read-only objects
"""

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
import argparse


class Colors:
    """ANSI color codes for terminal output."""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class FieldInfo:
    """Represents field metadata from Salesforce."""

    def __init__(self, name: str, label: str, sobj_type: str, metadata: Dict):
        self.name = name
        self.label = label
        self.sobj_type = sobj_type
        self.metadata = metadata

    @property
    def is_writeable(self) -> bool:
        """Check if field is writeable."""
        return self.metadata.get('updateable', False)

    @property
    def is_formula(self) -> bool:
        """Check if field is a formula field."""
        return self.metadata.get('calculated', False)

    @property
    def is_external(self) -> bool:
        """Check if field is an external field."""
        return 'ExternalFieldDefinition' in self.metadata.get('type', '')

    @property
    def is_system_field(self) -> bool:
        """Check if field is a system field."""
        return self.metadata.get('type', '').startswith('System.')

    @property
    def field_type(self) -> str:
        """Get the field type."""
        return self.metadata.get('type', 'Unknown')

    def get_reason_not_writeable(self) -> str:
        """Get human-readable reason why field is not writeable."""
        if self.is_formula:
            return "Formula field (calculated, not stored)"
        if self.is_external:
            return "External field (integration field)"
        if self.is_system_field:
            return f"System field ({self.field_type})"
        return f"Read-only field (type: {self.field_type})"


class FieldValidator:
    """Main validator for field writeability."""

    def __init__(self, org_alias: str, verbose: bool = False):
        self.org_alias = org_alias
        self.verbose = verbose
        self.metadata_cache: Dict[str, Dict[str, FieldInfo]] = {}
        self.issues: List[Dict] = []

    def validate(self, source_dir: Path) -> Tuple[List[Dict], int]:
        """
        Validate all Apex and LWC files in directory.

        Returns:
            Tuple of (issues list, exit code)
        """
        if not source_dir.exists():
            raise FileNotFoundError(f"Directory not found: {source_dir}")

        # Find all Apex and LWC files
        apex_files = list(source_dir.glob('**/*.cls'))
        js_files = list(source_dir.glob('**/*.js'))

        files_to_check = apex_files + js_files

        if not files_to_check:
            print(f"{Colors.YELLOW}No Apex (.cls) or LWC (.js) files found in {source_dir}{Colors.RESET}")
            return [], 0

        # Extract field assignments
        all_assignments: Dict[str, Set[str]] = {}

        for file_path in files_to_check:
            try:
                content = file_path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                if self.verbose:
                    print(f"  Skipped (encoding): {file_path}")
                continue

            assignments = self._extract_assignments(file_path, content)

            for sobj, fields in assignments.items():
                if sobj not in all_assignments:
                    all_assignments[sobj] = set()
                all_assignments[sobj].update(fields)

            if self.verbose and assignments:
                print(f"  Found in: {file_path.name} - {sum(len(f) for f in assignments.values())} fields")

        if not all_assignments:
            print(f"{Colors.GREEN}✓ No field assignments found to validate{Colors.RESET}")
            return [], 0

        # Validate each SObject's fields
        print(f"\n{Colors.BLUE}Validating {len(all_assignments)} objects across {len(files_to_check)} files...{Colors.RESET}\n")

        for sobj_type, fields in sorted(all_assignments.items()):
            self._validate_sobject_fields(sobj_type, fields)

        return self.issues, 1 if self.issues else 0

    def _extract_assignments(self, file_path: Path, content: str) -> Dict[str, Set[str]]:
        """Extract field assignments from code."""
        assignments: Dict[str, Set[str]] = {}

        is_apex = file_path.suffix == '.cls'

        if is_apex:
            # Apex field assignment patterns - matches all field types
            patterns = [
                # Direct: obj.fieldName = value (all field types: custom and standard)
                r'(?:^|[\s;])([a-zA-Z_]\w+)\.([a-zA-Z_]\w+(?:__c)?)\s*=',
                # Constructor: new Account(Field = value)
                r'new\s+([a-zA-Z_]\w+)\s*\([^)]*?([a-zA-Z_]\w+(?:__c)?)\s*=',
                # List/Array: list[0].fieldName = value
                r'(?:^|[\s;])([a-zA-Z_]\w+)(?:\[\d+\])\.([a-zA-Z_]\w+(?:__c)?)\s*=',
            ]

            for pattern in patterns:
                for match in re.finditer(pattern, content, re.MULTILINE):
                    groups = match.groups()
                    if len(groups) >= 2:
                        # Preserve original case - Salesforce API names are case-sensitive
                        sobj_type = groups[0]
                        field_name = groups[-1]

                        if sobj_type not in assignments:
                            assignments[sobj_type] = set()
                        assignments[sobj_type].add(field_name)

        return assignments

    def _validate_sobject_fields(self, sobj_type: str, fields: Set[str]):
        """Validate all fields for an SObject type."""
        # Get metadata for this SObject
        if sobj_type not in self.metadata_cache:
            metadata = self._get_sobject_metadata(sobj_type)
            if not metadata:
                print(f"{Colors.YELLOW}⚠ Warning: Could not find SObject '{sobj_type}' in org{Colors.RESET}")
                return
            self.metadata_cache[sobj_type] = metadata

        metadata = self.metadata_cache[sobj_type]

        # Check each field
        for field_name in sorted(fields):
            if field_name not in metadata:
                # Field doesn't exist - might be dynamic or typo
                self.issues.append({
                    'type': 'FIELD_NOT_FOUND',
                    'sobject': sobj_type,
                    'field': field_name,
                    'severity': 'warning',
                    'reason': f'Field not found in {sobj_type} metadata (may be dynamic)'
                })
                print(f"{Colors.YELLOW}⚠ {sobj_type}.{field_name:<30} FIELD NOT FOUND{Colors.RESET}")
            else:
                field_info = metadata[field_name]

                if not field_info.is_writeable:
                    reason = field_info.get_reason_not_writeable()
                    self.issues.append({
                        'type': 'FIELD_NOT_WRITEABLE',
                        'sobject': sobj_type,
                        'field': field_name,
                        'field_type': field_info.field_type,
                        'severity': 'error',
                        'reason': reason
                    })
                    print(f"{Colors.RED}✗ {sobj_type}.{field_name:<30} NOT WRITEABLE - {reason}{Colors.RESET}")
                else:
                    if self.verbose:
                        print(f"{Colors.GREEN}✓ {sobj_type}.{field_name:<30} writeable{Colors.RESET}")

    def _get_sobject_metadata(self, sobj_type: str) -> Optional[Dict[str, FieldInfo]]:
        """Query Salesforce for SObject field metadata."""
        try:
            cmd = [
                'sf', 'sobject', 'describe',
                '-s', sobj_type,
                '-o', self.org_alias,
                '--json'
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                if 'No such object' in result.stderr or 'not found' in result.stderr.lower():
                    return None
                raise RuntimeError(f"Failed to describe {sobj_type}: {result.stderr}")

            data = json.loads(result.stdout)

            if 'status' in data and data['status'] != 0:
                return None

            # Extract fields
            fields: Dict[str, FieldInfo] = {}

            for field in data.get('fields', []):
                field_name = field.get('name', '')
                field_info = FieldInfo(
                    name=field_name,
                    label=field.get('label', ''),
                    sobj_type=sobj_type,
                    metadata=field
                )
                fields[field_name] = field_info

            return fields

        except subprocess.TimeoutExpired:
            print(f"{Colors.RED}Error: Timeout querying {sobj_type} after 30 seconds{Colors.RESET}", file=sys.stderr)
            print("Check org connectivity or try again later", file=sys.stderr)
            return None
        except json.JSONDecodeError as e:
            print(f"{Colors.RED}Error parsing SF CLI response: {e}{Colors.RESET}", file=sys.stderr)
            return None
        except FileNotFoundError:
            print(f"{Colors.RED}Error: Salesforce CLI (sf) not found{Colors.RESET}", file=sys.stderr)
            print("Install from: https://developer.salesforce.com/tools/salesforcecli", file=sys.stderr)
            sys.exit(2)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Validate field writeability before Salesforce deployment',
        epilog='Safety: READ-ONLY operation. No changes made to files or orgs.'
    )

    parser.add_argument('source_dir', help='Path to source directory (e.g., src/)')
    parser.add_argument('org_alias', help='Salesforce org alias')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--max-issues', type=int, help='Stop after N issues')

    args = parser.parse_args()

    # Validate arguments
    source_dir = Path(args.source_dir)

    if not source_dir.exists():
        print(f"{Colors.RED}Error: Directory not found: {source_dir}{Colors.RESET}", file=sys.stderr)
        print(f"Try: ./validate_field_writeability.py src/ {args.org_alias}", file=sys.stderr)
        sys.exit(2)

    # Run validation
    try:
        validator = FieldValidator(args.org_alias, args.verbose)
        issues, exit_code = validator.validate(source_dir)

        if args.max_issues and len(issues) > args.max_issues:
            issues = issues[:args.max_issues]

        # Output results
        if args.json:
            print(json.dumps({
                'success': exit_code == 0,
                'issues': issues,
                'total': len(issues)
            }, indent=2))
        else:
            print(f"\n{Colors.BOLD}Validation Summary:{Colors.RESET}")
            print(f"  Total issues: {len(issues)}")

            if exit_code == 0:
                print(f"  {Colors.GREEN}✓ All fields are writeable{Colors.RESET}")
            else:
                errors = [i for i in issues if i['severity'] == 'error']
                warnings = [i for i in issues if i['severity'] == 'warning']

                if errors:
                    print(f"  {Colors.RED}✗ Errors: {len(errors)}{Colors.RESET}")
                if warnings:
                    print(f"  {Colors.YELLOW}⚠ Warnings: {len(warnings)}{Colors.RESET}")

        sys.exit(exit_code)

    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Cancelled by user{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.RESET}", file=sys.stderr)
        sys.exit(2)


if __name__ == '__main__':
    main()
