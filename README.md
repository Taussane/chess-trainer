# Chess Strategy Trainer

A mobile-first chess trainer with three exercises: **Position evaluation**, **Candidate moves** and **Move selection**. Free and open: positions from master games, and from your own Lichess and Chess.com games.

The project has two parts:

1. **The app** (`app/index.html`): a single page. Its training positions are embedded in it. It runs as a website (`index.html`, served by GitHub Pages) and inside Claude, where it was first built.
2. **The position finder** (`finder/`): turns games from the library into training positions, using the rules in `finder/rules.js`.

On the website, players **log in with Lichess** (Lichess's own sign-in, OAuth with PKCE: no password reaches the site, nothing asked beyond the public profile) or, without a Lichess account, **with Google**. In the Profile they can add a Chess.com username (Chess.com offers no sign-in to other sites yet, so its public games are read through the account server). The last 100 games of each site, bullet to classical, then sync by themselves, with Lichess's analysis where there is one. Inside Claude, where the page can't reach Lichess, players download their games file and add it. Either way the app finds positions in the games itself, in the browser.

## The website

`index.html` at the top of the repository is the app wrapped as a full web page, built by `python3 scripts/build-site.py` (`npm run site`). Edit `app/index.html`, then rebuild; `tests/website.py` fails when `index.html` is out of date.

GitHub Pages serves it: Settings › Pages › Deploy from a branch › `main` / root. Without logging in, progress stays in the browser; logged in, it is saved to the player's account (below). The site also serves `privacy.html` and `terms.html`.

How accounts and game sites work: `docs/accounts.md`.

## Accounts (the account server)

`worker/` is a small Cloudflare Worker with a D1 database: players log in with Lichess or Google on the website, and their progress and games are saved to their account, on every device (design: `docs/accounts.md`; privacy: `privacy.html`). Cloudflare deploys it from this repository on every push. Its address is set in `app/index.html` (`/*API_BASE*/`); left empty, everything stays in the browser.

Tests run it here without Cloudflare (`worker/test/local.mjs`: the same code on Node's built-in SQLite, with stand-ins for Lichess, Google and Chess.com): `npm run test:server` for its rules, `tests/accounts.py` for the website with it.

One-time setup on Cloudflare:
1. Storage & databases › D1 › Create database `chess-trainer`; put its Database ID in `worker/wrangler.toml`.
2. Workers & Pages › Create › Import a repository › this repository. Root directory `worker`; deploy command `npx wrangler d1 migrations apply chess-trainer --remote && npx wrangler deploy`.
3. For "Log in with Google": a Google Cloud OAuth client (Web application; authorised JavaScript origin `https://taussane.github.io`, redirect URI `https://taussane.github.io/chess-trainer/`); its client id (now `156223514087-…apps.googleusercontent.com`) goes in `worker/wrangler.toml` (`GOOGLE_CLIENT_ID`) and in `app/index.html` (`/*GOOGLE_CLIENT_ID*/`). Empty: the Google button doesn't show.
4. Put the Worker's address in `app/index.html` (`/*API_BASE*/`, now `https://chess-trainer-api.sauveur-guillaume.workers.dev`) and rebuild the site.

## Layout

| Folder | What it holds |
| --- | --- |
| `app/` | The app. Positions live between `/*POOLS*/` and `/*END POOLS*/`, the master games' moves (for "Open in Lichess") between `/*GAME_MOVES*/` and `/*END GAME_MOVES*/`, their dates and events between `/*GAME_INFO*/` and `/*END GAME_INFO*/`; `inject.py` writes them all (the last through `scripts/master-info.py`). The test positions (`scripts/make-test-positions.js`) are pasted after `/*TESTS*/`. |
| `library/` | Source games as PGN, moves only. `gm-classics.pgn` holds the 40 master games; `Added` is the day a game joined the library (newer additions are offered first); `EventShort` is a short, tidied event name shown above the board (`scripts/master-info.py` copies it and the date into the app); the `Tags` header says which collection a game belongs to: `gm-annotated`, `fischer-my-60-memorable-games` and `tal-life-and-games` (the last two from the CC0 collection at github.com/brianerdelyi/ChessPGN). |
| `finder/` | `finder.js` (master games), `own.js` (a player's own games, offline, to gauge the rules), `lib.js` (what both share: engine, saved searches, phases, grades, choosing positions), `rules.js` (every threshold), `report.js` (statistics, master output only), `inject.py` (copies the master pools into the app). |
| `data/` | The latest master finder output: `pools.json` (positions with their measurements and the rules version) and `stats.json` (per game, with its moves). |
| `tests/` | Browser tests with a stand-in engine (needs `pip install playwright`); `npm run test:all` runs them all, after the account server's own tests (`worker/test/api.test.mjs`). The exercises: `smoke.py` (a few positions of each), `edge_cases.py` (the test positions: checks, en passant, castling, promotions), `engine_down.py` (no Check without the engine), `lichess_link.py` ("Open in Lichess" opens the whole game at the right move). Your games: `my_games.py` (adding `lichess-sample.pgn` as a file, background analysis, ratings, your positions in the exercises), `pgn_import.py` (games read in full; games saved cut short completed), `fast_start.py` (positions from Lichess's analysis at once, checks before scans, waiting states), `load_speed.py` (190 saved games load without freezing the page). What comes next: `played_today.py` (a position played today isn't offered again today), `review_fixes.py` (results paging, unrecorded reviews, removed games, routine skipping, engine watchdog), `selection.py` (your positions: the 100-game core list, Replay's 10%, games leaving the list), `my_positions_order.py` (the same order for master games, by the day they joined the library; the Replay cap), `profile_replay.py` (the profile, missed positions, the chart). The website and accounts: `website.py` (the page, games synced from a stand-in Lichess), `lichess_login.py` (Lichess's sign-in, checked like the real one), `accounts.py` (devices, Chess.com, logging out, deleting the account, against the account server), `google_login.py` (Google login, connecting Lichess, merging accounts). `chesscom-sample.pgn` and `lichess-sample.pgn` are their games. |
| `vendor/` | chess.js 0.12.1 (BSD licence), the same version the app loads. |
| `scripts/` | `build-site.py` builds `index.html`; `setup-stockfish.sh` builds Stockfish 16.1 into `engine/` (not committed; if the build can't download its networks, it takes them from the networks repository through git); `master-info.py` copies each master game's date and `EventShort` into the app; `make-test-positions.js` and `make-lichess-sample.js` build the test data. |
| `worker/` | The account server (Cloudflare Worker + D1): `src/index.js`, `migrations/`, `wrangler.toml`, `test/`. |
| `docs/` | `accounts.md`: how accounts and game sites work. |

The rules are explained in plain words in the **Position finder rules** document (kept outside the repository, in Claude Docs). When a rule changes, change `finder/rules.js` and the doc together, and bump `VERSION`.

## Rebuilding the positions

```sh
npm run setup:engine          # once: builds engine/stockfish
npm run find                  # runs the finder on library/gm-classics.pgn into data/ (about 3 minutes per new game at depth 18)
npm run report                # prints the statistics
node finder/baseline.js data/pools.json   # how a no-thinking player scores (50/50, random top-5 move, random order)
npm run inject                # copies data/pools.json into app/index.html
npm run site                  # rebuilds index.html from the app
npm run test:all              # every test
```

Every engine search is kept in `finder/.cache/searches.jsonl` (not committed), so a re-run only analyses what it hasn't seen: trying a rule change on games already analysed takes seconds. Delete the file to start fresh.

To run on other games: `node finder/finder.js <games.pgn> <out-dir> [regex on "White - Black"]`, or for one player's games `node finder/own.js <games.pgn> <player> <out-dir>`.
For a quick trial at low depth, copy `rules.js`, lower `depth`, and run with `RULES=/absolute/path/to/copy.js` (a relative path is read from `finder/`) and an output folder other than `data/`.

## Licence

Free software under the GNU Affero General Public License v3.0 (`LICENSE`): anyone may use, study, change and share it, and any modified version offered to others, including as a website, must share its source under the same licence. Third-party parts and their licences (chess.js, Stockfish, scalachess's game phases) are listed in `THIRD_PARTY.md`.
