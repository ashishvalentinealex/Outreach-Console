#!/usr/bin/env bash
set -e

echo "==> Creating a clean virtual environment..."
python3 -m venv venv

echo "==> Activating virtual environment..."
source venv/bin/activate

echo "==> Removing obsolete pathlib package if present..."
pip uninstall pathlib -y 2>/dev/null || true

echo "==> Installing dependencies..."
pip install -r requirements.txt

echo "==> Building Linux executable..."
if pyinstaller OutreachConsole.spec --clean; then
    echo ""
    echo "  Build complete: dist/OutreachConsole"
    echo "  Run it with:   ./dist/OutreachConsole"
else
    echo ""
    echo "  ERROR: PyInstaller failed. Check the output above for details."
    exit 1
fi
