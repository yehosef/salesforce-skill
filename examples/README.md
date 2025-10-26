# Examples

This directory contains practical examples, sample queries, and expected outputs for the Salesforce skill.

## Contents

### 📝 SOQL Queries (`soql/`)
Sample SOQL queries demonstrating common patterns and use cases.

### 📊 Sample Outputs (`outputs/`)
Example output from various scripts showing expected formatting and results.

### 🔧 Script Examples (`scripts/`)
Complete workflow examples showing how to use scripts together.

### ⚡ Apex Examples (`apex/`)
Sample Apex code, test classes, and triggers.

## Quick Examples

### Query Accounts
```bash
./scripts/query_soql.py "$(cat examples/soql/basic-account-query.soql)" my-org
```

### Compare Orgs
```bash
./scripts/compare_orgs.sh sandbox production
```

### Deploy with Tests
```bash
./scripts/deploy_and_test.sh src/classes/MyClass.cls my-org
```

## See Also

- [SKILL.md](../SKILL.md) - Complete skill documentation
- [references/](../references/) - Reference guides and patterns
- [scripts/README.md](../scripts/README.md) - Script documentation
