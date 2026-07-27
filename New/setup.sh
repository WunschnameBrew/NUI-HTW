#!/usr/bin/env bash
# macOS/Linux setup script
set -euo pipefail
cd "$(dirname "$0")"

echo "🚀 Running Koa-AI Environment Setup..."
python3 setup_environment.py
