#!/usr/bin/env bash
set -e

# Master Cloud Runner & Mutagen Sync for Financial Document Intelligence System (FDIS)
CODESPACE_NAME="$1"
REPO="ashhal-kaleem/financial-document-intelligence-system"
LOCAL_DIR="/home/shaikhfardin/Projects/Project 2"

if [ -z "$CODESPACE_NAME" ]; then
    echo "Usage: ./dev-cloud.sh <codespace_name>"
    echo ""
    echo "To list existing codespaces: gh codespace list"
    echo "To create a new one:         gh codespace create -r $REPO --machine standardLinux4core"
    exit 1
fi

echo "=== 1. Starting Mutagen Real-Time Two-Way Sync ==="
# Ensure SSH config is ready for Codespaces
gh codespace ssh --config -c "$CODESPACE_NAME" > ~/.ssh/codespace_fdis
if ! grep -q "Include ~/.ssh/codespace_fdis" ~/.ssh/config 2>/dev/null; then
    mkdir -p ~/.ssh
    printf "Match all\n  Include ~/.ssh/codespace_fdis\n" >> ~/.ssh/config
fi

# Terminate existing sync if any
/home/shaikhfardin/.local/bin/mutagen sync terminate fdis-sync 2>/dev/null || true

# Start low-latency continuous synchronization
/home/shaikhfardin/.local/bin/mutagen sync create \
    --name=fdis-sync \
    --sync-mode=two-way-safe \
    --ignore-vcs \
    --ignore="node_modules" \
    --ignore=".venv" \
    --ignore="__pycache__" \
    --ignore=".next" \
    "$LOCAL_DIR" \
    "cs-$CODESPACE_NAME:/workspaces/financial-document-intelligence-system"

echo "✓ Mutagen sync established! Local edits in Antigravity IDE will auto-sync to Cloud in real-time."

echo "=== 2. Forwarding Ports (Local 3000 -> Cloud 3000, Local 8000 -> Cloud 8000) ==="
echo "You can now view the app at http://localhost:3000 (running in the cloud, zero laptop CPU load)!"
gh codespace ports forward 3000:3000 8000:8000 -c "$CODESPACE_NAME"
