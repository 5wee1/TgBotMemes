CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS users (
    user_id     INTEGER PRIMARY KEY,
    username    TEXT,
    created_at  TEXT DEFAULT (datetime('now')),
    plan        TEXT DEFAULT 'free',
    credits_balance    INTEGER DEFAULT 0,
    daily_free_used    INTEGER DEFAULT 0,
    daily_reset_date   TEXT DEFAULT (date('now')),
    last_active_at     TEXT DEFAULT (datetime('now')),
    ref_code           TEXT UNIQUE,
    referred_by        INTEGER,
    is_banned          INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS memes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    query       TEXT,
    style       TEXT,
    prompt_hash TEXT,
    file_id     TEXT,
    image_url   TEXT,
    created_at  TEXT DEFAULT (datetime('now')),
    is_favorite INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS payments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    provider        TEXT,
    amount          INTEGER,
    currency        TEXT DEFAULT 'RUB',
    status          TEXT DEFAULT 'pending',
    payload_json    TEXT,
    created_at      TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER,
    event_type  TEXT,
    meta_json   TEXT,
    created_at  TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_memes_user_id ON memes(user_id);
CREATE INDEX IF NOT EXISTS idx_memes_favorite ON memes(user_id, is_favorite);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
"""
