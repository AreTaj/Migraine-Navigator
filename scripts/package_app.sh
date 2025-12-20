#!/bin/bash

# Exit on error
set -e

# Project Root
PROJECT_ROOT=$(pwd)
TAURI_DIR="$PROJECT_ROOT/frontend/src-tauri"
BINARIES_DIR="$TAURI_DIR/binaries"

# 1. Detect Architecture for Sidecar Suffix
ARCH=$(uname -m)
if [ "$ARCH" == "arm64" ]; then
    TRIPLE="aarch64-apple-darwin"
else
    TRIPLE="x86_64-apple-darwin"
fi

echo "Detected architecture: $ARCH (Target: $TRIPLE)"

# 2. Setup Binaries Directory
mkdir -p "$BINARIES_DIR"

# 3. Build Python Sidecar
echo "Building Python backend..."
source .venv/bin/activate

# Install pyinstaller if needed (check if installed first to save time, or just pip install)
pip install pyinstaller

# Run PyInstaller
# --noconsole: Hide terminal window
# --onefile: Single executable
# --name: Specific name
# --distpath: Output directly to binaries dir (temp) or move later
pyinstaller --noconsole --onefile --name migraine-navigator-api scripts/api_entry.py

# 4. Move and Rename Binary for Tauri
echo "Preparing sidecar binary..."
# PyInstaller outputs to dist/ by default
mv "dist/migraine-navigator-api" "$BINARIES_DIR/migraine-navigator-api-$TRIPLE"

# Clean up PyInstaller artifacts
rm -rf build dist migraine-navigator-api.spec

echo "Sidecar binary created at: $BINARIES_DIR/migraine-navigator-api-$TRIPLE"

# 5. Build Tauri App
echo "Building Tauri App..."
cd frontend
npm install # Ensure deps are installed
npm run build # Vite build
npm run tauri build # Tauri build

echo "Build finished. Copying artifacts to 'releases/'..."
mkdir -p "$PROJECT_ROOT/releases"
cp "$TAURI_DIR/target/release/bundle/dmg/"*.dmg "$PROJECT_ROOT/releases/"

echo "Packaging Complete!"
echo "Installer available at: releases/$(basename "$TAURI_DIR/target/release/bundle/dmg/"*.dmg)"
