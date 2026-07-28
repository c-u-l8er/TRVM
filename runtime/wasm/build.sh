#!/usr/bin/env bash
# Rebuild ic32.wasm from ic32_wasm.c using clang + wasm-ld (no emscripten).
# Produces a freestanding wasm32 module that matches the C reference bit-for-bit.
set -euo pipefail
cd "$(dirname "$0")"

CLANG="${CLANG:-clang}"

# Ensure wasm-ld is on PATH.  clang invokes it by name ("wasm-ld") when
# targeting wasm32; if the system lld package lives under a versioned LLVM
# prefix (e.g. /usr/lib/llvm20/bin) it won't be found without help.
if ! command -v wasm-ld >/dev/null 2>&1; then
  for d in /usr/lib/llvm*/bin; do
    if [ -x "$d/wasm-ld" ]; then
      export PATH="$d:$PATH"
      break
    fi
  done
fi

"$CLANG" --target=wasm32 -O2 -nostdlib -ffreestanding -Wl,--no-entry \
  -Wl,--export-dynamic -Wl,-z,stack-size=16777216 \
  -Wl,--initial-memory=268435456 -o ic32.wasm ic32_wasm.c

echo "built ic32.wasm ($(wc -c < ic32.wasm) bytes)"
echo "smoke test:"
printf '%s' 'λx.x' | node wrun.js
