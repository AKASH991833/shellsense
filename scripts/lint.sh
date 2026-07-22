#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo "=== ShellSense AI - Linting ==="
echo ""

# Run ruff
echo "[+] Running ruff..."
python -m ruff check src/ tests/

# Run mypy
echo ""
echo "[+] Running mypy..."
python -m mypy src/

# Run black check
echo ""
echo "[+] Checking formatting with black..."
python -m black --check src/ tests/

echo ""
echo "[✓] All linting checks passed!"
