#!/usr/bin/env bash
set -e

# Real-Time Background File Sync to GitHub Codespace (ZERO Git Push Required)
CODESPACE="$1"
LOCAL_DIR="/home/shaikhfardin/Projects/Project 2"

if [ -z "$CODESPACE" ]; then
    CODESPACE=$(gh codespace list --json name --jq '.[0].name' 2>/dev/null || true)
    if [ -z "$CODESPACE" ]; then
        echo "Usage: ./dev-sync.sh <codespace_name>"
        echo "No active codespace found. Create one with: gh codespace create -R ashhal-kaleem/financial-document-intelligence-system"
        exit 1
    fi
fi

echo "Connecting to Codespace: $CODESPACE..."
mkdir -p ~/.ssh
gh codespace ssh --config -c "$CODESPACE" > ~/.ssh/codespaces_config
SSH_HOST=$(grep "^Host " ~/.ssh/codespaces_config | head -n 1 | awk '{print $2}')

echo "✓ Target SSH Host: $SSH_HOST"
echo "Starting continuous background file sync (1-second polling loop)..."

# Initial Full Sync
echo "=== 1. Initial Syncing local workspace to cloud ==="
rsync -avz --delete \
    --exclude '.git' \
    --exclude 'node_modules' \
    --exclude '.next' \
    --exclude '.venv' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '.DS_Store' \
    -e "ssh -F $HOME/.ssh/codespaces_config" \
    "$LOCAL_DIR/" \
    "$SSH_HOST:/workspaces/financial-document-intelligence-system/"

echo "=== 2. Continuous Background Watcher Active ==="
echo "Any edit saved locally will auto-sync to Cloud within 1 second!"

while true; do
    sleep 1
    rsync -avzq --update \
        --exclude '.git' \
        --exclude 'node_modules' \
        --exclude '.next' \
        --exclude '.venv' \
        --exclude '__pycache__' \
        -e "ssh -F $HOME/.ssh/codespaces_config" \
        "$LOCAL_DIR/" \
        "$SSH_HOST:/workspaces/financial-document-intelligence-system/" 2>/dev/null || true
done
