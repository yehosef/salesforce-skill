# Frequently Asked Questions (FAQ)

Common questions about the Salesforce Development Skill for Claude Code.

## General Questions

### What is this skill?

This is a comprehensive toolkit for Salesforce development that integrates with Claude Code. It provides automation scripts, reference guides, and templates to streamline common Salesforce development tasks like deployment, testing, SOQL queries, and org management.

### Do I need Salesforce knowledge to use this skill?

Yes, basic Salesforce knowledge is recommended. This skill is designed to accelerate Salesforce development, not teach Salesforce fundamentals. If you're new to Salesforce, check out [Trailhead](https://trailhead.salesforce.com) for free learning resources.

### How is this different from the Salesforce CLI?

This skill builds **on top** of the Salesforce CLI (sf). It provides:
- Automation scripts that combine multiple sf commands
- Formatted output (markdown tables, reports)
- Error handling and retry logic
- Best practices and reference guides
- CI/CD integration templates

You still need the Salesforce CLI installed - this skill just makes it easier to use.

## Installation & Setup

### Where should I install this skill?

Install to `~/.claude/skills/salesforce-dev/` for use with Claude Code. The installation script does this automatically.

### Can I use this without Claude Code?

Yes! All scripts can be run standalone from the command line. Claude Code integration just provides better context and automation.

### Do I need to install Python packages?

No, the core scripts use only Python standard library. Development dependencies (for contributors) are optional.

### Why isn't the sf CLI found?

Make sure you've installed the Salesforce CLI:
```bash
npm install -g @salesforce/cli
sf --version
```

If installed but not found, check your PATH:
```bash
which sf
echo $PATH
```

## Authentication & Orgs

### How do I authenticate to Salesforce?

Use the Salesforce CLI:
```bash
sf org login web -a my-org
```

This opens a browser for authentication and saves the alias "my-org".

### Can I use multiple orgs?

Yes! Authenticate to multiple orgs with different aliases:
```bash
sf org login web -a dev-sandbox
sf org login web -a uat-sandbox
sf org login web -a production
```

Then specify the alias when running scripts:
```bash
./scripts/query_soql.py "SELECT Id FROM Account" dev-sandbox
```

### How do I check which orgs I'm authenticated to?

```bash
sf org list
```

### My authentication expired. What do I do?

Re-authenticate:
```bash
sf org login web -a my-org
```

## Using Scripts

### Which scripts are safe to run?

See [scripts/README.md](scripts/README.md) for a complete safety matrix. Scripts marked "READ-ONLY" are completely safe. Scripts marked "DESTRUCTIVE" should only be run in sandbox/scratch orgs initially.

### How do I run a script?

Make sure scripts are executable:
```bash
chmod +x scripts/*.py scripts/*.sh
```

Then run with required arguments:
```bash
./scripts/query_soql.py "SELECT Id FROM Account LIMIT 5" my-org
```

### Can I run scripts from anywhere?

If you added the scripts directory to your PATH during installation, yes:
```bash
query_soql.py "SELECT Id FROM Account" my-org
```

Otherwise, use the full path or `cd` to the scripts directory first.

### Why do I get "permission denied"?

Scripts need execute permissions:
```bash
chmod +x scripts/*.py scripts/*.sh
```

## Deployment & Testing

### How do I deploy code to production?

**NEVER deploy directly to production without testing!**

Recommended workflow:
1. Create a snapshot: `./scripts/snapshot_org.sh production ./backups/pre-deploy`
2. Compare environments: `./scripts/compare_orgs.sh sandbox production`
3. Deploy to sandbox first: `./scripts/deploy_and_test.sh src/ sandbox`
4. If successful, deploy to production: `./scripts/deploy_and_test.sh src/ production`

### What test level should I use?

- **Sandbox**: `NoTestRun` or `RunLocalTests` (faster)
- **Production**: `RunLocalTests` (required by Salesforce)

### My deployment failed. Now what?

1. Check the error message in the output
2. Search for the error in [references/common-errors.md](references/common-errors.md)
3. If you have a snapshot, rollback: `./scripts/rollback_deployment.sh org ./backups/snapshot`

### How do I rollback a deployment?

If you created a snapshot before deployment:
```bash
./scripts/rollback_deployment.sh my-org ./backups/pre-deploy-snapshot
```

This deploys the old version back to the org.

## SOQL Queries

### My query returns "No results found" but I know there's data

Check:
1. Are you querying the right org?
2. Do you have field-level security access to those fields?
3. Are you filtering too strictly (check WHERE clause)?

### How do I query more than 2000 records?

Use the bulk export functionality:
```bash
sf data export bulk -q "SELECT Id, Name FROM Account" -o my-org
```

### Can I save query results to a file?

Yes, redirect the output:
```bash
./scripts/query_soql.py "SELECT Id FROM Account" my-org > results.md
```

Or use the export script for CSV:
```bash
./scripts/export_data.py "Account" my-org ./exports/
```

## Org Comparison

### How accurate is the org comparison?

The comparison retrieves metadata from both orgs and compares them. It's very accurate for detecting differences, but:
- Only compares metadata types you specify (or defaults)
- Doesn't compare data records
- May show false positives if formatting differs

### Can I compare more than 2 orgs?

Not directly, but you can run multiple comparisons:
```bash
./scripts/compare_orgs.sh org1 org2
./scripts/compare_orgs.sh org1 org3
./scripts/compare_orgs.sh org2 org3
```

### Where are comparison reports stored?

Reports are saved to `~/.claude/reports/org-comparison/runs/<timestamp>/` if using the report version:
```bash
./scripts/compare_orgs_and_report.sh sandbox production
```

## Performance & Optimization

### How do I find slow queries?

Use the profiling tools:
```bash
# Profile a specific query
./scripts/profile_soql.py "SELECT Id FROM Account" my-org

# Scan debug logs for slow queries
./scripts/find_slow_queries.sh ./logs 1000
```

### What's the governor limits threshold?

Check [references/governor-limits.md](references/governor-limits.md) for all limits. Key ones:
- SOQL queries: 100 synchronous, 200 asynchronous
- DML statements: 150
- Heap size: 6MB synchronous, 12MB asynchronous
- CPU time: 10 seconds synchronous, 60 seconds asynchronous

### How do I optimize my Apex code?

See [references/performance-tuning.md](references/performance-tuning.md) for detailed strategies:
- Bulkify triggers
- Move SOQL outside loops
- Use Maps for lookups
- Minimize DML operations

## Troubleshooting

### I'm getting "UNABLE_TO_LOCK_ROW" errors

See [references/common-errors.md](references/common-errors.md) for detailed solutions. Quick fixes:
- Add retry logic with exponential backoff
- Reduce concurrent operations
- Process records in smaller batches

### Scripts are slow. How can I speed them up?

- Use indexed fields in SOQL WHERE clauses
- Limit query results
- Run during off-peak hours
- Check API usage: `./scripts/org_limits_monitor.py my-org`

### The skill isn't working with Claude Code

1. Verify installation: `./verify-install.sh`
2. Check SKILL.md is present in skill directory
3. Restart Claude Code
4. Check Claude Code logs for errors

## Contributing

### How can I contribute?

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines. Quick steps:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### I found a bug. Where do I report it?

Open an issue on GitHub with:
- Description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Your environment (OS, Python version, sf CLI version)

### Can I add my own scripts?

Yes! Follow the structure in `scripts/` and add documentation. Consider contributing back to the project.

## Advanced Usage

### Can I customize the skill for my org?

Yes! Copy `config.example.yaml` to `config.yaml` and customize:
```bash
cp config.example.yaml config.yaml
# Edit config.yaml with your preferences
```

### How do I integrate with CI/CD?

See the templates in `assets/`:
- `salesforce-ci.yml` - GitHub Actions deployment pipeline
- `validate-pr.yml` - PR validation workflow

Copy to `.github/workflows/` in your project.

### Can I use this with other Salesforce tools?

Yes! This skill complements tools like:
- Salesforce VS Code Extensions
- Data Loader
- SFDMU
- Workbench

### How do I extend the skill with custom functionality?

1. Add your script to `scripts/`
2. Follow naming conventions (snake_case for Python, kebab-case for shell)
3. Add documentation header
4. Make executable: `chmod +x your-script.sh`
5. Add to scripts/README.md

## Getting Help

### Where can I get more help?

1. Check the documentation:
   - [README.md](README.md) - Overview and quick start
   - [SKILL.md](SKILL.md) - Complete skill documentation
   - [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues
   - [references/](references/) - Reference guides

2. Check existing issues on GitHub

3. Ask in Salesforce developer communities:
   - [Salesforce Stack Exchange](https://salesforce.stackexchange.com/)
   - [Salesforce Developer Forums](https://developer.salesforce.com/forums)

### How do I report security issues?

Email security issues privately to the maintainers rather than opening public issues. See [CONTRIBUTING.md](CONTRIBUTING.md) for contact information.

## License & Legal

### What license is this under?

MIT License. See [LICENSE](LICENSE) for full text. You're free to use, modify, and distribute.

### Can I use this commercially?

Yes, the MIT license allows commercial use.

### Is this officially supported by Salesforce or Anthropic?

No, this is a community-maintained project. Use at your own risk. Neither Salesforce nor Anthropic provides official support for this skill.
