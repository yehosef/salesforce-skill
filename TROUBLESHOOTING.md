# Troubleshooting Guide

Solutions for common issues when using the Salesforce Development Skill.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Authentication Problems](#authentication-problems)
- [Script Execution Errors](#script-execution-errors)
- [Deployment Failures](#deployment-failures)
- [Query Issues](#query-issues)
- [Performance Problems](#performance-problems)
- [Integration Issues](#integration-issues)

---

## Installation Issues

### sf CLI not found

**Symptom**: `command not found: sf` or `sf: command not found`

**Solution**:
```bash
# Install Salesforce CLI
npm install -g @salesforce/cli

# Verify installation
sf --version

# If still not found, check PATH
which sf
echo $PATH
```

If installed but not in PATH, add to your shell profile:
```bash
# For bash
echo 'export PATH="$PATH:$(npm config get prefix)/bin"' >> ~/.bashrc
source ~/.bashrc

# For zsh
echo 'export PATH="$PATH:$(npm config get prefix)/bin"' >> ~/.zshrc
source ~/.zshrc
```

### Python version too old

**Symptom**: `SyntaxError` or `f-string` errors

**Solution**:
Python 3.8+ is required. Check version:
```bash
python3 --version
```

Install/upgrade Python:
- **Mac**: `brew install python@3.11`
- **Ubuntu/Debian**: `sudo apt-get install python3.11`
- **Windows**: Download from [python.org](https://www.python.org/downloads/)

### Scripts not executable

**Symptom**: `Permission denied` when running scripts

**Solution**:
```bash
chmod +x scripts/*.py scripts/*.sh lib/*.sh
```

Or run installation script:
```bash
./install.sh
```

### Missing jq command

**Symptom**: `jq: command not found` when using report scripts

**Solution**:
```bash
# Mac
brew install jq

# Ubuntu/Debian
sudo apt-get install jq

# Windows (via Chocolatey)
choco install jq
```

---

## Authentication Problems

### Session expired

**Symptom**: `ERROR: This org appears to have a problem. Try refreshing your org connection`

**Solution**:
Re-authenticate:
```bash
sf org login web -a my-org
```

Or use JWT authentication for CI/CD:
```bash
sf org login jwt --client-id CLIENT_ID --jwt-key-file server.key --username user@example.com
```

### Wrong org selected

**Symptom**: Scripts run against wrong org or use default org

**Solution**:
1. Always specify org explicitly:
   ```bash
   ./scripts/query_soql.py "SELECT Id FROM Account" my-org
   ```

2. Check current default:
   ```bash
   sf config get target-org
   ```

3. Set default if needed:
   ```bash
   sf config set target-org=my-org
   ```

### Multiple orgs with same alias

**Symptom**: Unexpected behavior when switching between orgs

**Solution**:
List all authenticated orgs:
```bash
sf org list
```

Remove old/duplicate aliases:
```bash
sf org logout -o my-org
```

Re-authenticate with unique aliases:
```bash
sf org login web -a dev-sandbox
sf org login web -a prod
```

---

## Script Execution Errors

### Import errors in Python scripts

**Symptom**: `ModuleNotFoundError` or `ImportError`

**Solution**:
Scripts use only standard library. If you see import errors:

1. Check Python version (must be 3.8+)
2. Run from skill root directory or use full path
3. Verify script hasn't been modified

### Bash script syntax errors

**Symptom**: `syntax error near unexpected token` or `bad substitution`

**Solution**:
1. Ensure you're using bash (not sh):
   ```bash
   bash ./scripts/script-name.sh
   ```

2. Check file line endings (must be LF, not CRLF):
   ```bash
   dos2unix scripts/*.sh  # If dos2unix is available
   ```

3. Run shellcheck for detailed errors:
   ```bash
   shellcheck scripts/*.sh
   ```

### "No such file or directory" for scripts

**Symptom**: Script can't find referenced files

**Solution**:
1. Run scripts from skill root directory:
   ```bash
   cd ~/.claude/skills/salesforce-dev
   ./scripts/query_soql.py "..." my-org
   ```

2. Or use absolute paths:
   ```bash
   ~/.claude/skills/salesforce-dev/scripts/query_soql.py "..." my-org
   ```

---

## Deployment Failures

### INVALID_CROSS_REFERENCE_KEY

**Symptom**: `invalid cross reference id` during deployment

**Solution**:
Deploy dependencies first. See [references/common-errors.md](references/common-errors.md) for detailed solutions.

Quick fix:
```bash
# Deploy parent objects first
./scripts/deploy_and_test.sh src/objects/Parent__c my-org

# Then deploy children
./scripts/deploy_and_test.sh src/objects/Child__c my-org
```

### Test failures blocking deployment

**Symptom**: `CANNOT_INSERT_UPDATE_ACTIVATE_ENTITY` due to test failures

**Solution**:
1. Check which tests are failing:
   ```bash
   sf project deploy report
   ```

2. Run specific failing test:
   ```bash
   ./scripts/run_tests.py FailingTestClass my-org
   ```

3. Fix test or code issues

4. Re-deploy:
   ```bash
   ./scripts/deploy_and_test.sh src/ my-org
   ```

### Insufficient code coverage

**Symptom**: `INSUFFICIENT_CODE_COVERAGE` error (production)

**Solution**:
Production requires 75% code coverage. Check current coverage:
```bash
./scripts/org_health_check.py production
```

Add more test coverage:
1. Use template: `assets/apex-test-template.cls`
2. Follow guide: `references/testing-guide.md`
3. Aim for 80%+ coverage to have buffer

### Component still in use

**Symptom**: `FIELD_CUSTOM_VALIDATION_EXCEPTION` when deleting

**Solution**:
Find where component is used:
```bash
# Search in codebase
grep -r "ComponentName" src/

# Check dependencies
sf project deploy preview --metadata-dir src/
```

Remove references before deleting component.

---

## Query Issues

### SOQL syntax errors

**Symptom**: `MALFORMED_QUERY` or unexpected query results

**Solution**:
1. Test query in Developer Console first
2. Check for:
   - Missing quotes around strings
   - Invalid field names
   - Incorrect relationship notation
3. See query examples: `examples/soql/`

Common issues:
```soql
-- WRONG: Missing quotes
SELECT Id FROM Account WHERE Name = Acme

-- RIGHT: Quoted string
SELECT Id FROM Account WHERE Name = 'Acme'

-- WRONG: Invalid relationship
SELECT Account__r.Name FROM Contact

-- RIGHT: Correct relationship
SELECT Account.Name FROM Contact
```

### Query returns no results

**Symptom**: "No results found" when you expect data

**Checklist**:
1. Verify org: `sf org display -o my-org`
2. Check field-level security (FLS)
3. Review WHERE clause filters
4. Check object permissions
5. Verify spelling of field/object names

Debug:
```bash
# Check if object exists
sf sobject describe -s Account -o my-org

# Query without WHERE clause
./scripts/query_soql.py "SELECT Id FROM Account LIMIT 1" my-org

# Check FLS
sf data query -q "SELECT Id FROM FieldPermissions WHERE SobjectType='Account'" -o my-org
```

### Query too large / timeout

**Symptom**: Query takes forever or times out

**Solution**:
1. Add LIMIT clause:
   ```sql
   SELECT Id FROM Account LIMIT 100
   ```

2. Use bulk export for large datasets:
   ```bash
   sf data export bulk -q "SELECT Id FROM Account" -o my-org
   ```

3. Profile query performance:
   ```bash
   ./scripts/profile_soql.py "SELECT Id FROM Account" my-org
   ```

---

## Performance Problems

### Scripts running slowly

**Symptoms**: Long execution times, timeouts

**Solutions**:

1. **Check API limits**:
   ```bash
   ./scripts/org_limits_monitor.py my-org
   ```

2. **Reduce query size**:
   ```bash
   # Add LIMIT
   SELECT Id FROM Account WHERE CreatedDate = TODAY LIMIT 100
   ```

3. **Run during off-peak hours**:
   - Avoid 9am-5pm in your org's timezone
   - Weekends usually faster

4. **Use indexed fields in WHERE clauses**:
   ```sql
   -- FAST: Id is indexed
   SELECT Id FROM Account WHERE Id = '001...'

   -- SLOW: Custom field not indexed
   SELECT Id FROM Account WHERE Custom_Field__c = 'value'
   ```

### SOQL queries hitting governor limits

**Symptom**: `TOO_MANY_SOQL_QUERIES` error

**Solution**:
Bulkify your code. See [references/performance-tuning.md](references/performance-tuning.md).

Quick fixes:
- Move SOQL outside loops
- Use Collections to reduce queries
- Batch process records

### Deployment takes too long

**Symptom**: Deployment exceeds timeout

**Solution**:
1. Increase timeout:
   ```bash
   sf project deploy start -d src/ --wait 60  # 60 minutes
   ```

2. Deploy in smaller chunks:
   ```bash
   ./scripts/deploy_and_test.sh src/classes/ my-org
   ./scripts/deploy_and_test.sh src/triggers/ my-org
   ```

3. Use async deployment:
   ```bash
   sf project deploy start -d src/ --async
   # Check status later
   sf project deploy report
   ```

---

## Integration Issues

### GitHub Actions failing

**Symptom**: CI/CD pipeline fails

**Common causes**:
1. **Missing secrets**: Add `SALESFORCE_AUTH_URL` to GitHub secrets
2. **Wrong branch**: Check workflow triggers in `.github/workflows/`
3. **Test failures**: Review test results in Actions logs

Debug:
```bash
# Get auth URL for secrets
sf org display -o my-org --verbose | grep "Sfdx Auth Url"

# Test locally first
./scripts/deploy_and_test.sh src/ my-org
```

### VS Code tasks not working

**Symptom**: VS Code tasks fail or don't appear

**Solutions**:
1. Reload VS Code: `Cmd+Shift+P` → "Reload Window"
2. Check tasks.json exists: `.vscode/tasks.json`
3. Verify skill installation path in snippets
4. Run task manually to see error:
   ```bash
   ./scripts/query_soql.py "SELECT Id FROM Account" my-org
   ```

### SFDMU not working

**Symptom**: `sfdmu: command not found`

**Solution**:
Install SFDMU plugin:
```bash
sf plugins install sfdmu

# Verify
sf plugins
```

Or use standalone SFDMU:
```bash
npm install -g sfdmu
```

---

## Getting More Help

### Enable verbose logging

For more detailed error messages:

**Python scripts**:
```bash
# Add --verbose flag (if supported)
./scripts/script.py --verbose
```

**sf CLI**:
```bash
# Add --loglevel flag
sf data query -q "..." --loglevel debug
```

### Check log files

Salesforce CLI logs:
```bash
tail -f ~/.sf/sf.log
```

### Run verification

Check overall health:
```bash
./verify-install.sh --verbose
```

### Still stuck?

1. Check [FAQ.md](FAQ.md)
2. Review [references/common-errors.md](references/common-errors.md)
3. Search existing GitHub issues
4. Open a new issue with:
   - What you tried
   - Expected vs actual behavior
   - Error messages (full text)
   - Environment info:
     ```bash
     sf --version
     python3 --version
     uname -a
     ```

---

## Emergency Procedures

### Rollback a bad deployment

If deployment broke production:

1. **Immediate rollback**:
   ```bash
   ./scripts/rollback_deployment.sh production ./backups/latest-snapshot
   ```

2. **No snapshot? Quick fixes**:
   ```bash
   # Deactivate problematic trigger
   # Deactivate workflow rules
   # Fix and re-deploy
   ```

3. **Document incident**:
   - What was deployed
   - What broke
   - How it was fixed
   - Preventive measures

### Recover from accidental data deletion

If using `emergency_rollback.py`:
```bash
./scripts/emergency_rollback.py Account ./backups/accounts.csv production
```

**Prevention**: Always create snapshots before production changes:
```bash
./scripts/snapshot_org.sh production ./backups/$(date +%Y-%m-%d)
```

---

**Remember**: When in doubt, test in sandbox first!
