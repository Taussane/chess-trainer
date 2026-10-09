# Third-party notices

Chess Strategy Trainer is licensed under the GNU Affero General Public License v3.0 (see `LICENSE`). It uses or adapts the following, under their own licences.

## chess.js 0.12.1

Move generation and validation. Loaded by the app from a CDN; a copy is in `vendor/chess.js/` with its licence (BSD 2-Clause).

## Stockfish

The chess engine. The app loads Stockfish 10 (JavaScript build) from a CDN; the position finder uses Stockfish 16.1, built from source by `scripts/setup-stockfish.sh` and not stored here. Stockfish is licensed under the GNU General Public License v3.0: https://github.com/official-stockfish/Stockfish

## scalachess: game phases (Divider)

The game-phase detection (middlegame and endgame starts) in `finder/lib.js` and `app/index.html` is a port of `Divider.scala` from scalachess (https://github.com/lichess-org/scalachess), under this licence:

Copyright (c) 2012-2014 Thibault Duplessis

The MIT license

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is furnished
to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

## Lichess

The winning-chances curve used to grade moves follows the one Lichess publishes for its accuracy figures. Lichess (https://lichess.org) is free software under the GNU Affero General Public License v3.0. Games are downloaded from Lichess through its public API. The Lichess logo (`vendor/lichess-logo.svg`, inlined in the app's login buttons) comes from lila (`public/logo/lichess.svg`), under the same licence.

## Chess.com

Chess.com games are read through Chess.com's public API (by the account server). The Chess.com pawn (`vendor/chesscom-logo.svg`, inlined in the app's account section) is a trademark of Chess.com, used only to name the site. The SVG file comes from https://github.com/homarr-labs/dashboard-icons (Apache License 2.0). This project is not affiliated with Chess.com.

## Master games

`library/gm-classics.pgn` holds moves only (no annotations). Part of it comes from the CC0 collection at https://github.com/brianerdelyi/ChessPGN.
