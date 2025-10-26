# Architecture Overview

This document describes the architecture, design decisions, and internal structure of the Salesforce Development Skill.

## Table of Contents

- [Design Philosophy](#design-philosophy)
- [Directory Structure](#directory-structure)
- [Component Architecture](#component-architecture)
- [Data Flow](#data-flow)
- [Extension Points](#extension-points)
- [Security Considerations](#security-considerations)

---

## Design Philosophy

### Core Principles

1. **Simplicity First**: Use standard library and built-in tools where possible
2. **No Magic**: Explicit behavior, predictable outcomes
3. **Fail Fast**: Clear error messages, early validation
4. **Progressive Enhancement**: Core features work everywhere, advanced features are optional
5. **Documentation as Code**: Self-documenting scripts with embedded help

### Design Decisions

**Why Python + Bash?**
- Python: Cross-platform, standard library is powerful, easy to read
- Bash: Natural fit for CLI orchestration, ubiquitous on Unix systems
- Both: No runtime dependencies beyond what's already installed

**Why not a single binary/package?**
- Individual scripts are easier to understand and modify
- Users can pick and choose which scripts to use
- No build step required
- Direct inspection of what the code does

**Why markdown for reports?**
- Human-readable in terminal and GitHub
- No special viewer required
- Easy to diff and version control
- Claude Code renders it beautifully

---

## Directory Structure

```
salesforce-skill/
├── .github/                  # GitHub-specific files
│   └── workflows/            # CI/CD pipelines (future)
├── .vscode/                  # VS Code integration
│   ├── extensions.json       # Recommended extensions
│   ├── launch.json           # Debug configurations
│   ├── settings.json         # Editor settings
│   ├── tasks.json            # Task runner configs
│   └── *.code-snippets       # Code snippets
├── assets/                   # Templates and static resources
│   ├── apex-test-template.cls
│   ├── package-xml-template.xml
│   ├── salesforce-ci.yml
│   └── validate-pr.yml
├── examples/                 # Usage examples and samples
│   ├── apex/                 # Sample Apex code
│   ├── outputs/              # Example script outputs
│   ├── scripts/              # Workflow examples
│   └── soql/                 # Sample SOQL queries
├── lib/                      # Shared libraries
│   └── report-manager.sh     # Report framework
├── references/               # Reference documentation
│   ├── common-errors.md
│   ├── deployment-guide.md
│   ├── governor-limits.md
│   ├── metadata-types.md
│   ├── performance-tuning.md
│   ├── sf-cli-reference.md
│   ├── soql-patterns.md
│   └── testing-guide.md
├── scripts/                  # Automation scripts
│   ├── *.py                  # Python scripts
│   ├── *.sh                  # Bash scripts
│   └── README.md             # Script documentation
├── tests/                    # Test suite
│   ├── fixtures/             # Test data
│   ├── integration/          # Integration tests
│   ├── unit/                 # Unit tests
│   └── run-all-tests.sh      # Test runner
├── .editorconfig             # Editor configuration
├── .gitignore                # Git ignore rules
├── .pre-commit-config.yaml   # Pre-commit hooks
├── .pylintrc                 # Python linting config
├── .shellcheckrc             # Shell linting config
├── ARCHITECTURE.md           # This file
├── CHANGELOG.md              # Version history
├── CONTRIBUTING.md           # Contribution guide
├── FAQ.md                    # Frequently asked questions
├── LICENSE                   # MIT License
├── README.md                 # Project overview
├── SKILL.md                  # Skill documentation (Claude Code)
├── TROUBLESHOOTING.md        # Troubleshooting guide
├── config.example.yaml       # Configuration template
├── install.sh                # Installation script
├── package.json              # npm dependencies
├── pyproject.toml            # Python project config
├── requirements.txt          # Python dependencies (empty)
├── requirements-dev.txt      # Dev dependencies
├── uninstall.sh              # Uninstallation script
└── verify-install.sh         # Installation verification
```

---

## Component Architecture

### Layer Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    User Interface                        │
│  (Claude Code, CLI, VS Code Tasks, CI/CD)               │
└───────────────────┬─────────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────────┐
│                 Script Layer                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ Python   │  │ Bash     │  │ Report   │             │
│  │ Scripts  │  │ Scripts  │  │ Manager  │             │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘             │
│       │             │              │                     │
└───────┼─────────────┼──────────────┼─────────────────────┘
        │             │              │
┌───────▼─────────────▼──────────────▼─────────────────────┐
│              Salesforce CLI (sf)                          │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐                 │
│  │  org    │  │  data   │  │ project │                 │
│  │ commands│  │ commands│  │ commands│                 │
│  └────┬────┘  └────┬────┘  └────┬────┘                 │
└───────┼───────────┼──────────────┼───────────────────────┘
        │           │              │
┌───────▼───────────▼──────────────▼───────────────────────┐
│              Salesforce Platform                          │
│  (Production, Sandboxes, Scratch Orgs)                   │
└───────────────────────────────────────────────────────────┘
```

### Script Categories

**Query & Analysis** (Read-Only)
- `query_soql.py` - Execute and format SOQL queries
- `profile_soql.py` - Analyze query performance
- `org_health_check.py` - Comprehensive org health
- `org_limits_monitor.py` - Monitor API/storage limits
- `find_duplicates.py` - Detect duplicate records
- `analyze_apex_performance.py` - Parse debug logs

**Deployment & Testing** (Destructive)
- `deploy_and_test.sh` - Deploy with automatic testing
- `run_tests.py` - Execute Apex tests
- `snapshot_org.sh` - Create metadata snapshots
- `rollback_deployment.sh` - Rollback to snapshot

**Data Management** (Destructive)
- `export_data.py` - Export data with relationships
- `emergency_rollback.py` - Restore data from backup
- `seed_scratch_org.sh` - Populate scratch orgs

**Comparison & Reporting** (Read-Only)
- `compare_orgs.sh` - Interactive org comparison
- `compare_orgs_and_report.sh` - Comparison with reports
- `view-latest-report.sh` - View recent reports
- `list-reports.sh` - List all reports
- `compare-reports.sh` - Compare report runs

**Utilities**
- `retrieve_metadata.sh` - Bulk metadata retrieval
- `find_slow_queries.sh` - Scan logs for slow queries

### Shared Libraries

**report-manager.sh**
Standardized framework for report generation:
- Creates timestamped run directories
- Manages report metadata (JSON)
- Maintains "latest" symlinks
- Provides consistent structure

Used by:
- `compare_orgs_and_report.sh`
- (Future scripts that generate reports)

---

## Data Flow

### SOQL Query Flow

```
User Input → query_soql.py → sf data query → Salesforce API
                    ↓
            JSON Response ← Salesforce API
                    ↓
            Parse & Flatten
                    ↓
            Format as Markdown Table
                    ↓
            Output to Terminal
```

### Deployment Flow

```
User Input → deploy_and_test.sh
                    ↓
        ┌───────────┴───────────┐
        ↓                       ↓
   Validate Files         Show Preview
        ↓                       ↓
   User Confirms          Deploy Start
        ↓                       ↓
   sf project deploy start     │
        ↓                       │
   Wait for Completion         │
        ↓                       │
   Run Tests ←──────────────────┘
        ↓
   Display Results
```

### Org Comparison Flow

```
compare_orgs_and_report.sh
        ↓
┌───────┴────────┐
│ Initialize     │
│ Report Manager │
└───────┬────────┘
        ↓
┌───────┴────────────────┐
│ Retrieve Metadata      │
│ from Both Orgs         │
├─────────┬──────────────┤
│ Source  │   Target     │
└─────────┴──────────────┘
        ↓
┌───────┴────────┐
│ Compare Files  │
│ Generate Diffs │
└───────┬────────┘
        ↓
┌───────┴────────┐
│ Generate Report│
│ - Markdown     │
│ - Metadata     │
│ - Diffs        │
└───────┬────────┘
        ↓
┌───────┴────────┐
│ Save to        │
│ .claude/reports│
└────────────────┘
```

### Report Management Flow

```
Scripts with Reporting
        ↓
source lib/report-manager.sh
        ↓
report_init "tool-name"
        ↓
┌───────┴────────┐
│ Create Run Dir │
│ .claude/reports│
│ /tool-name/    │
│ runs/          │
│ YYYY-MM-DD-HHMM│
└───────┬────────┘
        ↓
report_save_artifact "file" "data"
report_save_metadata "key" "value"
        ↓
report_finalize
        ↓
┌───────┴────────┐
│ Write:         │
│ - report.md    │
│ - metadata.json│
│ - artifacts/   │
│ Update latest→ │
└────────────────┘
```

---

## Extension Points

### Adding a New Script

**Python Script Template**:
```python
#!/usr/bin/env python3
"""
Script description.

Usage:
    ./script.py <args>

Requirements:
    - Salesforce CLI
    - Python 3.8+

Safety: READ-ONLY or DESTRUCTIVE
"""
import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description="...")
    parser.add_argument("arg1")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    # Implementation

if __name__ == "__main__":
    main()
```

**Bash Script Template**:
```bash
#!/bin/bash
# Script description
#
# Usage: ./script.sh <arg1> <arg2>

set -euo pipefail

if [[ "${1:-}" == "--help" ]]; then
    echo "Usage: $0 <arg1> <arg2>"
    exit 0
fi

# Implementation
```

### Adding Report Support

Use the report manager framework:

```bash
#!/bin/bash
source "$(dirname "$0")/../lib/report-manager.sh"

# Initialize
REPORT_ID=$(report_init "my-tool")

# Save artifacts
report_save_artifact "results.txt" "$results"

# Save metadata
report_save_metadata "run_date" "$(date)"
report_save_metadata "status" "success"

# Finalize
report_finalize "$REPORT_ID" "Summary message"
```

### Custom Hooks

Config file supports hooks (future enhancement):

```yaml
hooks:
  pre_deploy: ./hooks/notify-team.sh
  post_deploy: ./hooks/update-dashboard.sh
  on_error: ./hooks/send-alert.sh
```

---

## Security Considerations

### Credential Management

**What we do**:
- Never store credentials in code
- Rely on sf CLI authentication
- Add `.env`, `*.pem`, `*-auth-url.txt` to `.gitignore`
- Use secrets detection in pre-commit hooks

**What users should do**:
- Use JWT auth for CI/CD (not username/password)
- Rotate credentials regularly
- Use separate auth for each environment
- Never commit auth files

### Input Validation

**SOQL Injection Prevention**:
Scripts don't construct SOQL with user input - they pass queries directly to sf CLI which handles sanitization.

**Path Traversal Prevention**:
```python
# Validate paths are within expected directories
import os
path = os.path.abspath(user_input)
if not path.startswith(SAFE_BASE_DIR):
    raise ValueError("Invalid path")
```

**Command Injection Prevention**:
Python scripts use `subprocess.run()` with list arguments (not shell=True):
```python
# GOOD
subprocess.run(["sf", "data", "query", "-q", query])

# BAD (vulnerable)
subprocess.run(f"sf data query -q '{query}'", shell=True)
```

### Destructive Operations

Scripts that modify data/code:
1. Are clearly marked as DESTRUCTIVE
2. Require explicit confirmation
3. Create backups when possible
4. Log all actions

### API Rate Limiting

Monitor limits:
```bash
./scripts/org_limits_monitor.py my-org --alert-threshold 80
```

Scripts respect limits by:
- Using bulk operations when available
- Adding delays between operations
- Checking limits before batch operations

---

## Performance Optimization

### Caching Strategy

Currently minimal caching (design decision):
- sf CLI handles its own caching
- Reports are cached on disk
- No in-memory caching (stateless scripts)

Future enhancement: Config option for result caching.

### Bulk Operations

Preferred patterns:
```bash
# GOOD: Single bulk export
sf data export bulk -q "SELECT..." -o org

# BAD: Multiple individual queries
for id in $(cat ids.txt); do
    sf data query -q "SELECT * FROM Account WHERE Id='$id'"
done
```

### Parallel Execution

Scripts are stateless and can be run in parallel:
```bash
# Compare multiple orgs simultaneously
./scripts/compare_orgs.sh dev prod &
./scripts/compare_orgs.sh staging prod &
wait
```

---

## Testing Strategy

### Test Pyramid

```
        ┌───────────┐
        │    E2E    │  ← Integration tests (with real SF org)
        └───────────┘
       ┌─────────────┐
       │ Integration │  ← Script execution tests
       └─────────────┘
      ┌───────────────┐
      │  Unit Tests   │  ← Function-level tests
      └───────────────┘
```

### Test Coverage Goals

- Unit tests: 80%+ coverage for Python functions
- Integration tests: All scripts executable
- E2E tests: Critical workflows (deploy, query, compare)

### CI/CD Testing

GitHub Actions workflow (future):
1. Lint all scripts (shellcheck, pylint)
2. Run unit tests
3. Run integration tests (no SF org needed)
4. Run E2E tests (against scratch org)

---

## Future Architecture Plans

### Phase 3 Enhancements

**Dependency Analyzer**:
```
scripts/analyze_dependencies.py
- Parse metadata relationships
- Generate dependency graph (DOT format)
- Detect circular dependencies
```

**Security Scanner**:
```
scripts/security_scan.py
- SOQL injection detection
- FLS/CRUD checks
- Hardcoded credential detection
- Overly permissive sharing rules
```

**Unused Metadata Finder**:
```
scripts/find_unused_metadata.py
- Identify unused Apex classes
- Find unreferenced fields
- Detect orphaned workflows
```

### Plugin System

Allow community extensions:
```
~/.claude/skills/salesforce-dev/plugins/
├── my-custom-script.py
└── plugin-manifest.yaml
```

---

## Contributing to Architecture

When proposing architectural changes:

1. **Open an issue** describing the problem and proposed solution
2. **Discuss alternatives** and trade-offs
3. **Update this document** with design decisions
4. **Add tests** for new components
5. **Document** in relevant guides

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## Questions?

Architecture questions? Open an issue with the `architecture` label.
