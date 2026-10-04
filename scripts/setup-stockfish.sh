#!/usr/bin/env bash
# Builds Stockfish 16.1 into engine/stockfish (the version the finder results were made with).
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p engine
if [ ! -d engine/src-sf ]; then
  git clone --depth 1 --branch sf_16.1 https://github.com/official-stockfish/Stockfish.git engine/src-sf
fi
# The build downloads its two neural networks; where that download is blocked, take them from
# the official networks repository through git instead.
for net in nn-b1a57edbea57.nnue nn-baff1ede1f90.nnue; do
  if [ ! -f "engine/src-sf/src/$net" ] && ! curl -sfL -o "engine/src-sf/src/$net" "https://tests.stockfishchess.org/api/nn/$net"; then
    rm -f "engine/src-sf/src/$net"
    [ -d engine/nets ] || git clone -q --depth 1 --filter=blob:none --sparse https://github.com/official-stockfish/networks engine/nets
    git -C engine/nets sparse-checkout add "$net" >/dev/null 2>&1 || git -C engine/nets sparse-checkout set --no-cone "$net"
    cp "engine/nets/$net" engine/src-sf/src/
  fi
done
make -C engine/src-sf/src -j"$(nproc 2>/dev/null || echo 2)" build ARCH="${ARCH:-x86-64-sse41-popcnt}"
cp engine/src-sf/src/stockfish engine/stockfish
echo "engine/stockfish ready"
