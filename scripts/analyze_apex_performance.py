#!/usr/bin/env python3
"""
Analyze Apex debug logs for performance bottlenecks.

Parses Salesforce debug logs to identify CPU-intensive methods,
heap usage, SOQL query hotspots, and governor limit usage.

Usage:
    ./analyze_apex_performance.py ./debug-log.txt
    ./analyze_apex_performance.py ./logs/ApexLog-2025-10-20.log

Features:
    - CPU time analysis by method
    - Heap usage tracking
    - SOQL query identification
    - DML operation counts
    - Governor limit summary
"""

import sys
import re
from collections import defaultdict


def parse_debug_log(log_file):
    """Parse debug log and extract performance metrics."""
    with open(log_file, 'r', encoding='utf-8') as f:
        content = f.read()

    metrics = {
        'cpu_time': [],
        'heap_usage': [],
        'soql_queries': [],
        'dml_operations': [],
        'methods': defaultdict(list),
        'limits': {}
    }

    lines = content.split('\n')

    current_method = None
    method_stack = []

    for line in lines:
        # Track method entry/exit
        method_entry = re.search(r'METHOD_ENTRY.*?(\w+\.\w+\([^\)]*\))', line)
        if method_entry:
            method_name = method_entry.group(1)
            method_stack.append(method_name)
            current_method = method_name

        method_exit = re.search(r'METHOD_EXIT.*?(\w+\.\w+\([^\)]*\))', line)
        if method_exit:
            if method_stack:
                method_stack.pop()
            current_method = method_stack[-1] if method_stack else None

        # Extract SOQL queries
        soql_match = re.search(r'SOQL_EXECUTE_BEGIN.*?\[(.*?)\]', line)
        if soql_match:
            query = soql_match.group(1)
            metrics['soql_queries'].append({
                'query': query[:200],  # Truncate long queries
                'method': current_method or 'Unknown'
            })

        # Extract DML operations
        dml_match = re.search(r'DML_BEGIN\s+\[.*?\]\s+Op:(\w+)', line)
        if dml_match:
            operation = dml_match.group(1)
            metrics['dml_operations'].append({
                'operation': operation,
                'method': current_method or 'Unknown'
            })

        # Extract cumulative limits
        limit_match = re.search(r'LIMIT_USAGE_FOR_NS.*?Number of SOQL queries:\s+(\d+)\s+out of\s+(\d+)', line)
        if limit_match:
            metrics['limits']['soql_queries'] = {
                'used': int(limit_match.group(1)),
                'limit': int(limit_match.group(2))
            }

        limit_match = re.search(r'Maximum CPU time:\s+(\d+)\s+out of\s+(\d+)', line)
        if limit_match:
            metrics['limits']['cpu_time'] = {
                'used': int(limit_match.group(1)),
                'limit': int(limit_match.group(2))
            }

        limit_match = re.search(r'Maximum heap size:\s+(\d+)\s+out of\s+(\d+)', line)
        if limit_match:
            metrics['limits']['heap_size'] = {
                'used': int(limit_match.group(1)),
                'limit': int(limit_match.group(2))
            }

        limit_match = re.search(r'Number of DML statements:\s+(\d+)\s+out of\s+(\d+)', line)
        if limit_match:
            metrics['limits']['dml_statements'] = {
                'used': int(limit_match.group(1)),
                'limit': int(limit_match.group(2))
            }

    return metrics


def format_analysis(metrics):
    """Format performance analysis report."""
    print("=" * 70)
    print("⚡ APEX PERFORMANCE ANALYSIS")
    print("=" * 70)

    # Governor Limits Summary
    if metrics['limits']:
        print("\n📊 Governor Limits Usage:")
        print("-" * 70)

        if 'cpu_time' in metrics['limits']:
            cpu = metrics['limits']['cpu_time']
            pct = (cpu['used'] / cpu['limit']) * 100
            status = "✅" if pct < 50 else "⚠️ " if pct < 80 else "❌"
            print(f"  {status} CPU Time: {cpu['used']:,} / {cpu['limit']:,} ms ({pct:.1f}%)")

        if 'heap_size' in metrics['limits']:
            heap = metrics['limits']['heap_size']
            pct = (heap['used'] / heap['limit']) * 100
            status = "✅" if pct < 50 else "⚠️ " if pct < 80 else "❌"
            print(f"  {status} Heap Size: {heap['used']:,} / {heap['limit']:,} bytes ({pct:.1f}%)")

        if 'soql_queries' in metrics['limits']:
            soql = metrics['limits']['soql_queries']
            pct = (soql['used'] / soql['limit']) * 100
            status = "✅" if pct < 50 else "⚠️ " if pct < 80 else "❌"
            print(f"  {status} SOQL Queries: {soql['used']} / {soql['limit']} ({pct:.1f}%)")

        if 'dml_statements' in metrics['limits']:
            dml = metrics['limits']['dml_statements']
            pct = (dml['used'] / dml['limit']) * 100
            status = "✅" if pct < 50 else "⚠️ " if pct < 80 else "❌"
            print(f"  {status} DML Statements: {dml['used']} / {dml['limit']} ({pct:.1f}%)")

    # SOQL Queries
    if metrics['soql_queries']:
        print(f"\n🔍 SOQL Queries ({len(metrics['soql_queries'])} total):")
        print("-" * 70)

        # Group by method
        queries_by_method = defaultdict(list)
        for query_info in metrics['soql_queries']:
            queries_by_method[query_info['method']].append(query_info['query'])

        for method, queries in sorted(queries_by_method.items(), key=lambda x: len(x[1]), reverse=True)[:5]:
            print(f"\n  Method: {method}")
            print(f"  Count: {len(queries)} queries")
            if len(queries) > 1:
                print(f"  ⚠️  Multiple queries in same method - consider bulkifying")
            for query in queries[:2]:  # Show first 2
                print(f"    • {query[:100]}...")

    # DML Operations
    if metrics['dml_operations']:
        print(f"\n💾 DML Operations ({len(metrics['dml_operations'])} total):")
        print("-" * 70)

        # Group by method and operation
        dml_by_method = defaultdict(lambda: defaultdict(int))
        for dml_info in metrics['dml_operations']:
            dml_by_method[dml_info['method']][dml_info['operation']] += 1

        for method, operations in sorted(dml_by_method.items(), key=lambda x: sum(x[1].values()), reverse=True)[:5]:
            total_dml = sum(operations.values())
            print(f"\n  Method: {method}")
            print(f"  Total DML: {total_dml}")
            if total_dml > 1:
                print(f"  ⚠️  Multiple DML operations - consider bulkifying")
            for op, count in operations.items():
                print(f"    • {op}: {count}")

    # Recommendations
    print("\n" + "=" * 70)
    print("💡 RECOMMENDATIONS")
    print("=" * 70)

    recommendations = []

    if metrics['limits'].get('cpu_time', {}).get('used', 0) / metrics['limits'].get('cpu_time', {}).get('limit', 1) > 0.5:
        recommendations.append("CPU usage is high. Consider:")
        recommendations.append("  - Moving complex logic to async (@future, Queueable, Batch)")
        recommendations.append("  - Reducing nested loops")
        recommendations.append("  - Caching expensive calculations")

    if metrics['limits'].get('heap_size', {}).get('used', 0) / metrics['limits'].get('heap_size', {}).get('limit', 1) > 0.5:
        recommendations.append("Heap usage is high. Consider:")
        recommendations.append("  - Loading fewer fields in SOQL queries")
        recommendations.append("  - Processing records in smaller batches")
        recommendations.append("  - Clearing large collections after use")

    if len(metrics['soql_queries']) > 50:
        recommendations.append("High SOQL query count. Consider:")
        recommendations.append("  - Bulkifying code to use fewer queries")
        recommendations.append("  - Using Maps for lookups instead of repeated queries")
        recommendations.append("  - Moving queries outside loops")

    if len(metrics['dml_operations']) > 50:
        recommendations.append("High DML operation count. Consider:")
        recommendations.append("  - Collecting records and using bulk DML (update list)")
        recommendations.append("  - Removing DML from loops")

    if recommendations:
        for rec in recommendations:
            print(f"  {rec}")
    else:
        print("  ✅ No major issues detected. Code appears well-optimized!")

    print("=" * 70)


def main():
    """Main execution."""
    if len(sys.argv) < 2:
        print("Usage: analyze_apex_performance.py <debug-log-file>")
        print("")
        print("Examples:")
        print("  ./analyze_apex_performance.py ./debug-log.txt")
        print("  ./analyze_apex_performance.py ./logs/ApexLog-2025-10-20.log")
        print("")
        print("How to get debug logs:")
        print("  1. Developer Console → Debug → Change Log Levels")
        print("  2. Set Apex Code = FINEST, Database = FINEST")
        print("  3. Execute your code")
        print("  4. Debug → View Log → Download log")
        print("")
        sys.exit(1)

    log_file = sys.argv[1]

    print(f"📂 Analyzing: {log_file}\n")

    try:
        metrics = parse_debug_log(log_file)
        format_analysis(metrics)
    except FileNotFoundError:
        print(f"Error: File not found: {log_file}")
        sys.exit(1)
    except Exception as e:
        print(f"Error parsing log file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
