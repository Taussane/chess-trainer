-- Positions reported as doubtful from a review (POST /api/report): no account, no name; the random device id.
-- (The server also creates this table itself if missing: see ensureReports.)
CREATE TABLE IF NOT EXISTS reports (
  ts INTEGER NOT NULL,                 -- when (ms)
  did TEXT NOT NULL,                   -- random device id (the browser's)
  a TEXT NOT NULL,                     -- exercise
  key TEXT NOT NULL,                   -- the position's key in the app
  fen TEXT NOT NULL,                   -- the position
  src TEXT,                            -- 'masters' | 'mine'
  game TEXT,                           -- master game (g123) or own game id
  ply INTEGER,                         -- half-move in that game
  label TEXT,                          -- where it comes from, as the app shows it
  acc INTEGER,                         -- the reporter's score on it
  why TEXT                             -- 'three': the app itself found a Move selection position with only 3 moves to rank (GET /api/skips)
);
CREATE INDEX IF NOT EXISTS reports_key ON reports(a, key);
-- (why came later: the server adds it to an older table itself)
