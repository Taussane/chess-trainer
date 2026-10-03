#!/usr/bin/env bash
# Builds Stockfish 16.1 into engine/stockfish (the version the finder results were made with).
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p engine
if [ ! -d engine/src-sf ]; then
  git clone --depth 1 --branch sf_16.1 https://github.com/official-stockfish/Stockfish.git engine/src-sf
fi
make -C engine/src-sf/src -j"$(nproc 2>/dev/null || echo 2)" build ARCH="${ARCH:-x86-64-sse41-popcnt}"
cp engine/src-sf/src/stockfish engine/stockfish
echo "engine/stockfish ready"
