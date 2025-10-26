# Example: Org Comparison Output

This shows the expected output from `compare_orgs.sh`.

## Command
```bash
./scripts/compare_orgs.sh dev-sandbox prod-sandbox
```

## Output

```
Comparing metadata between dev-sandbox and prod-sandbox...

Retrieving ApexClass from dev-sandbox... Done (45 classes)
Retrieving ApexClass from prod-sandbox... Done (42 classes)

=================================================
  Metadata Comparison Report
=================================================

ApexClass:
  Only in dev-sandbox (3):
    - NewPaymentController
    - DonationBatchProcessor
    - IntegrationHelper

  Only in prod-sandbox (0):

  Modified (2):
    - AccountTriggerHandler
      └─ 156 lines changed
    - OpportunityService
      └─ 23 lines changed

---

Retrieving ApexTrigger from dev-sandbox... Done (12 triggers)
Retrieving ApexTrigger from prod-sandbox... Done (12 triggers)

ApexTrigger:
  Only in dev-sandbox (0):

  Only in prod-sandbox (0):

  Modified (1):
    - AccountTrigger
      └─ 8 lines changed

=================================================
  Summary
=================================================

Total differences: 6
New in dev-sandbox: 3
Modified: 3
New in prod-sandbox: 0

Recommendation: Review modified components before deployment
```
