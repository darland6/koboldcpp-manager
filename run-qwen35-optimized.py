"""
Qwen3.5-35B-A3B optimized runner using llama-cpp-python
Optimization flags from community benchmarks:
  --cache-type-k q8_0 --cache-type-v q8_0 -np 1
  All layers on GPU (RTX 3090 24GB)
"""

import time
from llama_cpp import Llama

MODEL_PATH = r"C:\Users\cory\.lmstudio\models\lmstudio-community\Qwen3.5-35B-A3B-GGUF\Qwen3.5-35B-A3B-Q4_K_M.gguf"

# GGML_TYPE_Q8_0 = 8 (matches --cache-type-k q8_0 --cache-type-v q8_0)
GGML_TYPE_Q8_0 = 8

print("Loading Qwen3.5-35B-A3B with optimized KV cache...")
print(f"  Model: Q4_K_M quant")
print(f"  KV cache: Q8_0 (key + value)")
print(f"  GPU: RTX 3090 (index 1, 24GB)")
print(f"  GPU layers: all (-1)")
print()

start_load = time.time()

llm = Llama(
    model_path=MODEL_PATH,
    n_gpu_layers=-1,         # All layers on GPU
    main_gpu=1,              # RTX 3090 (24GB) is GPU index 1
    n_ctx=8192,              # Context window (start moderate, increase if stable)
    type_k=GGML_TYPE_Q8_0,  # --cache-type-k q8_0
    type_v=GGML_TYPE_Q8_0,  # --cache-type-v q8_0
    flash_attn=True,         # Enable flash attention for extra speed
    verbose=True,            # Show llama.cpp loading stats
)

load_time = time.time() - start_load
print(f"\nModel loaded in {load_time:.1f}s")
print("=" * 60)
print("Running benchmark prompt...")
print("=" * 60)

start_gen = time.time()

response = llm.create_chat_completion(
    messages=[
        {
            "role": "user",
            "content": "Explain quantum entanglement in 3 paragraphs. Be detailed and technical."
        }
    ],
    max_tokens=512,
    temperature=0.7,
)

gen_time = time.time() - start_gen

output = response["choices"][0]["message"]["content"]
usage = response["usage"]

print(f"\n{output}")
print()
print("=" * 60)
print("BENCHMARK RESULTS")
print("=" * 60)
print(f"  Prompt tokens:     {usage['prompt_tokens']}")
print(f"  Completion tokens: {usage['completion_tokens']}")
print(f"  Total time:        {gen_time:.2f}s")
print(f"  Tokens/sec:        {usage['completion_tokens'] / gen_time:.1f} tok/s")
print("=" * 60)
