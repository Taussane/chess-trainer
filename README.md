# Chess Strategy Trainer

A mobile-first chess trainer with three exercises: **Board analysis**, **Candidate moves** and **Final choice**. Free and open: positions from master games, and from your own Lichess games.

The project has two parts:

1. **The app** (`app/index.html`): a single page. Its training positions are embedded in it. It runs as a website (`index.html`, served by GitHub Pages) and inside Claude, where it was first built.
2. **The position finder** (`finder/`): turns games from the library into training positions, using the rules in `finder/rules.js`.

Players add their own Lichess games in the app ("My games"): on the website the app downloads them from Lichess by username; inside Claude, where the page can't reach Lichess, they download the file and add it. Either way the app finds positions in them itself, in the browser.

## The website

`index.html` at the top of the repository is the app wrapped as a full web page, built by `python3 scripts/build-site.py` (`npm run site`). Edit `app/index.html`, then rebuild; `tests/website.py` fails when `index.html` is out of date.

GitHub Pages serves it: Settings › Pages › Deploy from a branch › `main` / root. On the website, progress is kept in the browser (per device) until accounts are added.

## Layout

| Folder | What it holds |
| --- | --- |
| `app/` | The app. Positions live between `/*POOLS*/` and `/*END POOLS*/`, and the master games' moves (for "Open in Lichess") between `/*GAME_MOVES*/` and `/*END GAME_MOVES*/`; `inject.py` writes both. The test positions (`scripts/make-test-positions.js`) are pasted after `/*TESTS*/`. |
| `library/` | Source games as PGN, moves only. `gm-classics.pgn` holds the 40 master games; its `Tags` header says which collection a game belongs to: `gm-annotated`, `fischer-my-60-memorable-games` and `tal-life-and-games` (the last two from the CC0 collection at github.com/brianerdelyi/ChessPGN). |
| `finder/` | `finder.js` (master games), `own.js` (a player's own games, offline, to gauge the rules), `lib.js` (what both share: engine, saved searches, phases, grades, choosing positions), `rules.js` (every threshold), `report.js` (statistics, master output only), `inject.py` (copies the master pools into the app). |
| `data/` | The latest master finder output: `pools.json` (positions with their measurements and the rules version) and `stats.json` (per game, with its moves). |
| `tests/` | Browser tests with a stand-in engine: `smoke.py` (a few positions of each exercise), `edge_cases.py` (the test positions: checks, en passant, castling, promotions), `my_games.py` (adding `lichess-sample.pgn` as a file, background analysis, your positions in the exercises), `played_today.py`, `fast_start.py` (instant Board analysis, checks before scans, waiting states), `profile_replay.py` (profile page, missed positions), `review_fixes.py` (results paging, unrecorded reviews, removed games, routine skipping, engine watchdog, with a stand-in account database), `lichess_link.py` ("Open in Lichess" opens each position's whole game at the right move) and `website.py` (the website page, and games downloaded from a stand-in Lichess). `npm run test:all` runs them all (needs: `pip install playwright`). |
| `vendor/` | chess.js 0.12.1 (BSD licence), the same version the app loads. |
| `scripts/` | `build-site.py` builds `index.html`; `setup-stockfish.sh` builds Stockfish 16.1 into `engine/` (not committed; if the build can't download its networks, it takes them from the networks repository through git); `make-test-positions.js` and `make-lichess-sample.js` build the test data. |

The rules are explained in plain words in the **Position finder rules** doc. When a rule changes, change `finder/rules.js` and the doc together, and bump `VERSION`.

## Rebuilding the positions

```sh
npm run setup:engine          # once: builds engine/stockfish
npm run find                  # runs the finder on library/gm-classics.pgn into data/ (about 3 minutes per new game at depth 18)
npm run report                # prints the statistics
npm run inject                # copies data/pools.json into app/index.html
npm run site                  # rebuilds index.html from the app
npm run test:all              # every test
```

Every engine search is kept in `finder/.cache/searches.jsonl` (not committed), so a re-run only analyses what it hasn't seen: trying a rule change on games already analysed takes seconds. Delete the file to start fresh.

To run on other games: `node finder/finder.js <games.pgn> <out-dir> [regex on "White - Black"]`, or for one player's games `node finder/own.js <games.pgn> <player> <out-dir>`.
For a quick trial at low depth, copy `rules.js`, lower `depth`, and run with `RULES=/absolute/path/to/copy.js` (a relative path is read from `finder/`) and an output folder other than `data/`.

## Licence

Free software under the GNU Affero General Public License v3.0 (`LICENSE`): anyone may use, study, change and share it, and any modified version offered to others, including as a website, must share its source under the same licence. Third-party parts and their licences (chess.js, Stockfish, scalachess's game phases) are listed in `THIRD_PARTY.md`.
