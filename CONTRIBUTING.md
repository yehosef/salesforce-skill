# Contributing to Salesforce Development Skill

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to this project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Submitting Changes](#submitting-changes)
- [Release Process](#release-process)

## Code of Conduct

This project follows a standard code of conduct:
- Be respectful and inclusive
- Focus on constructive feedback
- Help create a welcoming environment
- Report unacceptable behavior

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/yourusername/salesforce-skill.git
   cd salesforce-skill
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/originalowner/salesforce-skill.git
   ```

## Development Setup

### Prerequisites

Install required tools:
```bash
# Salesforce CLI
npm install -g @salesforce/cli

# Python dependencies
pip install -r requirements.txt

# Code quality tools
pip install pylint black flake8
brew install shellcheck  # or: apt-get install shellcheck

# Pre-commit hooks
pip install pre-commit
pre-commit install
```

### Verify Installation

```bash
./verify-install.sh
```

## How to Contribute

### Types of Contributions

We welcome:
- **Bug fixes** - Fix issues in existing scripts
- **New scripts** - Add automation for common Salesforce tasks
- **Documentation** - Improve guides, add examples, fix typos
- **Reference guides** - Add new error solutions, patterns, best practices
- **Templates** - Add useful Apex/CI/CD templates
- **Tests** - Add unit tests or integration tests

### Before You Start

1. **Check existing issues** - Someone might already be working on it
2. **Create an issue** - Describe what you plan to do
3. **Get feedback** - Wait for maintainer approval before major changes
4. **Create a branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Coding Standards

### Shell Scripts (.sh)

```bash
#!/bin/bash
# Always use shebang

# Enable strict mode
set -euo pipefail

# Add description and usage
# Description: What this script does
# Usage: ./script.sh <arg1> <arg2>

# Document safety level
# Safety: READ-ONLY or DESTRUCTIVE

# Add help flag
if [[ "${1:-}" == "--help" ]]; then
    echo "Usage: $0 <arg1> <arg2>"
    exit 0
fi

# Use meaningful variable names
org_alias="${1}"
metadata_type="${2}"

# Quote all variables
echo "Deploying to: ${org_alias}"

# Check prerequisites
if ! command -v sf &> /dev/null; then
    echo "Error: sf CLI not found" >&2
    exit 1
fi
```

**Style Requirements:**
- Use `shellcheck` to lint all scripts
- Use `set -euo pipefail` for safety
- Quote all variable expansions
- Add `--help` flag to all scripts
- Document parameters and safety level

### Python Scripts (.py)

```python
#!/usr/bin/env python3
"""
Brief description of what the script does.

A more detailed explanation if needed.

Usage:
    ./script.py <arg1> <arg2>
    ./script.py --help

Requirements:
    - Salesforce CLI (sf) v2.x+
    - Python 3.8+
    - Authenticated Salesforce org

Safety: READ-ONLY or DESTRUCTIVE
    Explain what the script modifies or doesn't modify.

Dependencies:
    - List external dependencies
"""

import sys
import argparse
from typing import List, Dict, Any

def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Script description")
    parser.add_argument("arg1", help="First argument")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    # Implementation
    pass

if __name__ == "__main__":
    main()
```

**Style Requirements:**
- Use type hints for all functions
- Add docstrings to all functions and classes
- Use `pylint` and `black` for linting/formatting
- Use `argparse` for command-line arguments
- Add `--help`, `--verbose`, and `--version` flags
- Handle errors gracefully with try/except
- Use logging instead of print for status messages

### Reference Guides (.md)

```markdown
# Guide Title

Brief description of what this guide covers.

## When to Use

Explain when this guide is relevant.

## Quick Reference

Provide a quick lookup table or command list.

## Detailed Explanation

Provide detailed information with examples.

## Common Patterns

Show practical examples and patterns.

## Best Practices

List recommended approaches.

## Common Pitfalls

Warn about common mistakes.

## See Also

Link to related guides.
```

## Testing Guidelines

### Unit Tests

Add tests for all Python scripts:

```python
# tests/test_query_soql.py
import unittest
from unittest.mock import patch, MagicMock
import sys
sys.path.insert(0, '../scripts')
import query_soql

class TestQuerySOQL(unittest.TestCase):
    def test_flatten_record(self):
        record = {"Name": "Test", "Account": {"Name": "Parent"}}
        result = query_soql.flatten_record(record)
        self.assertEqual(result["Account.Name"], "Parent")
```

### Integration Tests

For bash scripts, create integration tests in `tests/integration/`:

```bash
#!/bin/bash
# tests/integration/test_compare_orgs.sh

# Test with mock orgs
source ../scripts/compare_orgs.sh

# Assert expected behavior
[[ $? -eq 0 ]] || exit 1
```

### Test Coverage

- Aim for 80%+ coverage on Python scripts
- Test both success and error paths
- Test with various input combinations
- Mock external sf CLI calls

Run tests:
```bash
# Python tests
python -m pytest tests/

# Shell tests
bats tests/integration/
```

## Submitting Changes

### Pull Request Process

1. **Update your branch**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run tests and linters**:
   ```bash
   ./scripts/run-tests.sh
   pylint scripts/*.py
   shellcheck scripts/*.sh
   ```

3. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat: add new script for org comparison"
   ```

   Use conventional commit format:
   - `feat:` - New feature
   - `fix:` - Bug fix
   - `docs:` - Documentation only
   - `style:` - Code style changes (formatting)
   - `refactor:` - Code refactoring
   - `test:` - Adding tests
   - `chore:` - Maintenance tasks

4. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Create Pull Request** on GitHub:
   - Provide clear title and description
   - Reference related issues
   - Describe testing performed
   - Add screenshots if relevant

### PR Review Process

- Maintainers will review within 3-5 days
- Address feedback in new commits
- Once approved, maintainers will merge

## Release Process

Releases follow semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

Maintainers handle releases:
1. Update CHANGELOG.md
2. Update version in scripts
3. Create git tag
4. Publish release notes

## Questions?

- **Open an issue** for questions
- **Check existing issues** first
- **Be patient** - maintainers are volunteers

## Recognition

Contributors will be:
- Listed in README.md
- Mentioned in release notes
- Credited in commit history

Thank you for contributing! 🎉
