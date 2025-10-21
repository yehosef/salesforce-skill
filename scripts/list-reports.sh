#!/bin/bash
# List all reports and runs for a tool
# Usage: ./list-reports.sh                    (all tools)
#        ./list-reports.sh org-comparison    (specific tool)

TOOL=${1:-}

# Find project root
PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
REPORTS_DIR="$PROJECT_ROOT/.claude/reports"

if [[ ! -d "$REPORTS_DIR" ]]; then
    echo "❌ No reports directory found"
    exit 1
fi

# If tool specified, show only that tool
if [[ -n "$TOOL" ]]; then
    if [[ ! -d "$REPORTS_DIR/$TOOL/runs" ]]; then
        echo "❌ No runs found for: $TOOL"
        exit 1
    fi

    echo "📋 Reports for: $TOOL"
    echo ""

    for run in $(ls -r "$REPORTS_DIR/$TOOL/runs" 2>/dev/null | grep -v "^latest$"); do
        local metadata_file="$REPORTS_DIR/$TOOL/runs/$run/metadata.json"
        if [[ -f "$metadata_file" ]]; then
            local status=$(jq -r '.status // "unknown"' "$metadata_file" 2>/dev/null)
            local timestamp=$(jq -r '.timestamp // "unknown"' "$metadata_file" 2>/dev/null)

            # Status emoji
            local emoji="✅"
            [[ "$status" == "warning" ]] && emoji="⚠️"
            [[ "$status" == "error" ]] && emoji="❌"

            echo "$emoji $run ($status)"
            echo "   Timestamp: $timestamp"
            echo "   View: cat $REPORTS_DIR/$TOOL/runs/$run/report.md"
            echo ""
        fi
    done
else
    # Show all tools and their latest runs
    echo "📊 All Reports"
    echo ""

    for tool_dir in "$REPORTS_DIR"/*; do
        [[ ! -d "$tool_dir" ]] && continue

        local tool_name=$(basename "$tool_dir")
        local latest_link="$tool_dir/runs/latest"

        if [[ -L "$latest_link" ]]; then
            local latest_run=$(readlink "$latest_link")
            local metadata_file="$tool_dir/runs/$latest_run/metadata.json"

            if [[ -f "$metadata_file" ]]; then
                local status=$(jq -r '.status // "unknown"' "$metadata_file" 2>/dev/null)
                local emoji="✅"
                [[ "$status" == "warning" ]] && emoji="⚠️"
                [[ "$status" == "error" ]] && emoji="❌"

                echo "$emoji $tool_name"
                echo "   Latest: $latest_run ($status)"
                echo "   View: ./scripts/view-latest-report.sh $tool_name"
                echo "   List: ./scripts/list-reports.sh $tool_name"
                echo ""
            fi
        fi
    done
fi
