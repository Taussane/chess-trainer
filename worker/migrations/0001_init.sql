-- Accounts and what each one keeps. See docs/accounts.md.
-- An account is ours; sites (Lichess now, Chess.com later) are connections to it.
CREATE TABLE accounts (
  id TEXT PRIMARY KEY,                 -- random id, never shown
  created_at INTEGER NOT NULL
);
CREATE TABLE connections (
  site TEXT NOT NULL,                  -- 'lichess', later 'chesscom'
  site_user_id TEXT NOT NULL,          -- the player's id on that site (Lichess: lowercase username)
  account_id TEXT NOT NULL REFERENCES accounts(id),
  username TEXT NOT NULL,              -- as the site spells it
  verified INTEGER NOT NULL,           -- 1: signed in through the site; 0: typed (public games only)
  added_at INTEGER NOT NULL,
  PRIMARY KEY (site, site_user_id)
);
CREATE INDEX connections_by_account ON connections(account_id);
-- Sign-ins already checked with the site, so not every request asks Lichess again (re-checked daily).
CREATE TABLE sessions (
  token_hash TEXT PRIMARY KEY,         -- SHA-256 of the site's token; the token itself is never stored
  account_id TEXT NOT NULL,
  site TEXT NOT NULL,
  checked_at INTEGER NOT NULL
);
CREATE TABLE results (
  account_id TEXT NOT NULL,
  ts INTEGER NOT NULL,                 -- when the position was played (ms)
  a TEXT NOT NULL,                     -- exercise
  data TEXT NOT NULL,                  -- the whole result as the app records it (JSON)
  PRIMARY KEY (account_id, ts, a)
);
CREATE TABLE games (
  account_id TEXT NOT NULL,
  id TEXT NOT NULL,                    -- Lichess id as is; other sites prefixed (cc-…)
  site TEXT NOT NULL,
  data TEXT NOT NULL,                  -- moves, evaluations, engine checks (JSON); positions are worked out again by the app
  updated_at INTEGER NOT NULL,
  PRIMARY KEY (account_id, id)
);
CREATE TABLE meta (
  account_id TEXT NOT NULL,
  name TEXT NOT NULL,                  -- profile, games-cleared, …
  data TEXT NOT NULL,
  PRIMARY KEY (account_id, name)
);
