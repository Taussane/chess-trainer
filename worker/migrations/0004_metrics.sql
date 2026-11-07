-- The usage dashboard, cheaper to read (the server also does this itself: ensureEvents).
-- Each device's first day: new devices without going through every event kept.
CREATE TABLE IF NOT EXISTS devices (did TEXT PRIMARY KEY, first TEXT NOT NULL) WITHOUT ROWID;
-- The dashboard's figures, kept 10 minutes.
CREATE TABLE IF NOT EXISTS metrics_cache (days INTEGER PRIMARY KEY, ts INTEGER NOT NULL, data TEXT NOT NULL);
-- One write less per event: nothing needs it.
DROP INDEX IF EXISTS events_did;
