#!/bin/bash
# Report Manager Library
# Standardized report generation and management for Salesforce tools
# Source this in any script that generates reports

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Initialize a new report run
# Usage: create_report_run "tool-name" '{"key": "value"}'
create_report_run() {
    local tool_name=$1
    local metadata=$2

    # Validate inputs
    if [[ -z "$tool_name" ]]; then
        echo -e "${RED}Error: tool_name required${NC}" >&2
        return 1
    fi

    # Determine project root (.claude/reports should be at project root)
    local project_root=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
    local reports_dir="$project_root/.claude/reports"

    # Create run ID (sortable, filesystem-safe: YYYY-MM-DD-HHMM)
    local run_id=$(date +%Y-%m-%d-%H%M)
    local run_dir="$reports_dir/$tool_name/runs/$run_id"

    # Create directory structure
    mkdir -p "$run_dir"/{diffs,artifacts,logs}

    # Save metadata with timestamp
    local timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    local metadata_with_ts=$(echo "$metadata" | jq --arg ts "$timestamp" '.timestamp = $ts')
    echo "$metadata_with_ts" | jq '.' > "$run_dir/metadata.json"

    # Export for use in calling script
    export REPORT_RUN_DIR="$run_dir"
    export REPORT_RUN_ID="$run_id"
    export REPORT_TOOL_NAME="$tool_name"
    export REPORT_PROJECT_ROOT="$project_root"

    echo "$run_dir"
}

# Finalize a report run and update indices
# Usage: finalize_report "tool-name" "success" "Optional message"
finalize_report() {
    local tool_name=$1
    local status=${2:-"success"}  # success, warning, error
    local message=${3:-""}

    if [[ -z "$REPORT_RUN_DIR" ]] || [[ -z "$REPORT_RUN_ID" ]]; then
        echo -e "${RED}Error: Must call create_report_run first${NC}" >&2
        return 1
    fi

    local project_root="${REPORT_PROJECT_ROOT:-.}"
    local reports_dir="$project_root/.claude/reports"

    # Update status in metadata
    jq --arg status "$status" --arg msg "$message" \
        '.status = $status | .message = $msg' \
        "$REPORT_RUN_DIR/metadata.json" > "$REPORT_RUN_DIR/metadata.json.tmp" && \
        mv "$REPORT_RUN_DIR/metadata.json.tmp" "$REPORT_RUN_DIR/metadata.json"

    # Update 'latest' symlink
    local latest_link="$reports_dir/$tool_name/runs/latest"
    mkdir -p "$(dirname "$latest_link")"
    ln -sfn "$REPORT_RUN_ID" "$latest_link"

    # Update INDEX.md
    update_report_index "$project_root"

    # Status emoji
    local emoji="✅"
    [[ "$status" == "warning" ]] && emoji="⚠️"
    [[ "$status" == "error" ]] && emoji="❌"

    echo -e "${GREEN}${emoji} Report finalized${NC}"
    echo -e "Location: ${BLUE}$REPORT_RUN_DIR${NC}"
    echo -e "Latest symlink: ${BLUE}$latest_link${NC}"
    echo -e "View: ${BLUE}cat $latest_link/report.md${NC}"
}

# Update the main INDEX.md with all tools and latest runs
# Usage: update_report_index "/path/to/project"
update_report_index() {
    local project_root=${1:-.}
    local reports_dir="$project_root/.claude/reports"
    local index_file="$reports_dir/INDEX.md"

    # Create index header
    cat > "$index_file" <<'HEADER'
# Reports Index

Last Updated: $(date)

## Quick Links to Latest Reports

HEADER

    # Add each tool's latest report
    if [[ -d "$reports_dir" ]]; then
        for tool_dir in "$reports_dir"/*; do
            [[ ! -d "$tool_dir" ]] && continue
            [[ "$(basename "$tool_dir")" == "INDEX.md" ]] && continue

            local tool_name=$(basename "$tool_dir")
            local latest_link="$tool_dir/runs/latest"

            if [[ -L "$latest_link" ]]; then
                local latest_run=$(readlink "$latest_link")
                local metadata_file="$tool_dir/runs/$latest_run/metadata.json"

                if [[ -f "$metadata_file" ]]; then
                    local status=$(jq -r '.status // "unknown"' "$metadata_file")
                    local timestamp=$(jq -r '.timestamp // "unknown"' "$metadata_file")

                    # Status emoji
                    local emoji="✅"
                    [[ "$status" == "warning" ]] && emoji="⚠️"
                    [[ "$status" == "error" ]] && emoji="❌"

                    cat >> "$index_file" <<EOF

### $emoji $tool_name

- **Latest Run**: \`$latest_run\`
- **Status**: $status
- **Timestamp**: $timestamp
- **View**: [\`$latest_run/report.md\`](./$tool_name/runs/$latest_run/report.md)

EOF
                fi
            fi
        done
    fi

    # Add footer
    cat >> "$index_file" <<'FOOTER'

## All Runs

View all historical runs in their respective directories:

```bash
ls -ltr .claude/reports/org-comparison/runs/
ls -ltr .claude/reports/test-results/runs/
ls -ltr .claude/reports/code-coverage/runs/
```

## Report Structure

Each run contains:
- `report.md` - Human-readable markdown report
- `metadata.json` - Machine-readable metadata
- `diffs/` - Detailed diff files (for comparison tools)
- `artifacts/` - Raw data and supporting files
- `logs/` - Execution logs

FOOTER
}

# Add content to report
# Usage: add_report_section "## Section Title" "content"
add_report_section() {
    local title=$1
    local content=$2

    if [[ -z "$REPORT_RUN_DIR" ]]; then
        echo -e "${RED}Error: Must call create_report_run first${NC}" >&2
        return 1
    fi

    cat >> "$REPORT_RUN_DIR/report.md" <<EOF

$title

$content

EOF
}

# Save a diff file
# Usage: save_diff "filename" "file1" "file2"
save_diff() {
    local filename=$1
    local file1=$2
    local file2=$3

    if [[ -z "$REPORT_RUN_DIR" ]]; then
        echo -e "${RED}Error: Must call create_report_run first${NC}" >&2
        return 1
    fi

    diff -u "$file1" "$file2" > "$REPORT_RUN_DIR/diffs/$filename" || true
}

# Save an artifact
# Usage: save_artifact "filename" "content"
save_artifact() {
    local filename=$1
    local content=$2

    if [[ -z "$REPORT_RUN_DIR" ]]; then
        echo -e "${RED}Error: Must call create_report_run first${NC}" >&2
        return 1
    fi

    echo "$content" > "$REPORT_RUN_DIR/artifacts/$filename"
}

# List all runs for a tool
# Usage: list_tool_runs "org-comparison"
list_tool_runs() {
    local tool_name=$1
    local project_root=${2:-.}
    local runs_dir="$project_root/.claude/reports/$tool_name/runs"

    if [[ ! -d "$runs_dir" ]]; then
        echo -e "${YELLOW}No runs found for $tool_name${NC}"
        return 0
    fi

    echo -e "${BLUE}Runs for $tool_name:${NC}"
    for run in $(ls -r "$runs_dir" | grep -v "^latest$"); do
        local metadata_file="$runs_dir/$run/metadata.json"
        if [[ -f "$metadata_file" ]]; then
            local status=$(jq -r '.status // "unknown"' "$metadata_file")
            local emoji="✅"
            [[ "$status" == "warning" ]] && emoji="⚠️"
            [[ "$status" == "error" ]] && emoji="❌"

            echo "$emoji $run"
        fi
    done
}

# Get latest run directory
# Usage: get_latest_run "org-comparison"
get_latest_run() {
    local tool_name=$1
    local project_root=${2:-.}
    local latest_link="$project_root/.claude/reports/$tool_name/runs/latest"

    if [[ ! -L "$latest_link" ]]; then
        echo -e "${RED}No runs found for $tool_name${NC}" >&2
        return 1
    fi

    echo "$(readlink "$latest_link")"
}

export -f create_report_run
export -f finalize_report
export -f update_report_index
export -f add_report_section
export -f save_diff
export -f save_artifact
export -f list_tool_runs
export -f get_latest_run
