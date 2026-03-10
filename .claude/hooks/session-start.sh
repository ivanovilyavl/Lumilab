#!/bin/bash
set -euo pipefail

# Only run in remote (Claude Code on the web) environments
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

echo "==> Installing Python dependencies..."
pip install -r requirements-dev.txt --quiet

echo "==> Installing miniapp Node dependencies..."
cd miniapp && npm install --silent && cd ..

echo "==> Session start complete."
