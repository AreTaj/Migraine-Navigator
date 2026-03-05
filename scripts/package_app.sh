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
pip install pyinstaller appdirs geocoder

# Run PyInstaller
# --noconsole: Hide terminal window
# --onefile: Single executable
# --name: Specific name
# --distpath: Output directly to binaries dir (temp) or move later
# --paths .: Add project root to sys.path
# Use --add-data for local packages (forecasting, services, api) to ensure they are bundled physically
pyinstaller --clean --noconsole --noconfirm --onefile --collect-all certifi --collect-all psutil --collect-all pandas --collect-all numpy --collect-all sklearn --hidden-import requests --hidden-import forecasting.inference --hidden-import forecasting.data_loader --hidden-import forecasting.feature_engine --hidden-import services.weather_service --hidden-import services.entry_service --hidden-import sklearn.ensemble._hist_gradient_boosting.gradient_boosting --hidden-import sklearn.ensemble._hist_gradient_boosting.histogram --hidden-import sklearn.ensemble._hist_gradient_boosting.splitting --hidden-import sklearn.ensemble._hist_gradient_boosting.predictor --exclude-module tensorflow --exclude-module keras --exclude-module legacy --add-data "forecasting:forecasting" --add-data "services:services" --add-data "api:api" --paths . --name migraine-navigator-api scripts/api_entry.py

# 4. Move and Rename Binary for Tauri
echo "Preparing sidecar binary..."
# PyInstaller outputs to dist/ by default
mv "dist/migraine-navigator-api" "$BINARIES_DIR/migraine-navigator-api-$TRIPLE"

# Clean up PyInstaller artifacts
rm -rf build dist migraine-navigator-api.spec

echo "Sidecar binary created at: $BINARIES_DIR/migraine-navigator-api-$TRIPLE"

# 5. Build Tauri App
echo "Building Tauri App (Bundling .app only to bypass DMG issues)..."
cd frontend
npm install # Ensure deps are installed
npm run build # Vite build

# Build only the .app first to guarantee success
npm run tauri build -- --bundles app

# Now try the DMG, but don't fail the whole script if it dies on aesthetics
echo "Attempting to build DMG (may fail on aesthetics, continuing anyway)..."
npm run tauri build -- --bundles dmg || echo "DMG build failed, but .app is ready."

# Build finished. Copying artifacts to 'releases/'...
mkdir -p "$PROJECT_ROOT/releases"
# Copy .app (if it exists)
if [ -d "$TAURI_DIR/target/release/bundle/macos/Migraine Navigator.app" ]; then
    cp -R "$TAURI_DIR/target/release/bundle/macos/Migraine Navigator.app" "$PROJECT_ROOT/releases/"
fi
# Copy .dmg
cp "$TAURI_DIR/target/release/bundle/dmg/"*.dmg "$PROJECT_ROOT/releases/" || true

echo "Packaging Complete!"
echo "Artifacts are in the 'releases/' folder."
