#!/bin/bash
# Start Qwen3.5-35B-A3B on llama.cpp with optimized KV cache
# Server: http://0.0.0.0:8080 (LAN accessible)
# GPU: RTX 3090 (index 1, 24GB)
# Optimizations: Q8_0 KV cache, flash attention, single slot

LLAMA_DIR="/c/Users/cory/projects/models/llama-cpp/bin"
MODEL_DIR="/c/Users/cory/.lmstudio/models/lmstudio-community/Qwen3.5-35B-A3B-GGUF"

# Model selection: prefer UD-Q4_K_XL (unsloth optimized), fall back to Q4_K_M
if [ -f "$MODEL_DIR/Qwen3.5-35B-A3B-UD-Q4_K_XL.gguf" ]; then
    MODEL="$MODEL_DIR/Qwen3.5-35B-A3B-UD-Q4_K_XL.gguf"
    QUANT="UD-Q4_K_XL (unsloth optimized)"
else
    MODEL="$MODEL_DIR/Qwen3.5-35B-A3B-Q4_K_M.gguf"
    QUANT="Q4_K_M"
fi

# Check if already running
if curl -s http://127.0.0.1:8080/health > /dev/null 2>&1; then
    echo "llama-server is already running on port 8080"
    exit 1
fi

echo "Starting Qwen3.5-35B-A3B ($QUANT) with optimized KV cache..."
echo "  Port: 8080 (0.0.0.0)"
echo "  GPU: RTX 3090 (index 1)"
echo "  KV cache: Q8_0 (key + value)"
echo "  Flash attention: on"
echo ""

"$LLAMA_DIR/llama-server.exe" \
    --model "$MODEL" \
    --host 0.0.0.0 \
    --port 8080 \
    --n-gpu-layers -1 \
    --main-gpu 1 \
    --cache-type-k q8_0 \
    --cache-type-v q8_0 \
    --flash-attn on \
    -np 1 \
    --ctx-size 100000
