#!/usr/bin/env bash
set -e

echo "==> Installing dependencies..."
pip install -r requirements.txt

echo "==> Building Linux executable..."
pyinstaller OutreachConsole.spec --clean

echo ""
echo "  Build complete: dist/OutreachConsole"
echo "  Run it with:   ./dist/OutreachConsole"
