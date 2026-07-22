#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo "=== ShellSense AI - Development Setup ==="
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "[+] Python version: $PYTHON_VERSION"

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "[+] Creating virtual environment..."
    python3 -m venv .venv
else
    echo "[+] Virtual environment already exists"
fi

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip
echo "[+] Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "[+] Installing development dependencies..."
pip install -r requirements-dev.txt

# Install package in editable mode
echo "[+] Installing ShellSense AI in editable mode..."
pip install -e .

# Verify installation
echo ""
echo "[+] Verifying installation..."
if python -m shellsense version 2>/dev/null; then
    echo ""
    echo "[✓] ShellSense AI installed successfully!"
    echo ""
    echo "Run 'ss --help' to get started."
    echo "Run 'ss doctor' to verify the system."
else
    echo "[!] Installation verification failed"
    exit 1
fi
