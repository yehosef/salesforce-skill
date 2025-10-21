#!/usr/bin/env python3
"""
Find duplicate records in Salesforce based on specified fields.

Identifies duplicates using GROUP BY queries and exports results to CSV.
Provides merge recommendations based on record age and data completeness.

Usage:
    ./find_duplicates.py Account "Name,BillingCity" my-org
    ./find_duplicates.py Contact "Email" dev-sandbox
    ./find_duplicates.py Custom_Object__c "External_Id__c" production

Requirements:
    - Salesforce CLI (sf) v2.x+ installed
    - Python 3.8+
    - Authenticated Salesforce org via: sf org login web -a <org-alias>
    - Write permissions for export directory

Safety: READ-ONLY (with file export)
    Reads duplicate records from org. Exports results to CSV files.
    No data in org is modified.

Features:
    - Supports single or multiple match fields
    - Groups duplicates for easy review
    - Recommends master record for merging
    - Exports to CSV for analysis
    - Handles custom and standard objects
"""

import sys
import json
import subprocess
from datetime import datetime
from collections import defaultdict


def run_command(cmd_list):
    """Execute command and return output."""
    try:
        result = subprocess.run(
            cmd_list,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {' '.join(cmd_list)}")
        print(f"Error: {e.stderr}")
        sys.exit(1)


def find_duplicate_field_values(sobject, fields, org_alias):
    """Find field values that appear more than once."""
    print(f"🔍 Searching for duplicates in {sobject}...")
    print(f"   Matching on: {', '.join(fields)}")

    # Build GROUP BY query
    field_list = ', '.join(fields)
    having_conditions = ' AND '.join([f"{field} != null" for field in fields])

    query = f"""
        SELECT {field_list}, COUNT(Id) cnt
        FROM {sobject}
        WHERE {having_conditions}
        GROUP BY {field_list}
        HAVING COUNT(Id) > 1
        ORDER BY COUNT(Id) DESC
        LIMIT 1000
    """

    query_oneline = ' '.join(query.split())

    print(f"\n📋 Query: {query_oneline}\n")

    cmd = ['sf', 'data', 'query', '-q', query_oneline, '-o', org_alias, '--json']
    output = run_command(cmd)

    try:
        data = json.loads(output)
        if data.get('result') and data['result'].get('records'):
            records = data['result']['records']

            # Remove attributes field
            clean_records = []
            for record in records:
                clean_record = {k: v for k, v in record.items() if k != 'attributes'}
                clean_records.append(clean_record)

            return clean_records
        else:
            return []

    except json.JSONDecodeError as e:
        print(f"Error parsing JSON output: {e}")
        return []


def get_duplicate_records(sobject, fields, field_values, org_alias):
    """Get all records that match the duplicate field values."""
    print(f"\n📦 Retrieving full details for duplicate records...")

    all_duplicates = []

    for values in field_values:
        # Build WHERE clause
        where_conditions = []
        for field in fields:
            value = values.get(field)
            if value:
                # Escape single quotes
                escaped_value = str(value).replace("'", "\\'")
                where_conditions.append(f"{field} = '{escaped_value}'")

        where_clause = ' AND '.join(where_conditions)

        # Query for all records with these field values
        query = f"""
            SELECT Id, {', '.join(fields)}, CreatedDate, LastModifiedDate
            FROM {sobject}
            WHERE {where_clause}
            ORDER BY CreatedDate ASC
        """

        query_oneline = ' '.join(query.split())

        cmd = ['sf', 'data', 'query', '-q', query_oneline, '-o', org_alias, '--json']
        output = run_command(cmd)

        try:
            data = json.loads(output)
            if data.get('result') and data['result'].get('records'):
                records = data['result']['records']

                # Clean attributes
                clean_records = []
                for record in records:
                    clean_record = {k: v for k, v in record.items() if k != 'attributes'}
                    clean_records.append(clean_record)

                # Add duplicate group info
                group_info = {
                    'match_values': values,
                    'count': values.get('cnt', len(clean_records)),
                    'records': clean_records
                }
                all_duplicates.append(group_info)

        except json.JSONDecodeError:
            continue

    return all_duplicates


def recommend_master_record(duplicate_group):
    """Recommend which record should be the master in a merge."""
    records = duplicate_group['records']

    if not records:
        return None

    # Strategy: Prefer oldest record (first created)
    # Secondary: Most recently modified (has most up-to-date data)

    # Sort by CreatedDate (oldest first), then LastModifiedDate (newest first)
    sorted_records = sorted(
        records,
        key=lambda r: (r.get('CreatedDate', ''), r.get('LastModifiedDate', '')),
        reverse=False
    )

    # First record is oldest (master)
    return sorted_records[0]['Id']


def format_duplicate_report(sobject, fields, duplicate_groups):
    """Format duplicate groups for display."""
    print("\n" + "=" * 70)
    print("🔍 DUPLICATE RECORDS FOUND")
    print("=" * 70)
    print(f"Object: {sobject}")
    print(f"Match Fields: {', '.join(fields)}")
    print(f"Duplicate Groups: {len(duplicate_groups)}")
    print("=" * 70)

    total_records = 0

    for i, group in enumerate(duplicate_groups, 1):
        match_values = group['match_values']
        records = group['records']
        count = len(records)
        total_records += count

        print(f"\n📌 Group {i} ({count} records):")

        # Show match values
        for field in fields:
            value = match_values.get(field, 'N/A')
            print(f"   {field}: {value}")

        # Show all records in group
        master_id = recommend_master_record(group)

        for record in records:
            record_id = record.get('Id', 'N/A')
            created = record.get('CreatedDate', 'N/A')[:10]  # Just date
            modified = record.get('LastModifiedDate', 'N/A')[:10]

            is_master = " [MASTER - Keep this]" if record_id == master_id else " [Duplicate - Merge]"

            print(f"      • {record_id} | Created: {created} | Modified: {modified}{is_master}")

    print("\n" + "=" * 70)
    print(f"📊 SUMMARY")
    print("=" * 70)
    print(f"   Total Duplicate Groups: {len(duplicate_groups)}")
    print(f"   Total Records Affected: {total_records}")
    print(f"   Records to Merge/Delete: {total_records - len(duplicate_groups)}")
    print("=" * 70)


def export_to_csv(sobject, fields, duplicate_groups, output_file):
    """Export duplicate groups to CSV for analysis."""
    import csv

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        # Build fieldnames
        fieldnames = ['Group', 'IsMaster', 'Id', 'CreatedDate', 'LastModifiedDate'] + fields

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for i, group in enumerate(duplicate_groups, 1):
            match_values = group['match_values']
            records = group['records']
            master_id = recommend_master_record(group)

            for record in records:
                row = {
                    'Group': i,
                    'IsMaster': 'Yes' if record['Id'] == master_id else 'No',
                    'Id': record.get('Id', ''),
                    'CreatedDate': record.get('CreatedDate', ''),
                    'LastModifiedDate': record.get('LastModifiedDate', '')
                }

                # Add match field values
                for field in fields:
                    row[field] = record.get(field, '')

                writer.writerow(row)

    print(f"\n💾 Exported to: {output_file}")
    print(f"   Open in Excel/Sheets for review and planning merges")


def main():
    """Main execution."""
    if len(sys.argv) < 4:
        print("Usage: find_duplicates.py <sobject> \"<field1>,<field2>,...\" <org-alias>")
        print("")
        print("Examples:")
        print('  ./find_duplicates.py Contact "Email" my-org')
        print('  ./find_duplicates.py Account "Name,BillingCity" dev-sandbox')
        print('  ./find_duplicates.py Custom_Object__c "External_Id__c,Name" production')
        print("")
        sys.exit(1)

    sobject = sys.argv[1]
    fields_str = sys.argv[2]
    org_alias = sys.argv[3]

    # Parse fields
    fields = [field.strip() for field in fields_str.split(',')]

    print("=" * 70)
    print("🔎 Salesforce Duplicate Finder")
    print("=" * 70)
    print(f"Object: {sobject}")
    print(f"Fields: {', '.join(fields)}")
    print(f"Org: {org_alias}")
    print("=" * 70)

    # Step 1: Find duplicate field values
    duplicate_field_values = find_duplicate_field_values(sobject, fields, org_alias)

    if not duplicate_field_values:
        print("\n✅ No duplicates found!")
        print(f"   All {sobject} records have unique values for: {', '.join(fields)}")
        sys.exit(0)

    print(f"\n✅ Found {len(duplicate_field_values)} duplicate field value combinations")

    # Step 2: Get full records for each duplicate group
    duplicate_groups = get_duplicate_records(sobject, fields, duplicate_field_values, org_alias)

    if not duplicate_groups:
        print("\n⚠️  Could not retrieve duplicate records")
        sys.exit(1)

    # Step 3: Display results
    format_duplicate_report(sobject, fields, duplicate_groups)

    # Step 4: Export to CSV
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_file = f"./duplicates-{sobject}-{timestamp}.csv"
    export_to_csv(sobject, fields, duplicate_groups, output_file)

    # Next steps
    print("\n💡 Next Steps:")
    print(f"   1. Review {output_file} in Excel/Sheets")
    print(f"   2. Verify master record recommendations")
    print(f"   3. Merge duplicates in Salesforce UI or via API")
    print(f"   4. Consider creating a Duplicate Rule to prevent future duplicates")
    print("")


if __name__ == "__main__":
    main()
