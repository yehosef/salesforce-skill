# Salesforce Development Skill for Claude Code

A comprehensive Claude Code skill that supercharges Salesforce development with automation, error troubleshooting, and CI/CD integration.

## 🚀 Features

### Core Capabilities

1. **Deployment & Retrieval** - Automated deployment workflows with preview and validation
2. **SOQL Query Execution** - Execute and format SOQL queries with markdown tables
3. **Apex Testing** - Run tests with detailed coverage reports and failure analysis
4. **Schema Exploration** - Navigate objects, fields, and relationships
5. **Command Reference** - Complete sf CLI command reference
6. **Error Troubleshooting** - 50+ common errors with instant solutions
7. **Org Comparison** - Compare metadata between environments
8. **CI/CD Integration** - Ready-to-use GitHub Actions workflows
9. **Data Migration & Duplicates** - SFDMU automation, duplicate detection, data export
10. **Performance Profiling** - SOQL profiling, Apex performance analysis, slow query detection
11. **Rollback & Recovery** - Metadata snapshots, deployment rollback, emergency data restoration
12. **Org Health Monitoring** - Comprehensive health checks, API limit monitoring

---

## 📦 What's Included

### Automation Scripts (17)

**Core Automation:**
- `query_soql.py` - Execute SOQL and format results as markdown table
- `deploy_and_test.sh` - Automated deploy-with-tests workflow
- `run_tests.py` - Run Apex tests with formatted results
- `retrieve_metadata.sh` - Bulk metadata retrieval

**Environment Management:**
- `compare_orgs.sh` - Compare metadata between two orgs
- `seed_scratch_org.sh` - Seed scratch org with test data (SFDMU)

**Data & Migration (Phase 2):**
- `export_data.py` - Export data with relationships to CSV
- `find_duplicates.py` - Find duplicate records with merge recommendations

**Performance (Phase 2):**
- `profile_soql.py` - Analyze SOQL query performance
- `analyze_apex_performance.py` - Parse debug logs for bottlenecks
- `find_slow_queries.sh` - Identify slow queries in logs

**Rollback & Recovery (Phase 2):**
- `snapshot_org.sh` - Create metadata snapshot
- `rollback_deployment.sh` - Rollback to previous snapshot
- `emergency_rollback.py` - Quick data restoration

**Monitoring (Phase 2):**
- `org_health_check.py` - Comprehensive org health analysis
- `org_limits_monitor.py` - Monitor API limits and usage

### Reference Guides (11)
- `sf-cli-reference.md` - Complete sf command reference
- `soql-patterns.md` - SOQL optimization patterns
- `deployment-guide.md` - Deployment best practices
- `testing-guide.md` - Apex testing strategies
- `governor-limits.md` - Salesforce limits reference
- `metadata-types.md` - Common metadata types
- `common-errors.md` - Top 50+ errors with solutions
- `data-migration-guide.md` - **Phase 2** SFDMU, Data Loader, external IDs
- `duplicate-detection.md` - **Phase 2** Matching rules, fuzzy matching
- `performance-tuning.md` - **Phase 2** SOQL/Apex optimization
- `rollback-procedures.md` - **Phase 2** Disaster recovery strategies

### Templates (4)
- `apex-test-template.cls` - Comprehensive test class template
- `package-xml-template.xml` - Package.xml for metadata retrieval
- `salesforce-ci.yml` - GitHub Actions CI/CD pipeline
- `validate-pr.yml` - GitHub Actions PR validation

---

## 🛠️ Installation

### For Claude Code

1. **Download the skill:**
   ```bash
   git clone https://github.com/yehosef/salesforce-skill.git
   ```

2. **Install to Claude Code:**
   ```bash
   cp -r salesforce-skill ~/.claude/skills/salesforce-dev
   ```

3. **Verify installation:**
   ```bash
   ls ~/.claude/skills/salesforce-dev
   ```

4. **Use the skill:**
   Just ask Claude Code Salesforce-related questions and the skill will automatically activate!  Sometimes it's necessary to call it explicity.

---

## 💡 Usage Examples

### Deploying Code
```bash
# Automated deployment with tests
~/.claude/skills/salesforce-dev/scripts/deploy_and_test.sh src/aura/MyComponent/ sandbox
```

### Running SOQL Queries
```bash
# Format query results as markdown table
~/.claude/skills/salesforce-dev/scripts/query_soql.py "SELECT Id, Name FROM Account LIMIT 5" sandbox
```

### Comparing Orgs
```bash
# See what's different between sandbox and production
~/.claude/skills/salesforce-dev/scripts/compare_orgs.sh sandbox production
```

### Seeding Scratch Orgs
```bash
# Install SFDMU first: sf plugins install sfdmu
~/.claude/skills/salesforce-dev/scripts/seed_scratch_org.sh dev-sandbox my-scratch
```

### Setting Up CI/CD
```bash
# Copy GitHub Actions workflows to your project
cp ~/.claude/skills/salesforce-dev/assets/salesforce-ci.yml .github/workflows/
cp ~/.claude/skills/salesforce-dev/assets/validate-pr.yml .github/workflows/
```

---

## 🎯 Common Use Cases

### 1. Troubleshooting Deployment Errors
Ask Claude Code:
> "I'm getting UNABLE_TO_LOCK_ROW error during salesforce deployment"

Claude will reference the common-errors guide and provide specific solutions.

### 2. Optimizing SOQL Queries
Ask Claude Code:
> "How can I optimize this SOQL query to avoid governor limits?"

Claude will reference soql-patterns and provide bulkification examples.

### 3. Setting Up CI/CD
Ask Claude Code:
> "Help me set up automated salesforce deployments with GitHub Actions"

Claude will guide you through using the CI/CD templates.

### 4. Comparing Environments
Ask Claude Code:
> "What's different between my sandbox and production salesforce instances?"

Claude will run the compare_orgs script and show you the differences.

---

## 🔧 Prerequisites

- **Salesforce CLI**: `npm install -g @salesforce/cli`
- **Python 3**: For scripts (usually pre-installed on Mac/Linux)
- **SFDMU** (optional, for data seeding): `sf plugins install sfdmu`
- **GitHub CLI** (optional, for PR automation): `brew install gh`

---

## 📚 Documentation

### Quick Start Guide
1. Deploy a component: `deploy_and_test.sh <path> <org>`
2. Run SOQL query: `query_soql.py "<SOQL>" <org>`
3. Compare orgs: `compare_orgs.sh <source> <target>`
4. Run tests: `run_tests.py <ClassName> <org>`

### Error Reference
See `references/common-errors.md` for comprehensive error solutions including:
- INVALID_CROSS_REFERENCE_KEY
- UNABLE_TO_LOCK_ROW
- TOO_MANY_SOQL_QUERIES
- FIELD_CUSTOM_VALIDATION_EXCEPTION
- INSUFFICIENT_ACCESS
- And 45+ more!

### SOQL Patterns
See `references/soql-patterns.md` for:
- Basic queries
- Relationship queries (parent-to-child, child-to-parent)
- Aggregation functions
- Governor limit optimization
- Query performance tuning

### Deployment Guide
See `references/deployment-guide.md` for:
- Pre-deployment checklist
- Deployment scenarios
- Error handling
- Rollback procedures
- Best practices

---

## 🤝 Contributing

Contributions are welcome! This skill is designed to be extended with additional automation and reference materials.

### Phase 2 Enhancements (✅ COMPLETED)
- ✅ Performance profiling tools (profile_soql.py, analyze_apex_performance.py, find_slow_queries.sh)
- ✅ Rollback automation (snapshot_org.sh, rollback_deployment.sh, emergency_rollback.py)
- ✅ Org health check scripts (org_health_check.py, org_limits_monitor.py)
- ✅ Data migration utilities (export_data.py, find_duplicates.py)
- ✅ Comprehensive reference guides (data-migration-guide.md, duplicate-detection.md, performance-tuning.md, rollback-procedures.md)

### Phase 3 Enhancements (Planned)
- Dependency analyzer (visualize component dependencies)
- Security scanner (identify security vulnerabilities)
- Unused metadata finder (identify and remove unused code)
- Code quality metrics (complexity analysis, maintainability scores)

---

## 📝 License

MIT License - Feel free to use and modify for your needs.

---

## 🙏 Acknowledgments

Built for use with [Claude Code](https://claude.ai/code) by Anthropic.

Inspired by common pain points in Salesforce development:
- Repetitive deployment tasks
- Time-consuming error diagnosis
- Manual org comparisons
- Lack of CI/CD automation
- Scratch org data seeding challenges

---

## 📞 Support

For issues or questions:
1. Check the reference guides in `references/`
2. Review common errors in `common-errors.md`
3. Open an issue on GitHub

---

## 🔄 Version History

### v2.0.0 (Current) - Phase 2 Complete
- ✅ **Data Migration & Duplicates**: export_data.py, find_duplicates.py, data-migration-guide.md, duplicate-detection.md
- ✅ **Performance Profiling**: profile_soql.py, analyze_apex_performance.py, find_slow_queries.sh, performance-tuning.md
- ✅ **Rollback & Recovery**: snapshot_org.sh, rollback_deployment.sh, emergency_rollback.py, rollback-procedures.md
- ✅ **Org Health Monitoring**: org_health_check.py, org_limits_monitor.py
- ✅ Enhanced SKILL.md with 4 new capability sections (9-12)
- ✅ 17 total scripts (+11 from v1.1.0)
- ✅ 11 reference guides (+4 from v1.1.0)

### v1.1.0 (Phase 1)
- ✅ Added error troubleshooting guide (50+ errors)
- ✅ Added org comparison script
- ✅ Added scratch org data seeding (SFDMU)
- ✅ Added GitHub Actions CI/CD templates
- ✅ Enhanced SKILL.md with 3 new capabilities

### v1.0.0 (Initial Release)
- Core deployment automation
- SOQL query execution
- Apex testing
- Reference guides (6)
- Basic scripts (4)

---

## 🌟 Star This Repo!

If this skill saves you time, please give it a star ⭐ on GitHub!

---

**Happy Salesforce Development! 🚀**
