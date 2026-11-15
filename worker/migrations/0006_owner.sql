-- The owner's tools (the server also does this itself: ensureReports, ensureFeedback, ensureKofi, cachedSearch):
-- positions hidden for everyone, Feedback messages, Ko-fi payments, Google's figures kept for the metrics.
CREATE TABLE IF NOT EXISTS hidden (a TEXT NOT NULL, key TEXT NOT NULL, fen TEXT, label TEXT, ts INTEGER NOT NULL, PRIMARY KEY (a, key)) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS feedback (id INTEGER PRIMARY KEY AUTOINCREMENT, ts INTEGER NOT NULL, did TEXT NOT NULL, msg TEXT NOT NULL, email TEXT, screen TEXT, lang TEXT, desk INTEGER, app INTEGER, done INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS kofi (id TEXT PRIMARY KEY, ts INTEGER NOT NULL, type TEXT, amount REAL, currency TEXT, sub INTEGER) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS search_cache (name TEXT NOT NULL, days INTEGER NOT NULL, ts INTEGER NOT NULL, data TEXT NOT NULL, PRIMARY KEY (name, days)) WITHOUT ROWID;
