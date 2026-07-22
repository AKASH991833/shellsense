#!/usr/bin/env bash
#
# ShellSense AI - Installer
#
# This script installs ShellSense AI on supported Linux distributions.
#
# Usage:
#   bash installer/install.sh
#
set -euo pipefail

VERSION="0.1.0"
PROJECT_NAME="shellsense"
INSTALL_DIR="${INSTALL_DIR:-/opt/shellsense}"
VENV_DIR="${INSTALL_DIR}/venv"
BIN_LINK="/usr/local/bin/ss"

COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[1;33m'
COLOR_RED='\033[0;31m'
COLOR_CYAN='\033[0;36m'
COLOR_RESET='\033[0m'

log_info() { echo -e "${COLOR_GREEN}[INFO]${COLOR_RESET} $1"; }
log_warn() { echo -e "${COLOR_YELLOW}[WARN]${COLOR_RESET} $1"; }
log_error() { echo -e "${COLOR_RED}[ERROR]${COLOR_RESET} $1"; }
log_step() { echo -e "${COLOR_CYAN}[STEP]${COLOR_RESET} $1"; }

# Check if running as root
check_root() {
    if [ "$(id -u)" -ne 0 ]; then
        log_error "This installer must be run as root (sudo)."
        echo "  sudo bash installer/install.sh"
        exit 1
    fi
}

# Check Python version
check_python() {
    if command -v python3 &>/dev/null; then
        PYTHON=$(command -v python3)
    else
        log_error "Python 3 is not installed."
        echo "  Install Python 3.12+ first:"
        echo "    Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
        echo "    Fedora:        sudo dnf install python3 python3-pip"
        echo "    Arch:          sudo pacman -S python python-pip"
        exit 1
    fi

    PYTHON_VERSION=$($PYTHON --version 2>&1 | awk '{print $2}')
    PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
    PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

    if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 12 ]; }; then
        log_error "Python 3.12+ required (found: $PYTHON_VERSION)."
        exit 1
    fi
    log_info "Python $PYTHON_VERSION found at $PYTHON"
}

# Detect distribution and install system dependencies
install_deps() {
    log_step "Installing system dependencies..."

    if command -v apt &>/dev/null; then
        apt update -qq
        apt install -y -qq python3 python3-pip python3-venv git
    elif command -v dnf &>/dev/null; then
        dnf install -y python3 python3-pip git
    elif command -v pacman &>/dev/null; then
        pacman -Sy --noconfirm python python-pip git
    elif command -v zypper &>/dev/null; then
        zypper install -y python3 python3-pip git
    else
        log_warn "Unsupported package manager. Ensure Python 3.12+ and pip are installed."
    fi

    log_info "System dependencies installed."
}

# Clone or copy project files
install_project() {
    log_step "Installing ShellSense AI..."

    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

    if [ -d "$INSTALL_DIR" ]; then
        log_warn "Install directory $INSTALL_DIR already exists."
        echo "  Backing up to ${INSTALL_DIR}.bak"
        rm -rf "${INSTALL_DIR}.bak"
        mv "$INSTALL_DIR" "${INSTALL_DIR}.bak"
    fi

    mkdir -p "$INSTALL_DIR"
    cp -r "$SCRIPT_DIR/"* "$INSTALL_DIR/"
    chown -R root:root "$INSTALL_DIR"

    log_info "Project files copied to $INSTALL_DIR"
}

# Create virtual environment and install package
setup_venv() {
    log_step "Setting up Python virtual environment..."

    $PYTHON -m venv "$VENV_DIR"
    source "${VENV_DIR}/bin/activate"

    pip install --upgrade pip -q
    pip install "$INSTALL_DIR" -q

    log_info "Virtual environment created at $VENV_DIR"
}

# Create symlink
create_symlink() {
    log_step "Creating symlink..."

    if [ -L "$BIN_LINK" ] || [ -f "$BIN_LINK" ]; then
        rm -f "$BIN_LINK"
    fi

    ln -sf "${VENV_DIR}/bin/ss" "$BIN_LINK"
    log_info "Symlink created: $BIN_LINK -> ${VENV_DIR}/bin/ss"
}

# Verify installation
verify() {
    log_step "Verifying installation..."

    if command -v ss &>/dev/null; then
        log_info "ShellSense AI $(ss --version 2>&1) installed successfully!"
    else
        log_error "Installation failed: 'ss' command not found."
        exit 1
    fi
}

print_summary() {
    echo ""
    echo "============================================"
    echo "  ShellSense AI v${VERSION} - Installed!"
    echo "============================================"
    echo ""
    echo "  Run: ss --help"
    echo "  Run: ss doctor"
    echo ""
    echo "  Install dir: $INSTALL_DIR"
    echo "  Binary:      $BIN_LINK"
    echo ""
}

main() {
    echo ""
    echo "============================================"
    echo "  ShellSense AI v${VERSION} Installer"
    echo "============================================"
    echo ""

    check_root
    check_python
    install_deps
    install_project
    setup_venv
    create_symlink
    verify
    print_summary
}

main
