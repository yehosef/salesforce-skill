#!/usr/bin/env python3
"""
Monitor Salesforce org limits and send alerts when thresholds are exceeded.

Tracks API usage, storage, and other critical limits. Can be run as a cron job
for continuous monitoring.

Usage:
    ./org_limits_monitor.py my-org
    ./org_limits_monitor.py production --alert-threshold 80

Features:
    - Monitors all org limits
    - Configurable alert thresholds
    - Identifies trending limits
    - Exports history for tracking
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
    """Get all org limits and usage."""
    cmd = ['sf', 'org', 'list', 'limits', '-o', org_alias, '--json']
    output = run_command(cmd)

    if not output:
        return None

    try:
        data = json.loads(output)
        return data.get('result', [])
    except json.JSONDecodeError:
        return None


def analyze_limits(limits, threshold=80):
    """Analyze limits and identify critical ones."""
    critical = []
    warning = []
    ok = []

    for limit in limits:
        name = limit.get('name', 'Unknown')
        max_val = limit.get('max', 0)
        remaining = limit.get('remaining', 0)

        if max_val == 0:
            continue

        used = max_val - remaining
        used_pct = (used / max_val) * 100

        limit_info = {
            'name': name,
            'used': used,
            'max': max_val,
            'remaining': remaining,
            'used_pct': used_pct
        }

        if used_pct >= 90:
            critical.append(limit_info)
        elif used_pct >= threshold:
            warning.append(limit_info)
        else:
            ok.append(limit_info)

    return critical, warning, ok


def format_report(org_alias, critical, warning, ok, threshold):
    """Format monitoring report."""
    print("=" * 70)
    print("📊 SALESFORCE ORG LIMITS MONITOR")
    print("=" * 70)
    print(f"Org: {org_alias}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Alert Threshold: {threshold}%")
    print("=" * 70)

    # Critical Limits
    if critical:
        print(f"\n🚨 CRITICAL LIMITS ({len(critical)}):")
        print("-" * 70)
        for limit in critical:
            print(f"  ❌ {limit['name']}")
            print(f"     {limit['used']:,} / {limit['max']:,} ({limit['used_pct']:.1f}%)")
            print(f"     Remaining: {limit['remaining']:,}")

    # Warning Limits
    if warning:
        print(f"\n⚠️  WARNING LIMITS ({len(warning)}):")
        print("-" * 70)
        for limit in warning:
            print(f"  ⚠️  {limit['name']}")
            print(f"     {limit['used']:,} / {limit['max']:,} ({limit['used_pct']:.1f}%)")
            print(f"     Remaining: {limit['remaining']:,}")

    # Summary
    print(f"\n📈 SUMMARY:")
    print("-" * 70)
    print(f"  Critical: {len(critical)}")
    print(f"  Warning: {len(warning)}")
    print(f"  OK: {len(ok)}")
    print(f"  Total: {len(critical) + len(warning) + len(ok)}")

    # Key Limits Always Shown
    print(f"\n🔑 KEY LIMITS:")
    print("-" * 70)

    key_limit_names = [
        'DailyApiRequests',
        'DailyAsyncApexExecutions',
        'DataStorageMB',
        'FileStorageMB'
    ]

    all_limits = critical + warning + ok

    for key_name in key_limit_names:
        matching = [l for l in all_limits if key_name in l['name']]
        if matching:
            limit = matching[0]
            status = "❌" if limit['used_pct'] >= 90 else "⚠️ " if limit['used_pct'] >= threshold else "✅"
            print(f"  {status} {limit['name']}")
            print(f"     {limit['used']:,} / {limit['max']:,} ({limit['used_pct']:.1f}%)")

    # Recommendations
    if critical or warning:
        print(f"\n💡 RECOMMENDATIONS:")
        print("-" * 70)

        if any('API' in l['name'] for l in critical + warning):
            print("  • Review API integrations and reduce callout frequency")
            print("  • Implement caching to reduce API calls")
            print("  • Use bulk API instead of REST API where possible")

        if any('Storage' in l['name'] for l in critical + warning):
            print("  • Archive old records")
            print("  • Remove unused files and attachments")
            print("  • Consider purchasing additional storage")

        if any('Async' in l['name'] for l in critical + warning):
            print("  • Reduce frequency of batch/scheduled jobs")
            print("  • Optimize batch sizes")

    print("=" * 70)

    # Return status code
    if critical:
        return 2  # Critical
    elif warning:
        return 1  # Warning
    else:
        return 0  # OK


def export_limits_history(org_alias, limits):
    """Export limits to CSV for historical tracking."""
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = f"./limits-history-{org_alias}-{timestamp}.json"

    data = {
        'timestamp': timestamp,
        'org': org_alias,
        'limits': limits
    }

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    print(f"\n💾 Exported limits history to: {filename}")


def main():
    """Main execution."""
    if len(sys.argv) < 2:
        print("Usage: org_limits_monitor.py <org-alias> [--alert-threshold N]")
        print("")
        print("Monitor Salesforce org limits and send alerts.")
        print("")
        print("Examples:")
        print("  ./org_limits_monitor.py my-org")
        print("  ./org_limits_monitor.py production --alert-threshold 75")
        print("")
        print("Options:")
        print("  --alert-threshold N   Alert when usage exceeds N% (default: 80)")
        print("  --export              Export limits history to JSON file")
        print("")
        sys.exit(1)

    org_alias = sys.argv[1]
    threshold = 80
    export = False

    # Parse options
    if '--alert-threshold' in sys.argv:
        idx = sys.argv.index('--alert-threshold')
        if idx + 1 < len(sys.argv):
            threshold = int(sys.argv[idx + 1])

    if '--export' in sys.argv:
        export = True

    print(f"🔍 Monitoring limits for {org_alias}...\n")

    # Get limits
    limits = get_org_limits(org_alias)

    if not limits:
        print("Error: Could not retrieve org limits")
        sys.exit(1)

    # Analyze
    critical, warning, ok = analyze_limits(limits, threshold)

    # Display report
    status_code = format_report(org_alias, critical, warning, ok, threshold)

    # Export if requested
    if export:
        export_limits_history(org_alias, limits)

    print("")

    sys.exit(status_code)


if __name__ == "__main__":
    main()
