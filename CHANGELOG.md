# Changelog

All notable changes to the Salesforce Development Skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Installation automation scripts (install.sh, verify-install.sh, uninstall.sh)
- Comprehensive testing infrastructure with unit tests
- Code quality tools (.pylintrc, .shellcheckrc, pre-commit hooks)
- Examples directory with sample data and outputs
- VS Code integration (snippets, tasks, launch configurations)
- Configuration management (config.example.yaml)
- Enhanced documentation (FAQ.md, TROUBLESHOOTING.md, ARCHITECTURE.md)
- GitHub Actions CI/CD for testing the skill
- Standardized CLI options (--help, --verbose, --version) across all scripts
- .gitignore for better credential protection
- LICENSE file (MIT)
- CONTRIBUTING.md with contribution guidelines

### Changed
- Enhanced all Python scripts with better error handling and logging
- Improved bash scripts with `set -euo pipefail` for safety
- Standardized script output formatting with color coding

## [2.0.0] - 2025-10-26

### Added
- **Data Migration & Duplicates**: export_data.py, find_duplicates.py
- **Performance Profiling**: profile_soql.py, analyze_apex_performance.py, find_slow_queries.sh
- **Rollback & Recovery**: snapshot_org.sh, rollback_deployment.sh, emergency_rollback.py
- **Org Health Monitoring**: org_health_check.py, org_limits_monitor.py
- **Report Management**: compare_orgs_and_report.sh with persistent timestamped reports
- **Report Tools**: view-latest-report.sh, list-reports.sh, compare-reports.sh
- **Library**: report-manager.sh standardized framework
- Reference guides: data-migration-guide.md, duplicate-detection.md, performance-tuning.md, rollback-procedures.md
- Enhanced SKILL.md with 4 new capability sections (9-12)
- Comprehensive scripts/README.md with safety levels and requirements matrix

### Security
- Fixed shell=True vulnerabilities in Python scripts
- Enhanced input validation across all scripts
- Added safety confirmations for destructive operations

## [1.1.0] - 2025-10-19

### Added
- Error troubleshooting guide (50+ common errors) in common-errors.md
- Org comparison script (compare_orgs.sh)
- Scratch org data seeding with SFDMU (seed_scratch_org.sh)
- GitHub Actions CI/CD templates (salesforce-ci.yml, validate-pr.yml)
- Enhanced SKILL.md with 3 new capabilities (6-8)

## [1.0.0] - 2025-10-15

### Added
- Initial release with core automation scripts
- SOQL query execution (query_soql.py)
- Automated deployment workflow (deploy_and_test.sh)
- Apex testing automation (run_tests.py)
- Metadata retrieval (retrieve_metadata.sh)
- Reference guides: sf-cli-reference.md, soql-patterns.md, deployment-guide.md, testing-guide.md, governor-limits.md, metadata-types.md
- Templates: apex-test-template.cls, package-xml-template.xml
- Comprehensive SKILL.md documentation
- README.md with usage examples

[Unreleased]: https://github.com/yourusername/salesforce-skill/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/yourusername/salesforce-skill/compare/v1.1.0...v2.0.0
[1.1.0]: https://github.com/yourusername/salesforce-skill/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/yourusername/salesforce-skill/releases/tag/v1.0.0
