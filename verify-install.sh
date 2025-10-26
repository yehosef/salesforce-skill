#!/bin/bash
# Verify Installation Script
#
# Checks that all required dependencies are installed and accessible.
# Use this to troubleshoot installation issues.
#
# Usage:
#   ./verify-install.sh [--verbose]

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

VERBOSE=false
ERRORS=0
WARNINGS=0

# Parse arguments
for arg in "$@"; do
    case $arg in
        --verbose)
            VERBOSE=true
            ;;
        --help)
            echo "Usage: $0 [--verbose]"
            echo ""
            echo "Verifies that all dependencies are correctly installed."
            exit 0
            ;;
    esac
done

print_header() {
    echo -e "${BLUE}===================================================${NC}"
    echo -e "${BLUE}  Salesforce Skill - Installation Verification${NC}"
    echo -e "${BLUE}===================================================${NC}"
    echo ""
}

check_command() {
    local cmd=$1
    local required=${2:-false}

    if command -v "$cmd" &> /dev/null; then
        echo -e "${GREEN}✓${NC} $cmd"

        if [ "$VERBOSE" = true ]; then
            local version
            case $cmd in
                sf)
                    version=$(sf --version 2>/dev/null | head -1)
                    echo "  └─ $version"
                    ;;
                python3)
                    version=$(python3 --version 2>/dev/null)
                    echo "  └─ $version"
                    ;;
                *)
                    version=$($cmd --version 2>/dev/null | head -1 || echo "version unknown")
                    echo "  └─ $version"
                    ;;
            esac
        fi
        return 0
    else
        if [ "$required" = true ]; then
            echo -e "${RED}✗${NC} $cmd (REQUIRED)"
            ((ERRORS++))
        else
            echo -e "${YELLOW}⚠${NC} $cmd (optional)"
            ((WARNINGS++))
        fi
        return 1
    fi
}

check_python_version() {
    if command -v python3 &> /dev/null; then
        local version
        version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        local major minor
        major=$(echo "$version" | cut -d. -f1)
        minor=$(echo "$version" | cut -d. -f2)

        if [ "$major" -ge 3 ] && [ "$minor" -ge 8 ]; then
            echo -e "${GREEN}✓${NC} Python version $version (>= 3.8 required)"
        else
            echo -e "${RED}✗${NC} Python version $version (3.8+ required)"
            ((ERRORS++))
        fi
    fi
}

check_sf_auth() {
    if command -v sf &> /dev/null; then
        local org_count
        org_count=$(sf org list --json 2>/dev/null | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('result', {}).get('nonScratchOrgs', [])))" 2>/dev/null || echo "0")

        if [ "$org_count" -gt 0 ]; then
            echo -e "${GREEN}✓${NC} Salesforce authentication ($org_count org(s) connected)"
        else
            echo -e "${YELLOW}⚠${NC} No Salesforce orgs authenticated"
            echo "  └─ Run: sf org login web -a my-org"
            ((WARNINGS++))
        fi
    fi
}

check_file_structure() {
    local base_dir="${1:-.}"

    echo ""
    echo "Checking file structure..."

    local required_dirs=("scripts" "references" "assets" "lib")
    local required_files=("SKILL.md" "README.md")

    for dir in "${required_dirs[@]}"; do
        if [ -d "${base_dir}/${dir}" ]; then
            echo -e "${GREEN}✓${NC} ${dir}/"
        else
            echo -e "${RED}✗${NC} ${dir}/ (missing)"
            ((ERRORS++))
        fi
    done

    for file in "${required_files[@]}"; do
        if [ -f "${base_dir}/${file}" ]; then
            echo -e "${GREEN}✓${NC} ${file}"
        else
            echo -e "${RED}✗${NC} ${file} (missing)"
            ((ERRORS++))
        fi
    done
}

check_script_permissions() {
    local base_dir="${1:-.}"

    echo ""
    echo "Checking script permissions..."

    local script_errors=0

    if [ -d "${base_dir}/scripts" ]; then
        for script in "${base_dir}"/scripts/*.py "${base_dir}"/scripts/*.sh; do
            if [ -f "$script" ]; then
                if [ -x "$script" ]; then
                    [ "$VERBOSE" = true ] && echo -e "${GREEN}✓${NC} $(basename "$script") is executable"
                else
                    echo -e "${YELLOW}⚠${NC} $(basename "$script") is not executable"
                    ((script_errors++))
                fi
            fi
        done

        if [ $script_errors -eq 0 ]; then
            echo -e "${GREEN}✓${NC} All scripts are executable"
        else
            echo -e "${YELLOW}⚠${NC} $script_errors script(s) are not executable"
            echo "  └─ Run: chmod +x ${base_dir}/scripts/*.py ${base_dir}/scripts/*.sh"
            ((WARNINGS++))
        fi
    fi
}

main() {
    print_header

    echo "Checking required dependencies..."
    check_command "sf" true
    check_command "python3" true
    check_command "bash" true

    echo ""
    echo "Checking optional dependencies..."
    check_command "jq" false
    check_command "git" false
    check_command "npm" false
    check_command "node" false

    echo ""
    check_python_version

    echo ""
    check_sf_auth

    # Check if installed in ~/.claude/skills
    if [ -d "${HOME}/.claude/skills/salesforce-dev" ]; then
        check_file_structure "${HOME}/.claude/skills/salesforce-dev"
        check_script_permissions "${HOME}/.claude/skills/salesforce-dev"
    else
        # Check current directory
        check_file_structure "."
        check_script_permissions "."
    fi

    echo ""
    echo -e "${BLUE}===================================================${NC}"

    if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
        echo -e "${GREEN}  All checks passed! ✓${NC}"
    elif [ $ERRORS -eq 0 ]; then
        echo -e "${YELLOW}  Passed with $WARNINGS warning(s) ⚠${NC}"
    else
        echo -e "${RED}  Failed with $ERRORS error(s) and $WARNINGS warning(s) ✗${NC}"
    fi

    echo -e "${BLUE}===================================================${NC}"
    echo ""

    if [ $ERRORS -gt 0 ]; then
        echo "Please fix the errors above and run this script again."
        exit 1
    elif [ $WARNINGS -gt 0 ]; then
        echo "The skill should work, but some features may be limited."
        exit 0
    else
        echo "Your installation is ready to use!"
        exit 0
    fi
}

main "$@"
