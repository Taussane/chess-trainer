-- Anonymous usage counts (POST /api/ev): no account, no name; a random device id kept in the browser.
-- (The server also creates this table itself if missing: see ensureEvents.)
CREATE TABLE IF NOT EXISTS events (
  ts INTEGER NOT NULL,                 -- when (ms)
  day TEXT NOT NULL,                   -- YYYY-MM-DD (UTC)
  did TEXT NOT NULL,                   -- random device id (the browser's)
  sid TEXT NOT NULL,                   -- random id of one visit (page load)
  k TEXT NOT NULL,                     -- 'open' (a visit), 'pos' (a position finished), 'games' (own games found)
  a TEXT,                              -- exercise (pos)
  acc INTEGER,                         -- score 0-100 (pos)
  src TEXT,                            -- 'masters' | 'mine' (pos)
  auth TEXT,                           -- 'guest' | 'lichess' | 'google'
  cc INTEGER,                          -- Chess.com username connected (0/1)
  lang TEXT,                           -- 'en' | 'fr'
  app INTEGER,                         -- opened as the installed app (0/1)
  n1 INTEGER,                          -- pos: in the daily routine (0/1); games: own games
  n2 INTEGER                           -- games: positions found in them
);
CREATE INDEX IF NOT EXISTS events_day ON events(day);
CREATE INDEX IF NOT EXISTS events_did ON events(did);
