#!/usr/bin/env bash
# macOS/Linux equivalent of start_llama.bat
# Serves the first .gguf found in Llama_Models/ on port 8001 (OpenAI-compatible API)
set -euo pipefail
cd "$(dirname "$0")"

MODEL=$(ls Llama_Models/*.gguf 2>/dev/null | head -1)
if [ -z "${MODEL:-}" ]; then
  echo "❌ No .gguf model found in Llama_Models/"
  exit 1
fi

echo "🧠 Starting llama-server with: $MODEL"
exec llama-server \
  --model "$MODEL" \
  --ctx-size 4096 \
  --n-gpu-layers -1 \
  --port 8001
