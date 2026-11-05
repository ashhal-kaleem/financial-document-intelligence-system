#!/usr/bin/env bash
# frontend/api/src is the copy of backend/src that Vercel runs. Keep it identical.
# Usage: scripts/sync-vercel-api.sh [--check]
set -euo pipefail
cd "$(dirname "$0")/.."
if [ "${1:-}" = "--check" ]; then
  diff -r -x __pycache__ backend/src frontend/api/src && echo "in sync"
else
  rsync -a --delete --exclude __pycache__ backend/src/ frontend/api/src/
  echo "synced backend/src -> frontend/api/src"
fi
