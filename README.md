# Chess Strategy Trainer

A mobile-first chess trainer with three activities: **Board analysis**, **Candidate moves** and **Final choice**.

The project has two parts:

1. **The app** (`app/index.html`): a single page. Its training positions are embedded in it.
2. **The position finder** (`finder/`): turns games from the library into training positions, using the rules in `finder/rules.js`.

## Layout

| Folder | What it holds |
| --- | --- |
| `app/` | The app. Positions live between `/*POOLS*/` and `/*END POOLS*/`. |
| `library/` | Source games as PGN, moves only. The `Tags` header says which collection a game belongs to: `gm-annotated`, `fischer-my-60-memorable-games` and `tal-life-and-games` (the last two from the CC0 collection at github.com/brianerdelyi/ChessPGN). |
| `finder/` | `finder.js` (the finder), `rules.js` (every threshold it uses), `report.js` (statistics), `inject.py` (copies the pools into the app). |
| `data/` | The latest finder output: `pools.json` (positions with their measurements and the rules version) and `stats.json`. |
| `tests/` | `smoke.py` opens the app with a fake engine and plays a few positions of each activity. |
| `vendor/` | chess.js 0.12.1 (BSD licence), the same version the app loads. |
| `scripts/` | `setup-stockfish.sh` builds Stockfish 16.1 into `engine/`. `engine/` is not committed. |

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

To run on other games: `node finder/finder.js <games.pgn> data [regex on "White - Black"]`.
For a quick trial at low depth, point `RULES` at a copy of `rules.js` with a smaller `depth`.
