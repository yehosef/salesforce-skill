#!/usr/bin/env python3
"""
Profile SOQL query performance and provide optimization recommendations.

Analyzes query execution time, record count, and provides suggestions
for improving query performance based on best practices.

Usage:
    ./profile_soql.py "SELECT Id, Name FROM Account" my-org
    ./profile_soql.py "SELECT Id FROM Contact WHERE Email = 'test@example.com'" dev-sandbox

Requirements:
    - Salesforce CLI (sf) v2.x+ installed
    - Python 3.8+
    - Authenticated Salesforce org via: sf org login web -a <org-alias>

Safety: READ-ONLY
    Executes SELECT queries only. No data is modified.

Features:
    - Measures query execution time
    - Counts records returned
    - Checks for common anti-patterns
    - Provides optimization recommendations
    - Estimates query selectivity
"""

import sys
import json
import subprocess
import time
import re


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


def execute_query_with_timing(query, org_alias):
    """Execute SOQL query and measure execution time."""
    print(f"⏱️  Executing query...")

    start_time = time.time()

    cmd = ['sf', 'data', 'query', '-q', query, '-o', org_alias, '--json']
    output = run_command(cmd)

    end_time = time.time()
    execution_time_ms = int((end_time - start_time) * 1000)

    try:
        data = json.loads(output)
        if data.get('result') and data['result'].get('records'):
            records = data['result']['records']
            record_count = len(records)
        else:
            records = []
            record_count = 0

        return {
            'execution_time_ms': execution_time_ms,
            'record_count': record_count,
            'records': records
        }

    except json.JSONDecodeError:
        print("Error: Could not parse query results")
        return None


def analyze_query_structure(query):
    """Analyze query structure and identify potential issues."""
    issues = []
    recommendations = []

    query_upper = query.upper()

    # Check for LIMIT clause
    if 'LIMIT' not in query_upper:
        issues.append("❌ Missing LIMIT clause")
        recommendations.append("Add LIMIT clause to prevent runaway queries (e.g., LIMIT 1000)")

    # Check for leading wildcard in LIKE
    if re.search(r"LIKE\s+'%", query, re.IGNORECASE):
        issues.append("❌ Leading wildcard in LIKE clause")
        recommendations.append("Use trailing wildcard (Name LIKE 'Acme%') instead of leading wildcard (Name LIKE '%Corp') for better index usage")

    # Check for SELECT *
    if 'SELECT *' in query_upper or 'FIELDS(ALL)' in query_upper:
        issues.append("❌ Selecting all fields (SELECT * or FIELDS(ALL))")
        recommendations.append("Select only needed fields to reduce heap usage and improve performance")

    # Check for functions on indexed fields in WHERE
    if re.search(r'WHERE.*?(YEAR|MONTH|DAY|HOUR)\(', query, re.IGNORECASE):
        issues.append("⚠️  Date function in WHERE clause may prevent index usage")
        recommendations.append("Use date literals instead: WHERE CreatedDate = THIS_YEAR instead of WHERE YEAR(CreatedDate) = 2024")

    # Check for != or <> (not equals)
    if re.search(r'(!=|<>)', query):
        issues.append("⚠️  Using != or <> in WHERE clause")
        recommendations.append("Consider using positive filters when possible (= instead of !=) for better index usage")

    # Check for OR conditions
    if ' OR ' in query_upper:
        issues.append("⚠️  Using OR in WHERE clause")
        recommendations.append("Consider using IN clause instead of OR for better performance: WHERE Status IN ('Active', 'Pending') instead of WHERE Status = 'Active' OR Status = 'Pending'")

    # Check for subqueries
    if query_upper.count('SELECT') > 1:
        issues.append("ℹ️  Query contains subqueries")
        recommendations.append("Subqueries are powerful but can be expensive. Consider if a relationship query would be more efficient.")

    # Positive feedback if query looks good
    if not issues:
        issues.append("✅ Query structure looks good!")

    return issues, recommendations


def estimate_selectivity(query, org_alias, record_count):
    """Estimate query selectivity (what % of total records is returned)."""
    # Extract object name from query
    match = re.search(r'FROM\s+(\w+)', query, re.IGNORECASE)
    if not match:
        return None

    sobject = match.group(1)

    # Get total record count for object
    count_query = f"SELECT COUNT(Id) cnt FROM {sobject}"
    cmd = ['sf', 'data', 'query', '-q', count_query, '-o', org_alias, '--json']

    try:
        output = run_command(cmd)
        data = json.loads(output)
        total_count = data['result']['records'][0]['cnt']

        if total_count > 0:
            selectivity_pct = (record_count / total_count) * 100
            return {
                'total_records': total_count,
                'filtered_records': record_count,
                'selectivity_pct': selectivity_pct
            }
    except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError, IndexError):
        pass

    return None


def check_indexed_fields(query):
    """Check if query uses indexed fields in WHERE clause."""
    indexed_fields = [
        'Id', 'Name', 'RecordTypeId', 'OwnerId', 'CreatedDate',
        'SystemModstamp', 'LastModifiedDate'
    ]

    query_upper = query.upper()

    # Extract WHERE clause
    where_match = re.search(r'WHERE\s+(.+?)(?:ORDER BY|GROUP BY|LIMIT|$)', query_upper, re.IGNORECASE)

    if not where_match:
        return None, []

    where_clause = where_match.group(1)

    indexed_in_where = []
    for field in indexed_fields:
        if field.upper() in where_clause:
            indexed_in_where.append(field)

    return where_clause, indexed_in_where


def format_recommendations(issues, recommendations, selectivity, indexed_fields):
    """Format optimization recommendations."""
    print("\n" + "=" * 70)
    print("🔍 QUERY ANALYSIS")
    print("=" * 70)

    print("\n📋 Structure Issues:")
    for issue in issues:
        print(f"   {issue}")

    if selectivity:
        print(f"\n📊 Selectivity:")
        print(f"   Total {selectivity['total_records']} records")
        print(f"   Returned {selectivity['filtered_records']} records")
        print(f"   Selectivity: {selectivity['selectivity_pct']:.2f}%")

        if selectivity['selectivity_pct'] > 10:
            print(f"   ⚠️  Query is not selective (>10% of records returned)")
            print(f"      Salesforce may use full table scan instead of index")
            recommendations.append("Make query more selective by adding more filters (aim for <10% of total records)")
        else:
            print(f"   ✅ Query is selective (<10% of records)")

    if indexed_fields[1]:  # indexed_in_where
        print(f"\n🔑 Indexed Fields in WHERE:")
        for field in indexed_fields[1]:
            print(f"   ✅ {field} (indexed)")
    else:
        print(f"\n🔑 Indexed Fields:")
        print(f"   ⚠️  No standard indexed fields found in WHERE clause")
        recommendations.append("Consider filtering on indexed fields (Id, Name, OwnerId, CreatedDate, etc.) for better performance")

    if recommendations:
        print(f"\n💡 Optimization Recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")

    print("=" * 70)


def main():
    """Main execution."""
    if len(sys.argv) < 3:
        print("Usage: profile_soql.py \"<SOQL query>\" <org-alias>")
        print("")
        print("Examples:")
        print('  ./profile_soql.py "SELECT Id, Name FROM Account WHERE Industry = \'Technology\' LIMIT 1000" my-org')
        print('  ./profile_soql.py "SELECT Id FROM Contact WHERE Email != null" dev-sandbox')
        print("")
        sys.exit(1)

    query = sys.argv[1]
    org_alias = sys.argv[2]

    print("=" * 70)
    print("⚡ SOQL Query Profiler")
    print("=" * 70)
    print(f"Query: {query}")
    print(f"Org: {org_alias}")
    print("=" * 70)

    # Execute query with timing
    result = execute_query_with_timing(query, org_alias)

    if not result:
        sys.exit(1)

    # Display results
    print(f"\n⏱️  Execution Time: {result['execution_time_ms']} ms")
    print(f"📊 Records Returned: {result['record_count']}")

    # Performance assessment
    if result['execution_time_ms'] < 500:
        print(f"✅ Performance: GOOD (< 500ms)")
    elif result['execution_time_ms'] < 1000:
        print(f"⚠️  Performance: MODERATE (500-1000ms)")
    else:
        print(f"❌ Performance: SLOW (> 1000ms)")

    # Analyze query structure
    issues, recommendations = analyze_query_structure(query)

    # Estimate selectivity
    selectivity = estimate_selectivity(query, org_alias, result['record_count'])

    # Check indexed fields
    indexed_fields = check_indexed_fields(query)

    # Format recommendations
    format_recommendations(issues, recommendations, selectivity, indexed_fields)

    # Show sample records (if small result set)
    if result['record_count'] > 0 and result['record_count'] <= 5:
        print("\n📄 Sample Records:")
        for i, record in enumerate(result['records'][:5], 1):
            clean_record = {k: v for k, v in record.items() if k != 'attributes'}
            print(f"   {i}. {json.dumps(clean_record, indent=6)}")

    print("")


if __name__ == "__main__":
    main()
