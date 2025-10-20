#!/bin/bash
# Find slow SOQL queries in Salesforce debug logs
# Searches for queries that exceed a specified execution time threshold

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

if [ $# -lt 2 ]; then
    echo "Usage: find_slow_queries.sh <log-directory> <threshold-ms>"
    echo ""
    echo "Finds SOQL queries that took longer than threshold milliseconds."
    echo ""
    echo "Examples:"
    echo "  find_slow_queries.sh ./logs 1000     # Find queries > 1 second"
    echo "  find_slow_queries.sh ./debug 500     # Find queries > 500ms"
    echo ""
    echo "How to get debug logs:"
    echo "  1. Developer Console → Debug → Change Log Levels"
    echo "  2. Set Database = FINEST"
    echo "  3. Run your code"
    echo "  4. Debug → View Log → Download logs to a directory"
    echo ""
    exit 1
fi

LOG_DIR=$1
THRESHOLD=$2

echo -e "${BLUE}🔍 Finding Slow SOQL Queries${NC}"
echo "======================================================================"
echo "Directory: $LOG_DIR"
echo "Threshold: ${THRESHOLD}ms"
echo "======================================================================"

if [ ! -d "$LOG_DIR" ]; then
    echo -e "${RED}Error: Directory not found: $LOG_DIR${NC}"
    exit 1
fi

# Count total log files
LOG_COUNT=$(find "$LOG_DIR" -type f \( -name "*.log" -o -name "*.txt" \) | wc -l | tr -d ' ')

if [ "$LOG_COUNT" -eq 0 ]; then
    echo -e "${YELLOW}⚠️  No log files found in $LOG_DIR${NC}"
    echo "   Looking for *.log or *.txt files"
    exit 1
fi

echo -e "\n${GREEN}Found $LOG_COUNT log file(s)${NC}"
echo ""

# Temporary file for results
TEMP_FILE=$(mktemp)

# Search for slow queries in all log files
find "$LOG_DIR" -type f \( -name "*.log" -o -name "*.txt" \) | while read -r log_file; do
    echo -e "${BLUE}Analyzing: $(basename "$log_file")${NC}"

    # Extract SOQL queries with execution time
    # Format: SOQL_EXECUTE_BEGIN|SOQL_EXECUTE_END
    # Look for patterns like: Number of rows: X  Execution time: YYY ms

    grep -n "SOQL_EXECUTE_BEGIN" "$log_file" | while IFS=: read -r line_num content; do
        # Get the query
        query=$(echo "$content" | sed -n 's/.*\[\(.*\)\].*/\1/p')

        # Look ahead for execution time in next few lines
        exec_time=""
        tail -n +$line_num "$log_file" | head -n 20 | grep "SOQL_EXECUTE_END" | while read -r end_line; do
            # Try to extract execution time (format varies)
            exec_time=$(echo "$end_line" | grep -oP 'Rows:\s*\d+\s*Execution time:\s*\K\d+(?=\s*ms)' || echo "")

            if [ -z "$exec_time" ]; then
                # Try alternative format
                exec_time=$(echo "$end_line" | grep -oP '\d+(?=\s*ms)' || echo "")
            fi

            if [ -n "$exec_time" ] && [ "$exec_time" -gt "$THRESHOLD" ]; then
                echo "$log_file|$line_num|$exec_time|$query" >> "$TEMP_FILE"
            fi
        done
    done
done

# Check if any slow queries were found
if [ ! -s "$TEMP_FILE" ]; then
    echo -e "\n${GREEN}✅ No slow queries found!${NC}"
    echo "   All queries executed in less than ${THRESHOLD}ms"
    rm "$TEMP_FILE"
    exit 0
fi

# Sort by execution time (descending)
sort -t'|' -k3 -rn "$TEMP_FILE" > "${TEMP_FILE}.sorted"

echo ""
echo "======================================================================"
echo -e "${RED}🐌 SLOW QUERIES FOUND${NC}"
echo "======================================================================"

count=0
while IFS='|' read -r file line exec_time query; do
    count=$((count + 1))
    echo ""
    echo -e "${YELLOW}[$count] ${exec_time}ms${NC} - $(basename "$file"):$line"
    echo "   Query: ${query:0:100}..."
done < "${TEMP_FILE}.sorted"

total=$(wc -l < "${TEMP_FILE}.sorted" | tr -d ' ')

echo ""
echo "======================================================================"
echo -e "${RED}📊 SUMMARY${NC}"
echo "======================================================================"
echo "  Total Slow Queries: $total"
echo "  Threshold: ${THRESHOLD}ms"
echo ""
echo -e "${BLUE}💡 Recommendations:${NC}"
echo "  1. Review queries above for optimization opportunities"
echo "  2. Check if queries use indexed fields (Id, Name, OwnerId, etc.)"
echo "  3. Ensure queries have selective WHERE clauses (<10% of records)"
echo "  4. Consider adding LIMIT clauses to prevent large result sets"
echo "  5. Use query plan tool: Developer Console → Query Plan"
echo ""
echo "  See references/performance-tuning.md for optimization strategies"
echo "======================================================================"

# Cleanup
rm "$TEMP_FILE" "${TEMP_FILE}.sorted"
