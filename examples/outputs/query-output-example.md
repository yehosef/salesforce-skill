# Example: SOQL Query Output

This shows the expected output format from `query_soql.py`.

## Command
```bash
./scripts/query_soql.py "SELECT Id, Name, Industry FROM Account LIMIT 5" my-org
```

## Output

Executing query: SELECT Id, Name, Industry FROM Account LIMIT 5
Target org: my-org

| Id | Name | Industry |
| --- | --- | --- |
| 001xx000003DGb2AAG | Acme Corporation | Technology |
| 001xx000003DGb3AAG | Global Industries | Manufacturing |
| 001xx000003DGb4AAG | Summit Partners | Financial Services |
| 001xx000003DGb5AAG | Ocean Logistics | Transportation |
| 001xx000003DGb6AAG | Mountain Retail | Retail |

**Total:** 5 record(s)
