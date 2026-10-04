# Chess Strategy Trainer

A mobile-first chess trainer with three activities: **Board analysis**, **Candidate moves** and **Final choice**.

The project has two parts:

1. **The app** (`app/index.html`): a single page. Its training positions are embedded in it.
2. **The position finder** (`finder/`): turns games from the library into training positions, using the rules in `finder/rules.js`.

Players can also add their own Lichess games in the app ("My games"): the app finds positions in them itself, in the browser, and keeps them private to the player's account.

## Layout

| Folder | What it holds |
| --- | --- |
| `app/` | The app. Positions live between `/*POOLS*/` and `/*END POOLS*/`. |
| `library/` | Source games as PGN, moves only. `gm-classics.pgn` holds the 40 master games; its `Tags` header says which collection a game belongs to: `gm-annotated`, `fischer-my-60-memorable-games` and `tal-life-and-games` (the last two from the CC0 collection at github.com/brianerdelyi/ChessPGN). `own/` holds the owner's Lichess games (private). |
| `finder/` | `finder.js` (master games), `own.js` (a player's own games), `lib.js` (what both share: engine, saved searches, phases, grades, choosing positions), `rules.js` (every threshold), `report.js` (statistics, master output only), `inject.py` (copies the master pools into the app). |
| `data/` | The latest master finder output: `pools.json` (positions with their measurements and the rules version) and `stats.json`. `draft/own/` is `own.js`'s output on the owner's games. |
| `tests/` | Browser tests with a stand-in engine: `smoke.py` (a few positions of each exercise), `edge_cases.py` (the test positions: checks, en passant, castling, promotions), `my_games.py` (uploading `lichess-sample.pgn`, background analysis, your positions in the exercises), `owner_seed.py`, `owner_upgrade.py`, `played_today.py`, `fast_start.py` (instant Board analysis, checks before scans, waiting states), `profile_replay.py` (profile page, missed positions: replays count, nothing played today is offered) and `review_fixes.py` (results paging, unrecorded reviews, removed games, routine skipping, engine watchdog, with a stand-in account database). `npm run test:all` runs them all. |
| `vendor/` | chess.js 0.12.1 (BSD licence), the same version the app loads. |
| `scripts/` | `setup-stockfish.sh` builds Stockfish 16.1 into `engine/` (not committed; if the build can't download its networks, it takes them from the networks repository through git); `make-test-positions.js` and `make-lichess-sample.js` build the test data; `make-owner-seed.js` builds the owner's built-in games from `finder/own.js`'s analysis. |

The rules are explained in plain words in the **Position finder rules** doc. When a rule changes, change `finder/rules.js` and the doc together, and bump `VERSION`.

## Rebuilding the positions

```sh
npm run setup:engine          # once: builds engine/stockfish
npm run find                  # runs the finder on library/gm-classics.pgn into data/ (about 3 minutes per new game at depth 18)
npm run report                # prints the statistics
npm run inject                # copies data/pools.json into app/index.html
npm test                      # smoke test (needs: pip install playwright)
```

Every engine search is kept in `finder/.cache/searches.jsonl` (not committed), so a re-run only analyses what it hasn't seen: trying a rule change on games already analysed takes seconds. Delete the file to start fresh.

To run on other games: `node finder/finder.js <games.pgn> <out-dir> [regex on "White - Black"]`.
For a quick trial at low depth, copy `rules.js`, lower `depth`, and run with `RULES=/absolute/path/to/copy.js` (a relative path is read from `finder/`) and an output folder other than `data/`.

## Rebuilding the owner's built-in games

```sh
node finder/own.js library/own/taussane.pgn Taussane data/draft/own      # positions and statistics (same engine and saved searches)
node scripts/make-owner-seed.js library/own/taussane.pgn Taussane /tmp/seed.json
```

Then paste `/tmp/seed.json` between `/*OWNER_SEED*/` and the `;` after it in `app/index.html`, and bump `SEED_VERSION` there so the owner's account takes the new copy. The test positions (`scripts/make-test-positions.js`) are pasted the same way after `/*TESTS*/`.
