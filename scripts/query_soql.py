#!/usr/bin/env python3
"""Execute SOQL query and format results as markdown table."""
import sys
import json
import subprocess
from typing import List, Dict, Any

def run_soql(query: str, org: str = None) -> Dict[str, Any]:
    """Execute SOQL query via sf CLI."""
    cmd = ["sf", "data", "query", "-q", query, "--json"]
    if org:
        cmd.extend(["-o", org])

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error executing query: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}", file=sys.stderr)
        print(f"Raw output: {result.stdout}", file=sys.stderr)
        sys.exit(1)

def flatten_record(record: Dict[str, Any], parent_key: str = '') -> Dict[str, Any]:
    """Flatten nested relationship fields."""
    flattened = {}

    for key, value in record.items():
        if key == 'attributes':
            continue

        new_key = f"{parent_key}.{key}" if parent_key else key

        if isinstance(value, dict) and 'attributes' in value:
            # This is a relationship field
            flattened.update(flatten_record(value, new_key))
        elif isinstance(value, list):
            # Subquery results - skip for table format
            continue
        else:
            flattened[new_key] = value

    return flattened

def format_table(records: List[Dict[str, Any]]) -> str:
    """Format query results as markdown table."""
    if not records:
        return "No results found."

    # Flatten all records
    flattened_records = [flatten_record(rec) for rec in records]

    # Get all unique headers
    headers = []
    for rec in flattened_records:
        for key in rec.keys():
            if key not in headers:
                headers.append(key)

    # Build table
    table = "| " + " | ".join(headers) + " |\n"
    table += "| " + " | ".join(["---"] * len(headers)) + " |\n"

    for record in flattened_records:
        row_values = []
        for header in headers:
            value = record.get(header, "")
            # Convert None to empty string
            if value is None:
                value = ""
            # Truncate long strings
            value_str = str(value)
            if len(value_str) > 50:
                value_str = value_str[:47] + "..."
            row_values.append(value_str)

        table += "| " + " | ".join(row_values) + " |\n"

    return table

def main():
    if len(sys.argv) < 2:
        print("Usage: query_soql.py '<SOQL>' [org-alias]")
        print()
        print("Examples:")
        print("  query_soql.py 'SELECT Id, Name FROM Account LIMIT 5' sandbox")
        print("  query_soql.py 'SELECT Id, Amount FROM Opportunity WHERE Amount > 1000'")
        sys.exit(1)

    query = sys.argv[1]
    org = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"Executing query: {query}")
    if org:
        print(f"Target org: {org}")
    print()

    result = run_soql(query, org)

    # Extract records from result
    records = result.get("result", {}).get("records", [])

    if not records:
        print("No results found.")
        return

    # Print table
    print(format_table(records))
    print()
    print(f"**Total:** {len(records)} record(s)")

    # Show total size if available
    total_size = result.get("result", {}).get("totalSize")
    if total_size and total_size != len(records):
        print(f"**Note:** Query returned {total_size} total records, showing {len(records)}")

if __name__ == "__main__":
    main()
