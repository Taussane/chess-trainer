-- Short links for shared positions (?s=<id>): the server also does this itself (ensureShares).
CREATE TABLE IF NOT EXISTS shares (id TEXT PRIMARY KEY, code TEXT NOT NULL, ts INTEGER NOT NULL) WITHOUT ROWID;
