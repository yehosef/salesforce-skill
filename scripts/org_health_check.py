#!/usr/bin/env python3
"""
Comprehensive Salesforce org health check.

Analyzes org configuration, limits, metadata, and provides
health score with actionable recommendations.

Usage:
    ./org_health_check.py my-org
    ./org_health_check.py production --detailed

Features:
    - API limits usage
    - Data storage usage
    - Metadata counts
    - Code coverage
    - Apex test failures
    - Active workflows/triggers
    - Health score (0-100)
"""

import sys
import json
import subprocess
from datetime import datetime


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
    except subprocess.CalledProcessError:
        return None


def get_org_limits(org_alias):
    """Get org limits and usage."""
    print("  Fetching org limits...")

    cmd = ['sf', 'org', 'list', 'limits', '-o', org_alias, '--json']
    output = run_command(cmd)

    if not output:
        return None

    try:
        data = json.loads(output)
        return data.get('result', [])
    except json.JSONDecodeError:
        return None


def get_apex_test_results(org_alias):
    """Get recent Apex test results."""
    print("  Checking Apex test coverage...")

    cmd = ['sf', 'apex', 'get', 'test', '-o', org_alias, '--code-coverage', '--json']
    output = run_command(cmd)

    if not output:
        return None

    try:
        data = json.loads(output)
        return data.get('result', {})
    except json.JSONDecodeError:
        return None


def get_metadata_counts(org_alias):
    """Get counts of various metadata types."""
    print("  Counting metadata components...")

    counts = {}

    # Count Apex classes
    cmd = ['sf', 'data', 'query', '-q', 'SELECT COUNT(Id) cnt FROM ApexClass', '-o', org_alias, '--json']
    output = run_command(cmd)
    if output:
        try:
            data = json.loads(output)
            counts['ApexClass'] = data['result']['records'][0]['cnt']
        except:
            counts['ApexClass'] = 0

    # Count Apex triggers
    cmd = ['sf', 'data', 'query', '-q', "SELECT COUNT(Id) cnt FROM ApexTrigger WHERE Status = 'Active'", '-o', org_alias, '--json']
    output = run_command(cmd)
    if output:
        try:
            data = json.loads(output)
            counts['ApexTrigger'] = data['result']['records'][0]['cnt']
        except:
            counts['ApexTrigger'] = 0

    # Count custom objects
    cmd = ['sf', 'sobject', 'list', '-o', org_alias, '--json']
    output = run_command(cmd)
    if output:
        try:
            data = json.loads(output)
            custom_objects = [obj for obj in data.get('result', []) if obj.endswith('__c')]
            counts['CustomObject'] = len(custom_objects)
        except:
            counts['CustomObject'] = 0

    return counts


def calculate_health_score(limits, test_results, metadata_counts):
    """Calculate overall org health score (0-100)."""
    score = 100
    issues = []

    # Check API limits (deduct up to 20 points)
    if limits:
        for limit in limits:
            if 'DailyApiRequests' in limit.get('name', ''):
                max_val = limit.get('max', 1)
                remaining = limit.get('remaining', max_val)
                used_pct = ((max_val - remaining) / max_val) * 100

                if used_pct > 90:
                    score -= 20
                    issues.append(f"API usage critical: {used_pct:.1f}%")
                elif used_pct > 75:
                    score -= 10
                    issues.append(f"API usage high: {used_pct:.1f}%")

            if 'DataStorageMB' in limit.get('name', ''):
                max_val = limit.get('max', 1)
                remaining = limit.get('remaining', max_val)
                used_pct = ((max_val - remaining) / max_val) * 100

                if used_pct > 90:
                    score -= 15
                    issues.append(f"Storage critical: {used_pct:.1f}%")
                elif used_pct > 75:
                    score -= 7
                    issues.append(f"Storage high: {used_pct:.1f}%")

    # Check code coverage (deduct up to 30 points)
    if test_results:
        coverage = test_results.get('summary', {}).get('orgWideCoverage', '0%')
        coverage_pct = float(coverage.strip('%'))

        if coverage_pct < 75:
            score -= 30
            issues.append(f"Code coverage below 75%: {coverage_pct}%")
        elif coverage_pct < 80:
            score -= 15
            issues.append(f"Code coverage low: {coverage_pct}%")

        # Check for failed tests (deduct up to 15 points)
        failures = test_results.get('summary', {}).get('failing', 0)
        if failures > 0:
            score -= min(failures * 5, 15)
            issues.append(f"{failures} test(s) failing")

    # Check metadata counts (deduct up to 15 points)
    if metadata_counts:
        apex_count = metadata_counts.get('ApexClass', 0)
        if apex_count > 1000:
            score -= 10
            issues.append(f"High Apex class count: {apex_count}")

        trigger_count = metadata_counts.get('ApexTrigger', 0)
        if trigger_count > 100:
            score -= 5
            issues.append(f"High trigger count: {trigger_count}")

    return max(0, score), issues


def format_report(org_alias, limits, test_results, metadata_counts, score, issues):
    """Format health check report."""
    print("\n" + "=" * 70)
    print("🏥 SALESFORCE ORG HEALTH CHECK")
    print("=" * 70)
    print(f"Org: {org_alias}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Health Score
    if score >= 90:
        status = "✅ EXCELLENT"
        color = "green"
    elif score >= 75:
        status = "✅ GOOD"
        color = "green"
    elif score >= 60:
        status = "⚠️  FAIR"
        color = "yellow"
    else:
        status = "❌ POOR"
        color = "red"

    print(f"\n🎯 Health Score: {score}/100 {status}")

    # Key Limits
    if limits:
        print("\n📊 Key Limits:")
        print("-" * 70)

        for limit in limits[:10]:  # Show top 10 limits
            name = limit.get('name', 'Unknown')
            max_val = limit.get('max', 0)
            remaining = limit.get('remaining', 0)
            used = max_val - remaining
            used_pct = (used / max_val * 100) if max_val > 0 else 0

            status_icon = "✅" if used_pct < 50 else "⚠️ " if used_pct < 75 else "❌"
            print(f"  {status_icon} {name}: {used:,} / {max_val:,} ({used_pct:.1f}%)")

    # Code Coverage
    if test_results:
        print("\n🧪 Code Coverage:")
        print("-" * 70)

        summary = test_results.get('summary', {})
        coverage = summary.get('orgWideCoverage', 'N/A')
        passing = summary.get('passing', 0)
        failing = summary.get('failing', 0)
        total = passing + failing

        print(f"  Coverage: {coverage}")
        print(f"  Tests: {passing}/{total} passing")

        if failing > 0:
            print(f"  ❌ {failing} test(s) failing")

    # Metadata Counts
    if metadata_counts:
        print("\n📦 Metadata:")
        print("-" * 70)

        for metadata_type, count in metadata_counts.items():
            print(f"  {metadata_type}: {count}")

    # Issues
    if issues:
        print("\n⚠️  Issues Found:")
        print("-" * 70)
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")

    # Recommendations
    print("\n💡 Recommendations:")
    print("-" * 70)

    if score >= 90:
        print("  ✅ Org is in excellent health. Keep monitoring regularly.")
    else:
        if any('API usage' in issue for issue in issues):
            print("  • Review API integrations and optimize callout frequency")
        if any('Storage' in issue for issue in issues):
            print("  • Archive old records or purchase additional storage")
        if any('Code coverage' in issue for issue in issues):
            print("  • Write additional Apex tests to increase coverage")
        if any('failing' in issue for issue in issues):
            print("  • Fix failing tests immediately")
        if any('Apex class count' in issue for issue in issues):
            print("  • Review and remove unused Apex classes")
        if any('trigger count' in issue for issue in issues):
            print("  • Consolidate triggers using trigger framework")

    print("=" * 70)


def main():
    """Main execution."""
    if len(sys.argv) < 2:
        print("Usage: org_health_check.py <org-alias>")
        print("")
        print("Examples:")
        print("  ./org_health_check.py my-org")
        print("  ./org_health_check.py production")
        print("")
        sys.exit(1)

    org_alias = sys.argv[1]

    print(f"🔍 Running health check on {org_alias}...\n")

    # Gather data
    limits = get_org_limits(org_alias)
    test_results = get_apex_test_results(org_alias)
    metadata_counts = get_metadata_counts(org_alias)

    # Calculate health score
    score, issues = calculate_health_score(limits, test_results, metadata_counts)

    # Display report
    format_report(org_alias, limits, test_results, metadata_counts, score, issues)

    print("")


if __name__ == "__main__":
    main()
