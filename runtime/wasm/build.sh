#!/usr/bin/env bash
# Rebuild ic32.wasm from ic32_wasm.c using clang-15 + lld-15 (no emscripten).
# Produces a freestanding wasm32 module that matches the C reference bit-for-bit.
set -euo pipefail
cd "$(dirname "$0")"

CLANG="${CLANG:-clang-15}"

"$CLANG" --target=wasm32 -O2 -nostdlib -ffreestanding -Wl,--no-entry \
  -Wl,--export-dynamic -Wl,-z,stack-size=16777216 \
  -Wl,--initial-memory=67108864 -o ic32.wasm ic32_wasm.c

echo "built ic32.wasm ($(wc -c < ic32.wasm) bytes)"
echo "smoke test:"
printf '%s' 'λx.x' | node wrun.js
