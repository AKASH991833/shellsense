#!/usr/bin/env bash
set -euo pipefail

REPO="shellsense-ai/shellsense"
VERSION="1.0.0"
INSTALL_DIR="${INSTALL_DIR:-$HOME/.shellsense}"
BIN_DIR="${BIN_DIR:-$HOME/.local/bin}"

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${CYAN}╭──────────────────────────────────────────╮${NC}"
echo -e "${CYAN}│      ShellSense AI - One-Click Install    │${NC}"
echo -e "${CYAN}│      Think Less. Command More.            │${NC}"
echo -e "${CYAN}╰──────────────────────────────────────────╯${NC}"
echo ""

# Detect OS
OS="$(uname -s)"
if [[ "$OS" != "Linux" ]]; then
    echo -e "${YELLOW}Warning: Only Linux is fully supported. Continuing anyway...${NC}"
fi

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "Error: Python 3.12+ is required. Install it first."
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "  Fedora: sudo dnf install python3 python3-pip"
    echo "  Arch: sudo pacman -S python python-pip"
    exit 1
fi

PY_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
if [[ "$(echo "$PY_VERSION >= 3.12" | bc 2>/dev/null || echo "0")" == "0" ]]; then
    if [[ "$(python3 -c "import sys; print(sys.version_info.major)" 2>/dev/null)" == "3" ]]; then
        MINOR=$(python3 -c "import sys; print(sys.version_info.minor)" 2>/dev/null)
        if [[ "$MINOR" -lt 12 ]]; then
            echo "Error: Python 3.12+ required (found $PY_VERSION)"
            exit 1
        fi
    else
        echo "Error: Python 3.12+ required (found $PY_VERSION)"
        exit 1
    fi
fi

echo -e "${GREEN}✓${NC} Python $PY_VERSION detected"

# Install from PyPI or source
echo ""
echo -e "${CYAN}Installing ShellSense AI v${VERSION}...${NC}"

if python3 -m pip install shellsense --break-system-packages 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Installed from PyPI"
elif python3 -m pip install shellsense --user 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Installed from PyPI (user)"
elif [[ -f dist/shellsense-${VERSION}-py3-none-any.whl ]]; then
    python3 -m pip install "dist/shellsense-${VERSION}-py3-none-any.whl" --break-system-packages 2>/dev/null || \
    python3 -m pip install "dist/shellsense-${VERSION}-py3-none-any.whl" --user 2>/dev/null
    echo -e "${GREEN}✓${NC} Installed from local wheel"
else
    echo "Error: Could not install ShellSense. Try manual install:"
    echo "  pip install shellsense"
    exit 1
fi

# Ensure bin dir is in PATH
mkdir -p "$BIN_DIR"
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo ""
    echo -e "${YELLOW}Add to your shell config:${NC}"
    echo "  echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.bashrc"
fi

# Verify installation
if command -v ss &>/dev/null; then
    echo -e "${GREEN}✓${NC} ShellSense is installed!"
    echo ""
    echo -e "  Version: $(ss --version 2>/dev/null || ss version 2>/dev/null || echo '1.0.0')"
    echo ""
    echo -e "${CYAN}Quick Start:${NC}"
    echo "  1. ${GREEN}ss daemon start${NC}           # Start background daemon"
    echo "  2. ${GREEN}ss discover scan --max 100${NC} # Discover commands from system"
    echo "  3. ${GREEN}ss doctor${NC}                  # Run diagnostics"
    echo ""
    echo -e "${CYAN}Shell Integration (auto-suggestions):${NC}"
    echo "  ${GREEN}ss install${NC}                    # Install shell hooks"
    echo "  Then restart your terminal or run: exec bash"
    echo ""
    echo -e "${CYAN}Examples:${NC}"
    echo "  ss search 'find large files'   # Search commands"
    echo "  ss explain tar                  # Explain a command"
    echo "  ss suggest 'git com'           # Auto-suggest"
    echo ""
    echo -e "${GREEN}ShellSense AI is ready! Happy commanding!${NC}"
else
    echo -e "${YELLOW}Installation complete but 'ss' command not found in PATH.${NC}"
    echo "  Add to ~/.bashrc: export PATH=\"\$HOME/.local/bin:\$PATH\""
fi
