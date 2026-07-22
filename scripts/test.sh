#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo "=== ShellSense AI - Test Suite ==="
echo ""

python -m pytest tests/ -v --tb=short "$@"

echo ""
echo "[✓] All tests completed!"
