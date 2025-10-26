#!/bin/bash
# Salesforce Skill Installation Script
#
# Automates installation of the Salesforce development skill for Claude Code.
#
# Usage:
#   ./install.sh [--dev]
#
# Options:
#   --dev    Install development dependencies (for contributors)

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SKILL_NAME="salesforce-dev"
INSTALL_DIR="${HOME}/.claude/skills/${SKILL_NAME}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEV_MODE=false

# Parse arguments
for arg in "$@"; do
    case $arg in
        --dev)
            DEV_MODE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [--dev]"
            echo ""
            echo "Options:"
            echo "  --dev    Install development dependencies"
            echo "  --help   Show this help message"
            exit 0
            ;;
    esac
done

# Helper functions
print_header() {
    echo -e "${BLUE}===================================================${NC}"
    echo -e "${BLUE}  Salesforce Skill Installer${NC}"
    echo -e "${BLUE}===================================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

check_command() {
    if command -v "$1" &> /dev/null; then
        print_success "$1 is installed"
        return 0
    else
        print_error "$1 is NOT installed"
        return 1
    fi
}

# Main installation
main() {
    print_header

    echo "Step 1/6: Checking prerequisites..."
    echo ""

    # Check required commands
    MISSING_DEPS=false

    if ! check_command "sf"; then
        print_info "Install Salesforce CLI: npm install -g @salesforce/cli"
        MISSING_DEPS=true
    fi

    if ! check_command "python3"; then
        print_info "Install Python 3.8+: https://www.python.org/downloads/"
        MISSING_DEPS=true
    else
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_info "Python version: ${PYTHON_VERSION}"
    fi

    if ! check_command "bash"; then
        print_error "bash shell is required"
        MISSING_DEPS=true
    fi

    echo ""

    if [ "$MISSING_DEPS" = true ]; then
        print_error "Missing required dependencies. Please install them first."
        exit 1
    fi

    # Check optional commands
    echo "Checking optional dependencies..."
    check_command "jq" || print_warning "jq is recommended for report management scripts"
    check_command "git" || print_warning "git is recommended for version control features"
    echo ""

    # Create installation directory
    echo "Step 2/6: Creating installation directory..."
    mkdir -p "${INSTALL_DIR}"
    print_success "Created ${INSTALL_DIR}"
    echo ""

    # Copy files
    echo "Step 3/6: Copying skill files..."

    # Copy all directories
    for dir in scripts references assets lib; do
        if [ -d "${SCRIPT_DIR}/${dir}" ]; then
            cp -r "${SCRIPT_DIR}/${dir}" "${INSTALL_DIR}/"
            print_success "Copied ${dir}/"
        fi
    done

    # Copy markdown files
    for file in SKILL.md README.md LICENSE CHANGELOG.md CONTRIBUTING.md; do
        if [ -f "${SCRIPT_DIR}/${file}" ]; then
            cp "${SCRIPT_DIR}/${file}" "${INSTALL_DIR}/"
            print_success "Copied ${file}"
        fi
    done

    # Copy config files
    for file in config.example.yaml .gitignore; do
        if [ -f "${SCRIPT_DIR}/${file}" ]; then
            cp "${SCRIPT_DIR}/${file}" "${INSTALL_DIR}/"
            print_success "Copied ${file}"
        fi
    done

    echo ""

    # Make scripts executable
    echo "Step 4/6: Making scripts executable..."
    chmod +x "${INSTALL_DIR}"/scripts/*.py "${INSTALL_DIR}"/scripts/*.sh "${INSTALL_DIR}"/lib/*.sh 2>/dev/null || true
    print_success "Scripts are now executable"
    echo ""

    # Install development dependencies
    if [ "$DEV_MODE" = true ]; then
        echo "Step 5/6: Installing development dependencies..."

        if [ -f "${SCRIPT_DIR}/requirements-dev.txt" ]; then
            python3 -m pip install -r "${SCRIPT_DIR}/requirements-dev.txt"
            print_success "Installed Python development dependencies"
        fi

        if [ -f "${SCRIPT_DIR}/package.json" ] && command -v npm &> /dev/null; then
            cd "${SCRIPT_DIR}"
            npm install --save-dev
            print_success "Installed npm development dependencies"
        fi

        # Install pre-commit hooks
        if command -v pre-commit &> /dev/null; then
            cd "${SCRIPT_DIR}"
            pre-commit install
            print_success "Installed pre-commit hooks"
        fi

        echo ""
    else
        echo "Step 5/6: Skipping development dependencies (use --dev to install)"
        echo ""
    fi

    # Create symlinks for easy access (optional)
    echo "Step 6/6: Creating convenience aliases..."

    # Check if user wants to add to PATH
    echo ""
    read -p "Add skill scripts to your PATH? This will modify your shell profile. (y/N): " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        SHELL_RC=""
        if [ -f "${HOME}/.bashrc" ]; then
            SHELL_RC="${HOME}/.bashrc"
        elif [ -f "${HOME}/.zshrc" ]; then
            SHELL_RC="${HOME}/.zshrc"
        fi

        if [ -n "${SHELL_RC}" ]; then
            echo "" >> "${SHELL_RC}"
            echo "# Salesforce Skill" >> "${SHELL_RC}"
            echo "export PATH=\"\${PATH}:${INSTALL_DIR}/scripts\"" >> "${SHELL_RC}"
            print_success "Added to ${SHELL_RC}"
            print_info "Run: source ${SHELL_RC}"
        fi
    else
        print_info "Skipped PATH modification"
    fi

    echo ""
    echo -e "${GREEN}===================================================${NC}"
    echo -e "${GREEN}  Installation Complete!${NC}"
    echo -e "${GREEN}===================================================${NC}"
    echo ""
    echo "Skill installed to: ${INSTALL_DIR}"
    echo ""
    echo "Next steps:"
    echo "  1. Authenticate to a Salesforce org:"
    echo "     sf org login web -a my-org"
    echo ""
    echo "  2. Try running a query:"
    echo "     ${INSTALL_DIR}/scripts/query_soql.py 'SELECT Id FROM Account LIMIT 5' my-org"
    echo ""
    echo "  3. Explore the skill:"
    echo "     cd ${INSTALL_DIR}"
    echo "     cat SKILL.md"
    echo ""
    echo "For help, see: ${INSTALL_DIR}/README.md"
    echo ""
}

# Run installation
main "$@"
