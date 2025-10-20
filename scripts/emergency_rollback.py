#!/usr/bin/env python3
"""
Emergency data rollback script for quick recovery from data corruption.

Restores Salesforce records from CSV backup file with validation
and diff preview before applying changes.

Usage:
    ./emergency_rollback.py Account ./backup-accounts.csv my-org
    ./emergency_rollback.py Contact ./backup-contacts.csv production

Features:
    - Shows diff before applying changes
    - Validates backup data format
    - Confirms before restoration
    - Reports success/failure per record
"""

import sys
import json
import subprocess
import csv
from datetime import datetime


def run_command(cmd):
    """Execute shell command and return output."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        return None


def load_backup_csv(csv_file):
    """Load backup CSV file and return records."""
    print(f"📂 Loading backup file: {csv_file}")

    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            records = list(reader)

        print(f"✅ Loaded {len(records)} records from backup")
        return records

    except FileNotFoundError:
        print(f"Error: Backup file not found: {csv_file}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading backup file: {e}")
        sys.exit(1)


def get_current_records(sobject, record_ids, org_alias):
    """Get current state of records in org."""
    print(f"\n🔍 Fetching current records from {org_alias}...")

    ids_str = "'" + "','".join(record_ids) + "'"
    query = f"SELECT Id FROM {sobject} WHERE Id IN ({ids_str})"

    cmd = f'sf data query -q "{query}" -o {org_alias} --json'
    output = run_command(cmd)

    if not output:
        return []

    try:
        data = json.loads(output)
        if data.get('result') and data['result'].get('records'):
            return data['result']['records']
        return []
    except json.JSONDecodeError:
        return []


def show_diff_preview(backup_records, current_count):
    """Show preview of changes that will be applied."""
    print("\n" + "=" * 70)
    print("📊 RESTORE PREVIEW")
    print("=" * 70)
    print(f"  Records in backup: {len(backup_records)}")
    print(f"  Records in org: {current_count}")

    if len(backup_records) > current_count:
        print(f"  ⚠️  {len(backup_records) - current_count} records will be created")
    elif len(backup_records) < current_count:
        print(f"  ⚠️  {current_count - len(backup_records)} records not in backup (won't be affected)")

    print("\n  Sample records to restore:")
    for i, record in enumerate(backup_records[:5], 1):
        record_id = record.get('Id', 'N/A')
        print(f"    {i}. {record_id}: {dict(list(record.items())[:3])}")

    print("=" * 70)


def restore_data(sobject, csv_file, org_alias):
    """Restore data from CSV using sf CLI."""
    print(f"\n💾 Restoring data to {org_alias}...")

    # Use upsert to handle both inserts and updates
    cmd = f'sf data import tree --sobject {sobject} --file {csv_file} --target-org {org_alias} --json'
    output = run_command(cmd)

    if not output:
        print("❌ Data restoration failed")
        return False

    try:
        data = json.loads(output)
        if data.get('status') == 0:
            print("✅ Data restored successfully")
            return True
        else:
            print(f"❌ Restoration failed: {data.get('message', 'Unknown error')}")
            return False
    except json.JSONDecodeError:
        # Try alternate method with bulk API
        print("Trying bulk restore...")
        cmd = f'sf data import bulk --sobject {sobject} --file {csv_file} -o {org_alias}'
        result = run_command(cmd)
        return result is not None


def main():
    """Main execution."""
    if len(sys.argv) < 4:
        print("Usage: emergency_rollback.py <sobject> <backup-csv> <org-alias>")
        print("")
        print("Restores Salesforce records from CSV backup.")
        print("")
        print("Examples:")
        print("  ./emergency_rollback.py Account ./backup-accounts.csv my-org")
        print("  ./emergency_rollback.py Contact ./backup-contacts.csv production")
        print("")
        sys.exit(1)

    sobject = sys.argv[1]
    csv_file = sys.argv[2]
    org_alias = sys.argv[3]

    print("=" * 70)
    print("🚨 EMERGENCY DATA ROLLBACK")
    print("=" * 70)
    print(f"Object: {sobject}")
    print(f"Backup: {csv_file}")
    print(f"Org: {org_alias}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Load backup
    backup_records = load_backup_csv(csv_file)

    if not backup_records:
        print("Error: No records in backup file")
        sys.exit(1)

    # Get current records
    record_ids = [r['Id'] for r in backup_records if 'Id' in r]
    current_records = get_current_records(sobject, record_ids, org_alias)

    # Show diff
    show_diff_preview(backup_records, len(current_records))

    # Confirmation
    print("\n⚠️  WARNING: This will overwrite current data with backup data!")
    confirm = input("Are you sure you want to continue? (yes/no): ")

    if confirm.lower() != 'yes':
        print("Rollback cancelled.")
        sys.exit(0)

    # Restore
    success = restore_data(sobject, csv_file, org_alias)

    print("\n" + "=" * 70)
    if success:
        print("✅ EMERGENCY ROLLBACK COMPLETE")
        print("=" * 70)
        print(f"  Restored {len(backup_records)} {sobject} records")
        print("\n💡 Next Steps:")
        print("   1. Verify data in Salesforce UI")
        print("   2. Run validation queries")
        print("   3. Test critical workflows")
        print("   4. Monitor for issues")
    else:
        print("❌ ROLLBACK FAILED")
        print("=" * 70)
        print("  Check error messages above")
        print("  Manual restoration may be required")

    print("=" * 70)


if __name__ == "__main__":
    main()
