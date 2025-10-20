#!/usr/bin/env python3
"""Run Apex tests and format results."""
import sys
import json
import subprocess
from typing import Dict, Any, List

def run_tests(class_name: str, org: str) -> Dict[str, Any]:
    """Execute Apex tests via sf CLI."""
    cmd = ["sf", "apex", "test", "run", "-n", class_name, "-o", org, "-c", "--json", "--wait", "10"]

    print(f"Running tests for: {class_name}")
    print(f"Target org: {org}")
    print("Please wait...\n")

    result = subprocess.run(cmd, capture_output=True, text=True)

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}", file=sys.stderr)
        print(f"Raw output: {result.stdout}", file=sys.stderr)
        sys.exit(1)

def format_results(data: Dict[str, Any]) -> str:
    """Format test results as readable markdown."""
    result = data.get("result", {})
    summary = result.get("summary", {})

    outcome = summary.get('outcome', 'Unknown')
    outcome_emoji = "✅" if outcome == "Passed" else "❌" if outcome == "Failed" else "⚠️"

    output = f"""
## {outcome_emoji} Test Results

**Outcome:** {outcome}
**Tests Run:** {summary.get('testsRan', 0)}
**Passed:** {summary.get('passing', 0)}
**Failed:** {summary.get('failing', 0)}
**Skipped:** {summary.get('skipped', 0)}

"""

    # Code coverage
    coverage_pct = summary.get('testRunCoverage', 'N/A')
    if coverage_pct != 'N/A':
        coverage_val = float(coverage_pct.replace('%', ''))
        coverage_emoji = "✅" if coverage_val >= 75 else "⚠️" if coverage_val >= 50 else "❌"
        output += f"**Coverage:** {coverage_emoji} {coverage_pct}\n\n"
    else:
        output += f"**Coverage:** N/A\n\n"

    # Show test details
    tests = result.get("tests", [])

    if tests:
        output += "### Test Details\n\n"
        output += "| Test Method | Outcome | Time (ms) |\n"
        output += "|-------------|---------|--------|\n"

        for test in tests:
            method_name = test.get('MethodName', 'Unknown')
            test_outcome = test.get('Outcome', 'Unknown')
            run_time = test.get('RunTime', 0)
            outcome_symbol = "✅" if test_outcome == "Pass" else "❌" if test_outcome == "Fail" else "⚠️"

            output += f"| {method_name} | {outcome_symbol} {test_outcome} | {run_time} |\n"

        output += "\n"

    # Show failures
    failures = [t for t in tests if t.get("Outcome") == "Fail"]

    if failures:
        output += "### ❌ Failures\n\n"
        for i, test in enumerate(failures, 1):
            output += f"**{i}. {test.get('MethodName')}**\n\n"
            message = test.get('Message', 'No message')
            stack_trace = test.get('StackTrace', '')

            output += f"```\n{message}\n"
            if stack_trace:
                output += f"\n{stack_trace}\n"
            output += "```\n\n"

    # Show coverage details
    coverage = result.get("codecoverage", [])
    if coverage:
        output += "### Code Coverage Details\n\n"
        output += "| Class/Trigger | Coverage | Lines |\n"
        output += "|---------------|----------|-------|\n"

        for cov in coverage:
            name = cov.get('name', 'Unknown')
            covered = cov.get('numLinesCovered', 0)
            uncovered = cov.get('numLinesUncovered', 0)
            total = covered + uncovered

            if total > 0:
                pct = (covered / total) * 100
                pct_emoji = "✅" if pct >= 75 else "⚠️" if pct >= 50 else "❌"
                output += f"| {name} | {pct_emoji} {pct:.1f}% | {covered}/{total} |\n"

    return output

def main():
    if len(sys.argv) < 3:
        print("Usage: run_tests.py <class-name> <org-alias>")
        print()
        print("Examples:")
        print("  run_tests.py MyClassTest sandbox")
        print("  run_tests.py \"MyClassTest, AnotherTest\" production")
        sys.exit(1)

    class_name = sys.argv[1]
    org = sys.argv[2]

    result = run_tests(class_name, org)

    # Check if command succeeded
    status = result.get("status", 1)
    if status != 0:
        error_msg = result.get("message", "Unknown error")
        print(f"Error running tests: {error_msg}", file=sys.stderr)
        sys.exit(1)

    # Format and print results
    formatted = format_results(result)
    print(formatted)

    # Exit with appropriate code
    outcome = result.get("result", {}).get("summary", {}).get("outcome", "Unknown")
    sys.exit(0 if outcome == "Passed" else 1)

if __name__ == "__main__":
    main()
