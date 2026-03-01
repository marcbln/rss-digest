#!/bin/bash
# Workflow: Generate digest and publish via email
# Usage: ./scripts/generate-and-email.sh <config-name> [--dry-run]
#
# Example: ./scripts/generate-and-email.sh ai-assisted-programming

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python"
RSS_DIGEST="$PROJECT_ROOT/.venv/bin/rss-digest"

# Check arguments
if [ $# -lt 1 ]; then
    echo "Usage: $0 <config-name> [--dry-run]"
    echo "Example: $0 ai-assisted-programming"
    exit 1
fi

CONFIG_NAME="$1"
DRY_RUN=false

if [ "$2" = "--dry-run" ]; then
    DRY_RUN=true
    echo "[DRY RUN] Would generate and publish: $CONFIG_NAME"
fi

# Check virtual environment exists
if [ ! -f "$RSS_DIGEST" ]; then
    echo "Error: Virtual environment not found at .venv/bin/rss-digest"
    echo "Please run: uv sync"
    exit 1
fi

cd "$PROJECT_ROOT"

echo "=== Step 1: Generating digest for '$CONFIG_NAME' ==="

# Generate digest with JSON output to capture file path
GENERATE_OUTPUT=$($RSS_DIGEST generate run -c "$CONFIG_NAME" --json 2>&1)

# Check if generation succeeded
if ! echo "$GENERATE_OUTPUT" | tail -1 | grep -q '"success": true'; then
    echo "Error: Digest generation failed"
    echo "$GENERATE_OUTPUT"
    exit 1
fi

# Extract file path from JSON output
DIGEST_FILE=$(echo "$GENERATE_OUTPUT" | tail -1 | $VENV_PYTHON -c "import sys, json; print(json.load(sys.stdin)['file_path'])")

if [ -z "$DIGEST_FILE" ]; then
    echo "Error: Could not extract file path from output"
    echo "$GENERATE_OUTPUT"
    exit 1
fi

echo "Generated: $DIGEST_FILE"

# Verify file exists
if [ ! -f "$DIGEST_FILE" ]; then
    echo "Error: Generated file not found: $DIGEST_FILE"
    exit 1
fi

echo ""
echo "=== Step 2: Publishing via email ==="

if [ "$DRY_RUN" = true ]; then
    echo "[DRY RUN] Would publish: $DIGEST_FILE"
    echo "[DRY RUN] Command: rss-digest publish email $DIGEST_FILE"
    echo ""
    echo "Dry run complete. Digest file exists at: $DIGEST_FILE"
else
    $RSS_DIGEST publish email "$DIGEST_FILE"
    echo ""
    echo "✓ Workflow complete! Digest generated and emailed."
fi
