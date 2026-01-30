#!/bin/bash
# Build script for Anki Image Picker add-on

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC_DIR="$SCRIPT_DIR/src"
OUTPUT_FILE="$SCRIPT_DIR/anki_image_picker.ankiaddon"

echo "Building Anki Image Picker..."

# Clean up cache files (AnkiWeb rejects these)
echo "Cleaning cache files..."
find "$SRC_DIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find "$SRC_DIR" -name ".DS_Store" -delete 2>/dev/null || true
find "$SRC_DIR" -name "*.pyc" -delete 2>/dev/null || true

# Remove old package if exists
rm -f "$OUTPUT_FILE"

# Create .ankiaddon package
echo "Creating package..."
cd "$SRC_DIR" && zip -r "$OUTPUT_FILE" *

echo ""
echo "Done! Created: $OUTPUT_FILE"
ls -lh "$OUTPUT_FILE"
