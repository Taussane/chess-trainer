#!/usr/bin/env bash
# Puts Stockfish 19 (the official Linux x86-64 build, network included) into engine/stockfish,
# the engine the finder uses. Set STOCKFISH=/path/to/stockfish to use another one.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p engine
tmp=$(mktemp -d)
curl -sSfL -o "$tmp/sf.tar.gz" https://github.com/official-stockfish/Stockfish/releases/download/sf_19/stockfish-linux-x86-64-universal.tar.gz
tar -xzf "$tmp/sf.tar.gz" -C "$tmp"
cp "$tmp/stockfish/stockfish-linux-x86-64-universal" engine/stockfish
rm -rf "$tmp"
echo "engine/stockfish ready: $(echo uci | engine/stockfish | grep -m1 'id name')"
