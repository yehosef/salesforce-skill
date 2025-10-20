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

---

## 📦 What's Included

### Automation Scripts (6)
- `query_soql.py` - Execute SOQL and format results as markdown table
- `deploy_and_test.sh` - Automated deploy-with-tests workflow
- `run_tests.py` - Run Apex tests with formatted results
- `retrieve_metadata.sh` - Bulk metadata retrieval
- `compare_orgs.sh` - Compare metadata between two orgs
- `seed_scratch_org.sh` - Seed scratch org with test data (SFDMU)

### Reference Guides (7)
- `sf-cli-reference.md` - Complete sf command reference
- `soql-patterns.md` - SOQL optimization patterns
- `deployment-guide.md` - Deployment best practices
- `testing-guide.md` - Apex testing strategies
- `governor-limits.md` - Salesforce limits reference
- `metadata-types.md` - Common metadata types
- `common-errors.md` - Top 50+ errors with solutions

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
   git clone https://github.com/yourusername/salesforce-skill.git
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
   Just ask Claude Code Salesforce-related questions and the skill will automatically activate!

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

## 📊 Productivity Impact

**Estimated Time Savings per Developer per Week:**
- Error troubleshooting: 3-4 hours
- Org comparison: 2-3 hours
- Scratch org setup: 1-2 hours
- CI/CD automation: 5-10 hours (one-time)

**Total: 6-9 hours/week = 15-23% productivity increase**

---

## 🎯 Common Use Cases

### 1. Troubleshooting Deployment Errors
Ask Claude Code:
> "I'm getting UNABLE_TO_LOCK_ROW error during deployment"

Claude will reference the common-errors guide and provide specific solutions.

### 2. Optimizing SOQL Queries
Ask Claude Code:
> "How can I optimize this SOQL query to avoid governor limits?"

Claude will reference soql-patterns and provide bulkification examples.

### 3. Setting Up CI/CD
Ask Claude Code:
> "Help me set up automated deployments with GitHub Actions"

Claude will guide you through using the CI/CD templates.

### 4. Comparing Environments
Ask Claude Code:
> "What's different between my sandbox and production?"

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

### Phase 2 Enhancements (Planned)
- Performance profiling tools
- Rollback automation
- Org health check scripts
- Data migration utilities

### Phase 3 Enhancements (Planned)
- Dependency analyzer
- Security scanner
- Unused metadata finder
- Code quality metrics

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

### v1.1.0 (Current)
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
