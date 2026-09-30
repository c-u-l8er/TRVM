#!/usr/bin/env bash
# Additive ABI v2 artifact. Never overwrites the legacy ic32.wasm.
set -euo pipefail
cd "$(dirname "$0")"
compiler="${CLANG:-clang}"
linker=()
if [ -n "${WASM_LD:-}" ]; then linker=("-fuse-ld=$WASM_LD"); fi
"$compiler" --target=wasm32 "${linker[@]}" -O2 -nostdlib -ffreestanding \
  -Wl,--no-entry -Wl,--export-dynamic -Wl,-z,stack-size=16777216 \
  -Wl,--initial-memory=268435456 -o ic32_checked.wasm ic32_wasm.c
